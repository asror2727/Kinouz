# Kino Bot

Node.js + MongoDB Telegram kino bot.

## Ishga tushirish

1. Node.js 18+ o'rnating.
2. `npm install`
3. `.env.example` ni `.env` qilib nusxalang.
4. `BOT_TOKEN`, `MONGODB_URI`, `ADMIN_IDS` ni to'ldiring.
5. `npm start`

## Admin

`ADMIN_IDS` ga Telegram numeric ID yoziladi. Bir nechta admin:
`ADMIN_IDS=123,456,789`

Bot ichida:
- `/admin` — admin panel
- `/addmovie` — kino qo'shish
- `/channels` — majburiy kanallar
- `/prices` — Premium narxlari
- `/emoji` — custom emoji ID lar
- `/stats` — statistika

## Kino qo'shish

`/addmovie`
Bot:
1. Kodni so'raydi
2. Kino nomini so'raydi
3. Video/faylni so'raydi
4. Tavsifni so'raydi

## Muhim

Render filesystem doimiy saqlash uchun mos emas. Kino fayllarini server diskiga emas, Telegram `file_id` orqali saqlaymiz. Shu sababli bot qayta deploy bo'lganda kino faylini qayta yuklash shart emas.

MongoDB foydalanuvchilar, kinolar, kanallar, premium va sozlamalarni saqlaydi.

Auto Payme/Click/Hazna uchun sizdagi mavjud API kodini yuboring. Bu starterda to'lov adapterlari uchun joy tayyorlangan, lekin haqiqiy merchant/API ma'lumotisiz avtomatik to'lovni "ishlaydi" deb uydirib bo'lmaydi.
