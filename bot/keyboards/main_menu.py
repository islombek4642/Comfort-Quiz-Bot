"""
Asosiy menyu tugmalari
"""
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


class MainMenuKeyboard:
    """Asosiy menyu tugmalari"""
    
    @staticmethod
    def start_menu() -> ReplyKeyboardMarkup:
        """Boshlang'ich menyu"""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="📄 Test yuklash"),
        )
        builder.row(
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="❓ Yordam")
        )
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Asosiy menyu"""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="📄 Test yuklash"),
            KeyboardButton(text="📋 Mening testlarim")
        )
        builder.row(
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="🔗 Test ulashish")
        )
        builder.row(
            KeyboardButton(text="❓ Yordam")
        )
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def cancel_menu() -> ReplyKeyboardMarkup:
        """Bekor qilish tugmasi"""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="❌ Bekor qilish")
        )
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def back_menu() -> ReplyKeyboardMarkup:
        """Orqaga tugmasi"""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="⬅️ Orqaga")
        )
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def help_inline() -> InlineKeyboardMarkup:
        """Yordam inline tugmalari"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📝 Format namunasi", callback_data="help_format"),
            InlineKeyboardButton(text="📖 Qo'llanma", callback_data="help_guide")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Muallif bilan bog'lanish", url="https://t.me/xamidullayev_i")
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")
        )
        return builder.as_markup()
    
    @staticmethod
    def my_quizzes(quizzes: list) -> InlineKeyboardMarkup:
        """Foydalanuvchi testlari ro'yxati"""
        builder = InlineKeyboardBuilder()
        
        for quiz in quizzes[:10]:  # Maksimum 10 ta
            title = quiz.title[:25] + "..." if len(quiz.title) > 25 else quiz.title
            builder.row(
                InlineKeyboardButton(
                    text=f"📝 {title}",
                    callback_data=f"quiz_view:{quiz.id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="📄 Yangi test yuklash", callback_data="upload_new")
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def share_quiz_menu(quiz_id: str, share_code: str, bot_username: str) -> InlineKeyboardMarkup:
        """Test ulashish menyusi"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📤 Do'stlarga ulashish",
                switch_inline_query=f"quiz_{share_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔗 Havolani ko'rish",
                callback_data=f"copy_link:{quiz_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"quiz_view:{quiz_id}"),
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_main")
        )
        
        return builder.as_markup()
