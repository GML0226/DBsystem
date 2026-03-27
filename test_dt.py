import asyncio
from app.core.database import get_db
from sqlalchemy.future import select
from app.models.models import ReservationRecord
from datetime import datetime, timezone
import dateutil.parser

async def main():
    async for db in get_db():
        # Suppose FastAPI parsed Z to aware datetime
        dt_aware = dateutil.parser.isoparse("2026-03-27T00:00:00.000Z")
        print("Param:", dt_aware)
        
        stmt = select(ReservationRecord).where(ReservationRecord.start_time >= dt_aware)
        res = await db.execute(stmt)
        print("Count:", len(res.scalars().all()))
        break

if __name__ == '__main__':
    asyncio.run(main())
