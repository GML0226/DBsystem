import asyncio
from sqlalchemy import text
from app.core.database import engine

async def verify_data():
    async with engine.connect() as conn:
        tables = ["LabMember", "Equipment", "Consumable", "ReservationRecord", "MaterialRequisition", "WarningLog"]
        
        print("--- Database Statistics ---")
        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"Table {table:20}: {count} records")
        
        print("\n--- Time Range Check ---")
        print("\n--- Consistency Check ---")
        min_qty_res = await conn.execute(text("SELECT MIN(quantity), name FROM Consumable"))
        min_qty, min_name = min_qty_res.fetchone()
        print(f"Minimum stock: {min_qty} (Item: {min_name})")
        if min_qty < 0:
            print("ERROR: Negative stock found!")
        else:
            print("SUCCESS: All stocks are non-negative.")

if __name__ == "__main__":
    asyncio.run(verify_data())
