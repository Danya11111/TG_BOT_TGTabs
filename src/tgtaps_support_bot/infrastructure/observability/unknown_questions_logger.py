from __future__ import annotations

import aiosqlite

from tgtaps_support_bot.infrastructure.persistence.sqlite_gateway import utc_now_iso
from tgtaps_support_bot.domain.value_objects.text_normalization import normalize_text


class UnknownQuestionsLogger:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

    async def log(
        self,
        *,
        user_id: int | None,
        chat_id: int | None,
        is_group: bool,
        question: str,
        category_hint: str | None = None,
    ) -> None:
        sql = """
        INSERT INTO kb_unknown_questions (
            user_id, chat_id, is_group, question, question_norm, category_hint, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_id,
            chat_id,
            1 if is_group else 0,
            question.strip(),
            normalize_text(question),
            category_hint,
            utc_now_iso(),
        )
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.execute(sql, params)
            await db.commit()
