from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.env.settings import get_settings
from tgtaps_support_bot.domain.value_objects.text_normalization import looks_like_question, normalize_text


THEME_RULES: list[dict[str, Any]] = [
    {
        "title": "Ошибки и поломки",
        "description": "Вопросы про неработающие функции, баги и сообщения об ошибках.",
        "keywords": (
            "не работает",
            "ошибка",
            "сломал",
            "падает",
            "баг",
            "проблем",
            "пофикс",
            "fix",
        ),
    },
    {
        "title": "UI и вёрстка",
        "description": "Настройка отображения экранов: размеры, отступы, картинки, iframe, адаптив.",
        "keywords": (
            "экран",
            "кнопк",
            "отступ",
            "размер",
            "ширин",
            "высот",
            "адапт",
            "вёрст",
            "верст",
            "дизайн",
            "интерфейс",
            "картин",
            "фон",
            "iframe",
            "айфрейм",
            "зум",
        ),
    },
    {
        "title": "Экономика и баланс",
        "description": "Логика поинтов/монет, фарминг, клейм, награды, уровни и игровой баланс.",
        "keywords": (
            "баланс",
            "монет",
            "поинт",
            "points",
            "фарм",
            "клейм",
            "наград",
            "аирдроп",
            "уров",
            "реф",
            "рефера",
            "тап",
            "энерг",
        ),
    },
    {
        "title": "Интеграции и внешние сервисы",
        "description": "Подключение платежей, ботов, API, кошельков и внешних платформ.",
        "keywords": (
            "робокасс",
            "оплат",
            "платеж",
            "wallet",
            "кошел",
            "api",
            "webhook",
            "бот",
            "telegram",
            "mini app",
            "tma",
            "домен",
            "хост",
            "сервер",
        ),
    },
    {
        "title": "Публикация и доступы",
        "description": "Публикация приложения, права доступа, модерация и проверка настроек запуска.",
        "keywords": (
            "опубликов",
            "публик",
            "доступ",
            "прав",
            "роль",
            "модерац",
            "вериф",
            "primary page",
            "настро",
            "запуск",
        ),
    },
    {
        "title": "Сценарии и логика приложения",
        "description": "Как реализовать фичу: переходы, условия, формы, навигация, пользовательские сценарии.",
        "keywords": (
            "как сделать",
            "можно ли",
            "реализовать",
            "логик",
            "сценар",
            "услов",
            "переход",
            "страниц",
            "меню",
            "форм",
            "онборд",
            "шаг",
        ),
    },
    {
        "title": "Контент, обучение и документация",
        "description": "Вопросы про шаблоны, гайды, обучающие материалы и примеры реализации.",
        "keywords": (
            "док",
            "докум",
            "гайд",
            "инструкц",
            "видео",
            "урок",
            "обуч",
            "пример",
            "шаблон",
            "заготов",
        ),
    },
]


@dataclass
class Msg:
    msg_id: str
    author: str
    author_norm: str
    text: str
    reply_ref: str | None
    source_file: str
    order: int


def extract_messages(html_path: Path) -> list[Msg]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    out: list[Msg] = []
    for idx, msg in enumerate(soup.select("div.message.default.clearfix")):
        msg_id = msg.get("id", "")
        text_node = msg.select_one("div.text")
        from_node = msg.select_one("div.from_name")
        if not text_node or not from_node:
            continue
        reply_node = msg.select_one("div.reply_to.details a")
        reply_ref = None
        if reply_node and reply_node.get("href", "").startswith("#go_to_message"):
            reply_ref = reply_node.get("href", "").replace("#go_to_message", "message")
        author = from_node.get_text(" ", strip=True)
        out.append(
            Msg(
                msg_id=msg_id,
                author=author,
                author_norm=author.strip().lower().lstrip("@"),
                text=text_node.get_text(" ", strip=True),
                reply_ref=reply_ref,
                source_file=html_path.as_posix(),
                order=idx,
            )
        )
    return out


def collect_pairs(messages: list[Msg], support_names: set[str]) -> list[dict[str, Any]]:
    by_id: dict[str, Msg] = {m.msg_id: m for m in messages if m.msg_id}
    replies_to: dict[str, list[Msg]] = defaultdict(list)
    for m in messages:
        if m.reply_ref:
            replies_to[m.reply_ref].append(m)

    pairs: list[dict[str, Any]] = []
    seen_questions: set[str] = set()

    for m in messages:
        if not looks_like_question(m.text):
            continue
        if m.author_norm in support_names:
            continue

        q_norm = normalize_text(m.text)
        if q_norm in seen_questions:
            continue

        answer: Msg | None = None

        # 1) Direct support reply to this message
        for cand in replies_to.get(m.msg_id, []):
            if cand.author_norm in support_names and not looks_like_question(cand.text):
                answer = cand
                break

        # 2) If user replied to something, find support reply to parent
        if not answer and m.reply_ref:
            parent = by_id.get(m.reply_ref)
            if parent:
                for cand in replies_to.get(parent.msg_id, []):
                    if cand.author_norm in support_names and not looks_like_question(cand.text):
                        answer = cand
                        break

        # 3) Fallback: any non-question reply by different author
        if not answer:
            for cand in replies_to.get(m.msg_id, []):
                if cand.author_norm == m.author_norm:
                    continue
                if looks_like_question(cand.text):
                    continue
                answer = cand
                break

        if not answer:
            continue

        seen_questions.add(q_norm)
        pairs.append(
            {
                "question": m.text,
                "question_norm": q_norm,
                "question_author": m.author,
                "answer": answer.text,
                "answer_author": answer.author,
                "is_support_answer": answer.author_norm in support_names,
                "question_message_id": m.msg_id,
                "answer_message_id": answer.msg_id,
                "source_file": m.source_file,
            }
        )
    return pairs


def _pick_theme(question_norm: str) -> str:
    for rule in THEME_RULES:
        for kw in rule["keywords"]:
            if kw in question_norm:
                return rule["title"]
    return "Прочее"


def _is_noise_like_question(question: str) -> bool:
    qn = normalize_text(question)
    if len(qn) > 320:
        return True
    if "youtube" in qn or "rutube" in qn:
        return True
    if "http://" in qn or "https://" in qn:
        return True
    if question.count(" - ") >= 4:
        return True
    return False


def _pick_examples(items: list[dict[str, Any]], limit: int = 2) -> list[str]:
    examples: list[str] = []
    for x in items:
        q = x["question"].strip()
        if _is_noise_like_question(q):
            continue
        examples.append(q)
        if len(examples) >= limit:
            break
    if len(examples) < limit:
        for x in items:
            q = x["question"].strip()
            if q in examples:
                continue
            examples.append(q)
            if len(examples) >= limit:
                break
    return examples


def build_theme_summary(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_theme: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in pairs:
        theme = _pick_theme(p["question_norm"])
        by_theme[theme].append(p)

    total = len(pairs) or 1
    ordered_titles = [r["title"] for r in THEME_RULES] + ["Прочее"]
    details = {r["title"]: r["description"] for r in THEME_RULES}
    details["Прочее"] = "Разные точечные запросы, которые не легли в крупные кластеры."

    out: list[dict[str, Any]] = []
    for title in ordered_titles:
        items = by_theme.get(title, [])
        if not items:
            continue
        examples = _pick_examples(items, limit=2)
        out.append(
            {
                "title": title,
                "description": details[title],
                "count": len(items),
                "share": len(items) / total * 100,
                "examples": examples,
            }
        )
    out.sort(key=lambda x: x["count"], reverse=True)
    return out


def write_report(
    files: list[Path],
    messages: list[Msg],
    pairs: list[dict[str, Any]],
    output_md: Path,
) -> None:
    authors = [m.author for m in messages]
    question_msgs = [m for m in messages if looks_like_question(m.text)]
    answer_lengths = [len(p["answer"]) for p in pairs]
    support_pairs = [p for p in pairs if p["is_support_answer"]]

    top_askers = Counter(p["question_author"] for p in pairs).most_common(10)
    top_responders = Counter(p["answer_author"] for p in pairs).most_common(10)
    themes = build_theme_summary(pairs)

    avg_ans = statistics.mean(answer_lengths) if answer_lengths else 0
    med_ans = statistics.median(answer_lengths) if answer_lengths else 0
    answer_rate = (len(pairs) / len(question_msgs) * 100) if question_msgs else 0.0
    support_rate = (len(support_pairs) / len(pairs) * 100) if pairs else 0.0

    lines: list[str] = []
    lines.append("# Аналитика групповых переписок")
    lines.append("")
    lines.append("## Сводка")
    lines.append("")
    lines.append(f"- Файлов экспорта: **{len(files)}**")
    lines.append(f"- Всего сообщений: **{len(messages)}**")
    lines.append(f"- Уникальных авторов: **{len(set(authors))}**")
    lines.append(f"- Сообщений, похожих на вопросы: **{len(question_msgs)}**")
    lines.append(f"- Извлечено Q/A-пар: **{len(pairs)}**")
    lines.append(f"- Доля вопросов с найденным ответом: **{answer_rate:.1f}%**")
    lines.append(f"- Ответы от support-аккаунтов среди Q/A: **{support_rate:.1f}%**")
    lines.append(f"- Средняя длина ответа: **{avg_ans:.1f}** символов")
    lines.append(f"- Медианная длина ответа: **{med_ans:.1f}** символов")
    lines.append("")
    lines.append("## Топ авторов вопросов")
    lines.append("")
    for name, count in top_askers:
        lines.append(f"- {name}: {count}")
    if not top_askers:
        lines.append("- Нет данных")
    lines.append("")
    lines.append("## Топ авторов ответов")
    lines.append("")
    for name, count in top_responders:
        lines.append(f"- {name}: {count}")
    if not top_responders:
        lines.append("- Нет данных")
    lines.append("")
    lines.append("## Ключевые темы запросов")
    lines.append("")
    for theme in themes[:8]:
        lines.append(
            f"- **{theme['title']}** — {theme['count']} вопросов ({theme['share']:.1f}%). {theme['description']}"
        )
        for ex in theme["examples"]:
            lines.append(f"  - Пример: «{ex[:180]}»")
    if not themes:
        lines.append("- Нет данных")
    lines.append("")
    lines.append("## Комментарий")
    lines.append("")
    lines.append(
        "- Q/A-пары собраны автоматически по reply-связям и эвристикам вопроса; "
        "часть диалогов без reply может не попасть в выборку."
    )
    lines.append(
        "- Рекомендуется просмотреть `data/group_qa_pairs.csv` и дополнять FAQ по темам "
        "с наибольшей частотой."
    )
    output_md.write_text("\n".join(lines), encoding="utf-8")


def write_qa_markdown(pairs: list[dict[str, Any]], output_md: Path) -> None:
    lines: list[str] = []
    lines.append("# Вопросы и ответы из групповых переписок")
    lines.append("")
    lines.append(f"Всего пар: **{len(pairs)}**")
    lines.append("")
    for idx, p in enumerate(pairs, start=1):
        lines.append(f"## {idx}. Вопрос")
        lines.append("")
        lines.append(p["question"])
        lines.append("")
        lines.append(f"- Автор вопроса: {p['question_author']}")
        lines.append(f"- Источник: `{p['source_file']}`")
        lines.append("")
        lines.append("### Ответ")
        lines.append("")
        lines.append(p["answer"])
        lines.append("")
        lines.append(f"- Автор ответа: {p['answer_author']}")
        lines.append("")
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build question-answer file and analytics from Telegram HTML exports."
    )
    parser.add_argument("--export-dir", default="data/raw_exports", help="Directory to scan for messages*.html")
    parser.add_argument("--out-dir", default="data/generated", help="Output directory")
    args = parser.parse_args()

    load_dotenv()
    settings = get_settings()
    support_names = settings.support_usernames_set

    export_root = Path(args.export_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(export_root.rglob("messages*.html"))
    messages: list[Msg] = []
    for f in files:
        messages.extend(extract_messages(f))

    pairs = collect_pairs(messages, support_names)

    qa_json = out_dir / "group_qa_pairs.json"
    qa_csv = out_dir / "group_qa_pairs.csv"
    qa_md = out_dir / "group_qa.md"
    report_md = out_dir / "group_chat_analytics.md"

    qa_json.write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    with qa_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "question",
                "question_author",
                "answer",
                "answer_author",
                "is_support_answer",
                "source_file",
                "question_message_id",
                "answer_message_id",
            ],
        )
        writer.writeheader()
        for row in pairs:
            writer.writerow(
                {
                    "question": row["question"],
                    "question_author": row["question_author"],
                    "answer": row["answer"],
                    "answer_author": row["answer_author"],
                    "is_support_answer": row["is_support_answer"],
                    "source_file": row["source_file"],
                    "question_message_id": row["question_message_id"],
                    "answer_message_id": row["answer_message_id"],
                }
            )

    write_report(files, messages, pairs, report_md)
    write_qa_markdown(pairs, qa_md)

    print(f"Exports scanned: {len(files)}")
    print(f"Messages parsed: {len(messages)}")
    print(f"Q/A pairs written: {len(pairs)}")
    print(f"Q/A JSON: {qa_json}")
    print(f"Q/A CSV: {qa_csv}")
    print(f"Q/A Markdown: {qa_md}")
    print(f"Analytics report: {report_md}")


if __name__ == "__main__":
    main()
