from __future__ import annotations

import logging
from collections import defaultdict

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import category_keyboard, disambiguation_keyboard
from app.db import (
    get_analytics_snapshot,
    get_article_by_id,
    get_user_last_answer,
    log_query_event,
    set_user_last_answer,
)
from app.formatters.analytics_formatter import format_analytics
from app.formatters.response_formatter import format_full_answer, format_group_answer
from app.observability.unknown_questions_logger import UnknownQuestionsLogger
from app.search.search_engine import SearchEngine

log = logging.getLogger(__name__)


class HandlerBundle:
    def __init__(
        self,
        *,
        sqlite_path: str,
        bot_username: str,
        search_engine: SearchEngine,
        anti_spam,
        unknown_logger: UnknownQuestionsLogger,
        min_confidence: float,
        ambiguity_delta: float,
        owner_ids: set[int],
    ):
        self.sqlite_path = sqlite_path
        self.bot_username = bot_username
        self.search_engine = search_engine
        self.anti_spam = anti_spam
        self.unknown_logger = unknown_logger
        self.min_confidence = min_confidence
        self.ambiguity_delta = ambiguity_delta
        self.owner_ids = owner_ids
        self.pending_results: dict[int, list] = defaultdict(list)

    def create_router(self) -> Router:
        router = Router()

        @router.message(F.chat.type == "private", Command("analitics", "analytics"))
        async def owner_analytics(message: Message) -> None:
            user_id = message.from_user.id if message.from_user else 0
            if user_id not in self.owner_ids:
                await message.answer("Команда доступна только владельцу бота.")
                return
            snapshot = await get_analytics_snapshot(self.sqlite_path, window_days=30)
            await message.answer(format_analytics(snapshot))

        @router.message(F.chat.type == "private", F.text)
        async def private_message(message: Message) -> None:
            question = (message.text or "").strip()
            if not question:
                return
            if question.startswith("/"):
                return
            await self._handle_private_question(message, question)

        @router.callback_query(F.data.startswith("pick:"))
        async def callback_pick(callback: CallbackQuery) -> None:
            if not callback.from_user:
                return
            article_id = callback.data.split(":", 1)[1]
            row = await get_article_by_id(self.sqlite_path, article_id)
            if not row:
                await callback.answer("Ответ устарел. Задайте вопрос заново.", show_alert=True)
                return
            last = await get_user_last_answer(self.sqlite_path, callback.from_user.id)
            text = format_full_answer(row, [], previous_article_id=last["article_id"] if last else None)
            await callback.message.answer(text, disable_web_page_preview=True)
            await set_user_last_answer(self.sqlite_path, callback.from_user.id, row["id"], row["question_norm"])
            await log_query_event(
                self.sqlite_path,
                user_id=callback.from_user.id,
                chat_id=callback.message.chat.id if callback.message else None,
                is_group=False,
                question=f"[pick] {row['question']}",
                question_norm=row["question_norm"],
                matched_article_id=row["id"],
                score=100.0,
                match_reason="manual_pick",
                category=row.get("category"),
            )
            await callback.answer("Готово")

        @router.callback_query(F.data.startswith("cat:"))
        async def callback_category(callback: CallbackQuery) -> None:
            category = callback.data.split(":", 1)[1]
            results = self.search_engine.search(category, category_hint=category)
            if not results:
                await callback.answer("В этой категории пока мало данных.", show_alert=True)
                return
            top = results[0]
            text = format_full_answer(top.row, results[1:])
            await callback.message.answer(text, disable_web_page_preview=True)
            if callback.from_user:
                await set_user_last_answer(
                    self.sqlite_path,
                    callback.from_user.id,
                    top.row["id"],
                    top.row["question_norm"],
                )
                await log_query_event(
                    self.sqlite_path,
                    user_id=callback.from_user.id,
                    chat_id=callback.message.chat.id if callback.message else None,
                    is_group=False,
                    question=f"[category:{category}]",
                    question_norm=top.row["question_norm"],
                    matched_article_id=top.row["id"],
                    score=top.score,
                    match_reason=top.reason,
                    category=top.row.get("category"),
                )
            await callback.answer("Показал ответ")

        @router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
        async def group_message(message: Message) -> None:
            question = (message.text or "").strip()
            if not question:
                return
            if question.startswith("/"):
                return

            norm = self.search_engine.normalize(question)
            if not await self.anti_spam.should_answer(message.chat.id, norm):
                return

            results = self.search_engine.search(question)
            if not results or results[0].score < self.min_confidence:
                await log_query_event(
                    self.sqlite_path,
                    user_id=message.from_user.id if message.from_user else None,
                    chat_id=message.chat.id,
                    is_group=True,
                    question=question,
                    question_norm=norm,
                    matched_article_id=None,
                    score=None,
                    match_reason="not_found",
                    category=None,
                )
                await self.unknown_logger.log(
                    user_id=message.from_user.id if message.from_user else None,
                    chat_id=message.chat.id,
                    is_group=True,
                    question=question,
                )
                return

            short = format_group_answer(results[0].row["summary"], self.bot_username)
            await message.reply(short, disable_web_page_preview=True)
            await log_query_event(
                self.sqlite_path,
                user_id=message.from_user.id if message.from_user else None,
                chat_id=message.chat.id,
                is_group=True,
                question=question,
                question_norm=norm,
                matched_article_id=results[0].row["id"],
                score=results[0].score,
                match_reason=results[0].reason,
                category=results[0].row.get("category"),
            )

        return router

    async def _handle_private_question(self, message: Message, question: str) -> None:
        results = self.search_engine.search(question)
        norm = self.search_engine.normalize(question)
        if not results or results[0].score < self.min_confidence:
            await log_query_event(
                self.sqlite_path,
                user_id=message.from_user.id if message.from_user else None,
                chat_id=message.chat.id,
                is_group=False,
                question=question,
                question_norm=norm,
                matched_article_id=None,
                score=None,
                match_reason="not_found",
                category=None,
            )
            await self.unknown_logger.log(
                user_id=message.from_user.id if message.from_user else None,
                chat_id=message.chat.id,
                is_group=False,
                question=question,
            )
            await message.answer(
                "Не нашёл точный ответ. Выберите категорию, и я уточню контекст:",
                reply_markup=category_keyboard(),
            )
            return

        if len(results) > 1 and (results[0].score - results[1].score) < self.ambiguity_delta:
            uid = message.from_user.id if message.from_user else 0
            self.pending_results[uid] = results[:4]
            await log_query_event(
                self.sqlite_path,
                user_id=message.from_user.id if message.from_user else None,
                chat_id=message.chat.id,
                is_group=False,
                question=question,
                question_norm=norm,
                matched_article_id=None,
                score=results[0].score,
                match_reason="ambiguous",
                category=None,
            )
            await message.answer(
                "Нашёл несколько близких вариантов. Уточните запрос:",
                reply_markup=disambiguation_keyboard(results),
            )
            return

        chosen = results[0]
        last = await get_user_last_answer(self.sqlite_path, message.from_user.id if message.from_user else 0)
        text = format_full_answer(chosen.row, results[1:], previous_article_id=last["article_id"] if last else None)
        await message.answer(text, disable_web_page_preview=True)
        await log_query_event(
            self.sqlite_path,
            user_id=message.from_user.id if message.from_user else None,
            chat_id=message.chat.id,
            is_group=False,
            question=question,
            question_norm=norm,
            matched_article_id=chosen.row["id"],
            score=chosen.score,
            match_reason=chosen.reason,
            category=chosen.row.get("category"),
        )
        if message.from_user:
            await set_user_last_answer(self.sqlite_path, message.from_user.id, chosen.row["id"], chosen.row["question_norm"])
        log.info("Answered private question with article_id=%s reason=%s", chosen.row["id"], chosen.reason)
