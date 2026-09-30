import asyncio, logging, os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import settings
from db import init_db, Session, BusinessConnection as BC
from services import refresh_expired, get_or_create_user
from bot_features import router as public_router
from admin import router as admin_router
from business import register_connection, handle_business_message, handle_edited, handle_deleted
from bio_ads import configure_default, apply_ad
from aiogram.filters import BaseFilter

logging.basicConfig(level=logging.INFO)

async def healthcheck(request):
    return web.json_response({"status": "ok"})

def create_health_app():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/healthz", healthcheck)
    return app

class BusinessUpdateFilter(BaseFilter):
    async def __call__(self, update: Update):
        return bool(update.business_connection or update.business_message or update.edited_business_message or update.deleted_business_messages)

async def background(bot):
    while True:
        try:
            await refresh_expired()
        except Exception:
            logging.exception("background task failed")
        await asyncio.sleep(60)

async def main():
    await init_db()
    await configure_default()
    bot=Bot(settings.bot_token)
    dp=Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(public_router)

    async def process_business(update: Update):
        if update.business_connection:
            await register_connection(update)
            if update.business_connection.is_enabled:
                await apply_ad(bot,update.business_connection.id)
        if update.business_message:
            await handle_business_message(bot,update.business_message)
        if update.edited_business_message:
            await handle_edited(bot,update.edited_business_message)
        if update.deleted_business_messages:
            await handle_deleted(bot,update.deleted_business_messages)

    @dp.update.outer_middleware()
    async def business_middleware(handler, event, data):
        if isinstance(event, Update) and (event.business_connection or event.business_message or event.edited_business_message or event.deleted_business_messages):
            await process_business(event)
            return None
        return await handler(event,data)

    runner = web.AppRunner(create_health_app())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "10000")))
    await site.start()
    background_task = asyncio.create_task(background(bot))
    logging.info("PRO chat bot started")
    try:
        await dp.start_polling(bot,allowed_updates=[
            "message","callback_query","business_connection","business_message",
            "edited_business_message","deleted_business_messages"
        ])
    finally:
        background_task.cancel()
        await asyncio.gather(background_task, return_exceptions=True)
        await runner.cleanup()

if __name__=="__main__":
    asyncio.run(main())
