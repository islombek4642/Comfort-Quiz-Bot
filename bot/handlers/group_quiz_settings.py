"""
Group quiz settings handler
Guruh quiz rejimini tanlash va sozlamalarni qo'llash
"""
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.keyboards import QuizKeyboard
from bot.services.quiz_manager import quiz_manager
from bot.models import QuizSettings
from bot.database import get_db
from bot.handlers.group import show_group_question

router = Router(name="group_quiz_settings")


@router.callback_query(F.data.startswith("group_quiz_mode:"))
async def group_quiz_mode_selection(callback: CallbackQuery, state: FSMContext):
    """Guruh quiz rejimini tanlash"""
    parts = callback.data.split(":")
    mode = parts[1]
    chat_id = int(parts[2])
    
    # Admin tekshirish
    session = quiz_manager.get_group_session(chat_id)
    if not session:
        await callback.answer("❌ Test sessiyasi topilmadi", show_alert=True)
        return
    
    if callback.from_user.id != session.creator_id:
        await callback.answer("❌ Faqat admin tanlashi mumkin!", show_alert=True)
        return
    
    # To'liq test
    if mode == "full":
        settings = QuizSettings(quiz_mode="full")
        session.settings = settings
        session._prepare_quiz_with_settings()
        
        await callback.message.edit_text(
            f"🎯 <b>{session.quiz.title}</b>\n\n"
            f"📚 <b>To'liq test</b> tanlandi\n"
            f"Savollar soni: {len(session.quiz.questions)}\n\n"
            f"Test 10 soniyadan keyin boshlanadi...",
            parse_mode="HTML"
        )
        await callback.answer()
        
        await asyncio.sleep(10)
        await show_group_question(callback.message, session)
    
    # Orqaliq test
    elif mode == "range":
        # FIX: state data sohralanadi
        await state.update_data(
            group_chat_id=chat_id,
            group_mode="range",
            waiting_for_range=True
        )
        await callback.message.edit_text(
            "🔢 <b>Test oralig'ini kiriting:</b>\n\n"
            "Misol: <code>1-50</code> yoki <code>50-100</code>\n\n"
            "Birinchi raqam - boshlang'ich savol\n"
            "Ikkinchi raqam - oxirgi savol",
            parse_mode="HTML"
        )
        await callback.answer()
    
    # Tasodifiy test
    elif mode == "random":
        # FIX: state data sohralanadi
        await state.update_data(
            group_chat_id=chat_id,
            group_mode="random",
            waiting_for_random=True
        )
        total_questions = len(session.quiz.questions)
        max_questions = min(200, total_questions)
        
        await callback.message.edit_text(
            f"🎲 <b>Nechta savoldan test tayyorlaylik?</b>\n\n"
            f"Masalan: <code>30</code>\n\n"
            f"📊 Testda jami: <b>{total_questions}</b> ta savol\n"
            f"Maksimal: <b>{max_questions}</b> ta savol",
            parse_mode="HTML"
        )
        await callback.answer()


@router.message(F.text, F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))
async def process_group_quiz_input(message: Message):
    """Guruhda rejim tanlash uchun input qabul qilish"""
    session = quiz_manager.get_group_session(message.chat.id)
    
    if not session:
        return
    
    # Faqat admin bo'lsa
    if message.from_user.id != session.creator_id:
        return
    
    # Oraliq test (1-50 formatida)
    if '-' in message.text:
        try:
            parts = message.text.strip().split('-')
            if len(parts) != 2:
                raise ValueError
            
            start, end = int(parts[0].strip()), int(parts[1].strip())
            
            if start < 1 or end <= start:
                raise ValueError
            
            # Oraliq tekshirish
            if end > len(session.quiz.questions):
                await message.answer(
                    f"❌ Noto'g'ri oraliq. Test {len(session.quiz.questions)} ta savolga ega.\n"
                    f"Iltimos, 1 dan {len(session.quiz.questions)} gacha bo'lgan oraliq kiriting."
                )
                return
            
            # Oraliq test sozlamalari
            settings = QuizSettings(
                quiz_mode="range",
                start_question=start,
                end_question=end
            )
            session.settings = settings
            session._prepare_quiz_with_settings()
            
            await message.answer(
                f"🎯 <b>{session.quiz.title}</b>\n\n"
                f"🔢 <b>Oraliq test</b> tanlandi\n"
                f"Savollar: {start}-{end}\n"
                f"Jami: {len(session.quiz.questions)} ta savol\n\n"
                f"Test 10 soniyadan keyin boshlanadi...",
                parse_mode="HTML"
            )
            
            await asyncio.sleep(10)
            await show_group_question(message, session)
            
        except (ValueError, IndexError):
            await message.answer(
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "Iltimos, quyidagi ko'rinishda kiriting:\n"
                "<code>1-50</code> yoki <code>50-100</code>",
                parse_mode="HTML"
            )
    
    # Tasodifiy test (raqam formatida)
    else:
        try:
            count = int(message.text.strip())
            
            if not 1 <= count <= 200:
                raise ValueError
            
            # Savollar sonini tekshirish
            if count > len(session.quiz.questions):
                await message.answer(
                    f"❌ Test {len(session.quiz.questions)} ta savolga ega.\n"
                    f"Iltimos, 1 dan {len(session.quiz.questions)} gacha bo'lgan son kiriting."
                )
                return
            
            # Tasodifiy test sozlamalari
            settings = QuizSettings(
                quiz_mode="random",
                question_count=count
            )
            session.settings = settings
            session._prepare_quiz_with_settings()
            
            await message.answer(
                f"🎯 <b>{session.quiz.title}</b>\n\n"
                f"🎲 <b>Tasodifiy test</b> tanlandi\n"
                f"Savollar soni: {len(session.quiz.questions)}\n\n"
                f"Test 10 soniyadan keyin boshlanadi...",
                parse_mode="HTML"
            )
            
            await asyncio.sleep(10)
            await show_group_question(message, session)
            
        except ValueError:
            await message.answer(
                "❌ <b>Noto'g'ri son kiritildi!</b>\n\n"
                "Iltimos, 1 dan 200 gacha bo'lgan son kiriting.\n"
                "Masalan: <code>30</code>",
                parse_mode="HTML"
            )


@router.message(F.text, F.chat.type == "private")
async def process_private_quiz_input(message: Message, state: FSMContext):
    """Private chat'da rejim tanlash uchun input qabul qilish"""
    data = await state.get_data()
    
    # Agar group_chat_id bo'lmasa, bu private chat uchun input emas
    if "group_chat_id" not in data:
        return
    
    chat_id = data.get("group_chat_id")
    session = quiz_manager.get_group_session(chat_id)
    
    if not session:
        await message.answer("❌ Test sessiyasi topilmadi")
        await state.clear()
        return
    
    # Admin tekshirish
    if message.from_user.id != session.creator_id:
        return
    
    mode = data.get("group_mode")
    
    # ORALIQ TEST
    if mode == "range":
        try:
            parts = message.text.strip().split('-')
            if len(parts) != 2:
                raise ValueError
            
            start, end = int(parts[0].strip()), int(parts[1].strip())
            
            if start < 1 or end <= start:
                raise ValueError
            
            # Oraliq tekshirish
            if end > len(session.quiz.questions):
                await message.answer(
                    f"❌ Noto'g'ri oraliq. Test {len(session.quiz.questions)} ta savolga ega.\n"
                    f"Iltimos, 1 dan {len(session.quiz.questions)} gacha bo'lgan oraliq kiriting."
                )
                return
            
            # Oraliq test sozlamalari
            settings = QuizSettings(
                quiz_mode="range",
                start_question=start,
                end_question=end
            )
            session.settings = settings
            session._prepare_quiz_with_settings()
            
            await message.answer(
                f"🎯 <b>{session.quiz.title}</b>\n\n"
                f"🔢 <b>Oraliq test</b> tanlandi\n"
                f"Savollar: {start}-{end}\n"
                f"Jami: {len(session.quiz.questions)} ta savol\n\n"
                f"Test 10 soniyadan keyin boshlanadi...",
                parse_mode="HTML"
            )
            
            await state.clear()
            await asyncio.sleep(10)
            await show_group_question(message, session)
            
        except (ValueError, IndexError):
            await message.answer(
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "Iltimos, quyidagi ko'rinishda kiriting:\n"
                "<code>1-50</code> yoki <code>50-100</code>",
                parse_mode="HTML"
            )
    
    # TASODIFIY TEST
    elif mode == "random":
        try:
            count = int(message.text.strip())
            
            if not 1 <= count <= 200:
                raise ValueError
            
            # Savollar sonini tekshirish
            if count > len(session.quiz.questions):
                await message.answer(
                    f"❌ Test {len(session.quiz.questions)} ta savolga ega.\n"
                    f"Iltimos, 1 dan {len(session.quiz.questions)} gacha bo'lgan son kiriting."
                )
                return
            
            # Tasodifiy test sozlamalari
            settings = QuizSettings(
                quiz_mode="random",
                question_count=count
            )
            session.settings = settings
            session._prepare_quiz_with_settings()
            
            await message.answer(
                f"🎯 <b>{session.quiz.title}</b>\n\n"
                f"🎲 <b>Tasodifiy test</b> tanlandi\n"
                f"Savollar soni: {len(session.quiz.questions)}\n\n"
                f"Test 10 soniyadan keyin boshlanadi...",
                parse_mode="HTML"
            )
            
            await state.clear()
            await asyncio.sleep(10)
            await show_group_question(message, session)
            
        except ValueError:
            await message.answer(
                "❌ <b>Noto'g'ri son kiritildi!</b>\n\n"
                "Iltimos, 1 dan 200 gacha bo'lgan son kiriting.\n"
                "Masalan: <code>30</code>",
                parse_mode="HTML"
            )