from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from services import get_or_create_user, is_pro, has_permission, stats, refresh_expired
from db import Session, RequiredChannel, User, PromoCode, PromoUse
from sqlalchemy import select
from config import settings

router=Router()

async def subscribed(bot, user_id):
    async with Session() as s:
        channels=(await s.execute(select(RequiredChannel).where(RequiredChannel.enabled==True))).scalars().all()
    for c in channels:
        try:
            member=await bot.get_chat_member(c.chat_id,user_id)
            if member.status in ("left","kicked"): return False
        except Exception:
            return False
    return True

@router.message(CommandStart())
async def start(m: Message):
    arg=m.text.partition(" ")[2].strip()
    referred=None
    if arg.startswith("ref_"):
        try: referred=int(arg[4:])
        except: pass
    u=await get_or_create_user(m.from_user.id,m.from_user.username,m.from_user.first_name,referred)
    if u.is_banned: await m.answer("❌ Siz bloklangansiz."); return
    if not await subscribed(m.bot,m.from_user.id):
        await m.answer("❌ Avval majburiy kanallarga obuna bo‘ling.\nSo‘ng /start ni qayta bosing.")
        return
    await m.answer("🤖 PRO chat bot\n\nSavolingizni yozing.")

@router.message(Command("stats"))
async def my_stats(m: Message):
    if m.from_user.id!=settings.owner_id:
        await m.answer("❌ Faqat owner.")
        return
    s=await stats()
    await m.answer(f"👥 {s['users']}\n💎 {s['pro']}\n🚫 {s['banned']}\n🎁 {s['referrals']}")

@router.message(Command("promo"))
async def promo(m: Message):
    code=m.text.partition(" ")[2].strip().upper()
    if not code: await m.answer("Foydalanish: /promo CODE"); return
    async with Session() as s:
        u=(await s.execute(select(User).where(User.telegram_id==m.from_user.id))).scalar_one_or_none()
        p=(await s.execute(select(PromoCode).where(PromoCode.code==code))).scalar_one_or_none()
        if not u or not p or p.uses>=p.max_uses:
            await m.answer("❌ Promo kod yaroqsiz."); return
        old=(await s.execute(select(PromoUse).where(PromoUse.promo_id==p.id,PromoUse.user_id==u.id))).scalar_one_or_none()
        if old: await m.answer("❌ Bu promo koddan foydalangansiz."); return
        from datetime import datetime, timezone, timedelta
        now=datetime.now(timezone.utc)
        u.is_pro=True; u.pro_until=max(u.pro_until or now,now)+timedelta(days=p.pro_days)
        p.uses+=1; s.add(PromoUse(promo_id=p.id,user_id=u.id)); await s.commit()
    await m.answer(f"💎 {p.pro_days} kun PRO berildi.")

@router.message(Command("ref"))
async def ref(m: Message):
    u=await get_or_create_user(m.from_user.id,m.from_user.username,m.from_user.first_name)
    await m.answer(f"🎁 Referral havolangiz:\nhttps://t.me/{settings.bot_username}?start={u.referral_code}")

@router.message(F.text)
async def normal_text(m: Message):
    # Main public bot chat. Business messages are handled separately.
    from ai_service import chat
    u=await get_or_create_user(m.from_user.id,m.from_user.username,m.from_user.first_name)
    if u.is_banned: return
    answer=await chat(settings.owner_id,m.chat.id,m.text)
    await m.answer(answer)
