"""
Sozlamalar tugmalari
Quiz yaratish jarayonidagi sozlamalar
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SettingsKeyboard:
    """Sozlamalar tugmalari"""
    
    @staticmethod
    def time_selection() -> InlineKeyboardMarkup:
        """Vaqt tanlash tugmalari"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="⏱ 10 soniya", callback_data="time:10"),
            InlineKeyboardButton(text="⏱ 20 soniya", callback_data="time:20")
        )
        builder.row(
            InlineKeyboardButton(text="⏱ 30 soniya", callback_data="time:30"),
            InlineKeyboardButton(text="⏱ 1 daqiqa", callback_data="time:60")
        )
        builder.row(
            InlineKeyboardButton(text="⏱ 2 daqiqa", callback_data="time:120"),
            InlineKeyboardButton(text="⏱ 3 daqiqa", callback_data="time:180")
        )
        builder.row(
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_setup")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def shuffle_selection() -> InlineKeyboardMarkup:
        """Aralashtirish tanlash tugmalari"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🔀 Aralashtirilsin", callback_data="shuffle:yes"),
        )
        builder.row(
            InlineKeyboardButton(text="📋 Aralashtirilmasin", callback_data="shuffle:no")
        )
        builder.row(
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_setup")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def quiz_ready(quiz_id: str) -> InlineKeyboardMarkup:
        """Test tayyor - boshqaruv tugmalari"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="▶️ Testni boshlash", callback_data=f"start_quiz:{quiz_id}")
        )
        builder.row(
            InlineKeyboardButton(text="👥 Guruhda boshlash", callback_data=f"group_quiz:{quiz_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔗 Testni ulashish", callback_data=f"share_quiz:{quiz_id}")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Statistika", callback_data=f"quiz_stats:{quiz_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_quiz:{quiz_id}")
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_quizzes_list"),
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def confirm_delete(quiz_id: str) -> InlineKeyboardMarkup:
        """O'chirishni tasdiqlash"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete:{quiz_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"quiz_view:{quiz_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def group_selection(groups: list) -> InlineKeyboardMarkup:
        """Guruh tanlash (bot qo'shilgan guruhlar)"""
        builder = InlineKeyboardBuilder()
        
        for group in groups:
            builder.row(
                InlineKeyboardButton(
                    text=f"👥 {group['title']}",
                    callback_data=f"select_group:{group['id']}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_quiz_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def add_bot_to_group(bot_username: str, quiz_id: str = "") -> InlineKeyboardMarkup:
        """Botni guruhga qo'shish tugmasi"""
        builder = InlineKeyboardBuilder()
        
        # startgroup parametri bilan bot guruhga qo'shiladi
        url = f"https://t.me/{bot_username}?startgroup=quiz_{quiz_id}" if quiz_id else f"https://t.me/{bot_username}?startgroup=true"
        
        builder.row(
            InlineKeyboardButton(
                text="➕ Botni guruhga qo'shish",
                url=url
            )
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"quiz_view:{quiz_id}" if quiz_id else "back_to_main")
        )
        
        return builder.as_markup()
