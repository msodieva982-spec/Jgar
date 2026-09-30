"""Payment boundary.

Do not grant PRO from an unverified client callback.
For Telegram Stars or another provider, verify the provider's successful payment/update,
store a unique provider payment id, then call grant_pro().
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from db import Session, User, Payment, Subscription

async def grant_pro(user_id:int, days:int, provider:str, provider_id:str, amount:int=0, currency:str="XTR"):
    now=datetime.now(timezone.utc)
    async with Session() as s:
        existing=(await s.execute(select(Payment).where(Payment.provider_id==provider_id))).scalar_one_or_none()
        if existing:
            return False
        u=(await s.execute(select(User).where(User.id==user_id))).scalar_one_or_none()
        if not u: return False
        base=max(u.pro_until or now,now)
        until=base+timedelta(days=days)
        u.is_pro=True; u.pro_until=until
        s.add(Payment(user_id=user_id,provider=provider,provider_id=provider_id,amount=amount,currency=currency,status="paid"))
        s.add(Subscription(user_id=user_id,plan="paid",started_at=now,expires_at=until,status="active",payment_id=provider_id))
        await s.commit()
        return True
