"""
Quiz settings handler (optimized)
Test rejimini tanlash va sozlamalarni qo'llash
"""

import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import QuizStates
from bot.keyboards import QuizKeyboard
from bot.models import QuizSettings
from bot.database import get_db
from bot.constants import (
    ERROR_TEST_NOT_FOUND,
    ERROR_ACTIVE_TEST_EXISTS,
    ERROR_INVALID_FORMAT,
    ERROR_INVALID_NUMBER,
    MSG_RANGE_FORMAT,
    MSG_NUMBER_RANGE
)
from bot.handlers.quiz import show_question
from bot.services.quiz_manager import quiz_manager

router = Router(name="quiz_settings")


# =============================
#     UNIVERSAL HELPERLAR
# =============================

async def load_quiz(quiz_id: str):
    """Database'dan testni olish"""
    db = await get_db()
    return await db.get_quiz(quiz_id)


async def start_quiz_message(message: Message, quiz, session, user_id: int, question_count: int | None = None):
    """Testni boshlash va birinchi savolni ko'rsatish"""
    try:
        count = question_count if question_count else len(session.quiz.questions)

        await message.answer(
            f"🎯 <b>{quiz.title}</b>\n\n"
            f"Test boshlanmoqda...\n"
            f"Savollar soni: {count}\n"
            f"Vaqt: {quiz.time_display}",
            parse_mode="HTML"
        )

        await asyncio.sleep(0.8)
        await show_question(message, session, user_id)
    except Exception as e:
        logging.error(f"start_quiz_message error: {e}", exc_info=True)
        await message.answer(f"❌ Xatolik: {e}")


def check_active_session(user_id: int):
    """Faol sessiya mavjudligini tekshirish"""
    return quiz_manager.has_active_session(user_id)


# =============================
#     START QUIZ CALLBACK
# =============================

@router.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz_with_settings(callback: CallbackQuery, state: FSMContext):
    quiz_id = callback.data.split(":")[1]
    await state.update_data(quiz_id=quiz_id)

    await callback.message.edit_text(
        "📚 <b>Test rejimini tanlang:</b>\n\n"
        "• <b>To'liq test</b> - barcha savollar\n"
        "• <b>Oraliq test</b> - masalan 50–100\n"
        "• <b>Tasodifiy test</b> - masalan 30 ta savol",
        parse_mode="HTML",
        reply_markup=QuizKeyboard.quiz_mode_menu()
    )
    await state.set_state(QuizStates.choosing_quiz_mode)
    await callback.answer()


# =============================
#     FULL MODE
# =============================

@router.callback_query(QuizStates.choosing_quiz_mode, F.data == "quiz_mode:full")
async def set_full_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id = data.get("quiz_id")

    quiz = await load_quiz(quiz_id)
    if not quiz:
        return await callback.answer(ERROR_TEST_NOT_FOUND, show_alert=True)

    if check_active_session(callback.from_user.id):
        return await callback.answer(ERROR_ACTIVE_TEST_EXISTS, show_alert=True)

    settings = QuizSettings(quiz_mode="full")
    session = quiz_manager.create_session(callback.from_user.id, quiz, settings)

    await state.set_state(QuizStates.quiz_in_progress)
    await state.update_data(current_quiz_id=quiz_id)

    await callback.message.edit_text("⏳ Test boshlanmoqda...")
    await callback.answer()

    await start_quiz_message(callback.message, quiz, session, callback.from_user.id)


# =============================
#     RANGE MODE
# =============================

@router.callback_query(QuizStates.choosing_quiz_mode, F.data == "quiz_mode:range")
async def set_range_quiz(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔢 <b>Test oralig'ini kiriting:</b>\n"
        "Masalan: <code>20-50</code>\n",
        parse_mode="HTML"
    )
    await state.set_state(QuizStates.entering_quiz_range)
    await callback.answer()


@router.message(QuizStates.entering_quiz_range)
async def process_quiz_range(message: Message, state: FSMContext):
    try:
        parts = message.text.replace(" ", "").split("-")
        if len(parts) != 2:
            raise ValueError

        start, end = int(parts[0]), int(parts[1])

        if start < 1 or end <= start:
            raise ValueError

        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        
        if not quiz_id:
            await message.answer("❌ Test ID topilmadi. Qaytadan boshlang.")
            await state.clear()
            return
        
        quiz = await load_quiz(quiz_id)

        if not quiz:
            return await message.answer(ERROR_TEST_NOT_FOUND)

        if end > len(quiz.questions):
            return await message.answer(
                f"❌ Test {len(quiz.questions)} ta savolga ega.\n"
                f"Iltimos, to‘g‘ri oraliq kiriting."
            )

        if check_active_session(message.from_user.id):
            return await message.answer(ERROR_ACTIVE_TEST_EXISTS)

        settings = QuizSettings(
            quiz_mode="range",
            start_question=start,
            end_question=end
        )

        session = quiz_manager.create_session(message.from_user.id, quiz, settings)
        count = end - start + 1

        await state.set_state(QuizStates.quiz_in_progress)

        await start_quiz_message(message, quiz, session, message.from_user.id, question_count=count)

    except (ValueError, IndexError):
        await message.answer(
            f"{ERROR_INVALID_FORMAT}\n\n{MSG_RANGE_FORMAT}\n\n"
            f"❌ Qaytadan urinib ko'ring yoki /cancel bosing.",
            parse_mode="HTML"
        )
        # State'ni o'zgartirmang - foydalanuvchi qaytadan urinishi mumkin
    except Exception as e:
        logging.error(f"process_quiz_range error: {e}", exc_info=True)
        await message.answer(
            f"❌ <b>Xatolik yuz berdi!</b>\n\n"
            f"Iltimos, qaytadan urinib ko'ring yoki /cancel bosing.",
            parse_mode="HTML"
        )


# =============================
#     RANDOM MODE
# =============================

@router.callback_query(QuizStates.choosing_quiz_mode, F.data == "quiz_mode:random")
async def set_random_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id = data.get("quiz_id")

    quiz = await load_quiz(quiz_id)
    if not quiz:
        return await callback.answer(ERROR_TEST_NOT_FOUND, show_alert=True)

    total = len(quiz.questions)
    max_allowed = min(200, total)

    await callback.message.edit_text(
        f"🎲 <b>Nechta tasodifiy savol?</b>\n"
        f"Testda jami: <b>{total}</b>\n"
        f"Maksimal: <b>{max_allowed}</b>",
        parse_mode="HTML"
    )

    await state.set_state(QuizStates.entering_question_count)
    await callback.answer()


@router.message(QuizStates.entering_question_count)
async def process_question_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)

        data = await state.get_data()
        quiz_id = data.get("quiz_id")
        
        if not quiz_id:
            await message.answer("❌ Test ID topilmadi. Qaytadan boshlang.")
            await state.clear()
            return
        
        quiz = await load_quiz(quiz_id)

        if not quiz:
            return await message.answer(ERROR_TEST_NOT_FOUND)

        total = len(quiz.questions)
        if not 1 <= count <= total:
            return await message.answer(
                f"❌ Testda {total} ta savol mavjud.\n"
                f"Iltimos, to‘g‘ri son kiriting."
            )

        if check_active_session(message.from_user.id):
            return await message.answer(ERROR_ACTIVE_TEST_EXISTS)

        settings = QuizSettings(
            quiz_mode="random",
            question_count=count
        )

        session = quiz_manager.create_session(message.from_user.id, quiz, settings)

        await state.set_state(QuizStates.quiz_in_progress)

        await start_quiz_message(message, quiz, session, message.from_user.id, question_count=count)

    except ValueError:
        await message.answer(
            f"{ERROR_INVALID_NUMBER}\n\n{MSG_NUMBER_RANGE}\n\n"
            f"❌ Qaytadan urinib ko'ring yoki /cancel bosing.",
            parse_mode="HTML"
        )
        # State'ni o'zgartirmang - foydalanuvchi qaytadan urinishi mumkin
    except Exception as e:
        logging.error(f"process_question_count error: {e}", exc_info=True)
        await message.answer(
            f"❌ <b>Xatolik yuz berdi!</b>\n\n"
            f"Iltimos, qaytadan urinib ko'ring yoki /cancel bosing.",
            parse_mode="HTML"
        )
