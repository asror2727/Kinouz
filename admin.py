from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from config import ADMIN_IDS
from keyboards import (
    admin_back_keyboard,
    admin_panel_keyboard,
    admin_prices_keyboard,
    confirm_delete_channel_keyboard,
)
from states import AdminStates

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 <b>Admin panel</b>", reply_markup=admin_panel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "adm_back")
async def cb_adm_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("🔧 <b>Admin panel</b>", reply_markup=admin_panel_keyboard(), parse_mode="HTML")
    await callback.answer()


# ---------------- Kanal qo'shish ----------------
@router.callback_query(F.data == "adm_add_channel")
async def cb_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_channel_forward)
    await callback.message.edit_text(
        "📢 Bot qo'shmoqchi bo'lgan kanalingizga <b>admin</b> qilib qo'shing.\n\n"
        "Keyin o'sha kanaldan istalgan xabarni shu yerga forward qiling "
        "(yoki kanal @username'ini yuboring, masalan: @mychannel).",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.waiting_channel_forward)
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
            link = await bot.create_chat_invite_link(chat.id)
            link = link.invite_link
        await db.add_channel(chat.id, chat.title, chat.username, link)
        await state.clear()
        await message.answer(f"✅ Kanal qo'shildi: {chat.title}", reply_markup=admin_back_keyboard())
    except Exception as ex:
        await message.answer(f"❌ Xatolik: {ex}\nQaytadan urinib ko'ring.")


# ---------------- Kanal o'chirish ----------------
@router.callback_query(F.data == "adm_del_channel")
async def cb_del_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    channels = await db.get_channels()
    if not channels:
        await callback.answer("Kanallar mavjud emas.", show_alert=True)
        return
    await callback.message.edit_text(
        "🗑 O'chirmoqchi bo'lgan kanalni tanlang:",
        reply_markup=confirm_delete_channel_keyboard(channels),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_delch_"))
async def cb_confirm_del_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    chat_id = callback.data.split("_", 2)[2]
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass
    await db.remove_channel(chat_id)
    await callback.answer("✅ Kanal o'chirildi.", show_alert=True)
    await cb_del_channel(callback)


# ---------------- Kino/kod qo'shish ----------------
@router.callback_query(F.data == "adm_add_movie")
async def cb_add_movie(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_movie_code)
    await callback.message.edit_text(
        "🔢 Kino uchun kod (raqam yoki nom) kiriting, masalan: 5",
        reply_markup=admin_back_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_movie_code)
async def process_movie_code(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip()
    await state.update_data(code=code)
    await state.set_state(AdminStates.waiting_movie_content)
    await message.answer(f"🎬 Endi #{code} kodi uchun kino faylini (video yoki hujjat) yuboring.")


@router.message(AdminStates.waiting_movie_content, F.video | F.document)
async def process_movie_content(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    code = data["code"]

    if message.video:
        file_id = message.video.file_id
        content_type = "video"
    else:
        file_id = message.document.file_id
        content_type = "document"

    title = message.caption or ""
    await db.add_movie(code, file_id, content_type, title=title)
    await state.clear()
    await message.answer(f"✅ #{code} kodli kino bazaga qo'shildi!", reply_markup=admin_back_keyboard())


@router.message(AdminStates.waiting_movie_content)
async def process_movie_content_wrong(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("❌ Iltimos video yoki fayl yuboring.")


# ---------------- Kino o'chirish ----------------
@router.callback_query(F.data == "adm_del_movie")
async def cb_del_movie(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_delete_code)
    await callback.message.edit_text("🗑 O'chirish uchun kino kodini yuboring:", reply_markup=admin_back_keyboard())
    await callback.answer()


@router.message(AdminStates.waiting_delete_code)
async def process_del_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip()
    await db.delete_movie(code)
    await state.clear()
    await message.answer(f"✅ #{code} o'chirildi.", reply_markup=admin_back_keyboard())


# ---------------- Narxlar ----------------
@router.callback_query(F.data == "adm_prices")
async def cb_prices(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    prices = await db.get_prices()
    await callback.message.edit_text(
        "💎 Narxni o'zgartirish uchun tarifni tanlang:", reply_markup=admin_prices_keyboard(prices)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_setprice_"))
async def cb_setprice(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    plan = callback.data.split("_", 2)[2]
    await state.set_state(AdminStates.waiting_price_amount)
    await state.update_data(plan=plan)
    await callback.message.edit_text(
        f"✏️ {plan} uchun yangi narxni so'mda kiriting (masalan: 15000):",
        reply_markup=admin_back_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_price_amount)
async def process_setprice(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam kiriting.")
        return
    data = await state.get_data()
    plan = data["plan"]
    amount = int(message.text.strip())
    await db.set_price(plan, amount)
    await state.clear()
    await message.answer(f"✅ {plan} narxi {amount:,} so'm qilib o'zgartirildi.".replace(",", " "), reply_markup=admin_back_keyboard())


# ---------------- Karta ma'lumoti ----------------
@router.callback_query(F.data == "adm_card")
async def cb_card(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_card_number)
    await callback.message.edit_text(
        "💳 Yangi karta ma'lumotini yuboring: <code>8600 1234 5678 9012 Ism Familiya</code>",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.waiting_card_number)
async def process_card(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    # Eslatma: bu qiymatni doimiy saqlash uchun DB'ga yozish tavsiya etiladi.
    # Hozircha .env dagi CARD_NUMBER / CARD_OWNER'ni qo'lda yangilang, chunki
    # ular runtime konfiguratsiya sifatida config.py orqali o'qiladi.
    await state.clear()
    await message.answer(
        "ℹ️ Karta ma'lumotini doimiy o'zgartirish uchun Render'dagi CARD_NUMBER va "
        "CARD_OWNER environment o'zgaruvchilarini yangilang (Settings → Environment).",
        reply_markup=admin_back_keyboard(),
    )


# ---------------- Kutayotgan to'lovlar ----------------
@router.callback_query(F.data == "adm_pending_payments")
async def cb_pending_payments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    payments = await db.payments_col.find({"status": "pending"}).to_list(length=20)
    if not payments:
        await callback.answer("Kutayotgan to'lovlar yo'q.", show_alert=True)
        return
    lines = [
        f"🆔 {p['_id']} | user: {p['user_id']} | {p['plan']} | {p['amount']:,} so'm | {p['method']}".replace(",", " ")
        for p in payments
    ]
    await callback.message.answer(
        "⏳ <b>Kutayotgan to'lovlar:</b>\n\n" + "\n".join(lines)
        + "\n\nTasdiqlash uchun: /confirm <id>\nBekor qilish uchun: /reject <id>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("confirm"))
async def cmd_confirm_payment(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /confirm <payment_id>")
        return
    payment = await db.get_payment(parts[1].strip())
    if not payment:
        await message.answer("❌ Bunday to'lov topilmadi.")
        return
    await db.confirm_payment(payment["_id"])
    days = db.PLAN_DAYS.get(payment["plan"], 30)
    until = await db.set_vip(payment["user_id"], days)
    await message.answer(f"✅ Tasdiqlandi. Foydalanuvchi VIP: {until:%Y-%m-%d}")
    try:
        await bot.send_message(
            payment["user_id"],
            "✅ To'lovingiz tasdiqlandi! Premium faollashtirildi. /start ni bosing.",
        )
    except Exception:
        pass


@router.message(Command("reject"))
async def cmd_reject_payment(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /reject <payment_id>")
        return
    payment = await db.get_payment(parts[1].strip())
    if not payment:
        await message.answer("❌ Bunday to'lov topilmadi.")
        return
    await db.reject_payment(payment["_id"])
    await message.answer("❌ To'lov bekor qilindi.")


# ---------------- To'lov tugmalari orqali tasdiqlash ----------------
@router.callback_query(F.data.startswith("apay_ok_"))
async def cb_apay_ok(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    payment_id = callback.data.split("_", 2)[2]
    payment = await db.get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await db.confirm_payment(payment["_id"])
    days = db.PLAN_DAYS.get(payment["plan"], 30)
    until = await db.set_vip(payment["user_id"], days)
    await callback.message.edit_text(callback.message.text + f"\n\n✅ Tasdiqlandi ({until:%Y-%m-%d} gacha)")
    await callback.answer("✅ Tasdiqlandi")
    try:
        await bot.send_message(
            payment["user_id"],
            "✅ To'lovingiz tasdiqlandi! Premium faollashtirildi. /start ni bosing.",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("apay_no_"))
async def cb_apay_no(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    payment_id = callback.data.split("_", 2)[2]
    payment = await db.get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await db.reject_payment(payment["_id"])
    await callback.message.edit_text(callback.message.text + "\n\n❌ Bekor qilindi")
    await callback.answer("❌ Bekor qilindi")
    try:
        await bot.send_message(payment["user_id"], "❌ To'lovingiz tasdiqlanmadi. Support bilan bog'laning.")
    except Exception:
        pass


# ---------------- Statistika ----------------
@router.callback_query(F.data == "adm_stats")
async def cb_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    users = await db.users_count()
    movies = await db.movies_count()
    pending = await db.payments_col.count_documents({"status": "pending"})
    confirmed = await db.payments_col.count_documents({"status": "confirmed"})
    await callback.message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"🎬 Kinolar: {movies}\n"
        f"⏳ Kutayotgan to'lovlar: {pending}\n"
        f"✅ Tasdiqlangan to'lovlar: {confirmed}",
        parse_mode="HTML",
    )
    await callback.answer()


# ---------------- Xabar yuborish (broadcast) ----------------
@router.callback_query(F.data == "adm_broadcast")
async def cb_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📣 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:",
        reply_markup=admin_back_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, bot: Bot, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await db.all_user_ids()
    sent, failed = 0, 0
    status_msg = await message.answer(f"📣 Yuborilmoqda... 0/{len(user_ids)}")
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ Yuborildi: {sent} | ❌ Xato: {failed}")
