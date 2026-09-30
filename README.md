# PRO chat bot — full modular project

This project implements the feasible parts of the requested PRO chat bot in separate Python modules.

## Core
- Telegram bot + Telegram Business updates
- AI conversations + per-chat memory
- temporary /away instructions
- voice transcription
- image understanding
- deleted/edited message event logging and owner alerts
- admin roles + permissions
- ban/unban
- PRO/trial/rewards
- referral tracking
- promo codes
- statistics
- broadcast (bot-side audience)
- force-subscribe (bot-side)
- AI admin assistant
- audit logs
- bio advertisement state management

## Important Telegram API limitation
Telegram currently exposes Business connection/message/edit/delete updates and a `setBusinessAccountBio` method. However, the Business API does not provide a general "get current business bio" operation or a bio-changed update. Therefore no honest implementation can continuously detect every manual bio edit and reconstruct it perfectly. This project stores the original bio when it is supplied/known and manages the ad state, but it does NOT pretend it can read an arbitrary current bio every 10 minutes.

Business replies are also constrained by Telegram Business rights and the 24-hour incoming-message rule. See the official docs before deployment.

## Setup
1. Create a Telegram bot with BotFather.
2. Put the bot token in Replit Secrets as BOT_TOKEN.
3. Put your OpenAI API key in OPENAI_API_KEY.
4. Put your numeric Telegram ID in OWNER_ID.
5. Set BOT_USERNAME.
6. Install requirements.
7. Run `python main.py`.

Never put real secrets into source files.

## Database
SQLite works for development. Use PostgreSQL in production:
DATABASE_URL=postgresql+asyncpg://...

## Payment
The code contains a provider interface and a Telegram Stars-ready service boundary. Payment confirmation must be connected to the actual provider/webhook flow you choose. Do not mark a user PRO based only on a client-side button.

## Business connection
The account owner connects the bot through Telegram Business settings. The bot must be granted the specific rights it needs, including reply/read/edit-bio as applicable.
