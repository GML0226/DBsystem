import asyncio
from app.api.dashboard import get_consumable_ranking
from app.core.database import SessionLocal

async def test_api():
    async with SessionLocal() as db:
        print("Testing 30 days:")
        res_30 = await get_consumable_ranking(days=30, db=db)
        print(f"Result count: {len(res_30)}")
        
        print("\nTesting 365 days:")
        res_365 = await get_consumable_ranking(days=365, db=db)
        print(f"Result count: {len(res_365)}")

if __name__ == "__main__":
    asyncio.run(test_api())
