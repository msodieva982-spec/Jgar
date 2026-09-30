from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from db import Session, User, Conversation, EventLog, Subscription, Referral, PromoCode, PromoUse, Admin, AdminPermission, FeatureFlag, RequiredChannel
from config import settings

PERMISSIONS = {
    "users_view","users_search","user_ban","user_unban",
    "pro_give","pro_remove","pro_manage","pro_features_manage",
    "referral_view","referral_manage","stats_view","broadcast_send",
    "admin_add","admin_remove","admin_permissions","channels_manage",
    "bio_manage","logs_view"
}

async def get_or_create_user(tg_id, username=None, first_name=None, referred_by=None):
    async with Session() as s:
        u = (await s.execute(select(User).where(User.telegram_id==tg_id))).scalar_one_or_none()
        if not u:
            u=User(telegram_id=tg_id, username=username, first_name=first_name,
                   referral_code=f"r{tg_id}")
            if referred_by and referred_by != tg_id:
                inv=(await s.execute(select(User).where(User.telegram_id==referred_by))).scalar_one_or_none()
                if inv:
                    u.referred_by=referred_by
                    s.add(Referral(inviter_id=referred_by, invited_id=tg_id))
            s.add(u); await s.commit()
        return u

async def ban_user(tg_id, value=True):
    async with Session() as s:
        u=(await s.execute(select(User).where(User.telegram_id==tg_id))).scalar_one_or_none()
        if u: u.is_banned=value; await s.commit(); return True
        return False

async def set_pro(tg_id, days, value=True):
    now=datetime.now(timezone.utc)
    async with Session() as s:
        u=(await s.execute(select(User).where(User.telegram_id==tg_id))).scalar_one_or_none()
        if not u: return False
        if value:
            base=max(u.pro_until or now, now)
            u.pro_until=base+timedelta(days=days); u.is_pro=True
            s.add(Subscription(user_id=u.id, plan="manual", started_at=now, expires_at=u.pro_until, status="active"))
        else:
            u.is_pro=False; u.pro_until=None
        await s.commit(); return True

async def refresh_expired():
    now=datetime.now(timezone.utc)
    async with Session() as s:
        rows=(await s.execute(select(User).where(User.is_pro==True, User.pro_until<=now))).scalars().all()
        for u in rows: u.is_pro=False
        await s.commit()

async def is_pro(tg_id):
    now=datetime.now(timezone.utc)
    async with Session() as s:
        u=(await s.execute(select(User).where(User.telegram_id==tg_id))).scalar_one_or_none()
        return bool(u and u.is_pro and u.pro_until and u.pro_until>now)

async def log_event(owner_id, event_type, actor_id=None, chat_id=None, details=None):
    async with Session() as s:
        s.add(EventLog(owner_id=owner_id, event_type=event_type, actor_id=actor_id, chat_id=chat_id, details=details))
        await s.commit()

async def has_permission(tg_id, permission):
    if tg_id==settings.owner_id: return True
    async with Session() as s:
        a=(await s.execute(select(Admin).where(Admin.telegram_id==tg_id, Admin.active==True))).scalar_one_or_none()
        if not a: return False
        p=(await s.execute(select(AdminPermission).where(AdminPermission.admin_id==a.id, AdminPermission.permission==permission))).scalar_one_or_none()
        return p is not None

async def add_admin(tg_id, permissions):
    async with Session() as s:
        a=(await s.execute(select(Admin).where(Admin.telegram_id==tg_id))).scalar_one_or_none()
        if not a:
            a=Admin(telegram_id=tg_id); s.add(a); await s.flush()
        for p in set(permissions)&PERMISSIONS:
            s.add(AdminPermission(admin_id=a.id, permission=p))
        await s.commit()

async def remove_admin(tg_id):
    async with Session() as s:
        a=(await s.execute(select(Admin).where(Admin.telegram_id==tg_id))).scalar_one_or_none()
        if a: a.active=False; await s.commit()

async def stats():
    async with Session() as s:
        return {
            "users": (await s.execute(select(func.count(User.id)))).scalar_one(),
            "pro": (await s.execute(select(func.count(User.id)).where(User.is_pro==True))).scalar_one(),
            "banned": (await s.execute(select(func.count(User.id)).where(User.is_banned==True))).scalar_one(),
            "referrals": (await s.execute(select(func.count(Referral.id)).where(Referral.valid==True))).scalar_one(),
        }

async def get_feature(name, default=True):
    async with Session() as s:
        x=(await s.execute(select(FeatureFlag).where(FeatureFlag.name==name))).scalar_one_or_none()
        return default if x is None else x.enabled

async def set_feature(name, enabled):
    async with Session() as s:
        x=(await s.execute(select(FeatureFlag).where(FeatureFlag.name==name))).scalar_one_or_none()
        if not x: x=FeatureFlag(name=name, enabled=enabled); s.add(x)
        else: x.enabled=enabled
        await s.commit()
