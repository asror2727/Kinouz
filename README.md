# 🎬 Kino Bot (bitta faylda)

Endi butun bot **faqat `main.py`** ichida. Fayl soni kamaydi — import xatosi
(`ModuleNotFoundError: No module named 'handlers'`) endi umuman bo'lishi
mumkin emas, chunki alohida papka/fayl yo'q.

## Fayllar (jami 6 ta)
```
main.py           - butun bot kodi
requirements.txt  - kutubxonalar
runtime.txt        - Python versiyasi (build xatosining oldini oladi)
.env.example       - sozlamalar namunasi
.gitignore
README.md
```

## ⚠️ Oxirgi xato haqida: TelegramConflictError

Bu xato **fayl sonига yoki kodga aloqasi yo'q**. U shuni bildiradi:
**bir xil BOT_TOKEN bilan bir vaqtning o'zida ikkita bot ishlab turibdi.**

Sabablari, tekshiring:
1. **Botni boshqa joyda ham ishga tushirmagansizmi?** (kompyuteringizda,
   boshqa Render service'da, boshqa hostingda) — bir vaqtning o'zida faqat
   BITTA joyda ishlashi mumkin.
2. **Render'da eski deploy hali "ishlab turibdimi"?** Dashboard → Events'da
   faqat bitta instance "Live" holatda bo'lishi kerak. Agar avvalgi deploy
   muzlab qolgan bo'lsa — "Manual Deploy" → "Clear build cache & deploy"
   ni bosing, bu eski jarayonni to'liq to'xtatib, yangisini ishga tushiradi.
3. **@BotFather orqali boshqa odam ham shu tokenni ishlatayotgan emasmi?**
   Agar tokenni kimgadir yuborgan bo'lsangiz yoki GitHub'da ochiq qoldirgan
   bo'lsangiz — tokenni **almashtiring**: @BotFather → `/mybots` → botingiz
   → "API Token" → "Revoke current token", so'ng yangisini Render
   Environment'ga qo'ying.

Kodning o'zida bu xatoni oldini olish uchun `bot.delete_webhook(drop_pending_updates=True)`
allaqachon bor — bu webhook rejimi bilan polling rejimi to'qnashmasligini
ta'minlaydi, lekin ikkita polling instance bir vaqtda ishlasa baribir shu
xato chiqadi (Telegram tomonidan cheklov).

## O'rnatish (qisqacha)

1. GitHub repo'ga shu 6 ta faylni yuklang (eski `handlers/` papkasi va undagi
   fayllarni **o'chirib tashlang** — endi kerak emas).
2. Render → Environment bo'limiga o'ting, quyidagilarni qo'shing:
   - `BOT_TOKEN`
   - `MONGO_URI`
   - `DB_NAME` = kino_bot
   - `ADMIN_IDS` (sizning Telegram user_id, @userinfobot orqali bilib oling)
   - `SUPPORT_USERNAME`, `DEV_USERNAME`, `CARD_NUMBER`, `CARD_OWNER`
3. "Manual Deploy" → "Clear build cache & deploy" bosing (bu eski jarayonni
   ham to'xtatadi, conflict xatosi chiqmasligi uchun muhim).
4. Loglarda xato bo'lmasa, botga `/start` yozib tekshiring.

## Botni sozlash

- `/admin` — admin panel (faqat ADMIN_IDS'dagi ID'lar uchun ochiladi)
- "📢 Kanal qo'shish" — botni kanalga admin qilib qo'shing, so'ng shu yerdan
  kanaldan xabar forward qiling
- "🎬 Kino/kod qo'shish" — kod kiriting (masalan `5`), keyin video/fayl yuboring
- "💎 Narxlarni sozlash" — 1/3/12 oylik narxlarni belgilang
- To'lov kelganda sizga (yoki PAYMENTS_CHAT_ID'ga) xabar keladi,
  "✅ Tasdiqlash" tugmasi bilan avtomatik VIP beriladi
