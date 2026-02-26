import re
from html import unescape


PUNCT_RE = re.compile(r"[^\w\s#@:/.-]+", re.UNICODE)
SPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = unescape(text or "")
    text = text.lower().strip()
    text = PUNCT_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text)
    return text.strip()


QUESTION_HINT_RE = re.compile(
    r"(\?$|^как\b|^почему\b|^зачем\b|^где\b|^что\b|не работает|ошибка|проблема|как сделать)",
    re.IGNORECASE,
)


def looks_like_question(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 6:
        return False
    return bool(QUESTION_HINT_RE.search(t))
