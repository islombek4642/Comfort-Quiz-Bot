"""
Group handler
Guruhda test o'tkazish
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.exceptions import TelegramRetryAfter

from bot.keyboards import QuizKeyboard, SettingsKeyboard
from bot.services.quiz_manager import quiz_manager
from bot.services import StatisticsService
from bot.database import get_db

router = Router(name="group")


@router.callback_query(F.data.startswith("group_quiz:"))
async def start_group_quiz_selection(callback: CallbackQuery, bot: Bot):
    """Guruhda test boshlash - guruh tanlash"""
    quiz_id = callback.data.split(":")[1]
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Bot username olish
    bot_info = await bot.get_me()
    
    await callback.message.edit_text(
        f"👥 <b>Guruhda test o'tkazish</b>\n\n"
        f"📝 Test: <b>{quiz.title}</b>\n\n"
        f"Guruhda test o'tkazish uchun:\n\n"
        f"1️⃣ Quyidagi tugmani bosib botni guruhga qo'shing\n"
        f"2️⃣ Botga admin huquqini bering\n"
        f"3️⃣ Guruhda quyidagi komandani yozing:\n\n"
        f"<code>/startquiz {quiz.share_code}</code>",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.add_bot_to_group(bot_info.username, quiz_id)
    )
    await callback.answer()


@router.message(F.text.startswith("/startquiz"))
async def start_quiz_in_group(message: Message, bot: Bot):
    """Guruhda testni boshlash"""
    # Faqat guruhda ishlaydi
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer(
            "❌ Bu komanda faqat guruhlarda ishlaydi.",
            parse_mode="HTML"
        )
        return
    
    # Mavjud sessiya bormi tekshirish
    if quiz_manager.get_group_session(message.chat.id):
        await message.answer(
            "⚠️ Bu guruhda allaqachon test o'tkazilmoqda.",
            parse_mode="HTML"
        )
        return
    
    # Admin ekanligini tekshirish
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer(
            "❌ Faqat adminlar test boshlashi mumkin.",
            parse_mode="HTML"
        )
        return
    
    # Share code ni olish
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Test kodi kiritilmagan.\n"
            "Format: <code>/startquiz KODINGIZ</code>",
            parse_mode="HTML"
        )
        return
    
    share_code = parts[1].upper()
    
    db = await get_db()
    quiz = await db.get_quiz_by_share_code(share_code)
    
    if not quiz:
        await message.answer(
            "❌ Test topilmadi. Kodni tekshiring.",
            parse_mode="HTML"
        )
        return
    
    # Yangi guruh sessiyasi yaratish
    session = quiz_manager.create_group_session(
        chat_id=message.chat.id,
        quiz=quiz,
        creator_id=message.from_user.id
    )
    
    total_questions = len(quiz.questions)
    
    # Agar 20 ta yoki undan kam savol bo'lsa, faqat to'liq test
    if total_questions <= 20:
        from bot.models import QuizSettings
        settings = QuizSettings(quiz_mode="full")
        session.settings = settings
        session._prepare_quiz_with_settings()
        
        await message.answer(
            f"🎯 <b>{quiz.title}</b>\n\n"
            f"📚 <b>To'liq test</b> tanlandi\n"
            f"Savollar soni: {total_questions}\n\n"
            f"Test 10 soniyadan keyin boshlanadi...",
            parse_mode="HTML"
        )
        
        await asyncio.sleep(10)
        await show_group_question(message, session)
    else:
        # 20 dan ko'p savol bo'lsa, rejim tanlash
        mode_msg = await message.answer(
            f"🎯 <b>{quiz.title}</b>\n\n"
            f"📚 <b>Test rejimini tanlang:</b>\n\n"
            f"📊 Jami savollar: <b>{total_questions}</b> ta\n\n"
            f"• <b>To'liq test</b> - Barcha {total_questions} ta savolni yechish\n"
            f"• <b>Oraliq test</b> - Masalan, 50-100 savollarni yechish\n"
            f"• <b>Tasodifiy test</b> - Masalan, 30 ta tasodifiy savol",
            parse_mode="HTML",
            reply_markup=QuizKeyboard.group_quiz_mode_menu(message.chat.id)
        )


async def group_ready_countdown(message: Message, session, seconds: int):
    """30 soniyalik tayyorgarlik countdown"""
    for remaining in range(seconds, 0, -1):
        await asyncio.sleep(1)
        
        # Sessiya hali faolmi
        current_session = quiz_manager.get_group_session(session.chat_id)
        if not current_session:
            return
        
        # Har 5 soniyada yangilash
        if remaining % 5 == 0 or remaining <= 5:
            try:
                # Session'dagi ishtirokchilar sonini olish
                ready_count = len(current_session.participants)
                time_emoji = "🔴" if remaining <= 5 else "⏳"
                
                await message.edit_text(
                    f"🎯 <b>{session.quiz.title}</b>\n\n"
                    f"👥 Guruh testi tayyorlanmoqda!\n"
                    f"❓ Savollar soni: {session.quiz.total_questions}\n"
                    f"⏱ Vaqt: {session.quiz.time_display}\n\n"
                    f"{time_emoji} <b>Test {remaining} soniyadan keyin boshlanadi...</b>\n"
                    f"✅ Tayyor: {ready_count} kishi",
                    parse_mode="HTML",
                    reply_markup=QuizKeyboard.group_ready_button(str(session.chat_id))
                )
            except Exception:
                pass
    
    # Test boshlash
    current_session = quiz_manager.get_group_session(session.chat_id)
    if current_session:
        ready_count = len(current_session.participants)
        try:
            await message.edit_text(
                f"🎯 <b>Test boshlanmoqda!</b>\n\n"
                f"✅ Ishtirokchilar: {ready_count} kishi",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    await asyncio.sleep(2)
    await show_group_question(message, session)


@router.callback_query(F.data.startswith("group_ready:"))
async def group_ready_callback(callback: CallbackQuery):
    """Tayyorman tugmasi bosilganda"""
    session_id = callback.data.split(":")[1]
    chat_id = int(session_id)
    
    session = quiz_manager.get_group_session(chat_id)
    if not session:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Foydalanuvchini ro'yxatga olish
    session.add_participant(
        callback.from_user.id,
        callback.from_user.username or callback.from_user.first_name
    )
    
    await callback.answer("✅ Siz ro'yxatga olindingiz!")


async def show_group_question(message: Message, session):
    """Guruhda savolni ko'rsatish"""
    question = session.current_question
    
    if not question:
        await finish_group_quiz(message, session)
        return
    
    # Savol matni
    progress = f"{session.current_index + 1}/{len(session.quiz.questions)}"
    time_limit = session.quiz.time_per_question
    
    question_text = (
        f"<b>{session.current_index + 1}-savol</b> ({progress})\n\n"
        f"```\n{question.text}\n```\n\n"
        f"⏱ <b>Vaqt: {time_limit} soniya</b>\n"
        f"👥 Javob berganlar: 0\n\n"
        f"<i>Admin: testni to'xtatish uchun /stop</i>"
    )
    
    # Savol xabari (variantlar bilan)
    question_msg = await message.answer(
        question_text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.group_question_options(
            question, 
            session.current_index,
            str(session.chat_id)
        )
    )
    
    # Timer boshlash
    asyncio.create_task(
        group_countdown_timer(question_msg, session, session.current_index, time_limit)
    )


async def update_group_question(question_msg: Message, session):
    """Guruhda savolni xabarni edit qilish (yangi xabar emas)"""
    question = session.current_question
    
    if not question:
        await finish_group_quiz(question_msg, session)
        return
    
    # Savol matni
    progress = f"{session.current_index + 1}/{len(session.quiz.questions)}"
    time_limit = session.quiz.time_per_question
    
    question_text = (
        f"<b>{session.current_index + 1}-savol</b> ({progress})\n\n"
        f"```\n{question.text}\n```\n\n"
        f"⏱ <b>Vaqt: {time_limit} soniya</b>\n"
        f"👥 Javob berganlar: 0\n\n"
        f"<i>Admin: testni to'xtatish uchun /stop</i>"
    )
    
    # Xabarni edit qilish
    try:
        await question_msg.edit_text(
            question_text,
            parse_mode="HTML",
            reply_markup=QuizKeyboard.group_question_options(
                question, 
                session.current_index,
                str(session.chat_id)
            )
        )
    except Exception:
        pass
    
    # Timer boshlash
    asyncio.create_task(
        group_countdown_timer(question_msg, session, session.current_index, time_limit)
    )


async def group_countdown_timer(question_msg: Message, session, question_index: int, time_left: int):
    """Guruh uchun real-time countdown timer"""
    while time_left > 0:
        await asyncio.sleep(1)
        time_left -= 1
        
        # Sessiya hali faolmi va shu savolda turganmi
        current_session = quiz_manager.get_group_session(session.chat_id)
        if not current_session or current_session.current_index != question_index:
            return
        
        # Faqat muhim paytlarda yangilash (flood control)
        # 20, 15, 10, 5 soniya va oxirgi 5 soniyada har soniyada
        should_update = (
            time_left in [20, 15, 10, 5] or  # Muhim nuqtalar
            time_left <= 5  # Oxirgi 5 soniya
        )
        
        if should_update:
            question = session.current_question
            if question:
                try:
                    progress = f"{question_index + 1}/{len(session.quiz.questions)}"
                    answered = len(session.answered_current)
                    time_emoji = "🔴" if time_left <= 5 else "⏱"
                    
                    question_text = (
                        f"<b>{question_index + 1}-savol</b> ({progress})\n\n"
                        f"```\n{question.text}\n```\n\n"
                        f"{time_emoji} <b>Vaqt: {time_left} soniya</b>\n"
                        f"👥 Javob berganlar: {answered}\n\n"
                        f"<i>Admin: testni to'xtatish uchun /stop</i>"
                    )
                    
                    await question_msg.edit_text(
                        question_text,
                        parse_mode="HTML",
                        reply_markup=QuizKeyboard.group_question_options(
                            question, question_index, str(session.chat_id)
                        )
                    )
                    
                except Exception:
                    pass  # Flood control xatosi bo'lsa, o'tkazib yuborish
    
    # Vaqt tugadi - savol va to'g'ri javobni ko'rsatish
    current_session = quiz_manager.get_group_session(session.chat_id)
    if current_session and current_session.current_index == question_index:
        question = session.current_question
        if question:
            progress = f"{question_index + 1}/{len(session.quiz.questions)}"
            
            # To'g'ri javobni olish
            correct_answer = question.correct_answer
            correct_letter = question.get_option_letter(question.correct_index)
            
            result_text = (
                f"⏰ <b>Vaqt tugadi!</b>\n\n"
                f"<b>{question_index + 1}-savol</b> ({progress})\n\n"
                f"{question.text}\n\n"
                f"✅ <b>To'g'ri javob: {correct_letter}) {correct_answer}</b>"
            )
            
            try:
                await question_msg.edit_text(
                    result_text,
                    parse_mode="HTML"
                )
            except Exception:
                pass
        
        if current_session.next_question():
            await asyncio.sleep(3)  # 3 soniya kutish (odamlar o'qishi uchun)
            # Keyingi savolni YANGI xabar sifatida yuborish, flood control xatolarini hisobga olib
            try:
                await show_group_question(question_msg, current_session)
            except TelegramRetryAfter as e:
                # Telegram flood control: biroz kutib, yana urinib ko'rish
                await asyncio.sleep(e.retry_after)
                try:
                    await show_group_question(question_msg, current_session)
                except Exception:
                    pass
            except Exception:
                # Har qanday boshqa xatoni e'tiborsiz qoldirish (testni to'xtatmaslik uchun)
                pass
        else:
            await asyncio.sleep(2)
            await finish_group_quiz(question_msg, current_session)


@router.callback_query(F.data.startswith("group_answer:"))
async def process_group_answer(callback: CallbackQuery):
    """Guruhda javobni qabul qilish"""
    parts = callback.data.split(":")
    session_id = parts[1]
    question_index = int(parts[2])
    option_index = int(parts[3])
    
    chat_id = int(session_id)
    session = quiz_manager.get_group_session(chat_id)
    
    if not session:
        await callback.answer("❌ Test tugagan", show_alert=True)
        return
    
    # Allaqachon javob berganmi
    if session.has_answered(callback.from_user.id):
        await callback.answer("⚠️ Siz allaqachon javob berdingiz", show_alert=True)
        return
    
    # Savol indeksini tekshirish
    if session.current_index != question_index:
        await callback.answer("⚠️ Bu savol tugagan", show_alert=True)
        return
    
    # Javobni qayd qilish (natijani ko'rsatmaslik)
    session.answer_question(
        user_id=callback.from_user.id,
        username=callback.from_user.username or callback.from_user.first_name,
        option_index=option_index
    )
    
    # Faqat qabul qilinganini bildirish
    await callback.answer("✅ Javobingiz qabul qilindi!")


@router.callback_query(F.data.startswith("group_next:"))
async def next_group_question(callback: CallbackQuery):
    """Keyingi savolga o'tish (admin uchun)"""
    session_id = callback.data.split(":")[1]
    chat_id = int(session_id)
    
    session = quiz_manager.get_group_session(chat_id)
    
    if not session:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Admin tekshirish
    if callback.from_user.id != session.creator_id:
        await callback.answer("⚠️ Faqat test boshlagan admin o'tkazishi mumkin", show_alert=True)
        return
    
    if session.next_question():
        await callback.answer()
        await show_group_question(callback.message, session)
    else:
        await finish_group_quiz(callback.message, session)


@router.callback_query(F.data.startswith("group_end:"))
async def end_group_quiz(callback: CallbackQuery):
    """Testni muddatidan oldin tugatish"""
    session_id = callback.data.split(":")[1]
    chat_id = int(session_id)
    
    session = quiz_manager.get_group_session(chat_id)
    
    if not session:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    if callback.from_user.id != session.creator_id:
        await callback.answer("⚠️ Faqat admin tugatishi mumkin", show_alert=True)
        return
    
    await finish_group_quiz(callback.message, session)
    await callback.answer()


@router.callback_query(F.data.startswith("group_stop:"))
async def stop_group_quiz(callback: CallbackQuery):
    """Testni to'xtatish (admin uchun)"""
    session_id = callback.data.split(":")[1]
    chat_id = int(session_id)
    
    session = quiz_manager.get_group_session(chat_id)
    
    if not session:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Faqat admin to'xtata oladi
    if callback.from_user.id != session.creator_id:
        await callback.answer("⚠️ Faqat admin testni to'xtata oladi", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛑 <b>Test admin tomonidan to'xtatildi!</b>",
        parse_mode="HTML"
    )
    
    await callback.answer("Test to'xtatildi")
    
    # Natijalarni ko'rsatish
    await finish_group_quiz(callback.message, session)


@router.callback_query(F.data == "refresh_count")
async def refresh_answer_count(callback: CallbackQuery):
    """Javob berganlar sonini yangilash"""
    await callback.answer("Avtomatik yangilanadi")


@router.message(F.text.startswith("/stop"))
async def stop_group_quiz_command(message: Message, bot: Bot):
    """Testni /stop komandasi bilan to'xtatish"""
    # Faqat guruhda ishlaydi
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    session = quiz_manager.get_group_session(message.chat.id)
    if not session:
        await message.answer(
            "❌ Faol test topilmadi.",
            parse_mode="HTML"
        )
        return
    
    # Faqat test boshlagan yoki admin to'xtata oladi
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if message.from_user.id != session.creator_id and member.status not in ["creator", "administrator"]:
        await message.answer(
            "❌ Faqat test boshlagan yoki admin testni to'xtata oladi.",
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        "🛑 <b>Test to'xtatildi!</b>",
        parse_mode="HTML"
    )
    
    # Natijalarni ko'rsatish
    await finish_group_quiz(message, session)


async def finish_group_quiz(message: Message, session):
    """Guruh testini tugatish"""
    quiz_manager.end_group_session(session.chat_id)
    
    # Natijalar
    leaderboard = session.get_leaderboard()
    
    result_text = StatisticsService.format_leaderboard(
        leaderboard,
        session.quiz.title
    )
    
    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=QuizKeyboard.group_result_actions(session.quiz.id, session.creator_id)
    )


@router.callback_query(F.data.startswith("group_restart:"))
async def restart_group_quiz(callback: CallbackQuery, bot: Bot):
    """Guruh testini qayta boshlash"""
    quiz_id = callback.data.split(":")[1]
    
    # Admin tekshirish
    member = await bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await callback.answer("⚠️ Faqat admin qayta boshlashi mumkin", show_alert=True)
        return
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    # Mavjud sessiyani tugatish
    quiz_manager.end_group_session(callback.message.chat.id)
    
    # Yangi sessiya
    session = quiz_manager.create_group_session(
        chat_id=callback.message.chat.id,
        quiz=quiz,
        creator_id=callback.from_user.id
    )

    total_questions = len(quiz.questions)

    # Agar 20 ta yoki undan kam savol bo'lsa, to'g'ridan-to'g'ri to'liq testni boshlash
    if total_questions <= 20:
        from bot.models import QuizSettings
        settings = QuizSettings(quiz_mode="full")
        session.settings = settings
        session._prepare_quiz_with_settings()

        await callback.message.answer(
            f"🔄 <b>{quiz.title}</b>\n\n"
            f"📚 <b>To'liq test</b> tanlandi\n"
            f"Savollar soni: {total_questions}\n\n"
            f"Test 10 soniyadan keyin boshlanadi...",
            parse_mode="HTML"
        )

        await callback.answer()
        await asyncio.sleep(10)
        await show_group_question(callback.message, session)
    else:
        # 20 dan ko'p savol bo'lsa, rejim tanlash menyusini ko'rsatish
        await callback.message.answer(
            f"🔄 <b>{quiz.title}</b>\n\n"
            f"📚 <b>Test rejimini tanlang:</b>\n\n"
            f"📊 Jami savollar: <b>{total_questions}</b> ta\n\n"
            f"• <b>To'liq test</b> - Barcha {total_questions} ta savolni yechish\n"
            f"• <b>Oraliq test</b> - Masalan, 50-100 savollarni yechish\n"
            f"• <b>Tasodifiy test</b> - Masalan, 30 ta tasodifiy savol",
            parse_mode="HTML",
            reply_markup=QuizKeyboard.group_quiz_mode_menu(callback.message.chat.id)
        )

        await callback.answer()


# Bot guruhga qo'shilganda
@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group(event: ChatMemberUpdated):
    """Bot guruhga qo'shilganda"""
    await event.answer(
        "👋 Salom! Men Quiz Botman.\n\n"
        "Guruhda test o'tkazish uchun:\n"
        "1. Menga admin huquqini bering\n"
        "2. <code>/startquiz TESTKODI</code> yozing\n\n"
        "Test kodini shaxsiy chatda yaratishingiz mumkin.",
        parse_mode="HTML"
    )
