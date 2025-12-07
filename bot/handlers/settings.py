"""
Settings handler
Test sozlamalari (sarlavha, vaqt, aralashtirish)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import QuizStates
from bot.keyboards import MainMenuKeyboard, SettingsKeyboard
from bot.models import Quiz, Question
from bot.database import get_db

router = Router(name="settings")


@router.message(QuizStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Test sarlavhasini qabul qilish"""
    title = message.text.strip()
    
    # Sarlavha uzunligini tekshirish
    if len(title) < 3:
        await message.answer(
            "❌ Sarlavha juda qisqa. Kamida 3 ta belgi bo'lishi kerak.",
            parse_mode="HTML"
        )
        return
    
    if len(title) > 100:
        await message.answer(
            "❌ Sarlavha juda uzun. Maksimum 100 ta belgi.",
            parse_mode="HTML"
        )
        return
    
    # Sarlavhani saqlash
    await state.update_data(quiz_title=title)
    await state.set_state(QuizStates.waiting_for_time)
    
    await message.answer(
        f"✅ <b>Sarlavha:</b> {title}\n\n"
        f"⏱ Endi har bir savol uchun vaqtni tanlang:",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.time_selection()
    )


@router.callback_query(QuizStates.waiting_for_time, F.data.startswith("time:"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Vaqt tanlash"""
    time_value = int(callback.data.split(":")[1])
    
    # Vaqtni saqlash
    await state.update_data(time_per_question=time_value)
    await state.set_state(QuizStates.waiting_for_shuffle)
    
    # Vaqtni chiroyli ko'rsatish
    if time_value == 0:
        time_text = "Cheksiz"
    elif time_value >= 60:
        time_text = f"{time_value // 60} daqiqa"
    else:
        time_text = f"{time_value} soniya"
    
    await callback.message.edit_text(
        f"⏱ <b>Vaqt:</b> {time_text}\n\n"
        f"🔀 Endi variantlar aralashtirilishini tanlang:",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.shuffle_selection()
    )
    await callback.answer()


@router.callback_query(QuizStates.waiting_for_shuffle, F.data.startswith("shuffle:"))
async def process_shuffle(callback: CallbackQuery, state: FSMContext):
    """Aralashtirish rejimini tanlash"""
    shuffle_value = callback.data.split(":")[1] == "yes"
    
    # Saqlash
    await state.update_data(shuffle_options=shuffle_value)
    
    # Ma'lumotlarni olish
    data = await state.get_data()
    
    # Quiz yaratish
    questions = [
        Question(
            id=q["id"],
            text=q["text"],
            options=q["options"],
            correct_index=q["correct_index"],
            original_options=q.get("original_options", q["options"])
        )
        for q in data["questions"]
    ]
    
    quiz = Quiz(
        id=data["quiz_id"],
        title=data["quiz_title"],
        questions=questions,
        creator_id=data["creator_id"],
        time_per_question=data["time_per_question"],
        shuffle_options=shuffle_value
    )
    
    # Database'ga saqlash
    db = await get_db()
    await db.save_quiz(quiz)
    
    # Statistikani yangilash
    await db.update_user_statistics(
        user_id=callback.from_user.id,
        username=callback.from_user.username or callback.from_user.first_name,
        quiz_created=True
    )
    
    # Quiz ID ni yangilash
    await state.update_data(current_quiz_id=quiz.id)
    await state.set_state(QuizStates.quiz_ready)
    
    # Natija xabari
    shuffle_text = "Ha ✅" if shuffle_value else "Yo'q ❌"
    
    await callback.message.edit_text(
        f"✅ <b>Test tayyor!</b>\n\n"
        f"📝 <b>Sarlavha:</b> {quiz.title}\n"
        f"❓ <b>Savollar soni:</b> {quiz.total_questions}\n"
        f"⏱ <b>Vaqt:</b> {quiz.time_display}\n"
        f"🔀 <b>Aralashtirish:</b> {shuffle_text}\n"
        f"🔗 <b>Ulashish kodi:</b> <code>{quiz.share_code}</code>\n\n"
        f"Quyidagi tugmalardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.quiz_ready(quiz.id)
    )
    await callback.answer("✅ Test tayyor!")


@router.callback_query(F.data == "cancel_setup")
async def cancel_setup(callback: CallbackQuery, state: FSMContext):
    """Sozlashni bekor qilish"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Test yaratish bekor qilindi.",
        parse_mode="HTML"
    )
    
    await callback.message.answer(
        "🏠 Bosh menyu",
        reply_markup=MainMenuKeyboard.main_menu()
    )
    await callback.answer()


@router.message(F.text == "📋 Mening testlarim")
async def my_quizzes(message: Message):
    """Foydalanuvchi testlari ro'yxati"""
    db = await get_db()
    quizzes = await db.get_user_quizzes(message.from_user.id)
    
    if not quizzes:
        await message.answer(
            "📋 Sizda hali testlar yo'q.\n\n"
            "Yangi test yaratish uchun \"📄 Test yuklash\" tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.main_menu()
        )
        return
    
    await message.answer(
        f"📋 <b>Sizning testlaringiz</b>\n\n"
        f"Jami: {len(quizzes)} ta test",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.my_quizzes(quizzes)
    )


@router.callback_query(F.data.startswith("quiz_view:"))
async def view_quiz(callback: CallbackQuery):
    """Quiz ma'lumotlarini ko'rish"""
    quiz_id = callback.data.split(":")[1]
    
    db = await get_db()
    quiz = await db.get_quiz(quiz_id)
    
    if not quiz:
        await callback.answer("❌ Test topilmadi", show_alert=True)
        return
    
    shuffle_text = "Ha ✅" if quiz.shuffle_options else "Yo'q ❌"
    
    await callback.message.edit_text(
        f"📝 <b>{quiz.title}</b>\n\n"
        f"❓ Savollar: <b>{quiz.total_questions}</b>\n"
        f"⏱ Vaqt: <b>{quiz.time_display}</b>\n"
        f"🔀 Aralashtirish: {shuffle_text}\n"
        f"🔗 Ulashish kodi: <code>{quiz.share_code}</code>\n"
        f"📅 Yaratilgan: {quiz.created_at.strftime('%d.%m.%Y')}",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.quiz_ready(quiz.id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_quiz:"))
async def delete_quiz_confirm(callback: CallbackQuery):
    """O'chirishni tasdiqlash"""
    quiz_id = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        "⚠️ <b>Testni o'chirmoqchimisiz?</b>\n\n"
        "Bu amalni qaytarib bo'lmaydi!",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.confirm_delete(quiz_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_quiz(callback: CallbackQuery):
    """Testni o'chirish"""
    quiz_id = callback.data.split(":")[1]
    
    db = await get_db()
    success = await db.delete_quiz(quiz_id)
    
    if success:
        # Testlar ro'yxatiga qaytish
        quizzes = await db.get_user_quizzes(callback.from_user.id)
        
        if quizzes:
            await callback.message.edit_text(
                f"✅ Test o'chirildi!\n\n"
                f"📋 <b>Sizning testlaringiz</b>\n"
                f"Jami: {len(quizzes)} ta test",
                parse_mode="HTML",
                reply_markup=MainMenuKeyboard.my_quizzes(quizzes)
            )
        else:
            await callback.message.edit_text(
                "✅ Test o'chirildi!\n\n"
                "📋 Sizda boshqa testlar yo'q.",
                parse_mode="HTML"
            )
        await callback.answer("O'chirildi")
    else:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "my_quizzes_list")
async def my_quizzes_list_callback(callback: CallbackQuery):
    """Mening testlarim ro'yxatiga qaytish"""
    db = await get_db()
    quizzes = await db.get_user_quizzes(callback.from_user.id)
    
    if not quizzes:
        await callback.message.edit_text(
            "📋 Sizda hali testlar yo'q.\n\n"
            "Yangi test yaratish uchun \"📄 Test yuklash\" tugmasini bosing.",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"📋 <b>Sizning testlaringiz</b>\n\n"
        f"Jami: {len(quizzes)} ta test",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.my_quizzes(quizzes)
    )
    await callback.answer()
