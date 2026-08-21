# 🎬 Kino Bot

Kanalga majburiy obuna, Premium/VIP obuna (to'lov bilan), kod bo'yicha kino
qidirish va admin panelli Telegram bot.

## Nima ishlaydi

- `/start` — kanallarga obuna tekshiradi, obuna bo'lmasa kanallar ro'yxatini
  va "✅ Tekshirish" tugmasini chiqaradi. Bo'lgan bo'lsa yoki foydalanuvchi
  VIP bo'lsa — asosiy menyuga o'tadi.
- 💎 Premium: tarif tanlash (1 oylik/3 oylik/1 yillik, narxlar admin panelda
  o'zgartiriladi) → to'lov usuli (Hazna/Payme/Click) → karta orqali qo'lda
  to'lov → admin tasdiqlaydi (tugma yoki `/confirm <id>`) → foydalanuvchi
  avtomatik VIP bo'ladi va kanallarsiz botdan foydalanadi.
- Kod kiritish: foydalanuvchi raqam yuborsa (masalan `5`), o'sha kodga
  admin panelda biriktirilgan video/fayl chiqadi. "Ko'proq kino",
  "Saqlangan kino", "Izoh yozish", "Saqlash" tugmalari bilan.
- `/rand`, `/top`, `/last`, `/help`, `/vip`, `/dev`, `/liv <kod>` buyruqlari.
- Admin panel `/admin`: kanal qo'shish/o'chirish, kino/kod qo'shish/o'chirish,
  narxlarni sozlash, kutayotgan to'lovlarni ko'rish/tasdiqlash, statistika,
  hammaga xabar yuborish (broadcast).

## ⚠️ Premium custom emoji haqida muhim eslatma

Siz bergan custom emoji ID'larini **tugma matnida** ishlatib bo'lmaydi —
bu Telegram Bot API'ning o'z cheklovi (inline tugmalar faqat oddiy matn
qabul qiladi). Shu sabab:
- Tugmalarda oddiy emoji ishlatilgan.
- Sizning premium emoji ID'laringiz xabar matnlarida (`/start`, obuna,
  ogohlantirish kabi joylarda) `<tg-emoji>` HTML tegi orqali ishlatilgan
  (`emojis.py` faylida).
- Bu emojilarni faqat Telegram **Premium** obunasi bor foydalanuvchilar
  chiroyli holda ko'radi, qolganlar uchun oddiy fallback emoji ko'rinadi.

## 1. Lokal ishga tushirish

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # so'ng .env faylini to'ldiring
python main.py
```

`.env` faylida albatta to'ldiring:
- `BOT_TOKEN` — @BotFather'dan
- `MONGO_URI` — MongoDB manzili (pastga qarang)
- `ADMIN_IDS` — sizning Telegram user_id'ingiz (masalan @userinfobot orqali
  bilib olasiz)

## 2. MongoDB — shart

Ha, MongoDB kerak — kanallar, kinolar, foydalanuvchilar, to'lovlar shu yerda
saqlanadi. Eng oson yo'l — **MongoDB Atlas** (bepul M0 tier yetadi):

1. https://www.mongodb.com/atlas → ro'yxatdan o'ting → bepul cluster yarating.
2. "Database Access" — foydalanuvchi (login/parol) yarating.
3. "Network Access" — `0.0.0.0/0` qo'shing (Render har xil IP'dan ulanadi).
4. "Connect" → "Drivers" dan connection string'ni oling, `.env` dagi
   `MONGO_URI` ga qo'ying.

## 3. GitHub'ga joylash

```bash
git init
git add .
git commit -m "Kino bot"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

`.env` faylini **hech qachon** GitHub'ga qo'ymang (`.gitignore` ga qo'shilgan
bo'lishi kerak — pastda tayyor variant bor).

## 4. Render'ga deploy

1. https://render.com → "New +" → "Background Worker" (Web Service EMAS,
   chunki bu bot doim ishlab turishi kerak, tashqi HTTP so'rov kutmaydi).
2. GitHub repo'ni tanlang.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. "Environment" bo'limida `.env.example` dagi barcha o'zgaruvchilarni
   qo'shing (`BOT_TOKEN`, `MONGO_URI`, `ADMIN_IDS`, va h.k.).
6. Deploy qiling — loglarda "Start polling" ko'rinsa, bot ishlayapti.

(`render.yaml` fayli tayyor — agar Render "Blueprint" orqali deploy qilsangiz,
bu faylni avtomatik o'qiydi, faqat "sync: false" qiymatlarni qo'lda kiritasiz.)

## 5. Botni sozlash (birinchi marta)

1. Botni yarating (@BotFather), token oling.
2. O'zingizning Telegram user_id'ingizni bilib oling (@userinfobot) va
   `ADMIN_IDS` ga qo'ying.
3. Botni kerakli kanal(lar)ga **admin** qilib qo'shing.
4. Botga `/admin` yozing → "📢 Kanal qo'shish" → kanaldan xabar forward
   qiling yoki `@kanal_username` yuboring.
5. "🎬 Kino/kod qo'shish" → kod kiriting (masalan `5`) → video/faylni
   yuboring.
6. "💎 Narxlarni sozlash" orqali 1/3/12 oylik narxlarni belgilang.
7. Foydalanuvchi to'lov qilganda admin guruhiga/sizga xabar keladi —
   "✅ Tasdiqlash" tugmasini bosasiz, foydalanuvchiga avtomatik VIP beriladi.

## 6. Keyingi qadam: avtomatik to'lov (Payme/Click)

Hozir to'lovlar **qo'lda tasdiqlash** rejimida ishlaydi (siz aytganingizdek —
"agar qila olmasang man tashiman amalab kor"). Payme/Click/Hazna uchun real
merchant ID va kalitlaringizni bersangiz, `handlers/user.py` dagi
`cb_choose_method` funksiyasidagi `TODO` joyiga checkout havolasi yaratish
va webhook orqali avtomatik tasdiqlash qo'shiladi — struktura shunga tayyor
turibdi (`payments_col`, `status: pending/confirmed`).
