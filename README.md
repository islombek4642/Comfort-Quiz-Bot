# 📝 Quiz Bot

Word (DOCX) fayllaridan avtomatik test yaratuvchi Telegram bot.

## ✨ Xususiyatlar

- 📄 **Word fayldan test yaratish** - DOCX formatdagi fayllarni avtomatik parse qilish
- ⏱ **Vaqt belgilash** - Har bir savol uchun vaqt limiti
- 🔀 **Variantlarni aralashtirish** - Har safar boshqa tartibda
- 👥 **Guruhda test** - Guruh a'zolari bilan raqobat
- 🔗 **Testni ulashish** - Do'stlarga link yuborish
- 📊 **Statistika** - Natijalar va tahlil

## 🏗 Loyiha Strukturasi

```
QuizBot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Asosiy ishga tushirish
│   ├── config.py            # Konfiguratsiya
│   │
│   ├── handlers/            # Xabar handlerlari
│   │   ├── start.py         # /start va yordam
│   │   ├── upload.py        # Fayl yuklash
│   │   ├── settings.py      # Test sozlamalari
│   │   ├── quiz.py          # Test jarayoni
│   │   ├── group.py         # Guruh testlari
│   │   ├── statistics.py    # Statistika
│   │   └── cancel.py        # Bekor qilish
│   │
│   ├── keyboards/           # Tugmalar
│   │   ├── main_menu.py
│   │   ├── settings_kb.py
│   │   └── quiz_kb.py
│   │
│   ├── services/            # Biznes logika
│   │   ├── docx_parser.py   # DOCX parser
│   │   ├── quiz_manager.py  # Quiz boshqaruvi
│   │   └── statistics_service.py
│   │
│   ├── models/              # Ma'lumot modellari
│   │   └── quiz_model.py
│   │
│   ├── database/            # Database
│   │   └── db.py
│   │
│   ├── states/              # FSM holatlar
│   │   └── quiz_states.py
│   │
│   └── utils/               # Yordamchi funksiyalar
│       └── helpers.py
│
├── data/                    # Database fayllari
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

## 🚀 O'rnatish

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/yourusername/quiz-bot.git
cd quiz-bot
```

### 2. Virtual muhit yaratish

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. Konfiguratsiya

`.env.example` faylini `.env` ga nusxalang va to'ldiring:

```bash
cp .env.example .env
```

`.env` faylni tahrirlang:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
```

### 5. Botni ishga tushirish

```bash
python run.py
```

## 📝 Word Fayl Formati

### Format 1: So'roq belgisi bilan (Tavsiya etiladi)

```
?Qaysi javobda axborot o'lchov birliklari o'sib borish tartibida ko'rsatilgan?
+bit, bayt, kilobayt, megabayt, gigabayt
=bayt, bit, megabayt, kilobayt, gigabayt
=bit, kilobayt, megabayt, bayt, gigabayt
=Mbayt, bayt, megabayt, gigabayt

?Kompyuter tarmog'ini tashkil etuvchilari nechta qatlamga tegishli bo'ladi
+4
=2
=3
=5
```

**Belgilar:**

- `?` - Savol boshlanishi
- `+` - To'g'ri javob
- `=` - Noto'g'ri variant

### Format 2: Klassik format

```
1. Savol matni?
A) Birinchi variant
B) Ikkinchi variant
*C) To'g'ri javob
D) To'rtinchi variant

2. Ikkinchi savol?
A) Variant 1
+B) To'g'ri javob
C) Variant 3
D) Variant 4
```

**To'g'ri javobni belgilash:**

- `*A) Javob` - Boshida yulduzcha
- `+B) Javob` - Boshida plus
- `C) Javob*` - Oxirida yulduzcha

## 🎮 Foydalanish

### Shaxsiy chatda:

1. Botga `/start` yozing
2. "📄 Test yuklash" tugmasini bosing
3. Word faylni yuboring
4. Sarlavha kiriting
5. Vaqt va sozlamalarni tanlang
6. Testni boshlang!

### Guruhda:

1. Botni guruhga qo'shing
2. Admin huquqini bering
3. `/startquiz TESTKODI` yozing

## 🛠 Texnologiyalar

- **Python 3.10+**
- **aiogram 3.x** - Telegram Bot API
- **python-docx** - Word fayllarni o'qish
- **aiosqlite** - Asinxron SQLite database
- **FSM** - Finite State Machine

## 📊 Ma'lumotlar bazasi

Bot SQLite database ishlatadi. Jadvallar:

- `quizzes` - Testlar
- `results` - Natijalar
- `user_statistics` - Foydalanuvchi statistikasi

## 🔧 Kengaytirish

Yangi handler qo'shish:

1. `bot/handlers/` papkasida yangi fayl yarating
2. Router yarating va handler'larni qo'shing
3. `bot/handlers/__init__.py` da import qiling
4. `get_all_routers()` funksiyasiga qo'shing

## 📄 Litsenziya

MIT License

## 👨‍💻 Muallif

Xamidullayev Islombek - https://t.me/xamidullayev_i

---

⭐ Loyiha yoqsa, yulduzcha qo'ying!
