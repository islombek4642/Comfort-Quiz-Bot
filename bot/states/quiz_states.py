"""
Quiz bot holatlari (States)
FSM (Finite State Machine) uchun holatlar
"""
from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    """Quiz yaratish holatlari"""
    
    # Fayl yuklash holati
    waiting_for_docx = State()
    
    # Test sarlavhasi kutish holati  
    waiting_for_title = State()
    
    # Vaqt tanlash holati
    waiting_for_time = State()
    
    # Aralashtirish rejimi tanlash holati
    waiting_for_shuffle = State()
    
    # Test tayyor holati
    quiz_ready = State()
    
    # Test rejimi tanlash holati
    choosing_quiz_mode = State()
    
    # Oraliq test oralig'i kiriting
    entering_quiz_range = State()
    
    # Tasodifiy test savollar soni kiriting
    entering_question_count = State()
    
    # Test jarayonida
    quiz_in_progress = State()
    
    # Guruh tanlash holati
    waiting_for_group = State()


class GroupQuizStates(StatesGroup):
    """Guruh quiz holatlari"""
    
    # Guruhda test boshlash
    group_quiz_active = State()
    
    # Guruhda javob kutish
    waiting_group_answer = State()
