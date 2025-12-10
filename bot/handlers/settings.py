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

    # Unicode belgilar sonini hisoblash
    title_len = len(title)
    
    if title_len < 3:
        await message.answer("❌ Sarlavha juda qisqa. Kamida 3 ta belgi bo'lishi kerak.")
        return

    if title_len > 100:
        await message.answer("❌ Sarlavha juda uzun. Maksimum 100 ta belgi.")
        return

    # Sarlavhani saqlash
    await state.update_data(quiz_title=title)
    await state.set_state(QuizStates.waiting_for_time)

    await message.answer(
        f"✅ <b>Sarlavha:</b> {title}\n\n⏱ Endi har bir savol uchun vaqtni tanlang:",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.time_selection()
    )


@router.callback_query(QuizStates.waiting_for_time, F.data.startswith("time:"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Vaqt tanlash"""
    try:
        time_value = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Noto‘g‘ri vaqt qiymati", show_alert=True)
        return

    # Vaqtni saqlash
    await state.update_data(time_per_question=time_value)
    await state.set_state(QuizStates.waiting_for_shuffle)

    # Vaqtni chiroyli ko‘rsatish
    if time_value == 0:
        time_text = "Cheksiz"
    else:
        minutes = time_value // 60
        seconds = time_value % 60
        time_text = f"{minutes} daqiqa {seconds} soniya" if minutes else f"{seconds} soniya"

    await callback.message.edit_text(
        f"⏱ <b>Vaqt:</b> {time_text}\n\n🔀 Endi variantlar aralashtirilishini tanlang:",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.shuffle_selection()
    )
    await callback.answer()


@router.callback_query(QuizStates.waiting_for_shuffle, F.data.startswith("shuffle:"))
async def process_shuffle(callback: CallbackQuery, state: FSMContext):
    """Aralashtirish rejimini tanlash"""
    try:
        value = callback.data.split(":")[1]
        shuffle_value = True if value.lower() == "yes" else False
    except IndexError:
        await callback.answer("❌ Noto‘g‘ri format", show_alert=True)
        return

    await state.update_data(shuffle_options=shuffle_value)

    # Ma'lumotlarni olish
    data = await state.get_data()
    questions_data = data.get("questions", [])

    if not questions_data:
        await callback.answer("❌ Savollar topilmadi", show_alert=True)
        return

    questions = [
        Question(
            id=q.get("id"),
            text=q.get("text"),
            options=q.get("options"),
            correct_index=q.get("correct_index"),
            original_options=q.get("original_options", q.get("options"))
        )
        for q in questions_data
    ]

    quiz = Quiz(
        id=data.get("quiz_id"),
        title=data.get("quiz_title"),
        questions=questions,
        creator_id=data.get("creator_id"),
        time_per_question=data.get("time_per_question"),
        shuffle_options=shuffle_value
    )

    # Database ga saqlash
    db = await get_db()
    try:
        await db.save_quiz(quiz)
        await db.update_user_statistics(
            user_id=callback.from_user.id,
            username=callback.from_user.username or callback.from_user.first_name,
            quiz_created=True
        )
    except Exception as e:
        await callback.answer(f"❌ Xatolik yuz berdi: {e}", show_alert=True)
        return

    await state.update_data(current_quiz_id=quiz.id)
    await state.set_state(QuizStates.quiz_ready)

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
    await callback.message.edit_text("❌ Test yaratish bekor qilindi.", parse_mode="HTML")
    await callback.message.answer("🏠 Bosh menyu", reply_markup=MainMenuKeyboard.main_menu())
    await callback.answer()


# Foydalanuvchi testlari bilan ishlash
@router.message(F.text == "📋 Mening testlarim")
async def my_quizzes(message: Message):
    """Foydalanuvchi testlari ro'yxati"""
    db = await get_db()
    quizzes = await db.get_user_quizzes(message.from_user.id) or []

    if not quizzes:
        await message.answer(
            "📋 Sizda hali testlar yo'q.\n\nYangi test yaratish uchun \"📄 Test yuklash\" tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.main_menu()
        )
        return

    await message.answer(
        f"📋 <b>Sizning testlaringiz</b>\n\nJami: {len(quizzes)} ta test",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.my_quizzes(quizzes)
    )


# Testni ko‘rish va o‘chirish
@router.callback_query(F.data.startswith("quiz_view:"))
async def view_quiz(callback: CallbackQuery):
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
    quiz_id = callback.data.split(":")[1]
    await callback.message.edit_text(
        "⚠️ <b>Testni o'chirmoqchimisiz?</b>\n\nBu amalni qaytarib bo'lmaydi!",
        parse_mode="HTML",
        reply_markup=SettingsKeyboard.confirm_delete(quiz_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_quiz(callback: CallbackQuery):
    quiz_id = callback.data.split(":")[1]
    db = await get_db()
    success = await db.delete_quiz(quiz_id)

    if success:
        quizzes = await db.get_user_quizzes(callback.from_user.id) or []
        if quizzes:
            await callback.message.edit_text(
                f"✅ Test o'chirildi!\n\n📋 <b>Sizning testlaringiz</b>\nJami: {len(quizzes)} ta test",
                parse_mode="HTML",
                reply_markup=MainMenuKeyboard.my_quizzes(quizzes)
            )
        else:
            await callback.message.edit_text("✅ Test o'chirildi!\n\n📋 Sizda boshqa testlar yo'q.", parse_mode="HTML")
        await callback.answer("O'chirildi")
    else:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
