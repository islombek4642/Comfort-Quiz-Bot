"""
Database moduli
SQLite yordamida ma'lumotlarni saqlash
"""
import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional
from bot.models import Quiz, Question, QuizResult, UserStatistics
from bot.config import config


class Database:
    """Asinxron database class"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database.path
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Database papkasini yaratish"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    async def init(self):
        """Database jadvallarini yaratish"""
        async with aiosqlite.connect(self.db_path) as db:
            # Quizlar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS quizzes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    questions TEXT NOT NULL,
                    time_per_question INTEGER DEFAULT 30,
                    shuffle_options INTEGER DEFAULT 1,
                    share_code TEXT UNIQUE,
                    created_at TEXT,
                    is_active INTEGER DEFAULT 0
                )
            """)
            
            # Natijalar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY,
                    quiz_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    wrong_answers TEXT,
                    answers TEXT,
                    started_at TEXT,
                    finished_at TEXT,
                    is_completed INTEGER DEFAULT 0,
                    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
                )
            """)
            
            # Foydalanuvchi statistikasi jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_statistics (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    total_quizzes_taken INTEGER DEFAULT 0,
                    total_questions_answered INTEGER DEFAULT 0,
                    total_correct_answers INTEGER DEFAULT 0,
                    quizzes_created INTEGER DEFAULT 0,
                    best_score REAL DEFAULT 0,
                    average_score REAL DEFAULT 0,
                    last_activity TEXT
                )
            """)
            
            # Indekslar
            await db.execute("CREATE INDEX IF NOT EXISTS idx_quiz_creator ON quizzes(creator_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_quiz_share ON quizzes(share_code)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_results_quiz ON results(quiz_id)")
            
            await db.commit()
    
    # ==================== QUIZ METHODS ====================
    
    async def save_quiz(self, quiz: Quiz) -> bool:
        """Quizni saqlash"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                questions_json = json.dumps([
                    {
                        "id": q.id,
                        "text": q.text,
                        "options": q.options,
                        "correct_index": q.correct_index,
                        "original_options": q.original_options
                    }
                    for q in quiz.questions
                ])
                
                await db.execute("""
                    INSERT OR REPLACE INTO quizzes 
                    (id, title, creator_id, questions, time_per_question, 
                     shuffle_options, share_code, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quiz.id,
                    quiz.title,
                    quiz.creator_id,
                    questions_json,
                    quiz.time_per_question,
                    1 if quiz.shuffle_options else 0,
                    quiz.share_code,
                    quiz.created_at.isoformat(),
                    1 if quiz.is_active else 0
                ))
                await db.commit()
                return True
        except Exception as e:
            print(f"Quiz saqlashda xato: {e}")
            return False
    
    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Quiz olish ID bo'yicha"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM quizzes WHERE id = ?", (quiz_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_quiz(row)
        return None
    
    async def get_quiz_by_share_code(self, share_code: str) -> Optional[Quiz]:
        """Quiz olish ulashish kodi bo'yicha"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM quizzes WHERE share_code = ?", (share_code.upper(),)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_quiz(row)
        return None
    
    async def get_user_quizzes(self, user_id: int) -> list[Quiz]:
        """Foydalanuvchi quizlarini olish"""
        quizzes = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM quizzes WHERE creator_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                async for row in cursor:
                    quizzes.append(self._row_to_quiz(row))
        return quizzes
    
    async def delete_quiz(self, quiz_id: str) -> bool:
        """Quizni o'chirish"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
                await db.execute("DELETE FROM results WHERE quiz_id = ?", (quiz_id,))
                await db.commit()
                return True
        except Exception:
            return False
    
    def _row_to_quiz(self, row) -> Quiz:
        """Database qatorini Quiz obyektiga aylantirish"""
        questions_data = json.loads(row["questions"])
        questions = [
            Question(
                id=q["id"],
                text=q["text"],
                options=q["options"],
                correct_index=q["correct_index"],
                original_options=q.get("original_options", q["options"])
            )
            for q in questions_data
        ]
        
        return Quiz(
            id=row["id"],
            title=row["title"],
            creator_id=row["creator_id"],
            questions=questions,
            time_per_question=row["time_per_question"],
            shuffle_options=bool(row["shuffle_options"]),
            share_code=row["share_code"],
            created_at=datetime.fromisoformat(row["created_at"]),
            is_active=bool(row["is_active"])
        )
    
    # ==================== RESULT METHODS ====================
    
    async def save_result(self, result: QuizResult) -> bool:
        """Natijani saqlash"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO results
                    (id, quiz_id, user_id, username, total_questions,
                     correct_answers, wrong_answers, answers, started_at,
                     finished_at, is_completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.id,
                    result.quiz_id,
                    result.user_id,
                    result.username,
                    result.total_questions,
                    result.correct_answers,
                    json.dumps(result.wrong_answers),
                    json.dumps(result.answers),
                    result.started_at.isoformat(),
                    result.finished_at.isoformat() if result.finished_at else None,
                    1 if result.is_completed else 0
                ))
                await db.commit()
                return True
        except Exception as e:
            print(f"Natija saqlashda xato: {e}")
            return False
    
    async def get_user_results(self, user_id: int) -> list[QuizResult]:
        """Foydalanuvchi natijalarini olish"""
        results = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM results WHERE user_id = ? ORDER BY finished_at DESC",
                (user_id,)
            ) as cursor:
                async for row in cursor:
                    results.append(self._row_to_result(row))
        return results
    
    async def get_quiz_results(self, quiz_id: str) -> list[QuizResult]:
        """Quiz natijalari (barcha foydalanuvchilar)"""
        results = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM results WHERE quiz_id = ? AND is_completed = 1 ORDER BY correct_answers DESC",
                (quiz_id,)
            ) as cursor:
                async for row in cursor:
                    results.append(self._row_to_result(row))
        return results
    
    def _row_to_result(self, row) -> QuizResult:
        """Database qatorini QuizResult obyektiga aylantirish"""
        return QuizResult(
            id=row["id"],
            quiz_id=row["quiz_id"],
            user_id=row["user_id"],
            username=row["username"] or "",
            total_questions=row["total_questions"],
            correct_answers=row["correct_answers"],
            wrong_answers=json.loads(row["wrong_answers"]),
            answers=json.loads(row["answers"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            is_completed=bool(row["is_completed"])
        )
    
    # ==================== STATISTICS METHODS ====================
    
    async def update_user_statistics(self, user_id: int, username: str, 
                                      result: QuizResult = None,
                                      quiz_created: bool = False) -> None:
        """Foydalanuvchi statistikasini yangilash"""
        async with aiosqlite.connect(self.db_path) as db:
            # Mavjud statistikani olish yoki yangi yaratish
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM user_statistics WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
            
            if row:
                stats = UserStatistics(
                    user_id=row["user_id"],
                    username=row["username"],
                    total_quizzes_taken=row["total_quizzes_taken"],
                    total_questions_answered=row["total_questions_answered"],
                    total_correct_answers=row["total_correct_answers"],
                    quizzes_created=row["quizzes_created"],
                    best_score=row["best_score"],
                    average_score=row["average_score"]
                )
            else:
                stats = UserStatistics(user_id=user_id, username=username)
            
            # Statistikani yangilash
            stats.username = username
            stats.last_activity = datetime.now()
            
            if result and result.is_completed:
                stats.total_quizzes_taken += 1
                stats.total_questions_answered += result.total_questions
                stats.total_correct_answers += result.correct_answers
                
                score = result.score_percent
                if score > stats.best_score:
                    stats.best_score = score
                
                # O'rtacha ballni hisoblash
                if stats.total_quizzes_taken > 0:
                    stats.average_score = round(
                        (stats.total_correct_answers / stats.total_questions_answered) * 100, 1
                    )
            
            if quiz_created:
                stats.quizzes_created += 1
            
            # Saqlash
            await db.execute("""
                INSERT OR REPLACE INTO user_statistics
                (user_id, username, total_quizzes_taken, total_questions_answered,
                 total_correct_answers, quizzes_created, best_score, average_score, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.user_id,
                stats.username,
                stats.total_quizzes_taken,
                stats.total_questions_answered,
                stats.total_correct_answers,
                stats.quizzes_created,
                stats.best_score,
                stats.average_score,
                stats.last_activity.isoformat()
            ))
            await db.commit()
    
    async def get_user_statistics(self, user_id: int) -> Optional[UserStatistics]:
        """Foydalanuvchi statistikasini olish"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM user_statistics WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return UserStatistics(
                        user_id=row["user_id"],
                        username=row["username"],
                        total_quizzes_taken=row["total_quizzes_taken"],
                        total_questions_answered=row["total_questions_answered"],
                        total_correct_answers=row["total_correct_answers"],
                        quizzes_created=row["quizzes_created"],
                        best_score=row["best_score"],
                        average_score=row["average_score"],
                        last_activity=datetime.fromisoformat(row["last_activity"]) if row["last_activity"] else None
                    )
        return None


# Global database instance
_db: Optional[Database] = None


async def get_db() -> Database:
    """Database instanceni olish"""
    global _db
    if _db is None:
        _db = Database()
        await _db.init()
    return _db
