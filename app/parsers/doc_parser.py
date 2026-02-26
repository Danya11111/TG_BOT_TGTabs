from __future__ import annotations

import hashlib
from collections import deque
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.parsers.normalize import normalize_text


def _same_site(base: str, candidate: str) -> bool:
    return urlparse(base).netloc == urlparse(candidate).netloc


def crawl_docs_to_articles(start_url: str, max_pages: int = 80, max_depth: int = 3) -> list[dict]:
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    visited: set[str] = set()
    pages: list[tuple[str, str]] = []

    with httpx.Client(timeout=10, follow_redirects=True) as client:
        while queue and len(visited) < max_pages:
            url, depth = queue.popleft()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                resp = client.get(url)
                if resp.status_code != 200 or "text/html" not in resp.headers.get("content-type", ""):
                    continue
            except httpx.HTTPError:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            title = (soup.title.get_text(strip=True) if soup.title else "").strip()
            body = soup.get_text(" ", strip=True)
            pages.append((url, f"{title}\n{body[:2400]}"))

            if depth == max_depth:
                continue
            for a in soup.select("a[href]"):
                href = a.get("href", "").strip()
                if not href or href.startswith("#"):
                    continue
                nxt = urljoin(url, href)
                if _same_site(start_url, nxt):
                    queue.append((nxt, depth + 1))

    return _pages_to_articles(pages)


def _pages_to_articles(pages: list[tuple[str, str]]) -> list[dict]:
    items: list[dict] = []
    for url, text in pages:
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        if not lines:
            continue
        title = lines[0]
        summary = " ".join(lines[1:4])[:280] if len(lines) > 1 else title
        question = f"Как работает: {title}?"
        q_norm = normalize_text(question)
        aid = "doc_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        items.append(
            {
                "id": aid,
                "question": question,
                "question_norm": q_norm,
                "summary": summary or title,
                "steps": [
                    "Откройте раздел документации по ссылке ниже.",
                    "Сверьте настройки с примером из документации.",
                    "Проверьте связанные блоки и параметры в вашем Mini App.",
                ],
                "docs_links": [{"title": title[:120], "url": url}],
                "video_links": [],
                "category": "docs",
                "tags": ["docs", "guide"],
                "aliases": [normalize_text(title), q_norm],
                "related_ids": [],
                "answer_version": 1,
                "status": "active",
                "source": "docs",
            }
        )
    return items
