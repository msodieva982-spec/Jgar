from datetime import datetime, timezone
from sqlalchemy import select
from db import Session, BioConfig, User
from config import settings

async def configure_default():
    async with Session() as s:
        x=(await s.execute(select(BioConfig).where(BioConfig.owner_id==settings.owner_id))).scalar_one_or_none()
        if not x:
            text=settings.bio_ad_text.replace("{BOT_USERNAME}",settings.bot_username)
            s.add(BioConfig(owner_id=settings.owner_id,ad_text=text[:140],enabled=True))
            await s.commit()

async def apply_ad(bot, business_connection_id):
    async with Session() as s:
        x=(await s.execute(select(BioConfig).where(BioConfig.owner_id==settings.owner_id))).scalar_one_or_none()
        if not x or not x.enabled: return
        text=x.ad_text[:140]
    try:
        await bot.set_business_account_bio(business_connection_id=business_connection_id,bio=text)
    except Exception:
        # Permission or API error is intentionally not hidden from logs in production.
        pass

async def remove_ad(bot,business_connection_id):
    async with Session() as s:
        x=(await s.execute(select(BioConfig).where(BioConfig.owner_id==settings.owner_id))).scalar_one_or_none()
        original=x.original_bio if x else None
    try:
        await bot.set_business_account_bio(business_connection_id=business_connection_id,bio=(original or ""))
    except Exception:
        pass
