from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from services import has_permission, ban_user, set_pro, add_admin, remove_admin, stats, set_feature, PERMISSIONS
from config import settings
from db import Session, EventLog
from sqlalchemy import select, desc

router=Router()

@router.message(Command("admin"))
async def admin_panel(m: Message):
    if not await has_permission(m.from_user.id,"stats_view"):
        await m.answer("❌ Sizga bu huquq berilmagan.")
        return
    s=await stats()
    await m.answer(
        f"👑 ADMIN PANEL\n\n👥 Users: {s['users']}\n💎 PRO: {s['pro']}\n🚫 Ban: {s['banned']}\n🎁 Referrals: {s['referrals']}\n\n"
        "/ban ID\n/unban ID\n/pro ID DAYS\n/removepro ID\n/addadmin ID\n/removeadmin ID\n/features"
    )

@router.message(Command("ban"))
async def ban(m: Message):
    if not await has_permission(m.from_user.id,"user_ban"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    parts=m.text.split()
    if len(parts)<2: await m.answer("Foydalanish: /ban ID"); return
    await ban_user(int(parts[1]),True); await m.answer("✅ Ban berildi.")

@router.message(Command("unban"))
async def unban(m: Message):
    if not await has_permission(m.from_user.id,"user_unban"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    parts=m.text.split()
    if len(parts)<2: await m.answer("Foydalanish: /unban ID"); return
    await ban_user(int(parts[1]),False); await m.answer("✅ Ban olib tashlandi.")

@router.message(Command("pro"))
async def pro(m: Message):
    if not await has_permission(m.from_user.id,"pro_give"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    p=m.text.split()
    if len(p)<3: await m.answer("Foydalanish: /pro ID DAYS"); return
    await set_pro(int(p[1]),int(p[2]),True); await m.answer("💎 PRO berildi.")

@router.message(Command("removepro"))
async def removepro(m: Message):
    if not await has_permission(m.from_user.id,"pro_remove"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    p=m.text.split()
    if len(p)<2: await m.answer("Foydalanish: /removepro ID"); return
    await set_pro(int(p[1]),0,False); await m.answer("✅ PRO olib tashlandi.")

@router.message(Command("addadmin"))
async def add_admin_cmd(m: Message):
    if not await has_permission(m.from_user.id,"admin_add"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    p=m.text.split(maxsplit=2)
    if len(p)<2: await m.answer("Foydalanish: /addadmin ID [permission1,permission2]"); return
    perms=p[2].split(",") if len(p)>2 else []
    await add_admin(int(p[1]),perms); await m.answer("✅ Admin qo‘shildi.")

@router.message(Command("removeadmin"))
async def remove_admin_cmd(m: Message):
    if not await has_permission(m.from_user.id,"admin_remove"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    p=m.text.split()
    if len(p)<2: await m.answer("Foydalanish: /removeadmin ID"); return
    if int(p[1])==settings.owner_id: await m.answer("❌ Ownerni o‘chirib bo‘lmaydi."); return
    await remove_admin(int(p[1])); await m.answer("✅ Admin o‘chirildi.")

@router.message(Command("features"))
async def features(m: Message):
    if not await has_permission(m.from_user.id,"pro_features_manage"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    await m.answer("Feature flags: /feature NAME on|off")

@router.message(Command("feature"))
async def feature(m: Message):
    if not await has_permission(m.from_user.id,"pro_features_manage"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    p=m.text.split()
    if len(p)<3: await m.answer("Foydalanish: /feature NAME on|off"); return
    await set_feature(p[1],p[2].lower()=="on"); await m.answer("✅ Saqlandi.")

@router.message(Command("logs"))
async def logs(m: Message):
    if not await has_permission(m.from_user.id,"logs_view"):
        await m.answer("❌ Sizga bu huquq berilmagan."); return
    async with Session() as s:
        rows=(await s.execute(select(EventLog).where(EventLog.owner_id==settings.owner_id).order_by(desc(EventLog.id)).limit(20))).scalars().all()
    await m.answer("\n".join(f"{x.event_type} | {x.actor_id} | {x.details or ''}" for x in rows) or "Log yo‘q.")
