import json
from datetime import datetime, timezone
from aiogram import Router
from aiogram.types import Update
from sqlalchemy import select
from db import Session, BusinessConnection, MessageRecord, ChatState
from services import log_event
from ai_service import chat
from config import settings

router=Router()

def kind_and_file(m):
    if m.voice: return "voice", m.voice.file_id
    if m.photo: return "photo", m.photo[-1].file_id
    if m.video: return "video", m.video.file_id
    if m.document: return "document", m.document.file_id
    if m.audio: return "audio", m.audio.file_id
    if m.sticker: return "sticker", m.sticker.file_id
    return "text", None

async def save_business_message(m):
    owner_id = m.business_connection_id and await owner_from_connection(m.business_connection_id)
    if not owner_id: return
    kind,file_id=kind_and_file(m)
    text=m.text or ""
    async with Session() as s:
        s.add(MessageRecord(connection_id=m.business_connection_id,owner_id=owner_id,chat_id=m.chat.id,message_id=m.message_id,
                             sender_id=m.from_user.id if m.from_user else None,kind=kind,text=text,file_id=file_id,caption=m.caption))
        st=(await s.execute(select(ChatState).where(ChatState.owner_id==owner_id,ChatState.chat_id==m.chat.id))).scalar_one_or_none()
        if not st:
            st=ChatState(owner_id=owner_id,chat_id=m.chat.id)
            s.add(st)
        st.last_incoming_at=datetime.now(timezone.utc)
        await s.commit()
    await log_event(owner_id,"message_received",m.from_user.id if m.from_user else None,m.chat.id,text)

async def owner_from_connection(connection_id):
    async with Session() as s:
        x=(await s.execute(select(BusinessConnection).where(BusinessConnection.connection_id==connection_id, BusinessConnection.is_enabled==True))).scalar_one_or_none()
        return x.owner_id if x else None

async def register_connection(update):
    bc=update.business_connection
    if not bc: return
    async with Session() as s:
        x=(await s.execute(select(BusinessConnection).where(BusinessConnection.connection_id==bc.id))).scalar_one_or_none()
        rights=bc.rights.model_dump_json() if getattr(bc,"rights",None) else "{}"
        if not x: x=BusinessConnection(connection_id=bc.id,owner_id=bc.user.id,is_enabled=bc.is_enabled,rights_json=rights); s.add(x)
        else: x.owner_id=bc.user.id; x.is_enabled=bc.is_enabled; x.rights_json=rights
        await s.commit()

async def handle_business_message(bot, m):
    await save_business_message(m)
    owner=await owner_from_connection(m.business_connection_id)
    if not owner: return
    text=m.text or m.caption
    if not text: return
    answer=await chat(owner,m.chat.id,text)
    # aiogram Bot API call supports business_connection_id.
    await bot.send_message(chat_id=m.chat.id,text=answer,business_connection_id=m.business_connection_id)

async def handle_edited(bot,m):
    owner=await owner_from_connection(m.business_connection_id)
    if not owner: return
    await log_event(owner,"message_edited",m.from_user.id if m.from_user else None,m.chat.id,
                    f"message_id={m.message_id}; new={m.text or m.caption or ''}")
    try:
        await bot.send_message(chat_id=m.chat.id,text="✏️ Xabar tahrirlandi.",business_connection_id=m.business_connection_id)
    except Exception:
        pass

async def handle_deleted(bot,deleted):
    owner=await owner_from_connection(deleted.business_connection_id)
    if not owner: return
    # Telegram's deletion update identifies the business connection; keep event for owner.
    await log_event(owner,"messages_deleted",None,None,json.dumps(deleted.model_dump(),ensure_ascii=False))
    try:
        await bot.send_message(chat_id=settings.owner_id,text="🗑 Business akkauntdagi xabar(lar) o‘chirildi.")
    except Exception:
        pass
