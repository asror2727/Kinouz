# -----------------------------------------------------------------------
# MUHIM: Telegram Bot API custom (premium) emoji'ni FAQAT xabar matnida
# HTML <tg-emoji emoji-id="..."> tegi orqali ko'rsatishga ruxsat beradi.
# InlineKeyboardButton (tugma) matnida custom emoji ISHLAMAYDI - bu
# Telegramning o'z cheklovi, bot buni chetlab o'ta olmaydi.
#
# Shu sabab: tugmalarda oddiy (fallback) emoji, oddiy matnlarda esa
# sizning premium emoji ID'laringiz ishlatiladi.
#
# Premium emoji'ni ko'rish uchun O'QUVCHIDA (xabar oluvchida) Telegram
# Premium obunasi bo'lishi kerak - bo'lmasa fallback emoji ko'rinadi.
# -----------------------------------------------------------------------

EMOJI = {
    "person": ("\U0001F464", "5271829423899845716"),      # 👤
    "wave": ("\U0001F44B", "5271765841203995324"),        # 👋
    "money": ("\U0001F4B0", "5271857409906745357"),       # 💰
    "support": ("\u260E\ufe0f", "5271586238556574482"),   # ☎️
    "id": ("\U0001F194", "5271628651358622439"),          # 🆔
    "back": ("\u2b05\ufe0f", "5271512047291507931"),      # ⬅️
    "click": ("\U0001F446", "5271857014769754460"),       # 👆
    "search": ("\U0001F50D", "5272013068111485452"),      # 🔍
    "dollar": ("\U0001F4B5", "5271739719212901906"),      # 💵
    "check": ("\u2705", "5271507881173227410"),           # ✅
    "card": ("\U0001F4B3", "5271907450570709756"),        # 💳
    "warning": ("\u26a0\ufe0f", "5271535227230028862"),   # ⚠️
    "dot": ("\u25aa\ufe0f", "5274239519028191789"),       # ▪️
}


def e(name: str) -> str:
    """Matn ichida ishlatish uchun premium custom emoji HTML tegi.
    Albatta parse_mode='HTML' bilan birga ishlatilishi kerak."""
    fallback, cid = EMOJI[name]
    return f'<tg-emoji emoji-id="{cid}">{fallback}</tg-emoji>'


def f(name: str) -> str:
    """Tugmalar uchun oddiy fallback emoji (custom emoji tugmada ishlamaydi)."""
    return EMOJI[name][0]
