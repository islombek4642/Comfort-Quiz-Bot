"""
Botni ishga tushirish uchun yordamchi script
"""
import asyncio
import sys
from pathlib import Path

# Loyiha papkasini PATH ga qo'shish
sys.path.insert(0, str(Path(__file__).parent))

from bot.main import main

if __name__ == "__main__":
    asyncio.run(main())
