"""
Statistics handler
Statistika ko'rish
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards import MainMenuKeyboard, QuizKeyboard
from bot.services import StatisticsService
from bot.database import get_db

router = Router(name="statistics")


@router.message(F.text.in_({"📊 Statistika", "Statistika"}))
async def show_statistics_menu(message: Message):
    """Statistika menyusini ko'rsatish"""
    await message.answer(
        "📊 <b>Statistika</b>\n\n"
        "Quyidagilardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=QuizKeyboard.statistics_menu()
    )


@router.callback_query(F.data == "stats_general")
async def show_general_stats(callback: CallbackQuery):
    """Umumiy statistika"""
    stats = await StatisticsService.get_user_stats(callback.from_user.id)
    stats_text = StatisticsService.format_user_stats(stats)
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.statistics_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "view_my_stats")
async def view_my_stats(callback: CallbackQuery):
    """Mening statistikam (quiz tugagandan keyin)"""
    stats = await StatisticsService.get_user_stats(callback.from_user.id)
    stats_text = StatisticsService.format_user_stats(stats)
    
    await callback.message.answer(
        stats_text,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "stats_history")
async def show_history(callback: CallbackQuery):
    """Test tarixi"""
    history = await StatisticsService.get_user_history(callback.from_user.id, limit=10)
    
    if not history:
        await callback.message.edit_text(
            "📜 <b>Test tarixi</b>\n\n"
            "Siz hali hech qanday test yechmadingiz.",
            parse_mode="HTML",
            reply_markup=QuizKeyboard.statistics_menu()
        )
        await callback.answer()
        return
    
    text = "📜 <b>Test tarixi</b>\n\n"
    
    for i, item in enumerate(history, 1):
        result = item["result"]
        text += (
            f"{i}. <b>{item['quiz_title']}</b>\n"
            f"   📅 {item['date']}\n"
            f"   🎯 {result.correct_answers}/{result.total_questions} ({result.score_percent}%)\n\n"
        )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.statistics_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "stats_my_quizzes")
async def show_my_quizzes_stats(callback: CallbackQuery):
    """Mening testlarim statistikasi"""
    db = await get_db()
    quizzes = await db.get_user_quizzes(callback.from_user.id)
    
    if not quizzes:
        await callback.message.edit_text(
            "📈 <b>Testlar statistikasi</b>\n\n"
            "Siz hali test yaratmagansiz.",
            parse_mode="HTML",
            reply_markup=QuizKeyboard.statistics_menu()
        )
        await callback.answer()
        return
    
    text = "📈 <b>Testlaringiz statistikasi</b>\n\n"
    
    for quiz in quizzes[:5]:
        stats = await StatisticsService.get_quiz_stats(quiz.id)
        text += (
            f"📝 <b>{quiz.title}</b>\n"
            f"   👥 O'tganlar: {stats['total_attempts']}\n"
            f"   📊 O'rtacha: {stats['average_score']}%\n\n"
        )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.statistics_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_stats:"))
async def show_quiz_stats(callback: CallbackQuery):
    """Bitta test statistikasi"""
    quiz_id = callback.data.split(":")[1]
    
    stats = await StatisticsService.get_quiz_stats(quiz_id)
    stats_text = StatisticsService.format_quiz_stats(stats)
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.stats_back_button()
    )
    await callback.answer()


# Group full statistics functionality has been removed


@router.callback_query(F.data == "stats_menu")
async def back_to_stats_menu(callback: CallbackQuery):
    """Statistika menyusiga qaytish"""
    await callback.message.edit_text(
        "📊 <b>Statistika</b>\n\n"
        "Quyidagilardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=QuizKeyboard.statistics_menu()
    )
    await callback.answer()
