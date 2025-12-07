"""
Quiz Bot - Asosiy fayl
Botni ishga tushirish uchun bu faylni run qiling
"""
import asyncio
import logging
import sys
from pathlib import Path

# Loyiha papkasini PATH ga qo'shish
sys.path.insert(0, str(Path(__file__).parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from bot.config import config
from bot.database import get_db
from bot.handlers import get_all_routers


# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Bot ishga tushganda"""
    logger.info("Bot ishga tushmoqda...")
    
    # Database'ni ishga tushirish
    db = await get_db()
    logger.info("Database tayyor")
    
    # Bot ma'lumotlarini olish
    bot_info = await bot.get_me()
    logger.info(f"Bot: @{bot_info.username} ({bot_info.full_name})")
    
    # Admin'larga xabar yuborish
    if config.bot.admin_ids:
        for admin_id in config.bot.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    "✅ <b>Bot ishga tushdi!</b>\n\n"
                    f"🤖 Bot: @{bot_info.username}",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.warning(f"Admin {admin_id} ga xabar yuborib bo'lmadi: {e}")


async def on_shutdown(bot: Bot):
    """Bot to'xtaganda"""
    logger.info("Bot to'xtatilmoqda...")
    
    # Admin'larga xabar
    if config.bot.admin_ids:
        for admin_id in config.bot.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    "⚠️ <b>Bot to'xtatildi!</b>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass


async def main():
    """Asosiy funksiya"""
    # Token tekshirish
    if not config.bot.token:
        logger.error("BOT_TOKEN topilmadi! .env faylni tekshiring.")
        sys.exit(1)
    
    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Routerlarni ro'yxatdan o'tkazish
    for router in get_all_routers():
        dp.include_router(router)
        logger.info(f"Router qo'shildi: {router.name}")
    
    # Startup va shutdown hodisalari
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Botni ishga tushirish
    logger.info("Polling boshlanmoqda...")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        raise
