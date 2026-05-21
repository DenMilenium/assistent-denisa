"""
Daily Schedule Reminder — Telegram Notifier
Sends reminders via Telegram bot
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_telegram_async(message: str, token: str, chat_id: str) -> bool:
    """Send a Telegram message asynchronously."""
    if not token or not chat_id:
        logger.warning("Telegram not configured — skipping message")
        return False

    try:
        from telegram import Bot
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message)
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_telegram(message: str, token: str, chat_id: str) -> bool:
    """Synchronous wrapper for send_telegram_async."""
    return asyncio.run(send_telegram_async(message, token, chat_id))


def test_connection(token: str, chat_id: str) -> tuple[bool, str]:
    """Test Telegram bot connection. Returns (success, message)."""
    try:
        import asyncio
        from telegram import Bot

        async def test():
            bot = Bot(token=token)
            me = await bot.get_me()
            await bot.send_message(
                chat_id=chat_id,
                text="✅ Daily Schedule Reminder: подключение работает!",
            )
            return f"✅ Бот @{me.username} подключён. Тестовое сообщение отправлено!"

        result = asyncio.run(test())
        return True, result
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
