import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pro_chat_bot.db")
    owner_id: int = int(os.getenv("OWNER_ID", "0") or 0)
    bot_username: str = os.getenv("BOT_USERNAME", "").lstrip("@")
    ai_model: str = os.getenv("AI_MODEL", "gpt-5-mini")
    stt_model: str = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
    bio_ad_text: str = os.getenv("BIO_AD_TEXT", "🤖 Avto chat bot @{BOT_USERNAME}")
    bio_check_interval_minutes: int = int(os.getenv("BIO_CHECK_INTERVAL_MINUTES", "10"))
    default_trial_hours: int = int(os.getenv("DEFAULT_TRIAL_HOURS", "3"))
    referrals_for_reward: int = int(os.getenv("REFERRALS_FOR_REWARD", "3"))
    referral_reward_days: int = int(os.getenv("REFERRAL_REWARD_DAYS", "1"))

settings = Settings()
if not settings.bot_token:
    raise RuntimeError("BOT_TOKEN is required")
