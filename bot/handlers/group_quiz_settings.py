"""
Group quiz settings handler (refactored & optimized)
Guruh test rejimini tanlash, sozlash va start berish
"""

import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command

from bot.keyboards import QuizKeyboard
from bot.services.quiz_manager import quiz_manager
from bot.models import QuizSettings
from bot.handlers.group import show_group_question
from bot.database import get_db

router = Router(name="group_quiz_settings")


# ================================
#      HELPERS & VALIDATORS
# ================================

async def is_admin(user_id: int, session, bot: Bot):
    """Foydalanuvchi adminmi yoki sesiyani yaratganmi yoki guruh adminimi"""
    # Sesiyani yaratgan foydalanuvchi
    if user_id == session.creator_id:
        return True
    
    # Guruh adminini tekshirish
    try:
        print(f"DEBUG is_admin: Checking user_id={user_id}, chat_id={session.chat_id}")
        member = await bot.get_chat_member(session.chat_id, user_id)
        print(f"DEBUG is_admin: member.status={member.status}")
        return member.status in ["creator", "administrator"]
    except Exception as e:
        print(f"DEBUG is_admin: Exception - {e}, user_id={user_id}, chat_id={session.chat_id}")
        return False


def parse_range(text: str) -> tuple[int, int] | None:
    """1-50 formatni parse qilish"""
    try:
        # Faqat raqamlar va "-" belgisini qoldirib, qolganini olib tashlash
        import re
        match = re.search(r'(\d+)\s*-\s*(\d+)', text)
        if not match:
            return None
        
        start, end = int(match.group(1)), int(match.group(2))
        if start < 1 or end <= start:
            return None

        return start, end
    except Exception:
        return None


def parse_number(text: str) -> int | None:
    """Faqat son"""
    try:
        import re
        match = re.search(r'(\d+)', text)
        if not match:
            return None
        num = int(match.group(1))
        if num < 1:
            return None
        return num
    except Exception:
        return None


async def start_group_quiz(message: Message, session, delay: int = 10):
    """Testni boshlash"""
    try:
        await message.answer(
            f"⏳ Test {delay} soniyadan keyin boshlanadi...",
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass

    await asyncio.sleep(delay)
    await show_group_question(message, session)


# ================================
#      CALLBACK — MODE SELECT
# ================================

@router.callback_query(F.data.startswith("group_quiz_mode:"))
async def group_quiz_mode(callback: CallbackQuery, state: FSMContext, bot: Bot):
    parts = callback.data.split(":")
    mode = parts[1]

    session = quiz_manager.get_group_session(callback.message.chat.id)
    if not session:
        return await callback.answer("❌ Test sessiyasi mavjud emas", show_alert=True)

    if not await is_admin(callback.from_user.id, session, bot):
        return await callback.answer("❌ Faqat admin tanlay oladi!", show_alert=True)

    # FULL MODE
    if mode == "full":
        session.settings = QuizSettings(quiz_mode="full")
        await callback.message.edit_text(
            f"🎯 <b>{session.quiz.title}</b>\n\n"
            f"📚 To‘liq test tanlandi\n"
            f"Savollar soni: {len(session.quiz.questions)}",
            parse_mode="HTML"
        )
        await start_group_quiz(callback.message, session)
        return

    # RANGE / RANDOM → Guruh chat'ida kiritiladi
    # Session'da waiting_mode'ni o'rnatish
    session.waiting_mode = mode

    if mode == "range":
        await callback.answer("✏️ Iltimos, oraliqni kiriting")
        await callback.message.answer(
            "🔢 <b>Admin, oraliqni kiriting:</b>\n\n"
            "<b>Masalan:</b> 1-50 yoki 50-120",
            parse_mode="HTML"
        )

    if mode == "random":
        await callback.answer("✏️ Iltimos, sonni kiriting")
        await callback.message.answer(
            "🎲 <b>Admin, nechta savol kerak?</b>\n\n"
            "<b>Masalan:</b> 30",
            parse_mode="HTML"
        )


# ================================
#         GROUP INPUT
# ================================

@router.message((F.chat.type == "group") | (F.chat.type == "supergroup"))
async def process_group_input(message: Message, state: FSMContext, bot: Bot):
    # /stop komandasi uchun - boshqa handler'ga o'tish
    if message.text and message.text.startswith("/stop"):
        return
    
    # Guruh chat'ida faol sessiyani topish
    session = quiz_manager.get_group_session(message.chat.id)
    if not session or not session.waiting_mode:
        return

    mode = session.waiting_mode

    # Debug
    is_creator = message.from_user.id == session.creator_id
    admin_result = await is_admin(message.from_user.id, session, bot)
    print(f"DEBUG oraliq: user_id={message.from_user.id}, creator_id={session.creator_id}, is_creator={is_creator}, is_admin={admin_result}, mode={mode}")
    
    if not admin_result:
        await message.answer("❌ Faqat admin kirita oladi!", parse_mode="HTML")
        return

    # RANGE MODE
    if mode == "range":
        rng = parse_range(message.text)
        if not rng:
            return await message.answer(
                "❌ Noto'g'ri format!\n\n"
                "To‘g‘ri misol: <code>1-50</code>",
                parse_mode="HTML"
            )

        start, end = rng
        if end > len(session.quiz.questions):
            return await message.answer(
                f"❌ Testda {len(session.quiz.questions)} ta savol bor.\n"
                "To‘g‘ri oraliq kiriting."
            )

        session.settings = QuizSettings(
            quiz_mode="range",
            start_question=start,
            end_question=end
        )
        session._prepare_quiz_with_settings()

        await message.answer(
            f"🎯 Oraliq belgilandi: {start}-{end}\n"
            f"Jami: {end - start + 1} ta savol",
            parse_mode="HTML"
        )
        session.waiting_mode = None
        return await start_group_quiz(message, session)

    # RANDOM MODE
    if mode == "random":
        num = parse_number(message.text)
        if not num:
            return await message.answer(
                "❌ Noto'g'ri son!\nMasalan: <code>30</code>",
                parse_mode="HTML"
            )

        if num > len(session.quiz.questions):
            return await message.answer(
                f"❌ Testda {len(session.quiz.questions)} ta savol bor."
            )

        session.settings = QuizSettings(
            quiz_mode="random",
            question_count=num
        )
        session._prepare_quiz_with_settings()

        await message.answer(
            f"🎲 Tasodifiy test: {num} ta savol",
            parse_mode="HTML"
        )
        session.waiting_mode = None
        await start_group_quiz(message, session)
