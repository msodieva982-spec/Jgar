from openai import AsyncOpenAI
from config import settings
from db import Session, Conversation, Instruction, Memory
from sqlalchemy import select
from datetime import datetime, timezone

client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

SYSTEM = """You are PRO chat bot, the AI assistant of the account owner.
Do not impersonate the owner. If asked who you are, say you are their AI assistant.
Use only supplied facts. Never invent the owner's location, schedule, relationships, phone number, or actions.
Be natural, helpful and concise. If the owner supplied a temporary instruction, follow it while it is active.
"""

async def temporary_instruction(owner_id):
    async with Session() as s:
        now=datetime.now(timezone.utc)
        x=(await s.execute(select(Instruction).where(Instruction.owner_id==owner_id).order_by(Instruction.id.desc()))).scalars().first()
        return x.text if x and (x.expires_at is None or x.expires_at>now) else ""

async def chat(owner_id, chat_id, text):
    if not client:
        return "OPENAI_API_KEY sozlanmagan."
    async with Session() as s:
        rows=(await s.execute(select(Conversation).where(Conversation.owner_id==owner_id, Conversation.chat_id==chat_id).order_by(Conversation.created_at.desc()).limit(16))).scalars().all()
        rows.reverse()
        inst=await temporary_instruction(owner_id)
        messages=[{"role":"system","content":SYSTEM+(f"\nTemporary instruction:\n{inst}" if inst else "")}]
        messages += [{"role":x.role,"content":x.content} for x in rows]
        messages.append({"role":"user","content":text})
        r=await client.chat.completions.create(model=settings.ai_model,messages=messages,temperature=0.7)
        answer=r.choices[0].message.content or "Javob tayyorlay olmadim."
        s.add(Conversation(owner_id=owner_id,chat_id=chat_id,role="user",content=text))
        s.add(Conversation(owner_id=owner_id,chat_id=chat_id,role="assistant",content=answer))
        await s.commit()
        return answer

async def transcribe(path):
    if not client: return None
    with open(path,"rb") as f:
        r=await client.audio.transcriptions.create(model=settings.stt_model,file=f)
    return getattr(r,"text",None)

async def analyze_image(image_url, question):
    if not client: return "OPENAI_API_KEY sozlanmagan."
    r=await client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role":"user","content":[
            {"type":"text","text":question or "Rasmni tushuntir."},
            {"type":"image_url","image_url":{"url":image_url}}
        ]}]
    )
    return r.choices[0].message.content or "Rasmni tahlil qila olmadim."
