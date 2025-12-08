"""
Quiz settings handler
Test rejimini tanlash va sozlamalarni qo'llash
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import QuizStates
from bot.keyboards import QuizKeyboard
from bot.services.quiz_manager import quiz_manager
from bot.models import QuizSettings
from bot.database import get_db
from bot.handlers.quiz import show_question

router = Router(name="quiz_settings")


@router.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz_with_settings(callback: CallbackQuery, state: FSMContext):
    """Testni sozlamalar bilan boshlash"""
    quiz_id = callback.data.split(":")[1]
    await state.update_data(quiz_id=quiz_id)
    
    await callback.message.edit_text(
        "📚 <b>Test rejimini tanlang:</b>\n\n"
        "• <b>To'liq test</b> - Barcha savollarni yechish\n"
        "• <b>Oraliq test</b> - Masalan, 50-100 savollarni yechish\n"
        "• <b>Tasodifiy test</b> - Masalan, 30 ta tasodifiy savol",
        parse_mode="HTML",
        reply_markup=QuizKeyboard.quiz_mode_menu()
    )
    await state.set_state(QuizStates.choosing_quiz_mode)
    await callback.answer()


@router.callback_query(QuizStates.choosing_quiz_mode, F.data == "quiz_mode:full")
async def set_full_quiz(callback: CallbackQuery, state: FSMContext):
    """To'liq test rejimi"""
    data = await state.get_data()
    quiz_id = data.get("quiz_id")
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Mavjud sessiyani tekshirish
    if quiz_manager.has_active_session(callback.from_user.id):
        await callback.answer("⚠️ Sizda allaqachon faol test bor!", show_alert=True)
        return
    
    # To'liq test sozlamalari
    settings = QuizSettings(quiz_mode="full")
    
    # Sessiyani yaratish
    session = quiz_manager.create_session(
        callback.from_user.id,
        quiz,
        settings
    )
    
    await state.set_state(QuizStates.quiz_in_progress)
    await state.update_data(current_quiz_id=quiz_id)
    
    await callback.message.edit_text(
        f"🎯 <b>{quiz.title}</b>\n\n"
        f"Test boshlanmoqda...\n"
        f"Savollar soni: {len(quiz.questions)}\n"
        f"Vaqt: {quiz.time_display}",
        parse_mode="HTML"
    )
    
    await callback.answer()
    
    # Birinchi savolni ko'rsatish
    await asyncio.sleep(1)
    await show_question(callback.message, session, callback.from_user.id)


@router.callback_query(QuizStates.choosing_quiz_mode, F.data == "quiz_mode:range")
async def set_range_quiz(callback: CallbackQuery, state: FSMContext):
    """Oraliq test rejimi"""
    await callback.message.edit_text(
        "🔢 <b>Test oralig'ini kiriting:</b>\n\n"
        "Misol: <code>1-50</code> yoki <code>50-100</code>\n\n"
        "Birinchi raqam - boshlang'ich savol\n"
        "Ikkinchi raqam - oxirgi savol",
        parse_mode="HTML"
    )
    await state.set_state(QuizStates.entering_quiz_range)
    await callback.answer()


@router.message(QuizStates.entering_quiz_range)
async def process_quiz_range(message: Message, state: FSMContext):
    """Test oraliqini qabul qilish"""
    try:
        parts = message.text.strip().split('-')
        if len(parts) != 2:
            raise ValueError
        
        start, end = int(parts[0].strip()), int(parts[1].strip())
        
        if start < 1 or end <= start:
            raise ValueError
        
        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        
        db = await get_db()
        quiz = await db.get_quiz(quiz_id)
        
        if not quiz:
            await message.answer("❌ Test topilmadi")
            return
        
        # Oraliq tekshirish
        if end > len(quiz.questions):
            await message.answer(
                f"❌ Noto'g'ri oraliq. Test {len(quiz.questions)} ta savolga ega.\n"
                f"Iltimos, 1 dan {len(quiz.questions)} gacha bo'lgan oraliq kiriting."
            )
            return
        
        # Mavjud sessiyani tekshirish
        if quiz_manager.has_active_session(message.from_user.id):
            await message.answer("⚠️ Sizda allaqachon faol test bor!")
            return
        
        # Oraliq test sozlamalari
        settings = QuizSettings(
            quiz_mode="range",
            start_question=start,
            end_question=end
        )
        
        # Sessiyani yaratish
        session = quiz_manager.create_session(
            message.from_user.id,
            quiz,
            settings
        )
        
        await state.set_state(QuizStates.quiz_in_progress)
        await state.update_data(current_quiz_id=quiz_id)
        
        await message.answer(
            f"🎯 <b>{quiz.title}</b>\n\n"
            f"Test boshlanmoqda...\n"
            f"Savollar soni: {len(quiz.questions)}\n"
            f"Vaqt: {quiz.time_display}",
            parse_mode="HTML"
        )
        
        # Birinchi savolni ko'rsatish
        await asyncio.sleep(1)
        await show_question(message, session, message.from_user.id)
        
    except (ValueError, IndexError):
        await message.answer(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "Iltimos, quyidagi ko'rinishda kiriting:\n"
            "<code>1-50</code> yoki <code>50-100</code>",
            parse_mode="HTML"
        )


@router.callback_query(QuizStates.choosing_quiz_mode, F.data == "quiz_mode:random")
async def set_random_quiz(callback: CallbackQuery, state: FSMContext):
    """Tasodifiy test rejimi"""
    data = await state.get_data()
    quiz_id = data.get("quiz_id")
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    total_questions = len(quiz.questions)
    max_questions = min(200, total_questions)
    
    await callback.message.edit_text(
        f"🎲 <b>Nechta savoldan test tayyorlaylik?</b>\n\n"
        f"Masalan: <code>30</code>\n\n"
        f"📊 Testda jami: <b>{total_questions}</b> ta savol\n"
        f"Maksimal: <b>{max_questions}</b> ta savol",
        parse_mode="HTML"
    )
    await state.set_state(QuizStates.entering_question_count)
    await callback.answer()


@router.message(QuizStates.entering_question_count)
async def process_question_count(message: Message, state: FSMContext):
    """Savollar sonini qabul qilish"""
    try:
        count = int(message.text.strip())
        
        if not 1 <= count <= 200:
            raise ValueError
        
        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        
        db = await get_db()
        quiz = await db.get_quiz(quiz_id)
        
        if not quiz:
            await message.answer("❌ Test topilmadi")
            return
        
        # Savollar sonini tekshirish
        if count > len(quiz.questions):
            await message.answer(
                f"❌ Test {len(quiz.questions)} ta savolga ega.\n"
                f"Iltimos, 1 dan {len(quiz.questions)} gacha bo'lgan son kiriting."
            )
            return
        
        # Mavjud sessiyani tekshirish
        if quiz_manager.has_active_session(message.from_user.id):
            await message.answer("⚠️ Sizda allaqachon faol test bor!")
            return
        
        # Tasodifiy test sozlamalari
        settings = QuizSettings(
            quiz_mode="random",
            question_count=count
        )
        
        # Sessiyani yaratish
        session = quiz_manager.create_session(
            message.from_user.id,
            quiz,
            settings
        )
        
        await state.set_state(QuizStates.quiz_in_progress)
        await state.update_data(current_quiz_id=quiz_id)
        
        await message.answer(
            f"🎯 <b>{quiz.title}</b>\n\n"
            f"Test boshlanmoqda...\n"
            f"Savollar soni: {len(quiz.questions)}\n"
            f"Vaqt: {quiz.time_display}",
            parse_mode="HTML"
        )
        
        # Birinchi savolni ko'rsatish
        await asyncio.sleep(1)
        await show_question(message, session, message.from_user.id)
        
    except ValueError:
        await message.answer(
            "❌ <b>Noto'g'ri son kiritildi!</b>\n\n"
            "Iltimos, 1 dan 200 gacha bo'lgan son kiriting.\n"
            "Masalan: <code>30</code>",
            parse_mode="HTML"
        )
