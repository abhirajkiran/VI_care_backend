from datetime import date
import random
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import get_redis_client
from app.models.appointment import Appointment


async def generate_token(db: AsyncSession, doctor_id: str, visit_date: date) -> tuple[str, int]:
    """Generates an atomic sequential daily token (e.g. 'A-01', 'A-14')."""
    try:
        redis = await get_redis_client()
        key = f"vicare:tokens:{doctor_id}:{visit_date.isoformat()}"
        seq = await redis.incr(key)
        if seq == 1:
            await redis.expire(key, 172800)  # Expire after 48 hours
        token_str = f"A-{seq:02d}"
        return token_str, seq
    except Exception:
        # Fallback to database count if Redis is offline
        stmt = (
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == visit_date,
            )
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        seq = count + 1
        return f"A-{seq:02d}", seq
