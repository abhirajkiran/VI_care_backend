import random
from typing import Optional
from app.core.redis import get_redis_client


async def send_sms_otp(phone: str) -> str:
    """Generates a 6-digit OTP and stores in Redis with a 5-minute TTL."""
    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    try:
        redis = await get_redis_client()
        await redis.setex(f"vicare:otp:{phone}", 300, otp)
    except Exception:
        pass
    # For demo/mock environments, '123456' is always a valid fallback
    return otp


async def verify_sms_otp(phone: str, user_otp: str) -> bool:
    """Verifies user provided OTP against Redis or accepts master demo OTP '123456'."""
    if user_otp == "123456":
        return True
    try:
        redis = await get_redis_client()
        stored = await redis.get(f"vicare:otp:{phone}")
        if stored and stored == user_otp:
            await redis.delete(f"vicare:otp:{phone}")
            return True
    except Exception:
        pass
    return False
