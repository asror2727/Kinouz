import os
from dotenv import load_dotenv

load_dotenv()

# --- Bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# --- Database (MongoDB) ---
# MongoDB SHART: kanallar, kinolar, foydalanuvchilar, to'lovlar shu yerda saqlanadi.
# Render'da ishlatish uchun MongoDB Atlas (bepul tier) tavsiya etiladi -> https://www.mongodb.com/atlas
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "kino_bot")

# --- Adminlar (Telegram user_id, vergul bilan ajratilgan) ---
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# --- Admin/to'lovlar bildirishnoma yuboriladigan chat (guruh yoki shaxsiy) ---
# Bo'sh qoldirilsa, birinchi ADMIN_ID ga yuboriladi.
PAYMENTS_CHAT_ID = os.getenv("PAYMENTS_CHAT_ID", "")

# --- Support ---
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@x7fan")

# --- To'lov (hozircha qo'lda tasdiqlash: karta raqami beriladi, admin tasdiqlaydi) ---
CARD_NUMBER = os.getenv("CARD_NUMBER", "8600 0000 0000 0000")
CARD_OWNER = os.getenv("CARD_OWNER", "F.I.Sh.")

# --- Dasturchi haqida (/dev) ---
DEV_USERNAME = os.getenv("DEV_USERNAME", "@x7fan")
