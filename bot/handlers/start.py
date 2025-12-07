"""
Start handler
/start komandasi va asosiy menyu
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards import MainMenuKeyboard, SettingsKeyboard
from bot.database import get_db
from bot.states import QuizStates

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    /start komandasi
    Deep link orqali test boshlash ham mumkin
    """
    await state.clear()
    
    # Deep link tekshirish (quiz_XXXXXX)
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if args and args.startswith("quiz_"):
        share_code = args.replace("quiz_", "")
        db = await get_db()
        quiz = await db.get_quiz_by_share_code(share_code)
        
        if quiz:
            # Test topildi, to'liq quiz menyusini ko'rsatish
            await message.answer(
                f"📝 <b>Test topildi!</b>\n\n"
                f"📌 Sarlavha: <b>{quiz.title}</b>\n"
                f"❓ Savollar soni: <b>{quiz.total_questions}</b>\n"
                f"⏱ Vaqt: <b>{quiz.time_display}</b>\n\n"
                f"Quyidagi tugmalardan birini tanlang:",
                parse_mode="HTML",
                reply_markup=SettingsKeyboard.quiz_ready(quiz.id)
            )
            
            # Quizni state'ga saqlash
            await state.update_data(shared_quiz_id=quiz.id)
            return
        else:
            await message.answer(
                "❌ Kechirasiz, bu test topilmadi yoki o'chirilgan.",
                reply_markup=MainMenuKeyboard.main_menu()
            )
            return
    
    # Oddiy start
    welcome_text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men Word (DOCX) faylidan avtomatik test yaratadigan quiz botman.\n\n"
        "🎯 <b>Qulayliklar:</b>\n"
        "• Word fayldan savollarni avtomatik o'qish\n"
        "• Variantlarni aralashtirish\n"
        "• Vaqt belgilash\n"
        "• Guruhda test o'tkazish\n"
        "• Statistika va natijalar\n\n"
        "Boshlash uchun quyidagi tugmadan foydalaning 👇"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.main_menu()
    )


@router.message(Command("help"))
@router.message(F.text == "❓ Yordam")
async def show_help(message: Message):
    """Yordam ko'rsatish (/help va "❓ Yordam" tugmasi)"""
    help_text = (
        "📖 <b>Qo'llanma</b>\n\n"
        "<b>1. Test yaratish:</b>\n"
        "• \"📄 Test yuklash\" tugmasini bosing\n"
        "• Word (.docx) faylni yuboring\n"
        "• Test sarlavhasini kiriting\n"
        "• Vaqt va sozlamalarni tanlang\n\n"
        "<b>2. Word fayl formati:</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<code>1. Savol matni?\n"
        "A) Birinchi variant\n"
        "B) Ikkinchi variant\n"
        "*C) To'g'ri javob\n"
        "D) To'rtinchi variant\n\n"
        "2. Ikkinchi savol?\n"
        "A) Variant 1\n"
        "+B) To'g'ri javob\n"
        "C) Variant 3</code>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <b>To'g'ri javobni belgilash:</b>\n"
        "• Boshida <code>*</code> yoki <code>+</code> qo'ying\n"
        "• Yoki oxirida <code>*</code> qo'ying\n\n"
        "<b>3. Guruhda test:</b>\n"
        "• Botni guruhga qo'shing\n"
        "• Admin huquqini bering\n"
        "• \"👥 Guruhda boshlash\" tugmasini bosing"
    )
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.help_inline()
    )


@router.callback_query(F.data == "help_format")
async def show_format_help(callback: CallbackQuery):
    """Format namunasini ko'rsatish"""
    format_text = (
        "📝 <b>Word fayl formati namunasi</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<b>Format 1:</b> So'roq belgisi bilan ✅\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<code>?Savol matni\n"
        "+To'g'ri javob\n"
        "=Noto'g'ri variant\n"
        "=Noto'g'ri variant\n"
        "=Noto'g'ri variant</code>\n\n"
        "<b>Belgilar:</b>\n"
        "• <code>?</code> - Savol\n"
        "• <code>+</code> - To'g'ri javob\n"
        "• <code>=</code> - Noto'g'ri variant\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<b>Format 2:</b> Klassik format\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<code>1. Savol matni?\n"
        "A) Variant 1\n"
        "*B) To'g'ri javob\n"
        "C) Variant 3\n"
        "D) Variant 4</code>"
    )
    
    await callback.message.edit_text(
        format_text,
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.help_inline()
    )
    await callback.answer()


@router.callback_query(F.data == "help_guide")
async def show_full_guide(callback: CallbackQuery):
    """To'liq qo'llanmani ko'rsatish"""
    await callback.message.edit_text(
        "📖 <b>To'liq qo'llanma</b>\n\n"
        "<b>Test yaratish bosqichlari:</b>\n\n"
        "1️⃣ Word faylni tayyorlang\n"
        "   • Har bir savol raqam bilan boshlansin\n"
        "   • Variantlar A), B), C)... bilan\n"
        "   • To'g'ri javobni * yoki + bilan belgilang\n\n"
        "2️⃣ Faylni botga yuboring\n"
        "   • .docx formati bo'lishi kerak\n"
        "   • Bot avtomatik tekshiradi\n\n"
        "3️⃣ Sozlamalarni tanlang\n"
        "   • Test sarlavhasini kiriting\n"
        "   • Savol vaqtini tanlang\n"
        "   • Aralashtirish rejimini tanlang\n\n"
        "4️⃣ Testni boshlang yoki ulashing\n"
        "   • O'zingiz yechishingiz mumkin\n"
        "   • Do'stlarga link yuboring\n"
        "   • Guruhda o'tkazing",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.help_inline()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Bosh menyuga qaytish"""
    await state.clear()
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(
        "🏠 <b>Bosh menyu</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "close_menu")
async def close_menu(callback: CallbackQuery):
    """Menyuni yopish"""
    await callback.message.delete()
    await callback.answer("Yopildi")
