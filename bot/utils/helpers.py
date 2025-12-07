"""
Yordamchi funksiyalar
"""
import html
import uuid
import re
from typing import Optional


def escape_html(text: str) -> str:
    """HTML belgilarini escape qilish"""
    return html.escape(text)


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Matnni qisqartirish"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_time(seconds: int) -> str:
    """Vaqtni chiroyli formatda ko'rsatish"""
    if seconds == 0:
        return "Cheksiz"
    elif seconds < 60:
        return f"{seconds} soniya"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds:
            return f"{minutes} daqiqa {remaining_seconds} soniya"
        return f"{minutes} daqiqa"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes:
            return f"{hours} soat {remaining_minutes} daqiqa"
        return f"{hours} soat"


def generate_share_code(length: int = 6) -> str:
    """Ulashish kodi yaratish"""
    return str(uuid.uuid4())[:length].upper()


def clean_text(text: str) -> str:
    """Matnni tozalash"""
    # Ortiqcha bo'sh joylarni olib tashlash
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_valid_docx_filename(filename: str) -> bool:
    """DOCX fayl nomini tekshirish"""
    return filename.lower().endswith('.docx')


def parse_question_number(text: str) -> Optional[int]:
    """Savol raqamini ajratib olish"""
    match = re.match(r'^(\d+)', text.strip())
    if match:
        return int(match.group(1))
    return None


def format_percentage(value: float, decimals: int = 1) -> str:
    """Foizni formatlash"""
    return f"{value:.{decimals}f}%"


def get_grade_emoji(percentage: float) -> str:
    """Foiz asosida emoji olish"""
    if percentage >= 90:
        return "🏆"
    elif percentage >= 80:
        return "🥇"
    elif percentage >= 70:
        return "🥈"
    elif percentage >= 60:
        return "🥉"
    elif percentage >= 50:
        return "👍"
    else:
        return "📚"


def get_option_letter(index: int) -> str:
    """Variant indeksini harfga aylantirish (0 -> A, 1 -> B, ...)"""
    return chr(65 + index)


def letter_to_index(letter: str) -> int:
    """Harfni indeksga aylantirish (A -> 0, B -> 1, ...)"""
    return ord(letter.upper()) - 65


def format_duration(start_time, end_time) -> str:
    """Davomiylikni formatlash"""
    if not start_time or not end_time:
        return "-"
    
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    
    return format_time(total_seconds)
