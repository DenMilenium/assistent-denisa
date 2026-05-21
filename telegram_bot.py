"""
Assistent denisa — Telegram Bot with voice command support
Handles text and voice messages, processes commands, sends responses
"""

import asyncio
import io
import logging
import threading
from datetime import datetime
from typing import Optional

from telegram import Update, Bot, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import database
from voice_commands import parse_command
from command_actions import process_command
from voice_assistant import text_to_speech_sync

logger = logging.getLogger(__name__)

# Bot instance
_application: Optional[Application] = None
_bot_task: Optional[threading.Thread] = None


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Привет, Денис! Я твой голосовой ассистент.\n\n"
        "🎤 Отправь голосовое сообщение — я пойму и выполню.\n"
        "💬 Или напиши текстом.\n\n"
        "Примеры команд:\n"
        "• «Добавь встречу в пятницу в 15:00»\n"
        "• «Что у меня на сегодня?»\n"
        "• «Отметь прогресс по книге 30%»\n"
        "• «Помощь» — полный список"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    from voice_commands import _handle_help as get_help
    result = get_help()
    await update.message.reply_text(result["text"])


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages — transcribe, parse, execute."""
    if not update.message or not update.message.voice:
        return
    
    # Notify user we're processing
    processing_msg = await update.message.reply_text("🎤 Слушаю...")
    
    try:
        # Get voice file
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        
        # Download as bytes
        voice_bytes = io.BytesIO()
        await file.download_to_memory(voice_bytes)
        voice_bytes = voice_bytes.getvalue()
        
        await processing_msg.edit_text("🧠 Распознаю речь...")
        
        # Transcribe
        from stt_engine import transcribe_voice_bytes
        text = transcribe_voice_bytes(voice_bytes)
        
        if not text:
            await processing_msg.edit_text(
                "😔 Не удалось распознать речь. Попробуй ещё раз или напиши текстом."
            )
            return
        
        # Parse command
        await processing_msg.edit_text(f"📝 Распознал: «{text}»\n\n🤔 Анализирую...")
        
        command = parse_command(text)
        
        # Execute
        result = process_command(command)
        
        response_text = result.get("text", "Что-то пошло не так.")
        success = result.get("success", False)
        
        # Send response as voice message if possible
        try:
            # Try to send as voice
            audio_data = text_to_speech_sync(response_text)
            if audio_data:
                await processing_msg.delete()
                voice_file = io.BytesIO(audio_data)
                voice_file.name = "response.ogg"
                await update.message.reply_voice(
                    voice=InputFile(voice_file),
                    caption="✅" if success else "❌",
                )
                return
        except Exception as e:
            logger.warning(f"Voice response failed: {e}")
        
        # Fallback to text
        await processing_msg.edit_text(
            ("✅ " if success else "❌ ") + response_text
        )
    
    except Exception as e:
        logger.error(f"Voice handler error: {e}")
        await processing_msg.edit_text(f"❌ Ошибка: {e}")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages — parse and execute."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    processing_msg = await update.message.reply_text("🤔 Анализирую...")
    
    # Parse command
    command = parse_command(text)
    
    # Execute
    result = process_command(command)
    response_text = result.get("text", "Что-то пошло не так.")
    success = result.get("success", False)
    
    # Send response
    await processing_msg.edit_text(
        ("✅ " if success else "❌ ") + response_text
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error: {context.error}")


def start_bot():
    """Start the Telegram bot in a background thread."""
    global _application
    
    token = database.get_setting("telegram_token")
    if not token:
        logger.warning("Telegram token not configured, bot not started")
        return False
    
    try:
        # Build application
        app = Application.builder().token(token).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(MessageHandler(filters.VOICE, voice_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
        app.add_error_handler(error_handler)
        
        # Start polling in background
        _application = app
        
        # Run in a separate event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Starting Telegram bot polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
        return True
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        return False


def stop_bot():
    """Stop the Telegram bot."""
    global _application
    if _application:
        try:
            _application.stop()
        except:
            pass
        _application = None


async def test_bot_token(token: str) -> tuple[bool, str]:
    """Test if bot token is valid."""
    try:
        app = Application.builder().token(token).build()
        bot = app.bot
        me = await bot.get_me()
        return True, f"✅ Бот @{me.username} готов к работе!"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"


# For testing
if __name__ == "__main__":
    start_bot()
