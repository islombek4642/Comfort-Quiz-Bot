"""
Quiz ma'lumot modellari
Dataclass'lar yordamida ma'lumotlarni saqlash
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
import random


@dataclass
class Question:
    """Savol modeli"""
    id: str
    text: str
    options: list[str]  # Barcha variantlar
    correct_index: int  # To'g'ri javob indeksi (0 dan boshlanadi)
    original_options: list[str] = field(default_factory=list)  # Asl tartibdagi variantlar
    
    def __post_init__(self):
        if not self.original_options:
            self.original_options = self.options.copy()
    
    @property
    def correct_answer(self) -> str:
        """To'g'ri javobni qaytarish"""
        return self.options[self.correct_index]
    
    def shuffle_options(self) -> None:
        """Variantlarni aralashtirish"""
        correct_text = self.options[self.correct_index]
        random.shuffle(self.options)
        self.correct_index = self.options.index(correct_text)
    
    def get_option_letter(self, index: int) -> str:
        """Variant harfini olish (A, B, C, D...)"""
        return chr(65 + index)  # 65 = 'A' ASCII kodi


@dataclass
class Quiz:
    """Quiz modeli"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    questions: list[Question] = field(default_factory=list)
    creator_id: int = 0
    time_per_question: int = 30  # Soniyada
    shuffle_options: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = False
    share_code: str = field(default_factory=lambda: str(uuid.uuid4())[:6].upper())
    
    @property
    def total_questions(self) -> int:
        """Umumiy savollar soni"""
        return len(self.questions)
    
    @property
    def time_display(self) -> str:
        """Vaqtni chiroyli ko'rinishda"""
        if self.time_per_question >= 60:
            minutes = self.time_per_question // 60
            seconds = self.time_per_question % 60
            if seconds:
                return f"{minutes} daqiqa {seconds} soniya"
            return f"{minutes} daqiqa"
        else:
            return f"{self.time_per_question} soniya"
    
    def prepare_quiz(self) -> None:
        """Quizni tayyorlash (variantlarni aralashtirish)"""
        if self.shuffle_options:
            for question in self.questions:
                question.shuffle_options()


@dataclass
class QuizResult:
    """Quiz natijasi modeli"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    quiz_id: str = ""
    user_id: int = 0
    username: str = ""
    total_questions: int = 0
    correct_answers: int = 0
    wrong_answers: list[int] = field(default_factory=list)  # Noto'g'ri javob berilgan savol indekslari
    answers: dict = field(default_factory=dict)  # {savol_indeksi: tanlangan_variant}
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    is_completed: bool = False
    
    @property
    def score_percent(self) -> float:
        """Foiz hisobida ball"""
        if self.total_questions == 0:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 1)
    
    @property
    def grade_emoji(self) -> str:
        """Ball asosida emoji"""
        percent = self.score_percent
        if percent >= 90:
            return "🏆"
        elif percent >= 80:
            return "🥇"
        elif percent >= 70:
            return "🥈"
        elif percent >= 60:
            return "🥉"
        elif percent >= 50:
            return "👍"
        else:
            return "📚"
    
    @property
    def grade_text(self) -> str:
        """Ball asosida matn"""
        percent = self.score_percent
        if percent >= 90:
            return "A'lo!"
        elif percent >= 80:
            return "Yaxshi!"
        elif percent >= 70:
            return "Qoniqarli"
        elif percent >= 60:
            return "O'rtacha"
        elif percent >= 50:
            return "Yetarli"
        else:
            return "Qayta o'qing"


@dataclass
class QuizSettings:
    """Quiz sozlamalari"""
    quiz_mode: str = "full"  # full/range/random
    start_question: int = 1
    end_question: Optional[int] = None
    question_count: Optional[int] = None
    shuffle: bool = True


@dataclass
class UserStatistics:
    """Foydalanuvchi statistikasi"""
    user_id: int
    username: str = ""
    total_quizzes_taken: int = 0
    total_questions_answered: int = 0
    total_correct_answers: int = 0
    quizzes_created: int = 0
    best_score: float = 0.0
    average_score: float = 0.0
    last_activity: Optional[datetime] = None
    
    @property
    def overall_accuracy(self) -> float:
        """Umumiy to'g'ri javoblar foizi"""
        if self.total_questions_answered == 0:
            return 0.0
        return round((self.total_correct_answers / self.total_questions_answered) * 100, 1)
