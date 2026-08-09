"""
Export the deduplicated books table from PostgreSQL to the
project-relative parquet file that recommender.py reads at
startup (settings.books_path).

Must run AFTER entity_resolution.py and BEFORE starting the
backend (or encode_books.py, which reads books directly from
PostgreSQL and does not need this file -- but the running
FastAPI app does).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.config import settings


async def export_books():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT book_id, title, authors, description, "
                "genre, avg_rating, ratings_count, isbn13, image_url "
                "FROM books ORDER BY book_id"
            )
        )
        rows = result.fetchall()
        df = pd.DataFrame(
            rows,
            columns=[
                "book_id", "title", "authors", "description",
                "genre", "avg_rating", "ratings_count", "isbn13", "image_url",
            ],
        )
        print(f"Exporting {len(df):,} books to {settings.books_path}")
        settings.books_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(settings.books_path, index=False)
        print("Done")


if __name__ == "__main__":
    asyncio.run(export_books())
