"""
Upload handler
DOCX fayl yuklash va tekshirish
"""
import os
import tempfile
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import QuizStates
from bot.keyboards import MainMenuKeyboard, SettingsKeyboard
from bot.services import DocxParser
from bot.models import Quiz
from bot.database import get_db

router = Router(name="upload")


@router.message(F.text == "📄 Test yuklash")
async def start_upload(message: Message, state: FSMContext):
    """Test yuklashni boshlash"""
    await state.set_state(QuizStates.waiting_for_docx)
    
    await message.answer(
        "📄 <b>Test yuklash</b>\n\n"
        "Iltimos, test savollari yozilgan <b>.docx</b> formatdagi faylni yuboring.\n\n"
        "💡 <i>Fayl formati haqida ma'lumot uchun \"❓ Yordam\" tugmasini bosing.</i>",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.cancel_menu()
    )


@router.callback_query(F.data == "upload_new")
async def upload_new_callback(callback: CallbackQuery, state: FSMContext):
    """Yangi test yuklash (callback)"""
    await state.set_state(QuizStates.waiting_for_docx)
    
    await callback.message.answer(
        "📄 <b>Yangi test yuklash</b>\n\n"
        "Iltimos, test savollari yozilgan <b>.docx</b> formatdagi faylni yuboring.",
        parse_mode="HTML",
        reply_markup=MainMenuKeyboard.cancel_menu()
    )
    await callback.answer()


@router.message(QuizStates.waiting_for_docx, F.document)
async def process_docx(message: Message, state: FSMContext, bot: Bot):
    """DOCX faylni qabul qilish va tekshirish"""
    document = message.document
    
    # Fayl turini tekshirish
    if not document.file_name.endswith('.docx'):
        await message.answer(
            "❌ <b>Noto'g'ri fayl formati!</b>\n\n"
            "Faqat <b>.docx</b> (Word) formatdagi fayllar qabul qilinadi.\n"
            "Iltimos, to'g'ri formatdagi faylni yuboring.",
            parse_mode="HTML"
        )
        return
    
    # Fayl hajmini tekshirish (10 MB gacha)
    if document.file_size > 10 * 1024 * 1024:
        await message.answer(
            "❌ <b>Fayl juda katta!</b>\n\n"
            "Maksimal fayl hajmi: 10 MB",
            parse_mode="HTML"
        )
        return
    
    # Yuklanmoqda xabari
    processing_msg = await message.answer("⏳ Fayl tekshirilmoqda...")
    
    try:
        # Faylni yuklab olish
        file = await bot.get_file(document.file_id)
        file_bytes = await bot.download_file(file.file_path)
        
        # DOCX ni parse qilish
        parser = DocxParser()
        result = await parser.parse_bytes(file_bytes.read())
        
        if not result.success:
            await processing_msg.edit_text(
                f"❌ <b>Xatolik!</b>\n\n{result.error_message}",
                parse_mode="HTML"
            )
            return
        
        # Muvaffaqiyatli parse qilindi
        questions = result.questions
        
        # Quiz obyektini yaratish va state'ga saqlash
        quiz = Quiz(
            questions=questions,
            creator_id=message.from_user.id
        )
        
        await state.update_data(
            quiz_id=quiz.id,
            quiz_title="",
            questions=[{
                "id": q.id,
                "text": q.text,
                "options": q.options,
                "correct_index": q.correct_index,
                "original_options": q.original_options
            } for q in questions],
            creator_id=message.from_user.id
        )
        
        # Sarlavha so'rash
        await state.set_state(QuizStates.waiting_for_title)
        
        # Natija haqida xabar
        warnings_text = ""
        if result.warnings:
            warnings_text = "\n\n⚠️ <b>Ogohlantirishlar:</b>\n" + "\n".join(result.warnings)
        
        await processing_msg.edit_text(
            f"✅ <b>Test yuklandi!</b>\n\n"
            f"📊 Topilgan savollar: <b>{len(questions)}</b>\n"
            f"{warnings_text}\n\n"
            f"📝 Endi test sarlavhasini kiriting.\n"
            f"<i>Masalan: \"Informatika bo'yicha sinov 1\"</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ <b>Xatolik yuz berdi!</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Iltimos, qaytadan urinib ko'ring.",
            parse_mode="HTML"
        )


@router.message(QuizStates.waiting_for_docx)
async def wrong_file_type(message: Message):
    """Noto'g'ri fayl turi"""
    if message.text and not message.document:
        await message.answer(
            "📄 Iltimos, <b>.docx</b> formatdagi fayl yuboring.\n"
            "Matn emas, fayl kerak.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Faqat <b>.docx</b> (Word) formatdagi fayllar qabul qilinadi.",
            parse_mode="HTML"
        )
