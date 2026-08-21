from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from config import ADMIN_IDS, CARD_NUMBER, CARD_OWNER, DEV_USERNAME, PAYMENTS_CHAT_ID, SUPPORT_USERNAME
from emojis import e
from keyboards import (
    admin_payment_notify_keyboard,
    back_menu_keyboard,
    main_menu_keyboard,
    movie_keyboard,
    payment_confirm_keyboard,
    payment_method_keyboard,
    subscribe_keyboard,
    support_keyboard,
    vip_info_keyboard,
    vip_plans_keyboard,
)
from states import UserStates
from utils import check_subscription

router = Router()

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


async def send_main_menu(target_message: Message):
    await target_message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


async def gate_or_menu(bot: Bot, chat_id: int, user_id: int, message: Message):
    """VIP bo'lsa yoki barcha kanallarga obuna bo'lsa - menu, aks holda obuna talab qilinadi."""
    if await db.is_vip(user_id):
        await send_main_menu(message)
        return
    ok, missing = await check_subscription(bot, user_id)
    if ok:
        await send_main_menu(message)
    else:
        await message.answer(
            f"{e('warning')} Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscribe_keyboard(missing),
            parse_mode="HTML",
        )


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    await db.add_user(message.from_user.id, message.from_user.username)
    await gate_or_menu(bot, message.chat.id, message.from_user.id, message)


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, bot: Bot):
    ok, missing = await check_subscription(bot, callback.from_user.id)
    if ok:
        await callback.message.delete()
        await send_main_menu(callback.message)
        await callback.answer("Xush kelibsiz! ✅")
    else:
        await callback.answer(
            "❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True
        )


@router.callback_query(F.data == "back_to_start")
async def cb_back_to_start(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await gate_or_menu(bot, callback.message.chat.id, callback.from_user.id, callback.message)
    await callback.answer()


# ---------------- VIP / Premium ----------------
@router.message(Command("vip"))
async def cmd_vip(message: Message):
    await message.answer(VIP_TEXT, reply_markup=vip_info_keyboard())


@router.callback_query(F.data == "vip_info")
async def cb_vip_info(callback: CallbackQuery):
    await callback.message.edit_text(VIP_TEXT, reply_markup=vip_info_keyboard())
    await callback.answer()


@router.callback_query(F.data == "vip_buy")
async def cb_vip_buy(callback: CallbackQuery):
    prices = await db.get_prices()
    await callback.message.edit_text(
        "➡️ Kerakli ta'rifni tanlang:", reply_markup=vip_plans_keyboard(prices)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan_"))
async def cb_choose_plan(callback: CallbackQuery):
    plan = callback.data.split("_", 1)[1]
    await callback.message.edit_text(
        "💳 To'lov usulini tanlang:", reply_markup=payment_method_keyboard(plan)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def cb_choose_method(callback: CallbackQuery, bot: Bot):
    _, method, plan = callback.data.split("_")
    prices = await db.get_prices()
    amount = prices.get(plan, 0)

    payment_id = await db.create_payment(callback.from_user.id, plan, amount, method)

    # TODO: Payme/Click uchun avtomatik checkout havolasi shu yerga qo'shiladi
    # (merchant ID va kalitlar tayyor bo'lgach). Hozircha karta orqali qo'lda
    # to'lov qilinadi va admin /confirm buyrug'i yoki tugma orqali tasdiqlaydi.
    pay_url = None

    text = (
        f"🚀 {amount:,} so'm to'lov qilish uchun quyidagi ma'lumot orqali to'lang:\n\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Egasi: {CARD_OWNER}\n\n"
        "To'lovdan so'ng ✅ Tekshirish tugmasini bosing."
    ).replace(",", " ")

    await callback.message.edit_text(
        text, reply_markup=payment_confirm_keyboard(pay_url), parse_mode="HTML"
    )
    await callback.answer()

    # Adminga (yoki to'lovlar guruhiga) bildirishnoma
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
            await bot.send_message(
                notify_chat,
                info,
                reply_markup=admin_payment_notify_keyboard(str(payment_id), u.id),
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.callback_query(F.data == "check_payment")
async def cb_check_payment(callback: CallbackQuery):
    payment = await db.get_pending_payment(callback.from_user.id)
    if not payment:
        await callback.answer("Sizda tasdiqlanmagan to'lov topilmadi.", show_alert=True)
        return
    if payment["status"] == "confirmed":
        await callback.message.delete()
        await send_main_menu(callback.message)
        await callback.answer("✅ To'lovingiz tasdiqlandi! Premium faollashtirildi.", show_alert=True)
    else:
        await callback.answer(
            "⏳ To'lovingiz hali admin tomonidan tasdiqlanmagan. Iltimos kuting.", show_alert=True
        )


# ---------------- Support / Dev ----------------
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        f"{e('support')} Savol va takliflar uchun murojaat qiling:",
        reply_markup=support_keyboard(SUPPORT_USERNAME),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery):
    await callback.message.edit_text(
        f"{e('support')} Savol va takliflar uchun murojaat qiling:",
        reply_markup=support_keyboard(SUPPORT_USERNAME),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("dev"))
async def cmd_dev(message: Message):
    await message.answer(f"🧑\u200d💻 Dasturchi: {DEV_USERNAME}")


# ---------------- Kod kiritish / kino qidirish ----------------
@router.callback_query(F.data == "enter_code")
async def cb_enter_code(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_code)
    await callback.message.answer("5 kabi kino kodini yuboring:")
    await callback.answer()


async def send_movie_by_code(message: Message, code: str):
    movie = await db.get_movie(code)
    if not movie:
        await message.answer("❌ Bunday kodli kino topilmadi. Qaytadan urinib ko'ring.")
        return

    if movie.get("is_premium") and not await db.is_vip(message.from_user.id):
        await message.answer(
            "💎 Bu kino faqat PREMIUM foydalanuvchilar uchun.", reply_markup=vip_info_keyboard()
        )
        return

    await db.inc_views(code)
    caption = movie.get("title") or f"🎬 Kino #{code}"
    kb = movie_keyboard(code)

    if movie["content_type"] == "video":
        await message.answer_video(movie["file_id"], caption=caption, reply_markup=kb)
    else:
        await message.answer_document(movie["file_id"], caption=caption, reply_markup=kb)


@router.message(UserStates.waiting_code)
async def process_code(message: Message, state: FSMContext):
    await state.clear()
    await send_movie_by_code(message, message.text.strip())


@router.message(F.text.regexp(r"^\d+$"))
async def process_direct_code(message: Message):
    """Foydalanuvchi to'g'ridan-to'g'ri raqam yuborsa ham kino chiqadi."""
    await send_movie_by_code(message, message.text.strip())


# ---------------- /rand /top /last ----------------
@router.message(Command("rand"))
async def cmd_rand(message: Message):
    movie = await db.get_random_movie()
    if not movie:
        await message.answer("Hozircha bazada kino yo'q.")
        return
    await send_movie_by_code(message, movie["_id"])


@router.message(Command("top"))
async def cmd_top(message: Message):
    movies = await db.get_top_movies()
    if not movies:
        await message.answer("Hozircha bazada kino yo'q.")
        return
    text = "🏆 <b>Top kinolar:</b>\n\n" + "\n".join(
        f"{i + 1}. #{m['_id']} - {m.get('title') or 'nomsiz'} ({m.get('views', 0)} ko'rishlar)"
        for i, m in enumerate(movies)
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("last"))
async def cmd_last(message: Message):
    movies = await db.get_last_movies()
    if not movies:
        await message.answer("Hozircha bazada kino yo'q.")
        return
    text = "📽️ <b>Oxirgi yuklangan kinolar:</b>\n\n" + "\n".join(
        f"▪️ #{m['_id']} - {m.get('title') or 'nomsiz'}" for m in movies
    )
    await message.answer(text, parse_mode="HTML")


# ---------------- Ko'proq kino / Saqlangan kino ----------------
@router.callback_query(F.data == "more_movies")
async def cb_more_movies(callback: CallbackQuery):
    channels = await db.get_channels()
    if not channels:
        await callback.answer("Hozircha kanallar qo'shilmagan.", show_alert=True)
        return
    text = "📢 Ko'proq kinolar uchun kanallarimizga o'ting:\n\n" + "\n".join(
        f"➕ {ch.get('title')}" for ch in channels
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "saved_movies")
async def cb_saved_movies(callback: CallbackQuery):
    saved = await db.get_saved_movies(callback.from_user.id)
    if not saved:
        await callback.answer("Sizda saqlangan kino yo'q.", show_alert=True)
        return
    text = "💾 <b>Saqlangan kinolaringiz:</b>\n\n" + "\n".join(
        f"▪️ #{s['code']}" for s in saved
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("save_"))
async def cb_save_movie(callback: CallbackQuery):
    code = callback.data.split("_", 1)[1]
    await db.save_movie(callback.from_user.id, code)
    await callback.answer("💾 Saqlandi!", show_alert=True)


# ---------------- Izohlar ----------------
@router.callback_query(F.data.startswith("comment_"))
async def cb_comment_start(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_", 1)[1]
    await state.set_state(UserStates.waiting_comment)
    await state.update_data(code=code)
    await callback.message.answer(f"💬 #{code} kinosi uchun izohingizni yozing:")
    await callback.answer()


@router.message(UserStates.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data.get("code")
    await state.clear()
    await db.add_comment(code, message.from_user.id, message.from_user.username, message.text)
    count = await db.comments_count(code)
    await message.answer(f"✅ Izohingiz uchun rahmat! Bu kino uchun jami {count} ta izoh bor.")


@router.message(Command("liv"))
async def cmd_liv(message: Message):
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.answer("Foydalanish: /liv <kino_kodi>")
        return
    code = text[1].strip()
    comments = await db.get_comments(code)
    if not comments:
        await message.answer("Bu kino uchun hali izohlar yo'q.")
        return
    lines = [f"👤 {c.get('username') or c['user_id']}: {c['text']}" for c in comments]
    await message.answer("💬 <b>Izohlar:</b>\n\n" + "\n".join(lines), parse_mode="HTML")
