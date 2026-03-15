"""Parser for Kindle vocab.db files."""

import sqlite3
from dataclasses import dataclass


@dataclass
class VocabEntry:
    word: str
    stem: str
    usage: str
    book_title: str
    book_authors: str
    book_asin: str
    book_lang: str
    lookup_time: int
    lookup_count: int


def parse_vocab_db(db_path: str) -> list[VocabEntry]:
    """Parse a Kindle vocab.db file and extract vocabulary entries.

    The Kindle vocab.db has the following schema:
    - WORDS: id, word, stem, lang, category, timestamp, profileid
    - LOOKUPS: id, word_key, book_key, dict_key, pos, usage, timestamp
    - BOOK_INFO: id, asin, guid, lang, title, authors
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT
                w.word,
                w.stem,
                l.usage,
                COALESCE(b.title, 'Unknown') AS book_title,
                COALESCE(b.authors, '') AS book_authors,
                COALESCE(b.asin, '') AS book_asin,
                COALESCE(b.lang, '') AS book_lang,
                l.timestamp AS lookup_time,
                COUNT(*) OVER (PARTITION BY w.word) AS lookup_count
            FROM LOOKUPS l
            LEFT JOIN WORDS w ON l.word_key = w.id
            LEFT JOIN BOOK_INFO b ON l.book_key = b.id
            WHERE w.word IS NOT NULL
            ORDER BY l.timestamp DESC
            """,
        ).fetchall()

        entries = []
        for row in rows:
            entries.append(
                VocabEntry(
                    word=row["word"],
                    stem=row["stem"] or row["word"],
                    usage=row["usage"] or "",
                    book_title=row["book_title"],
                    book_authors=row["book_authors"],
                    book_asin=row["book_asin"],
                    book_lang=row["book_lang"],
                    lookup_time=row["lookup_time"] or 0,
                    lookup_count=row["lookup_count"],
                )
            )
        return entries
    finally:
        conn.close()
