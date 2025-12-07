from aiogram import Router

from .start import router as start_router
from .upload import router as upload_router
from .settings import router as settings_router
from .quiz import router as quiz_router
from .quiz_settings import router as quiz_settings_router
from .group import router as group_router
from .group_quiz_settings import router as group_quiz_settings_router
from .statistics import router as statistics_router
from .cancel import router as cancel_router


def get_all_routers() -> list[Router]:
    """Barcha routerlarni qaytarish"""
    return [
        start_router,
        cancel_router,  # Cancel birinchi bo'lishi kerak
        upload_router,
        settings_router,
        group_quiz_settings_router,  # Group quiz settings birinchi
        quiz_settings_router,
        quiz_router,
        group_router,
        statistics_router,
    ]


__all__ = [
    "get_all_routers",
    "start_router",
    "upload_router", 
    "settings_router",
    "quiz_settings_router",
    "group_quiz_settings_router",
    "quiz_router",
    "group_router",
    "statistics_router",
    "cancel_router",
]
