from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from emojis import f
from database import PLAN_NAMES


# ---------------- Majburiy obuna ----------------
def subscribe_keyboard(channels, show_vip: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        title = ch.get("title") or "Kanal"
        kb.row(InlineKeyboardButton(text=f"➕ {title}", url=ch["link"]))
    kb.row(InlineKeyboardButton(text=f"{f('check')} Tekshirish", callback_data="check_sub"))
    if show_vip:
        kb.row(InlineKeyboardButton(text="💎 PREMIUM", callback_data="vip_info"))
    return kb.as_markup()


# ---------------- VIP / Premium ----------------
def vip_info_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🛒 Sotib olish", callback_data="vip_buy"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Menu", callback_data="back_to_start"))
    return kb.as_markup()


def vip_plans_keyboard(prices: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for plan in ("1m", "3m", "1y"):
        amount = prices.get(plan, 0)
        kb.row(
            InlineKeyboardButton(
                text=f"{PLAN_NAMES[plan]} - {amount:,} so'm".replace(",", " "),
                callback_data=f"plan_{plan}",
            )
        )
    kb.row(InlineKeyboardButton(text=f"{f('back')} Orqaga", callback_data="vip_info"))
    return kb.as_markup()


def payment_method_keyboard(plan: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('card')} Hazna", callback_data=f"pay_hazna_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('card')} Payme", callback_data=f"pay_payme_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('card')} Click", callback_data=f"pay_click_{plan}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Orqaga", callback_data="vip_buy"))
    return kb.as_markup()


def payment_confirm_keyboard(pay_url: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if pay_url:
        kb.row(InlineKeyboardButton(text="🚀 To'lov qilish", url=pay_url))
    kb.row(InlineKeyboardButton(text=f"{f('check')} Tekshirish", callback_data="check_payment"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Orqaga", callback_data="vip_buy"))
    return kb.as_markup()


def admin_payment_notify_keyboard(payment_id: str, user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"apay_ok_{payment_id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"apay_no_{payment_id}"),
    )
    return kb.as_markup()


# ---------------- Asosiy menyu ----------------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('search')} Kod kiritish", callback_data="enter_code"))
    kb.row(InlineKeyboardButton(text=f"{f('support')} Support", callback_data="support"))
    return kb.as_markup()


def support_keyboard(support_username: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    uname = support_username.lstrip("@")
    kb.row(InlineKeyboardButton(text=f"{f('support')} Yozish", url=f"https://t.me/{uname}"))
    kb.row(InlineKeyboardButton(text=f"{f('back')} Menu", callback_data="back_to_start"))
    return kb.as_markup()


# ---------------- Kino ----------------
def movie_keyboard(code: str, channels_link: str | None = None) -> InlineKeyboardMarkup:
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


def back_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('back')} Menu", callback_data="back_to_start"))
    return kb.as_markup()


# ---------------- Admin panel ----------------
def admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📢 Kanal qo'shish", callback_data="adm_add_channel"))
    kb.row(InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="adm_del_channel"))
    kb.row(InlineKeyboardButton(text="🎬 Kino/kod qo'shish", callback_data="adm_add_movie"))
    kb.row(InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="adm_del_movie"))
    kb.row(InlineKeyboardButton(text="💎 Narxlarni sozlash", callback_data="adm_prices"))
    kb.row(InlineKeyboardButton(text="💳 Karta ma'lumotini sozlash", callback_data="adm_card"))
    kb.row(InlineKeyboardButton(text="⏳ Kutayotgan to'lovlar", callback_data="adm_pending_payments"))
    kb.row(InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats"))
    kb.row(InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="adm_broadcast"))
    return kb.as_markup()


def admin_back_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"{f('back')} Admin panel", callback_data="adm_back"))
    return kb.as_markup()


def admin_prices_keyboard(prices: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for plan in ("1m", "3m", "1y"):
        amount = prices.get(plan, 0)
        kb.row(
            InlineKeyboardButton(
                text=f"{PLAN_NAMES[plan]}: {amount:,} so'm".replace(",", " "),
                callback_data=f"adm_setprice_{plan}",
            )
        )
    kb.row(InlineKeyboardButton(text=f"{f('back')} Admin panel", callback_data="adm_back"))
    return kb.as_markup()


def confirm_delete_channel_keyboard(channels) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.row(
            InlineKeyboardButton(
                text=f"🗑 {ch.get('title', ch['_id'])}", callback_data=f"adm_delch_{ch['_id']}"
            )
        )
    kb.row(InlineKeyboardButton(text=f"{f('back')} Admin panel", callback_data="adm_back"))
    return kb.as_markup()
