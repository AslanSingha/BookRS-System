"""Load books from parquet into PostgreSQL"""
import asyncio
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal, init_db
from app.models.book import Book

async def load_books():
    print("Loading books parquet...")
    df = pd.read_parquet(
        Path.home() / "projects/BookRS-DataPrep/outputs/bookrs_ucsd_books.parquet"
    )
    print(f"Total books: {len(df):,}")

    await init_db()

    async with AsyncSessionLocal() as session:
        print("Inserting books in batches of 5,000...")
        batch_size = 5000
        total = 0
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            books = [
                Book(
                    book_id=str(row.book_id),
                    title=str(row.title)[:500],
                    authors=str(row.authors)[:500],
                    description=str(row.description)[:5000] if pd.notna(row.description) else None,
                    genre=str(row.genre) if pd.notna(row.genre) else None,
                    avg_rating=float(row.avg_rating) if pd.notna(row.avg_rating) else 0.0,
                    ratings_count=int(row.ratings_count) if pd.notna(row.ratings_count) else 0,
                    isbn13=str(row.isbn13) if pd.notna(row.isbn13) else None,
                    image_url=str(row.image_url) if pd.notna(row.image_url) else None,
                )
                for _, row in batch.iterrows()
            ]
            session.add_all(books)
            await session.commit()
            total += len(books)
            if total % 50000 == 0:
                print(f"  Inserted {total:,} / {len(df):,} books...")

        print(f"Done! {total:,} books loaded into PostgreSQL")

asyncio.run(load_books())
