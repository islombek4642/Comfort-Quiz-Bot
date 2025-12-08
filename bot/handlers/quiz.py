"""
Quiz handler
Test jarayonini boshqarish
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.fsm.context import FSMContext

from bot.states import QuizStates
from uuid import uuid4
from bot.keyboards import MainMenuKeyboard, QuizKeyboard, SettingsKeyboard
from bot.services import QuizManager, StatisticsService
from bot.services.quiz_manager import quiz_manager
from bot.models import Quiz, Question
from bot.database import get_db

router = Router(name="quiz")


# start_quiz handler quiz_settings.py faylida joylashgan

@router.callback_query(F.data.startswith("restart_quiz:"))
async def restart_quiz(callback: CallbackQuery, state: FSMContext):
    """Testni qayta boshlash"""
    quiz_id = callback.data.split(":")[1]
    
    # Mavjud sessiyani tugatish
    quiz_manager.end_session(callback.from_user.id)
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Yangi sessiya yaratish
    session = quiz_manager.create_session(callback.from_user.id, quiz)
    
    await state.set_state(QuizStates.quiz_in_progress)
    
    await callback.message.edit_text(
        f"🔄 <b>{quiz.title}</b>\n\n"
        f"Test qayta boshlanmoqda...",
        parse_mode="HTML"
    )
    
    await callback.answer()
    
    await asyncio.sleep(1)
    await show_question(callback.message, session, callback.from_user.id)


async def show_question(message: Message, session, user_id: int):
    """Joriy savolni ko'rsatish"""
    question = session.current_question
    
    if not question:
        # Test tugadi
        await finish_quiz(message, user_id)
        return
    
    # Savol matni
    time_limit = session.time_limit
    
    question_text = (
        f"<b>{session.current_index + 1}-savol:</b> ({session.progress})\n\n"
        f"{question.text}\n\n"
        f"⏱ <b>Vaqt: {time_limit} soniya</b>"
    )
    
    # Xabarni yuborish
    sent_message = await message.answer(
        question_text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.question_options(question, session.current_index)
    )
    
    # Vaqt hisoblagichini boshlash
    asyncio.create_task(
        countdown_timer(sent_message, session, user_id, session.current_index, time_limit)
    )


async def countdown_timer(message: Message, session, user_id: int, question_index: int, time_left: int):
    """Real-time countdown timer"""
    from bot.services.quiz_manager import quiz_manager
    
    while time_left > 0:
        await asyncio.sleep(1)
        time_left -= 1
        
        # Sessiya hali faolmi va shu savolda turganmi tekshirish
        current_session = quiz_manager.get_session(user_id)
        if not current_session or current_session.current_index != question_index:
            return  # Javob berilgan yoki test tugatilgan
        
        # Har 5 soniyada yoki oxirgi 5 soniyada yangilash
        if time_left <= 5 or time_left % 5 == 0:
            question = session.current_question
            if question:
                try:
                    # Vaqt ko'rsatgichni yangilash
                    time_emoji = "🔴" if time_left <= 5 else "⏱"
                    question_text = (
                        f"<b>{question_index + 1}-savol:</b> ({session.progress})\n\n"
                        f"{question.text}\n\n"
                        f"{time_emoji} <b>Vaqt: {time_left} soniya</b>"
                    )
                    await message.edit_text(
                        question_text,
                        parse_mode="HTML",
                        reply_markup=QuizKeyboard.question_options(question, question_index)
                    )
                except Exception:
                    pass  # Xabar o'chirilgan bo'lishi mumkin
    
    # Vaqt tugadi
    current_session = quiz_manager.get_session(user_id)
    if current_session and current_session.current_index == question_index:
        session.skip_question()
        
        try:
            await message.edit_text(
                "⏰ <b>Vaqt tugadi!</b>\nSavol o'tkazib yuborildi.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        if not session.is_finished:
            await asyncio.sleep(1.5)
            await show_question(message, session, user_id)
        else:
            await finish_quiz(message, user_id)


@router.callback_query(F.data == "stop_quiz")
async def stop_quiz(callback: CallbackQuery, state: FSMContext):
    """Testni to'xtatish"""
    session = quiz_manager.get_session(callback.from_user.id)
    
    if not session:
        await callback.answer("❌ Faol test topilmadi", show_alert=True)
        return
    
    # Testni tugatish
    await callback.message.edit_text(
        "🛑 <b>Test to'xtatildi!</b>",
        parse_mode="HTML"
    )
    
    await callback.answer("Test to'xtatildi")
    
    # Natijani ko'rsatish
    await finish_quiz(callback.message, callback.from_user.id)


@router.callback_query(F.data.startswith("answer:"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    """Javobni qabul qilish"""
    parts = callback.data.split(":")
    question_index = int(parts[1])
    option_index = int(parts[2])
    
    session = quiz_manager.get_session(callback.from_user.id)
    
    if not session:
        await callback.answer("❌ Faol test topilmadi", show_alert=True)
        return
    
    # Javobni tekshirish
    if session.current_index != question_index:
        await callback.answer("⚠️ Bu savol allaqachon javob berilgan", show_alert=True)
        return
    
    is_correct, correct_answer = session.answer_question(option_index)
    
    # Natija xabari
    question_number = question_index + 1
    current_question = session.quiz.questions[question_index]
    
    if is_correct:
        result_text = (
            f"✅ <b>To'g'ri!</b>\n\n"
            f"📝 <b>{question_number}-savol</b>\n"
            f"{current_question.text}"
        )
    else:
        result_text = (
            f"❌ <b>Noto'g'ri!</b>\n\n"
            f"📝 <b>{question_number}-savol</b>\n"
            f"{current_question.text}\n\n"
            f"💡 To'g'ri javob: <i>{correct_answer}</i>"
        )
    
    await callback.message.edit_text(
        result_text,
        parse_mode="HTML"
    )
    
    await callback.answer("✅ To'g'ri!" if is_correct else "❌ Noto'g'ri")
    
    # Keyingi savol yoki natija
    if not session.is_finished:
        await asyncio.sleep(1.5)
        await show_question(callback.message, session, callback.from_user.id)
    else:
        await asyncio.sleep(1)
        await finish_quiz(callback.message, callback.from_user.id)


async def finish_quiz(message: Message, user_id: int):
    """Testni tugatish va natijani ko'rsatish"""
    result = quiz_manager.end_session(user_id)
    
    if not result:
        return
    
    # Natijani saqlash
    db = await get_db()
    quiz = await db.get_quiz(result.quiz_id)
    quiz_title = quiz.title if quiz else "Noma'lum test"
    
    # Username olish
    result.username = message.chat.username or message.chat.first_name or "Foydalanuvchi"
    
    await db.save_result(result)
    
    # Statistikani yangilash
    await db.update_user_statistics(
        user_id=user_id,
        username=result.username,
        result=result
    )
    
    # Natija xabari
    result_text = StatisticsService.format_result(result, quiz_title)
    
    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.quiz_result_actions(result.quiz_id)
    )


@router.callback_query(F.data == "skip_question")
async def skip_current_question(callback: CallbackQuery):
    """Savolni o'tkazib yuborish"""
    session = quiz_manager.get_session(callback.from_user.id)
    
    if not session:
        await callback.answer("❌ Faol test topilmadi", show_alert=True)
        return
    
    session.skip_question()
    
    await callback.message.edit_text(
        "⏭ Savol o'tkazib yuborildi.",
        parse_mode="HTML"
    )
    
    await callback.answer()
    
    if not session.is_finished:
        await asyncio.sleep(1)
        await show_question(callback.message, session, callback.from_user.id)
    else:
        await finish_quiz(callback.message, callback.from_user.id)


@router.callback_query(F.data.startswith("share_quiz:"))
async def share_quiz(callback: CallbackQuery, bot: Bot):
    """Testni ulashish"""
    quiz_id = callback.data.split(":")[1]
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start=quiz_{quiz.share_code}"
    
    share_text = (
        f"🔗 <b>Test ulashish</b>\n\n"
        f"📝 <b>{quiz.title}</b>\n"
        f"❓ Savollar: {quiz.total_questions}\n\n"
        f"🔗 Havola:\n<code>{share_link}</code>\n\n"
        f"📤 Do'stlaringizga yuboring yoki \"Ulashish\" tugmasini bosing."
    )
    
    await callback.message.edit_text(
        share_text,
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.share_quiz_menu(quiz_id, quiz.share_code, bot_info.username)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("copy_link:"))
async def copy_link(callback: CallbackQuery, bot: Bot):
    """Havolani nusxalash uchun ko'rsatish"""
    quiz_id = callback.data.split(":")[1]
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if quiz:
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=quiz_{quiz.share_code}"
        # Havolani oddiy xabar ko'rinishida yuborish, foydalanuvchi oson nusxalashi yoki ulashishi uchun
        await callback.message.answer(
            f"🔗 <b>Test havolasi</b>\n\n"
            f"<code>{link}</code>",
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Test topilmadi", show_alert=True)


@router.message(F.text.func(lambda t: isinstance(t, str) and "Test ulashish" in t))
async def share_test_menu(message: Message):
    """Test ulashish menyusi"""
    db = await get_db()
    quizzes = await db.get_user_quizzes(message.from_user.id)
    
    if not quizzes:
        await message.answer(
            "📋 Sizda hali testlar yo'q.\n"
            "Avval test yarating.",
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        "🔗 <b>Ulashish uchun testni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.my_quizzes(quizzes)
    )


@router.inline_query()
async def inline_quiz_search(inline_query: InlineQuery, bot: Bot):
    """Inline rejimda quiz_XXXX kodlari bo'yicha testni ulashish"""
    query = (inline_query.query or "").strip()

    # Faqat quiz_ bilan boshlanadigan so'rovlar uchun ishlaymiz
    if not query.startswith("quiz_"):
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    share_code = query.replace("quiz_", "").upper()

    db = await get_db()
    quiz = await db.get_quiz_by_share_code(share_code)

    if not quiz:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=quiz_{quiz.share_code}"

    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title=f"{quiz.title}",
        description=f"Savollar soni: {quiz.total_questions}",
        input_message_content=InputTextMessageContent(
            message_text=(
                f"📝 <b>{quiz.title}</b>\n"
                f"❓ Savollar soni: {quiz.total_questions}\n\n"
                f"🔗 Test havolasi:\n{link}"
            ),
            parse_mode="HTML"
        )
    )

    await inline_query.answer([result], cache_time=1, is_personal=True)
