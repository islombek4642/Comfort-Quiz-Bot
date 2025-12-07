"""
Statistics Service
Statistika hisoblash va taqdim etish
"""
from typing import Optional
from bot.models import Quiz, QuizResult, UserStatistics
from bot.database import get_db


class StatisticsService:
    """Statistika xizmati"""
    
    @staticmethod
    async def get_user_stats(user_id: int) -> Optional[UserStatistics]:
        """Foydalanuvchi statistikasini olish"""
        db = await get_db()
        return await db.get_user_statistics(user_id)
    
    @staticmethod
    async def get_quiz_stats(quiz_id: str) -> dict:
        """Quiz statistikasini olish"""
        db = await get_db()
        
        quiz = await db.get_quiz(quiz_id)
        if not quiz:
            return {}
        
        results = await db.get_quiz_results(quiz_id)
        
        if not results:
            return {
                "quiz": quiz,
                "total_attempts": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "question_stats": []
            }
        
        # Umumiy statistika
        scores = [r.score_percent for r in results]
        
        # Har bir savol uchun statistika
        question_stats = []
        for i, question in enumerate(quiz.questions):
            wrong_count = sum(1 for r in results if i in r.wrong_answers)
            correct_count = len(results) - wrong_count
            
            question_stats.append({
                "index": i + 1,
                "text": question.text[:50] + "..." if len(question.text) > 50 else question.text,
                "correct_count": correct_count,
                "wrong_count": wrong_count,
                "accuracy": round((correct_count / len(results)) * 100, 1) if results else 0
            })
        
        # Eng ko'p xato qilingan savollar
        hardest_questions = sorted(question_stats, key=lambda x: x["accuracy"])[:3]
        
        return {
            "quiz": quiz,
            "total_attempts": len(results),
            "average_score": round(sum(scores) / len(scores), 1),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "question_stats": question_stats,
            "hardest_questions": hardest_questions,
            "results": results[:10]  # Oxirgi 10 ta natija
        }
    
    @staticmethod
    async def get_user_history(user_id: int, limit: int = 10) -> list[dict]:
        """Foydalanuvchi test tarixi"""
        db = await get_db()
        results = await db.get_user_results(user_id)
        
        history = []
        for result in results[:limit]:
            quiz = await db.get_quiz(result.quiz_id)
            history.append({
                "result": result,
                "quiz_title": quiz.title if quiz else "Noma'lum test",
                "date": result.finished_at.strftime("%d.%m.%Y %H:%M") if result.finished_at else "-"
            })
        
        return history
    
    @staticmethod
    def format_user_stats(stats: UserStatistics) -> str:
        """Foydalanuvchi statistikasini formatlash"""
        if not stats:
            return "📊 Sizda hali statistika yo'q.\nTest yechib ko'ring!"
        
        return (
            f"📊 <b>Sizning statistikangiz</b>\n\n"
            f"👤 Foydalanuvchi: {stats.username}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📝 Yechilgan testlar: <b>{stats.total_quizzes_taken}</b>\n"
            f"❓ Javob berilgan savollar: <b>{stats.total_questions_answered}</b>\n"
            f"✅ To'g'ri javoblar: <b>{stats.total_correct_answers}</b>\n"
            f"📈 Umumiy aniqlik: <b>{stats.overall_accuracy}%</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 Eng yaxshi natija: <b>{stats.best_score}%</b>\n"
            f"📊 O'rtacha ball: <b>{stats.average_score}%</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"✏️ Yaratilgan testlar: <b>{stats.quizzes_created}</b>\n"
        )
    
    @staticmethod
    def format_quiz_stats(stats: dict) -> str:
        """Quiz statistikasini formatlash"""
        if not stats or not stats.get("quiz"):
            return "📊 Statistika topilmadi."
        
        quiz = stats["quiz"]
        
        text = (
            f"📊 <b>Test statistikasi</b>\n\n"
            f"📝 Test: <b>{quiz.title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Jami urinishlar: <b>{stats['total_attempts']}</b>\n"
            f"📊 O'rtacha ball: <b>{stats['average_score']}%</b>\n"
            f"🏆 Eng yuqori: <b>{stats['highest_score']}%</b>\n"
            f"📉 Eng past: <b>{stats['lowest_score']}%</b>\n"
        )
        
        if stats.get("hardest_questions"):
            text += "\n━━━━━━━━━━━━━━━━━━━\n"
            text += "🔴 <b>Eng qiyin savollar:</b>\n"
            for q in stats["hardest_questions"]:
                text += f"  {q['index']}. {q['text']} ({q['accuracy']}%)\n"
        
        return text
    
    @staticmethod
    def format_result(result: QuizResult, quiz_title: str = "") -> str:
        """Natijani formatlash"""
        wrong_count = result.total_questions - result.correct_answers
        
        return (
            f"🏁 <b>Test tugadi!</b>\n\n"
            f"📝 Test: <b>{quiz_title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Umumiy savollar: <b>{result.total_questions}</b>\n"
            f"✅ To'g'ri javoblar: <b>{result.correct_answers}</b>\n"
            f"❌ Noto'g'ri javoblar: <b>{wrong_count}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Ball: <b>{result.score_percent}%</b>\n"
            f"{result.grade_emoji} {result.grade_text}"
        )
    
    @staticmethod
    def format_leaderboard(participants: list, quiz_title: str = "") -> str:
        """Guruh natijalarini formatlash"""
        if not participants:
            return "👥 Hech kim ishtirok etmadi."
        
        text = f"🏆 <b>Natijalar</b>\n"
        if quiz_title:
            text += f"📝 {quiz_title}\n"
        text += "━━━━━━━━━━━━━━━━━━━\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, p in enumerate(participants):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} <b>{p.username}</b>\n"
            text += f"    ✅ {p.correct_count}/{p.total_answered} ({p.accuracy}%)\n\n"
        
        return text
