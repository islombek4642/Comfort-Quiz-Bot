"""
Bot konfiguratsiya fayli
Barcha sozlamalar shu yerda saqlanadi
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Bot asosiy sozlamalari"""
    token: str
    admin_ids: list[int]
    

@dataclass
class DatabaseConfig:
    """Database sozlamalari"""
    path: str = "data/quiz_bot.db"


@dataclass
class QuizConfig:
    """Quiz sozlamalari"""
    min_options: int = 2  # Minimal variant soni
    max_options: int = 6  # Maksimal variant soni
    default_time: int = 30  # Default vaqt (soniya)
    time_options: dict = None  # Vaqt variantlari
    
    def __post_init__(self):
        if self.time_options is None:
            self.time_options = {
                "10_sec": 10,
                "20_sec": 20,
                "30_sec": 30,
                "1_min": 60,
                "2_min": 120,
                "3_min": 180
            }


@dataclass
class Config:
    """Umumiy konfiguratsiya"""
    bot: BotConfig
    database: DatabaseConfig
    quiz: QuizConfig


def load_config() -> Config:
    """Konfiguratsiyani yuklash"""
    return Config(
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN", ""),
            admin_ids=[int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
        ),
        database=DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "data/quiz_bot.db")
        ),
        quiz=QuizConfig()
    )


# Global config instance
config = load_config()
