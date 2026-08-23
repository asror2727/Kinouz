"""
KINO BOT - hammasi bitta faylda.
Kam fayl = kam xato ehtimoli. Barcha qism (config, DB, klaviatura, handler)
shu yerda ketma-ket yozilgan.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
load_dotenv()

# ============================================================
# 1. CONFIG
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "kino_bot")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
PAYMENTS_CHAT_ID = os.getenv("PAYMENTS_CHAT_ID", "")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@x7fan")
DEV_USERNAME = os.getenv("DEV_USERNAME", "@x7fan")
CARD_NUMBER = os.getenv("CARD_NUMBER", "8600 0000 0000 0000")
CARD_OWNER = os.getenv("CARD_OWNER", "F.I.Sh.")

PLAN_DAYS = {"1m": 30, "3m": 90, "1y": 365}
PLAN_NAMES = {"1m": "1 oylik", "3m": "3 oylik", "1y": "1 yillik"}

# ============================================================
# 2. PREMIUM EMOJI (faqat matn ichida ishlaydi, tugmada emas -
#    bu Telegram Bot API'ning o'z cheklovi)
# ============================================================
EMOJI = {
    "person": ("\U0001F464", "5271829423899845716"),
    "wave": ("\U0001F44B", "5271765841203995324"),
    "money": ("\U0001F4B0", "5271857409906745357"),
    "support": ("\u260E\ufe0f", "5271586238556574482"),
    "id": ("\U0001F194", "5271628651358622439"),
    "back": ("\u2b05\ufe0f", "5271512047291507931"),
    "click": ("\U0001F446", "5271857014769754460"),
    "search": ("\U0001F50D", "5272013068111485452"),
    "dollar": ("\U0001F4B5", "5271739719212901906"),
    "check": ("\u2705", "5271507881173227410"),
    "card": ("\U0001F4B3", "5271907450570709756"),
    "warning": ("\u26a0\ufe0f", "5271535227230028862"),
    "dot": ("\u25aa\ufe0f", "5274239519028191789"),
}


def e(name: str) -> str:
    fb, cid = EMOJI[name]
    return f'<tg-emoji emoji-id="{cid}">{fb}</tg-emoji>'


def f(name: str) -> str:
    return EMOJI[name][0]


# ============================================================
# 3. DATABASE (MongoDB)
# ============================================================
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
users_col = db["users"]
channels_col = db["channels"]
movies_col = db["movies"]
prices_col = db["prices"]
payments_col = db["payments"]
comments_col = db["comments"]
saved_col = db["saved_movies"]


async def add_user(user_id, username):
    await users_col.update_one(
        {"_id": user_id},
        {"$setOnInsert": {"_id": user_id, "joined_at": datetime.utcnow(), "vip_until": None}},
        upsert=True,
    )
    if username:
        await users_col.update_one({"_id": user_id}, {"$set": {"username": username}})


async def get_user(user_id):
    return await users_col.find_one({"_id": user_id})


async def all_user_ids():
    return [d["_id"] async for d in users_col.find({}, {"_id": 1})]


async def users_count():
    return await users_col.count_documents({})


async def set_vip(user_id, days):
    u = await get_user(user_id)
    base = datetime.utcnow()
    if u and u.get("vip_until") and u["vip_until"] > base:
        base = u["vip_until"]
    until = base + timedelta(days=days)
    await users_col.update_one({"_id": user_id}, {"$set": {"vip_until": until}}, upsert=True)
    return until


async def is_vip(user_id):
    u = await get_user(user_id)
    return bool(u and u.get("vip_until") and u["vip_until"] > datetime.utcnow())


async def add_channel(chat_id, title, username, link):
    await channels_col.update_one(
        {"_id": chat_id}, {"$set": {"title": title, "username": username, "link": link}}, upsert=True
    )


async def remove_channel(chat_id):
    await channels_col.delete_one({"_id": chat_id})


async def get_channels():
    return await channels_col.find().to_list(length=100)


async def add_movie(code, file_id, content_type, title=""):
    await movies_col.update_one(
        {"_id": str(code)},
        {
            "$set": {"file_id": file_id, "content_type": content_type, "title": title, "added_at": datetime.utcnow()},
            "$setOnInsert": {"views": 0},
        },
        upsert=True,
    )


async def get_movie(code):
    return await movies_col.find_one({"_id": str(code)})


async def delete_movie(code):
    await movies_col.delete_one({"_id": str(code)})


async def inc_views(code):
    await movies_col.update_one({"_id": str(code)}, {"$inc": {"views": 1}})


async def get_random_movie():
    r = await movies_col.aggregate([{"$sample": {"size": 1}}]).to_list(length=1)
    return r[0] if r else None


async def get_top_movies(limit=10):
    return await movies_col.find().sort("views", -1).limit(limit).to_list(length=limit)


async def get_last_movies(limit=10):
    return await movies_col.find().sort("added_at", -1).limit(limit).to_list(length=limit)


async def movies_count():
    return await movies_col.count_documents({})


async def get_prices():
    p = await prices_col.find_one({"_id": "plans"})
    if not p:
        p = {"_id": "plans", "1m": 10000, "3m": 25000, "1y": 75000}
        await prices_col.insert_one(p)
    return p


async def set_price(plan, amount):
    await prices_col.update_one({"_id": "plans"}, {"$set": {plan: amount}}, upsert=True)


async def create_payment(user_id, plan, amount, method):
    res = await payments_col.insert_one(
        {"user_id": user_id, "plan": plan, "amount": amount, "method": method,
         "status": "pending", "created_at": datetime.utcnow()}
    )
    return res.inserted_id


async def get_pending_payment(user_id):
    return await payments_col.find_one({"user_id": user_id, "status": "pending"}, sort=[("created_at", -1)])


async def get_payment(payment_id):
    if isinstance(payment_id, str):
        payment_id = ObjectId(payment_id)
    return await payments_col.find_one({"_id": payment_id})


async def confirm_payment(payment_id):
    if isinstance(payment_id, str):
        payment_id = ObjectId(payment_id)
    await payments_col.update_one({"_id": payment_id}, {"$set": {"status": "confirmed", "confirmed_at": datetime.utcnow()}})


async def reject_payment(payment_id):
    if isinstance(payment_id, str):
        payment_id = ObjectId(payment_id)
    await payments_col.update_one({"_id": payment_id}, {"$set": {"status": "rejected"}})


async def add_comment(code, user_id, username, text):
    await comments_col.insert_one(
        {"code": str(code), "user_id": user_id, "username": username, "text": text, "created_at": datetime.utcnow()}
    )


async def get_comments(code, limit=5):
    return await comments_col.find({"code": str(code)}).sort("created_at", -1).limit(limit).to_list(length=limit)


async def comments_count(code):
    return await comments_col.count_documents({"code": str(code)})


async def save_movie(user_id, code):
    await saved_col.update_one(
        {"user_id": user_id, "code": str(code)},
        {"$setOnInsert": {"user_id": user_id, "code": str(code), "saved_at": datetime.utcnow()}},
        upsert=True,
    )


async def get_saved_movies(user_id, limit=20):
    return await saved_col.find({"user_id": user_id}).sort("saved_at", -1).limit(limit).to_list(length=limit)


# ============================================================
# 4. FSM HOLATLARI
# ============================================================
class UserStates(StatesGroup):
    waiting_code = State()
    waiting_comment = State()


class AdminStates(StatesGroup):
    waiting_channel_forward = State()
    waiting_movie_code = State()
    waiting_movie_content = State()
    waiting_delete_code = State()
    waiting_price_amount = State()
    waiting_broadcast = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# 5. KLAVIATURALAR
# ============================================================
def kb_subscribe(channels, show_vip=True):
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.row(InlineKeyboardButton(text=f"➕ {ch.get('title') or 'Kanal'}", url=ch["link"]))
    kb.row(InlineKeyboardButton(text=f"{f('check')} Tekshirish", callback_data="check_sub"))
    if show_vip:
        kb.row(InlineKeyboardButton(text="💎 PREMIUM", callback_data="vip_info"))
    return kb.as_markup()


def kb_vip_info():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🛒 Sotib olish", callback_data="vip_buy"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Menu", callback_data="back_to_start"))
    return kb.as_markup()


def kb_vip_plans(prices):
    kb = InlineKeyboardBuilder()
    for plan in ("1m", "3m", "1y"):
        amount = prices.get(plan, 0)
        kb.row(InlineKeyboardButton(text=f"{PLAN_NAMES[plan]} - {amount:,} so'm".replace(",", " "), callback_data=f"plan_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Orqaga", callback_data="vip_info"))
    return kb.as_markup()


def kb_payment_method(plan):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('card')} Hazna", callback_data=f"pay_hazna_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('card')} Payme", callback_data=f"pay_payme_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('card')} Click", callback_data=f"pay_click_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Orqaga", callback_data="vip_buy"))
    return kb.as_markup()


def kb_payment_confirm():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('check')} Tekshirish", callback_data="check_payment"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Orqaga", callback_data="vip_buy"))
    return kb.as_markup()


def kb_admin_payment_notify(payment_id):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"apay_ok_{payment_id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"apay_no_{payment_id}"),
    )
    return kb.as_markup()


def kb_main_menu():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('search')} Kod kiritish", callback_data="enter_code"))
    kb.row(InlineKeyboardButton(text=f"{f('support')} Support", callback_data="support"))
    return kb.as_markup()


def kb_support():
    kb = InlineKeyboardBuilder()
    uname = SUPPORT_USERNAME.lstrip("@")
    kb.row(InlineKeyboardButton(text=f"{f('support')} Yozish", url=f"https://t.me/{uname}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Menu", callback_data="back_to_start"))
    return kb.as_markup()


def kb_movie(code):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📢 Ko'proq kino", callback_data="more_movies"),
        InlineKeyboardButton(text="💾 Saqlangan kino", callback_data="saved_movies"),
    )
    kb.row(
        InlineKeyboardButton(text="💬 Izoh yozish", callback_data=f"comment_{code}"),
        InlineKeyboardButton(text="💾 Saqlash", callback_data=f"save_{code}"),
    )
    return kb.as_markup()


def kb_admin_panel():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📢 Kanal qo'shish", callback_data="adm_add_channel"))
    kb.row(InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="adm_del_channel"))
    kb.row(InlineKeyboardButton(text="🎬 Kino/kod qo'shish", callback_data="adm_add_movie"))
    kb.row(InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="adm_del_movie"))
    kb.row(InlineKeyboardButton(text="💎 Narxlarni sozlash", callback_data="adm_prices"))
    kb.row(InlineKeyboardButton(text="⏳ Kutayotgan to'lovlar", callback_data="adm_pending_payments"))
    kb.row(InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats"))
    kb.row(InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="adm_broadcast"))
    return kb.as_markup()


def kb_admin_back():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('back')} Admin panel", callback_data="adm_back"))
    return kb.as_markup()


def kb_admin_prices(prices):
    kb = InlineKeyboardBuilder()
    for plan in ("1m", "3m", "1y"):
        amount = prices.get(plan, 0)
        kb.row(InlineKeyboardButton(text=f"{PLAN_NAMES[plan]}: {amount:,} so'm".replace(",", " "), callback_data=f"adm_setprice_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Admin panel", callback_data="adm_back"))
    return kb.as_markup()


def kb_confirm_del_channel(channels):
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.row(InlineKeyboardButton(text=f"🗑 {ch.get('title', ch['_id'])}", callback_data=f"adm_delch_{ch['_id']}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Admin panel", callback_data="adm_back"))
    return kb.as_markup()


# ============================================================
# 6. YORDAMCHI: obuna tekshirish
# ============================================================
NOT_MEMBER = {"left", "kicked"}


async def check_subscription(bot: Bot, user_id: int):
    channels = await get_channels()
    if not channels:
        return True, []
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["_id"], user_id=user_id)
            if member.status in NOT_MEMBER:
                missing.append(ch)
        except TelegramBadRequest:
            missing.append(ch)
    return len(missing) == 0, missing


# ============================================================
# 7. USER ROUTER
# ============================================================
user_router = Router()

WELCOME_TEXT = (
    f"{e('wave')} Salom ♪\n\n"
    "/rand - 🔄 Random kino\n"
    "/top - 🏆 Top kino\n"
    "/last - 📽️ Oxirgi yuklangan\n"
    "/help - ☎️ Qo'llab quvvatlash\n"
    "/vip - 💎 Premium\n"
    "/dev - 🧑\u200d💻 Dasturchi\n"
    "/liv - izoh\n\n"
    "🍿 Kino kodi yoki nomini yuboring:"
)

VIP_TEXT = (
    "💎 «PREMIUM» obunasi nima uchun kerak?\n\n"
    f"{e('warning')} • Kanallarga obuna bo'lish shart emas.\n"
    "🚫 • Hech qanday reklamalarsiz.\n"
    "🎞 • Kerakli kinolar sifatli formatda.\n"
    "💎 • Premium kinolarni ko'rish imkoniyati."
)


async def send_main_menu(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=kb_main_menu())


async def gate_or_menu(bot: Bot, user_id: int, message: Message):
    if await is_vip(user_id):
        await send_main_menu(message)
        return
    ok, missing = await check_subscription(bot, user_id)
    if ok:
        await send_main_menu(message)
    else:
        await message.answer(
            f"{e('warning')} Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=kb_subscribe(missing),
        )


@user_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    await add_user(message.from_user.id, message.from_user.username)
    await gate_or_menu(bot, message.from_user.id, message)


@user_router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, bot: Bot):
    ok, missing = await check_subscription(bot, callback.from_user.id)
    if ok:
        await callback.message.delete()
        await send_main_menu(callback.message)
        await callback.answer("Xush kelibsiz! ✅")
    else:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)


@user_router.callback_query(F.data == "back_to_start")
async def cb_back_to_start(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await gate_or_menu(bot, callback.from_user.id, callback.message)
    await callback.answer()


@user_router.message(Command("vip"))
async def cmd_vip(message: Message):
    await message.answer(VIP_TEXT, reply_markup=kb_vip_info())


@user_router.callback_query(F.data == "vip_info")
async def cb_vip_info(callback: CallbackQuery):
    await callback.message.edit_text(VIP_TEXT, reply_markup=kb_vip_info())
    await callback.answer()


@user_router.callback_query(F.data == "vip_buy")
async def cb_vip_buy(callback: CallbackQuery):
    prices = await get_prices()
    await callback.message.edit_text("➡️ Kerakli ta'rifni tanlang:", reply_markup=kb_vip_plans(prices))
    await callback.answer()


@user_router.callback_query(F.data.startswith("plan_"))
async def cb_choose_plan(callback: CallbackQuery):
    plan = callback.data.split("_", 1)[1]
    await callback.message.edit_text("💳 To'lov usulini tanlang:", reply_markup=kb_payment_method(plan))
    await callback.answer()


@user_router.callback_query(F.data.startswith("pay_"))
async def cb_choose_method(callback: CallbackQuery, bot: Bot):
    _, method, plan = callback.data.split("_")
    prices = await get_prices()
    amount = prices.get(plan, 0)
    payment_id = await create_payment(callback.from_user.id, plan, amount, method)

    text = (
        f"🚀 {amount:,} so'm to'lov qilish uchun quyidagi ma'lumot orqali to'lang:\n\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: {CARD_OWNER}\n\n"
        "To'lovdan so'ng ✅ Tekshirish tugmasini bosing."
    ).replace(",", " ")
    await callback.message.edit_text(text, reply_markup=kb_payment_confirm())
    await callback.answer()

    notify_chat = PAYMENTS_CHAT_ID or (ADMIN_IDS[0] if ADMIN_IDS else None)
    if notify_chat:
        u = callback.from_user
        info = (
            f"💳 <b>Yangi to'lov</b>\n\n"
            f"👤 {u.full_name} (@{u.username or '—'}, id: {u.id})\n"
            f"📦 Tarif: {plan} | Usul: {method}\n"
            f"💰 Summa: {amount:,} so'm".replace(",", " ")
        )
        try:
            await bot.send_message(notify_chat, info, reply_markup=kb_admin_payment_notify(str(payment_id)))
        except Exception:
            pass


@user_router.callback_query(F.data == "check_payment")
async def cb_check_payment(callback: CallbackQuery):
    payment = await get_pending_payment(callback.from_user.id)
    if not payment:
        await callback.answer("Sizda tasdiqlanmagan to'lov topilmadi.", show_alert=True)
        return
    if payment["status"] == "confirmed":
        await callback.message.delete()
        await send_main_menu(callback.message)
        await callback.answer("✅ To'lovingiz tasdiqlandi! Premium faollashtirildi.", show_alert=True)
    else:
        await callback.answer("⏳ To'lovingiz hali admin tomonidan tasdiqlanmagan.", show_alert=True)


@user_router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(f"{e('support')} Savol va takliflar uchun murojaat qiling:", reply_markup=kb_support())


@user_router.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery):
    await callback.message.edit_text(f"{e('support')} Savol va takliflar uchun murojaat qiling:", reply_markup=kb_support())
    await callback.answer()


@user_router.message(Command("dev"))
async def cmd_dev(message: Message):
    await message.answer(f"🧑\u200d💻 Dasturchi: {DEV_USERNAME}")


@user_router.callback_query(F.data == "enter_code")
async def cb_enter_code(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_code)
    await callback.message.answer("5 kabi kino kodini yuboring:")
    await callback.answer()


async def send_movie_by_code(message: Message, code: str):
    movie = await get_movie(code)
    if not movie:
        await message.answer("❌ Bunday kodli kino topilmadi. Qaytadan urinib ko'ring.")
        return
    await inc_views(code)
    caption = movie.get("title") or f"🎬 Kino #{code}"
    kb = kb_movie(code)
    if movie["content_type"] == "video":
        await message.answer_video(movie["file_id"], caption=caption, reply_markup=kb)
    else:
        await message.answer_document(movie["file_id"], caption=caption, reply_markup=kb)


@user_router.message(UserStates.waiting_code)
async def process_code(message: Message, state: FSMContext):
    await state.clear()
    await send_movie_by_code(message, message.text.strip())


@user_router.message(F.text.regexp(r"^\d+$"))
async def process_direct_code(message: Message):
    await send_movie_by_code(message, message.text.strip())


@user_router.message(Command("rand"))
async def cmd_rand(message: Message):
    movie = await get_random_movie()
    if not movie:
        await message.answer("Hozircha bazada kino yo'q.")
        return
    await send_movie_by_code(message, movie["_id"])


@user_router.message(Command("top"))
async def cmd_top(message: Message):
    movies = await get_top_movies()
    if not movies:
        await message.answer("Hozircha bazada kino yo'q.")
        return
    text = "🏆 <b>Top kinolar:</b>\n\n" + "\n".join(
        f"{i + 1}. #{m['_id']} - {m.get('title') or 'nomsiz'} ({m.get('views', 0)} ko'rishlar)"
        for i, m in enumerate(movies)
    )
    await message.answer(text)


@user_router.message(Command("last"))
async def cmd_last(message: Message):
    movies = await get_last_movies()
    if not movies:
        await message.answer("Hozircha bazada kino yo'q.")
        return
    text = "📽️ <b>Oxirgi yuklangan kinolar:</b>\n\n" + "\n".join(
        f"▪️ #{m['_id']} - {m.get('title') or 'nomsiz'}" for m in movies
    )
    await message.answer(text)


@user_router.callback_query(F.data == "more_movies")
async def cb_more_movies(callback: CallbackQuery):
    channels = await get_channels()
    if not channels:
        await callback.answer("Hozircha kanallar qo'shilmagan.", show_alert=True)
        return
    text = "📢 Ko'proq kinolar uchun kanallarimizga o'ting:\n\n" + "\n".join(f"➕ {ch.get('title')}" for ch in channels)
    await callback.message.answer(text)
    await callback.answer()


@user_router.callback_query(F.data == "saved_movies")
async def cb_saved_movies(callback: CallbackQuery):
    saved = await get_saved_movies(callback.from_user.id)
    if not saved:
        await callback.answer("Sizda saqlangan kino yo'q.", show_alert=True)
        return
    text = "💾 <b>Saqlangan kinolaringiz:</b>\n\n" + "\n".join(f"▪️ #{s['code']}" for s in saved)
    await callback.message.answer(text)
    await callback.answer()


@user_router.callback_query(F.data.startswith("save_"))
async def cb_save_movie(callback: CallbackQuery):
    code = callback.data.split("_", 1)[1]
    await save_movie(callback.from_user.id, code)
    await callback.answer("💾 Saqlandi!", show_alert=True)


@user_router.callback_query(F.data.startswith("comment_"))
async def cb_comment_start(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_", 1)[1]
    await state.set_state(UserStates.waiting_comment)
    await state.update_data(code=code)
    await callback.message.answer(f"💬 #{code} kinosi uchun izohingizni yozing:")
    await callback.answer()


@user_router.message(UserStates.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data.get("code")
    await state.clear()
    await add_comment(code, message.from_user.id, message.from_user.username, message.text)
    count = await comments_count(code)
    await message.answer(f"✅ Izohingiz uchun rahmat! Bu kino uchun jami {count} ta izoh bor.")


@user_router.message(Command("liv"))
async def cmd_liv(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /liv <kino_kodi>")
        return
    code = parts[1].strip()
    comments = await get_comments(code)
    if not comments:
        await message.answer("Bu kino uchun hali izohlar yo'q.")
        return
    lines = [f"👤 {c.get('username') or c['user_id']}: {c['text']}" for c in comments]
    await message.answer("💬 <b>Izohlar:</b>\n\n" + "\n".join(lines))


# ============================================================
# 8. ADMIN ROUTER
# ============================================================
admin_router = Router()


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 <b>Admin panel</b>", reply_markup=kb_admin_panel())


@admin_router.callback_query(F.data == "adm_back")
async def cb_adm_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("🔧 <b>Admin panel</b>", reply_markup=kb_admin_panel())
    await callback.answer()


@admin_router.callback_query(F.data == "adm_add_channel")
async def cb_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_channel_forward)
    await callback.message.edit_text(
        "📢 Botni kerakli kanalga <b>admin</b> qilib qo'shing.\n\n"
        "Keyin o'sha kanaldan istalgan xabarni shu yerga forward qiling "
        "(yoki @username yuboring).",
        reply_markup=kb_admin_back(),
    )
    await callback.answer()


@admin_router.message(AdminStates.waiting_channel_forward)
async def process_add_channel(message: Message, bot: Bot, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    chat_id = None
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
    elif message.text and message.text.startswith("@"):
        chat_id = message.text.strip()
    else:
        await message.answer("❌ Kanaldan xabar forward qiling yoki @username yuboring.")
        return
    try:
        chat = await bot.get_chat(chat_id)
        member = await bot.get_chat_member(chat.id, bot.id)
        if member.status not in ("administrator", "creator"):
            await message.answer("❌ Bot ushbu kanalda admin emas. Avval botni admin qiling.")
            return
        link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
        if not link:
            link = (await bot.create_chat_invite_link(chat.id)).invite_link
        await add_channel(chat.id, chat.title, chat.username, link)
        await state.clear()
        await message.answer(f"✅ Kanal qo'shildi: {chat.title}", reply_markup=kb_admin_back())
    except Exception as ex:
        await message.answer(f"❌ Xatolik: {ex}\nQaytadan urinib ko'ring.")


@admin_router.callback_query(F.data == "adm_del_channel")
async def cb_del_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    channels = await get_channels()
    if not channels:
        await callback.answer("Kanallar mavjud emas.", show_alert=True)
        return
    await callback.message.edit_text("🗑 O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=kb_confirm_del_channel(channels))
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_delch_"))
async def cb_confirm_del_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    chat_id = callback.data.split("_", 2)[2]
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass
    await remove_channel(chat_id)
    await callback.answer("✅ Kanal o'chirildi.", show_alert=True)
    await cb_del_channel(callback)


@admin_router.callback_query(F.data == "adm_add_movie")
async def cb_add_movie(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_movie_code)
    await callback.message.edit_text("🔢 Kino uchun kod kiriting, masalan: 5", reply_markup=kb_admin_back())
    await callback.answer()


@admin_router.message(AdminStates.waiting_movie_code)
async def process_movie_code(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip()
    await state.update_data(code=code)
    await state.set_state(AdminStates.waiting_movie_content)
    await message.answer(f"🎬 Endi #{code} kodi uchun kino faylini (video yoki hujjat) yuboring.")


@admin_router.message(AdminStates.waiting_movie_content, F.video | F.document)
async def process_movie_content(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    code = data["code"]
    if message.video:
        file_id, content_type = message.video.file_id, "video"
    else:
        file_id, content_type = message.document.file_id, "document"
    await add_movie(code, file_id, content_type, title=message.caption or "")
    await state.clear()
    await message.answer(f"✅ #{code} kodli kino bazaga qo'shildi!", reply_markup=kb_admin_back())


@admin_router.message(AdminStates.waiting_movie_content)
async def process_movie_content_wrong(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("❌ Iltimos video yoki fayl yuboring.")


@admin_router.callback_query(F.data == "adm_del_movie")
async def cb_del_movie(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_delete_code)
    await callback.message.edit_text("🗑 O'chirish uchun kino kodini yuboring:", reply_markup=kb_admin_back())
    await callback.answer()


@admin_router.message(AdminStates.waiting_delete_code)
async def process_del_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip()
    await delete_movie(code)
    await state.clear()
    await message.answer(f"✅ #{code} o'chirildi.", reply_markup=kb_admin_back())


@admin_router.callback_query(F.data == "adm_prices")
async def cb_prices(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    prices = await get_prices()
    await callback.message.edit_text("💎 Narxni o'zgartirish uchun tarifni tanlang:", reply_markup=kb_admin_prices(prices))
    await callback.answer()


@admin_router.callback_query(F.data.startswith("adm_setprice_"))
async def cb_setprice(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    plan = callback.data.split("_", 2)[2]
    await state.set_state(AdminStates.waiting_price_amount)
    await state.update_data(plan=plan)
    await callback.message.edit_text(f"✏️ {plan} uchun yangi narxni so'mda kiriting (masalan: 15000):", reply_markup=kb_admin_back())
    await callback.answer()


@admin_router.message(AdminStates.waiting_price_amount)
async def process_setprice(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam kiriting.")
        return
    data = await state.get_data()
    plan = data["plan"]
    amount = int(message.text.strip())
    await set_price(plan, amount)
    await state.clear()
    await message.answer(f"✅ {plan} narxi {amount:,} so'm qilib o'zgartirildi.".replace(",", " "), reply_markup=kb_admin_back())


@admin_router.callback_query(F.data == "adm_pending_payments")
async def cb_pending_payments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    payments = await payments_col.find({"status": "pending"}).to_list(length=20)
    if not payments:
        await callback.answer("Kutayotgan to'lovlar yo'q.", show_alert=True)
        return
    lines = [
        f"🆔 {p['_id']} | user: {p['user_id']} | {p['plan']} | {p['amount']:,} so'm | {p['method']}".replace(",", " ")
        for p in payments
    ]
    await callback.message.answer(
        "⏳ <b>Kutayotgan to'lovlar:</b>\n\n" + "\n".join(lines) + "\n\nTasdiqlash: /confirm <id>\nBekor qilish: /reject <id>"
    )
    await callback.answer()


@admin_router.message(Command("confirm"))
async def cmd_confirm_payment(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /confirm <payment_id>")
        return
    payment = await get_payment(parts[1].strip())
    if not payment:
        await message.answer("❌ Bunday to'lov topilmadi.")
        return
    await confirm_payment(payment["_id"])
    days = PLAN_DAYS.get(payment["plan"], 30)
    until = await set_vip(payment["user_id"], days)
    await message.answer(f"✅ Tasdiqlandi. Foydalanuvchi VIP: {until:%Y-%m-%d}")
    try:
        await bot.send_message(payment["user_id"], "✅ To'lovingiz tasdiqlandi! Premium faollashtirildi. /start ni bosing.")
    except Exception:
        pass


@admin_router.message(Command("reject"))
async def cmd_reject_payment(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /reject <payment_id>")
        return
    payment = await get_payment(parts[1].strip())
    if not payment:
        await message.answer("❌ Bunday to'lov topilmadi.")
        return
    await reject_payment(payment["_id"])
    await message.answer("❌ To'lov bekor qilindi.")


@admin_router.callback_query(F.data.startswith("apay_ok_"))
async def cb_apay_ok(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    payment_id = callback.data.split("_", 2)[2]
    payment = await get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await confirm_payment(payment["_id"])
    days = PLAN_DAYS.get(payment["plan"], 30)
    until = await set_vip(payment["user_id"], days)
    await callback.message.edit_text(callback.message.text + f"\n\n✅ Tasdiqlandi ({until:%Y-%m-%d} gacha)")
    await callback.answer("✅ Tasdiqlandi")
    try:
        await bot.send_message(payment["user_id"], "✅ To'lovingiz tasdiqlandi! Premium faollashtirildi. /start ni bosing.")
    except Exception:
        pass


@admin_router.callback_query(F.data.startswith("apay_no_"))
async def cb_apay_no(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    payment_id = callback.data.split("_", 2)[2]
    payment = await get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await reject_payment(payment["_id"])
    await callback.message.edit_text(callback.message.text + "\n\n❌ Bekor qilindi")
    await callback.answer("❌ Bekor qilindi")
    try:
        await bot.send_message(payment["user_id"], "❌ To'lovingiz tasdiqlanmadi. Support bilan bog'laning.")
    except Exception:
        pass


@admin_router.callback_query(F.data == "adm_stats")
async def cb_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    users = await users_count()
    movies = await movies_count()
    pending = await payments_col.count_documents({"status": "pending"})
    confirmed = await payments_col.count_documents({"status": "confirmed"})
    await callback.message.answer(
        f"📊 <b>Statistika</b>\n\n👥 Foydalanuvchilar: {users}\n🎬 Kinolar: {movies}\n"
        f"⏳ Kutayotgan to'lovlar: {pending}\n✅ Tasdiqlangan to'lovlar: {confirmed}"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "adm_broadcast")
async def cb_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text("📣 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:", reply_markup=kb_admin_back())
    await callback.answer()


@admin_router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await all_user_ids()
    sent, failed = 0, 0
    status_msg = await message.answer(f"📣 Yuborilmoqda... 0/{len(user_ids)}")
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ Yuborildi: {sent} | ❌ Xato: {failed}")


# ============================================================
# 9. ISHGA TUSHIRISH
# ============================================================
async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env / Environment'da ko'rsatilmagan!")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # admin_router user_router'dan OLDIN - admin FSM holatlari
    # (masalan kod/narx kiritish) user'ning "raqam=kino qidir" qoidasidan
    # ustun turishi uchun.
    dp.include_router(admin_router)
    dp.include_router(user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
