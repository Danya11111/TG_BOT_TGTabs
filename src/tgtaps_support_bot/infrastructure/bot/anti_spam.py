from __future__ import annotations

import hashlib
import time

import aiosqlite


class GroupAntiSpam:
    def __init__(self, sqlite_path: str, ttl_sec: int):
        self.sqlite_path = sqlite_path
        self.ttl_sec = ttl_sec

    @staticmethod
    def _dedup_key(chat_id: int, question_norm: str) -> str:
        digest = hashlib.sha1(question_norm.encode("utf-8")).hexdigest()[:20]
        return f"{chat_id}:{digest}"

    async def should_answer(self, chat_id: int, question_norm: str) -> bool:
        now = int(time.time())
        dedup_key = self._dedup_key(chat_id, question_norm)
        expires_at = now + self.ttl_sec

        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.execute("DELETE FROM group_question_dedup WHERE expires_at_epoch < ?", (now,))
            cursor = await db.execute(
                "SELECT dedup_key FROM group_question_dedup WHERE dedup_key = ?",
                (dedup_key,),
            )
            exists = await cursor.fetchone()
            if exists:
                await db.commit()
                return False

            await db.execute(
                """
                INSERT INTO group_question_dedup (dedup_key, chat_id, question_norm, expires_at_epoch)
                VALUES (?, ?, ?, ?)
                """,
                (dedup_key, chat_id, question_norm, expires_at),
            )
            await db.commit()
            return True
