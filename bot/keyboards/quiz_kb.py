"""
Quiz tugmalari
Test jarayonidagi tugmalar
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.models import Question


class QuizKeyboard:
    """Quiz tugmalari"""
    
    @staticmethod
    def question_options(question: Question, question_index: int, time_left: int = 0) -> InlineKeyboardMarkup:
        """Savol variantlari tugmalari"""
        builder = InlineKeyboardBuilder()
        
        for i, option in enumerate(question.options):
            letter = question.get_option_letter(i)
            # Matnni qisqartirish (agar juda uzun bo'lsa)
            display_text = f"{letter}) {option}"
            if len(display_text) > 60:
                display_text = display_text[:57] + "..."
            
            builder.row(
                InlineKeyboardButton(
                    text=display_text,
                    callback_data=f"answer:{question_index}:{i}"
                )
            )
        
        # Testni tugatish tugmasi
        builder.row(
            InlineKeyboardButton(
                text="🛑 Testni tugatish",
                callback_data="stop_quiz"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def question_with_timer(question: Question, question_index: int, time_left: int) -> InlineKeyboardMarkup:
        """Savol variantlari + vaqt ko'rsatgich"""
        builder = InlineKeyboardBuilder()
        
        for i, option in enumerate(question.options):
            letter = question.get_option_letter(i)
            display_text = f"{letter}) {option}"
            if len(display_text) > 60:
                display_text = display_text[:57] + "..."
            
            builder.row(
                InlineKeyboardButton(
                    text=display_text,
                    callback_data=f"answer:{question_index}:{i}"
                )
            )
        
        # Testni tugatish tugmasi
        builder.row(
            InlineKeyboardButton(
                text="🛑 Testni tugatish",
                callback_data="stop_quiz"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def quiz_result_actions(quiz_id: str) -> InlineKeyboardMarkup:
        """Test tugagandan keyin tugmalar"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🔄 Qayta boshlash", callback_data=f"restart_quiz:{quiz_id}")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Statistikani ko'rish", callback_data=f"view_my_stats")
        )
        builder.row(
            InlineKeyboardButton(text="📄 Yangi test yuklash", callback_data="upload_new")
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def group_question_options(question: Question, question_index: int, session_id: str, answered_count: int = 0) -> InlineKeyboardMarkup:
        """Guruh uchun savol variantlari"""
        builder = InlineKeyboardBuilder()
        
        for i, option in enumerate(question.options):
            letter = question.get_option_letter(i)
            display_text = f"{letter}) {option}"
            if len(display_text) > 60:
                display_text = display_text[:57] + "..."
            
            builder.row(
                InlineKeyboardButton(
                    text=display_text,
                    callback_data=f"group_answer:{session_id}:{question_index}:{i}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def group_ready_button(session_id: str) -> InlineKeyboardMarkup:
        """Tayyorman tugmasi"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Tayyorman",
                callback_data=f"group_ready:{session_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def group_admin_controls(session_id: str, time_left: int = 0, answered_count: int = 0) -> InlineKeyboardMarkup:
        """Guruh admini uchun boshqaruv tugmalari"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text=f"👥 Javob berganlar: {answered_count}",
                callback_data="refresh_count"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="➡️ Keyingi savol",
                callback_data=f"group_next:{session_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🛑 Testni to'xtatish",
                callback_data=f"group_stop:{session_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def group_next_question(session_id: str) -> InlineKeyboardMarkup:
        """Guruhda keyingi savol tugmasi (faqat admin uchun)"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="➡️ Keyingi savol",
                callback_data=f"group_next:{session_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏁 Testni tugatish",
                callback_data=f"group_end:{session_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def group_result_actions(quiz_id: str, admin_id: int = None) -> InlineKeyboardMarkup:
        """Guruh testi tugagandan keyin tugmalar"""
        builder = InlineKeyboardBuilder()
        
        # Faqat admin uchun "Qayta o'tkazish" tugmasi
        if admin_id:
            builder.row(
                InlineKeyboardButton(text="🔄 Qayta o'tkazish", callback_data=f"group_restart:{quiz_id}")
            )
        
        return builder.as_markup()
    
    @staticmethod
    def skip_question() -> InlineKeyboardMarkup:
        """Savolni o'tkazib yuborish"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_question")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def statistics_menu() -> InlineKeyboardMarkup:
        """Statistika menyusi"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="stats_general")
        )
        builder.row(
            InlineKeyboardButton(text="📜 Test tarixi", callback_data="stats_history")
        )
        builder.row(
            InlineKeyboardButton(text="📈 Mening testlarim statistikasi", callback_data="stats_my_quizzes")
        )
        builder.row(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def quiz_mode_menu() -> InlineKeyboardMarkup:
        """Test rejimi menyusi (Shaxsiy quiz)"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📚 To'liq test",
                callback_data="quiz_mode:full"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔢 Oraliq test",
                callback_data="quiz_mode:range"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🎲 Tasodifiy test",
                callback_data="quiz_mode:random"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="back_to_main"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def group_quiz_mode_menu(chat_id: int) -> InlineKeyboardMarkup:
        """Test rejimi menyusi (Guruh quiz)"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📚 To'liq test",
                callback_data=f"group_quiz_mode:full:{chat_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔢 Oraliq test",
                callback_data=f"group_quiz_mode:range:{chat_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🎲 Tasodifiy test",
                callback_data=f"group_quiz_mode:random:{chat_id}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def share_result(quiz_id: str, score: float) -> InlineKeyboardMarkup:
        """Natijani ulashish"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📤 Natijani ulashish",
                switch_inline_query=f"result_{quiz_id}_{score}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def private_hint_button() -> InlineKeyboardMarkup:
        """Private chat'ga o'tish tugmasi"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="💬 Private chat'ga o'tish",
                url="https://t.me/comfort_quiz_bot"
            )
        )
        
        return builder.as_markup()
