from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.search.search_engine import SearchResult


def disambiguation_keyboard(results: list[SearchResult]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for result in results[:4]:
        title = result.row["question"][:64]
        builder.button(text=title, callback_data=f"pick:{result.row['id']}")
    builder.adjust(1)
    return builder.as_markup()


def category_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in ("wallet", "payments", "referrals", "tasks", "analytics", "general"):
        builder.button(text=item.capitalize(), callback_data=f"cat:{item}")
    builder.adjust(2)
    return builder.as_markup()
