"""
Start Quiz handler
/startquiz komandasi - guruh va private chat uchun
/stop komandasi - guruh test to'xtatish
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from bot.keyboards import QuizKeyboard, SettingsKeyboard
from bot.database import get_db
from bot.models import Quiz
from bot.services.quiz_manager import quiz_manager

router = Router(name="startquiz")


@router.message(Command("startquiz"))
async def cmd_startquiz(message: Message, state: FSMContext):
    """
    /startquiz komandasi
    Guruh va private chat'da test boshlash
    Masalan: /startquiz 4CF93F
    """
    await state.clear()
    
    # Quiz ID'ni olish
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if not args:
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Masalan: <code>/startquiz 4CF93F</code>",
            parse_mode="HTML"
        )
        return
    
    # "quiz_" prefix'ini olib tashlash (agar bo'lsa)
    share_code = args.replace("quiz_", "") if args.startswith("quiz_") else args
    
    db = await get_db()
    # Share code bilan topish
    quiz = await db.get_quiz_by_share_code(share_code)
    
    if not quiz:
        await message.answer(
            "❌ Test topilmadi yoki o'chirilgan.",
            parse_mode="HTML"
        )
        return
    
    # GURUH CHAT'DA
    if message.chat.type in ["group", "supergroup"]:
        # Guruh sessiyasini yaratish
        session = quiz_manager.create_group_session(
            chat_id=message.chat.id,
            quiz=quiz,
            creator_id=message.from_user.id
        )
        
        # Guruh rejim menyusini ko'rsatish
        await message.answer(
            f"👥 <b>Guruh testi: {quiz.title}</b>\n\n"
            f"❓ Savollar soni: <b>{quiz.total_questions}</b>\n"
            f"⏱ Vaqt: <b>{quiz.time_display}</b>\n\n"
            f"<b>Test rejimini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=QuizKeyboard.group_quiz_mode_menu(message.chat.id)
        )
        
        # State'ga guruh ma'lumotlarini saqlash
        await state.update_data(
            group_chat_id=message.chat.id,
            quiz_id=quiz.id
        )
        return
    
    # PRIVATE CHAT'DA
    # Agar bu test boshqa foydalanuvchi tomonidan yaratilgan bo'lsa,
    # joriy foydalanuvchi uchun shaxsiy nusxa yaratamiz
    if quiz.creator_id != message.from_user.id:
        cloned_quiz = Quiz(
            title=quiz.title,
            questions=quiz.questions,
            creator_id=message.from_user.id,
            time_per_question=quiz.time_per_question,
            shuffle_options=quiz.shuffle_options,
        )
        
        # Yangi quizni saqlash
        await db.save_quiz(cloned_quiz)
        
        # Statistika: foydalanuvchi uchun "yaratilgan test" sifatida hisoblash
        await db.update_user_statistics(
            user_id=message.from_user.id,
            username=message.from_user.username or message.from_user.first_name,
            quiz_created=True
        )
        
        quiz = cloned_quiz
    
    # Test topildi, rejim tanlash menyusini ko'rsatish
    await message.answer(
        f"📝 <b>Test topildi!</b>\n\n"
        f"📌 Sarlavha: <b>{quiz.title}</b>\n"
        f"❓ Savollar soni: <b>{quiz.total_questions}</b>\n"
        f"⏱ Vaqt: <b>{quiz.time_display}</b>\n\n"
        f"<b>Test rejimini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.quiz_ready(quiz.id)
    )
    
    # Quizni state'ga saqlash
    await state.update_data(shared_quiz_id=quiz.id)


# /stop komandasi - Guruhda test to'xtatish
@router.message(Command("stop"))
async def cmd_stop_group_quiz(message: Message):
    """Testni /stop komandasi bilan to'xtatish"""
    from aiogram import Bot
    
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
    bot = message.bot
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
    
    # Natijalarni ko'rsatish (group.py'dan import qilish kerak)
    from bot.handlers.group import finish_group_quiz
    await finish_group_quiz(message, session)
