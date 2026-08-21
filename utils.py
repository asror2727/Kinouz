from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from database import get_channels

NOT_MEMBER_STATUSES = {"left", "kicked"}


async def check_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    """
    Foydalanuvchini barcha admin qo'shgan kanallarga obuna bo'lganini tekshiradi.
    Qaytaradi: (hammasiga_obuna_bolganmi, obuna_bolmagan_kanallar_royxati)
    """
    channels = await get_channels()
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["_id"], user_id=user_id)
            if member.status in NOT_MEMBER_STATUSES:
                not_subscribed.append(ch)
        except TelegramBadRequest:
            # Bot ushbu kanalda admin emas yoki kanal ID xato - xavfsizlik uchun
            # obuna bo'lmagan deb hisoblaymiz va adminlar buni logdan ko'radi.
            not_subscribed.append(ch)
    return len(not_subscribed) == 0, not_subscribed
