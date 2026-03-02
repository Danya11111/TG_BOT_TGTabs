from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgtaps_support_bot.domain.services.search_engine import SearchResult


TOPIC_LABELS = {
    "wallet": "Wallet и TON",
    "payments": "Платежи и Stars",
    "referrals": "Рефералы",
    "tasks": "Задания и сценарии",
    "analytics": "Аналитика",
    "general": "Общие вопросы",
    "community": "Примеры из чата",
}


def category_label(category: str | None) -> str:
    if not category:
        return "Другая тема"
    return TOPIC_LABELS.get(category, category.capitalize())


def disambiguation_keyboard(results: list[SearchResult]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    seen_categories: set[str] = set()
    for result in results[:6]:
        category = result.row.get("category") or "general"
        if category in seen_categories:
            continue
        seen_categories.add(category)
        builder.button(text=category_label(category), callback_data=f"cat:{category}")
        if len(seen_categories) >= 4:
            break
    if not seen_categories:
        for result in results[:4]:
            title = result.row["question"][:64]
            builder.button(text=title, callback_data=f"pick:{result.row['id']}")
    builder.adjust(1)
    return builder.as_markup()


def category_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in ("wallet", "payments", "referrals", "tasks", "analytics", "general"):
        builder.button(text=category_label(item), callback_data=f"cat:{item}")
    builder.adjust(2)
    return builder.as_markup()
