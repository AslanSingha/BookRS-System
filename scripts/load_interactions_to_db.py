"""Load UCSD interactions from parquet into PostgreSQL interactions table."""
import asyncio
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal, init_db
from app.models.interaction import Interaction

async def load_interactions():
    print("Loading interactions parquet...")
    df = pd.read_parquet(
        Path.home() / "projects/BookRS-DataPrep/outputs/bookrs_ucsd_interactions.parquet"
    )
    print(f"Total interactions: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print(df.head(3))

    await init_db()

    async with AsyncSessionLocal() as session:
        print("Inserting interactions in batches of 10,000...")
        batch_size = 10000
        total = 0
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            interactions = [
                Interaction(
                    user_id=str(row.user_id),
                    book_id=str(row.book_id),
                    rating=int(row.rating),
                    is_reviewed=int(row.is_reviewed) if hasattr(row, 'is_reviewed') and pd.notna(row.is_reviewed) else 0,
                )
                for _, row in batch.iterrows()
            ]
            session.add_all(interactions)
            await session.commit()
            total += len(interactions)
            if total % 500000 == 0:
                print(f"  Inserted {total:,} / {len(df):,} interactions...")

        print(f"Done! {total:,} interactions loaded into PostgreSQL")

asyncio.run(load_interactions())
