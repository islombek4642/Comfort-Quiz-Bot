"""
Cancel handler
Bekor qilish va /cancel komandasi
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards import MainMenuKeyboard
from bot.services.quiz_manager import quiz_manager

router = Router(name="cancel")


@router.message(Command("cancel"))
@router.message(F.text == "❌ Bekor qilish")
async def cmd_cancel(message: Message, state: FSMContext):
    """
    /cancel komandasi yoki Bekor qilish tugmasi
    Joriy amalni bekor qiladi
    """
    current_state = await state.get_state()
    
    # Faol quiz sessiyasini tugatish
    if quiz_manager.has_active_session(message.from_user.id):
        quiz_manager.end_session(message.from_user.id)
    
    await state.clear()
    
    if current_state:
        await message.answer(
            "❌ <b>Bekor qilindi.</b>\n\n"
            "Yangi Word fayl yuklash uchun tayyorman.",
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.main_menu()
        )
    else:
        await message.answer(
            "🤷 Bekor qiladigan narsa yo'q.\n\n"
            "Yangi test yaratish uchun \"📄 Test yuklash\" tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=MainMenuKeyboard.main_menu()
        )


@router.message(F.text == "⬅️ Orqaga")
async def back_button(message: Message, state: FSMContext):
    """Orqaga tugmasi"""
    await state.clear()
    
    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=MainMenuKeyboard.main_menu()
    )


@router.callback_query(F.data == "back_to_quiz_menu")
async def back_to_quiz_menu(callback: CallbackQuery):
    """Quiz menyusiga qaytish"""
    await callback.message.answer(
        "📋 Menyuga qaytish uchun tugmani bosing.",
        reply_markup=MainMenuKeyboard.main_menu()
    )
    await callback.answer()
