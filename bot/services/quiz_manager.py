"""
Quiz Manager Service
Quiz jarayonini boshqarish
"""
from datetime import datetime
from typing import Optional
import random
from bot.models import Quiz, Question, QuizResult, QuizSettings
from bot.database import get_db


class QuizManager:
    """Quiz jarayonini boshqaruvchi class"""
    
    def __init__(self):
        self.active_sessions: dict[int, QuizSession] = {}  # user_id -> QuizSession
        self.group_sessions: dict[int, GroupQuizSession] = {}  # chat_id -> GroupQuizSession
    
    # ==================== SHAXSIY QUIZ ====================
    
    def create_session(self, user_id: int, quiz: Quiz, settings: Optional[QuizSettings] = None) -> 'QuizSession':
        """Yangi quiz sessiya yaratish"""
        session = QuizSession(user_id=user_id, quiz=quiz, settings=settings)
        self.active_sessions[user_id] = session
        return session
    
    def get_session(self, user_id: int) -> Optional['QuizSession']:
        """Mavjud sessiyani olish"""
        return self.active_sessions.get(user_id)
    
    def end_session(self, user_id: int) -> Optional[QuizResult]:
        """Sessiyani tugatish va natijani qaytarish"""
        session = self.active_sessions.pop(user_id, None)
        if session:
            return session.get_result()
        return None
    
    def has_active_session(self, user_id: int) -> bool:
        """Faol sessiya bormi"""
        return user_id in self.active_sessions
    
    # ==================== GURUH QUIZ ====================
    
    def create_group_session(self, chat_id: int, quiz: Quiz, creator_id: int, settings: Optional[QuizSettings] = None) -> 'GroupQuizSession':
        """Guruh uchun quiz sessiya yaratish"""
        session = GroupQuizSession(chat_id=chat_id, quiz=quiz, creator_id=creator_id, settings=settings)
        self.group_sessions[chat_id] = session
        return session
    
    def get_group_session(self, chat_id: int) -> Optional['GroupQuizSession']:
        """Guruh sessiyasini olish"""
        return self.group_sessions.get(chat_id)
    
    def end_group_session(self, chat_id: int) -> Optional['GroupQuizSession']:
        """Guruh sessiyasini tugatish"""
        return self.group_sessions.pop(chat_id, None)


class QuizSession:
    """Shaxsiy quiz sessiyasi"""
    
    def __init__(self, user_id: int, quiz: Quiz, settings: Optional[QuizSettings] = None):
        self.user_id = user_id
        self.quiz = quiz
        self.settings = settings or QuizSettings()
        self.current_index = 0
        self.answers: dict[int, int] = {}  # savol_index -> tanlangan_variant_index
        self.correct_count = 0
        self.wrong_indices: list[int] = []
        self.started_at = datetime.now()
        self.is_completed = False
        
        # Quizni sozlamalar asosida tayyorlash
        self._prepare_quiz_with_settings()
    
    @property
    def current_question(self) -> Optional[Question]:
        """Joriy savolni olish"""
        if 0 <= self.current_index < len(self.quiz.questions):
            return self.quiz.questions[self.current_index]
        return None
    
    @property
    def is_finished(self) -> bool:
        """Quiz tugaganmi"""
        return self.current_index >= len(self.quiz.questions)
    
    @property
    def progress(self) -> str:
        """Jarayon holati"""
        return f"{self.current_index + 1}/{len(self.quiz.questions)}"
    
    @property
    def time_limit(self) -> int:
        """Vaqt limiti (soniyada)"""
        return self.quiz.time_per_question
    
    def _prepare_quiz_with_settings(self) -> None:
        """Quizni sozlamalar asosida tayyorlash"""
        # Oraliq test
        if self.settings.quiz_mode == "range" and self.settings.end_question:
            start_idx = max(0, self.settings.start_question - 1)
            end_idx = min(self.settings.end_question, len(self.quiz.questions))
            self.quiz.questions = self.quiz.questions[start_idx:end_idx]
        
        # Tasodifiy test
        elif self.settings.quiz_mode == "random" and self.settings.question_count:
            questions_copy = self.quiz.questions.copy()
            random.shuffle(questions_copy)
            self.quiz.questions = questions_copy[:self.settings.question_count]
        
        # Variantlarni aralashtirish
        if self.settings.shuffle and self.quiz.shuffle_options:
            self.quiz.prepare_quiz()
    
    def answer_question(self, option_index: int) -> tuple[bool, str]:
        """
        Savolga javob berish.
        Qaytaradi: (to'g'rimi, to'g'ri_javob_matni)
        """
        question = self.current_question
        if not question:
            return False, ""
        
        self.answers[self.current_index] = option_index
        is_correct = option_index == question.correct_index
        
        if is_correct:
            self.correct_count += 1
        else:
            self.wrong_indices.append(self.current_index)
        
        correct_answer = question.correct_answer
        
        # Keyingi savolga o'tish
        self.current_index += 1
        
        # Quiz tugadimi tekshirish
        if self.is_finished:
            self.is_completed = True
        
        return is_correct, correct_answer
    
    def skip_question(self) -> None:
        """Savolni o'tkazib yuborish (vaqt tugaganda)"""
        self.wrong_indices.append(self.current_index)
        self.current_index += 1
        
        if self.is_finished:
            self.is_completed = True
    
    def get_result(self) -> QuizResult:
        """Natijani olish"""
        return QuizResult(
            quiz_id=self.quiz.id,
            user_id=self.user_id,
            total_questions=len(self.quiz.questions),
            correct_answers=self.correct_count,
            wrong_answers=self.wrong_indices,
            answers=self.answers,
            started_at=self.started_at,
            finished_at=datetime.now(),
            is_completed=self.is_completed
        )


class GroupQuizSession:
    """Guruh quiz sessiyasi"""
    
    def __init__(self, chat_id: int, quiz: Quiz, creator_id: int, settings: Optional[QuizSettings] = None):
        self.chat_id = chat_id
        self.quiz = quiz
        self.creator_id = creator_id
        self.settings = settings or QuizSettings()
        self.current_index = 0
        self.participants: dict[int, ParticipantScore] = {}  # user_id -> ParticipantScore
        self.started_at = datetime.now()
        self.is_active = True
        self.answered_current: set[int] = set()  # Joriy savolga javob berganlar
        self.waiting_mode: Optional[str] = None  # "range" yoki "random" - input kutish rejimi
        
        # Quizni sozlamalar asosida tayyorlash
        self._prepare_quiz_with_settings()
    
    @property
    def current_question(self) -> Optional[Question]:
        """Joriy savol"""
        if 0 <= self.current_index < len(self.quiz.questions):
            return self.quiz.questions[self.current_index]
        return None
    
    @property
    def is_finished(self) -> bool:
        """Quiz tugaganmi"""
        return self.current_index >= len(self.quiz.questions)
    
    def _prepare_quiz_with_settings(self) -> None:
        """Quizni sozlamalar asosida tayyorlash"""
        # Orqaliq test
        if self.settings.quiz_mode == "range" and self.settings.end_question:
            start_idx = max(0, self.settings.start_question - 1)
            end_idx = min(self.settings.end_question, len(self.quiz.questions))
            self.quiz.questions = self.quiz.questions[start_idx:end_idx]
        
        # Tasodifiy test
        elif self.settings.quiz_mode == "random" and self.settings.question_count:
            questions_copy = self.quiz.questions.copy()
            random.shuffle(questions_copy)
            self.quiz.questions = questions_copy[:self.settings.question_count]
        
        # Variantlarni aralashtirish
        if self.settings.shuffle and self.quiz.shuffle_options:
            self.quiz.prepare_quiz()
    
    def add_participant(self, user_id: int, username: str) -> None:
        """Yangi ishtirokchi qo'shish"""
        if user_id not in self.participants:
            self.participants[user_id] = ParticipantScore(user_id=user_id, username=username)
    
    def has_answered(self, user_id: int) -> bool:
        """Foydalanuvchi joriy savolga javob berganmi"""
        return user_id in self.answered_current
    
    def answer_question(self, user_id: int, username: str, option_index: int) -> tuple[bool, str]:
        """
        Savolga javob berish.
        Qaytaradi: (to'g'rimi, to'g'ri_javob_matni)
        """
        # Ishtirokchini qo'shish
        self.add_participant(user_id, username)
        
        question = self.current_question
        if not question or user_id in self.answered_current:
            return False, ""
        
        self.answered_current.add(user_id)
        is_correct = option_index == question.correct_index
        
        participant = self.participants[user_id]
        participant.total_answered += 1
        
        if is_correct:
            participant.correct_count += 1
        
        return is_correct, question.correct_answer
    
    def next_question(self) -> bool:
        """Keyingi savolga o'tish. True qaytaradi agar yana savol bor bo'lsa"""
        self.current_index += 1
        self.answered_current.clear()
        return not self.is_finished
    
    def get_leaderboard(self) -> list['ParticipantScore']:
        """Natijalar reytingi"""
        return sorted(
            self.participants.values(),
            key=lambda p: (p.correct_count, -p.total_answered),
            reverse=True
        )


class ParticipantScore:
    """Guruh ishtirokchisi natijasi"""
    
    def __init__(self, user_id: int, username: str):
        self.user_id = user_id
        self.username = username
        self.correct_count = 0
        self.total_answered = 0
    
    @property
    def accuracy(self) -> float:
        """To'g'ri javoblar foizi"""
        if self.total_answered == 0:
            return 0.0
        return round((self.correct_count / self.total_answered) * 100, 1)


# Global quiz manager
quiz_manager = QuizManager()
