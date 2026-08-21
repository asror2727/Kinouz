const TelegramBot = require("node-telegram-bot-api");
const express = require("express");
const { token, port, admins, support } = require("./config");
const {
  kb, getUser, gate, welcome, searchMovie, randomMovie, topMovies,
  lastMovies, savedMovies, comments
} = require("./handlers/user");
const {
  isAdmin, adminPanel, addMovie, addChannel, setPrice,
  showPrices, emojiPanel, stats, handleAdminStep
} = require("./handlers/admin");
const { createPayment, verifyPayment } = require("./services/payments");
const { readData, writeData } = require("./services/db");

if (!token) throw new Error("BOT_TOKEN topilmadi");

const bot = new TelegramBot(token, { polling: true });
const app = express();

app.get("/", (_, res) => res.send("Kino bot ishlayapti ✅"));
app.get("/health", (_, res) => res.json({ ok: true }));
app.listen(port, () => console.log(`HTTP server :${port}`));

bot.onText(/^\/start$/, async msg => {
  const user = await getUser(msg);
  user.step = null; 
  user.temp = {};
  
  const data = readData();
  const idx = data.users.findIndex(u => u.telegramId === msg.from.id);
  if (idx !== -1) {
    data.users[idx] = user;
    writeData(data);
  }

  const premium = user.premiumUntil && new Date(user.premiumUntil) > new Date();
  if (!premium) {
    const ok = await isSubscribed(bot, msg.from.id);
    if (!ok) {
      const { sendSubscribe } = require("./handlers/user");
      return sendSubscribe(bot, msg.chat.id);
    }
  }
  welcome(bot, msg.chat.id);
});

bot.onText(/^\/(rand|random)$/i, async msg => {
  if (!(await gate(bot, msg))) return;
  randomMovie(bot, msg.chat.id);
});

bot.onText(/^\/top$/i, async msg => {
  if (!(await gate(bot, msg))) return;
  topMovies(bot, msg.chat.id);
});

bot.onText(/^\/last$/i, async msg => {
  if (!(await gate(bot, msg))) return;
  lastMovies(bot, msg.chat.id);
});

bot.onText(/^\/help$/i, msg => bot.sendMessage(msg.chat.id, `☎️ Support: @${support}`));
bot.onText(/^\/dev$/i, msg => bot.sendMessage(msg.chat.id, "🧑‍💻 Dasturchi: @x7fan"));
bot.onText(/^\/liv$/i, msg => bot.sendMessage(msg.chat.id, "💬 Izohlar kino ostidagi «Izoh yozish» tugmasi orqali yuboriladi."));

bot.onText(/^\/vip$/i, async msg => {
  const text =
`💎 <b>«PREMIUM» obunasi nima uchun kerak?</b>

⚠️ • Kanallarga obuna bo'lish shart emas.
🚫 • Hech qanday reklamalarsiz.
🎞 • Kerakli kinolar sifatli formatda.
💎 • Premium kinolarni ko'rish imkoniyati.

➡️ Kerakli ta'rifni tanlang:`;
  bot.sendMessage(msg.chat.id, text, { parse_mode: "HTML", reply_markup: { inline_keyboard: kb.vip } });
});

bot.onText(/^\/admin$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  adminPanel(bot, msg);
});

bot.onText(/^\/addmovie$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  const u = await getUser(msg); 
  addMovie(bot, msg, u);
});

bot.onText(/^\/addchannel$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  const u = await getUser(msg); 
  addChannel(bot, msg, u);
});

bot.onText(/^\/setprice$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  const u = await getUser(msg); 
  setPrice(bot, msg, u);
});

bot.onText(/^\/prices$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  showPrices(bot, msg.chat.id);
});

bot.onText(/^\/emoji$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  const u = await getUser(msg); 
  emojiPanel(bot, msg, u);
});

bot.onText(/^\/stats$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  stats(bot, msg.chat.id);
});

bot.onText(/^\/channels$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  const dbData = readData();
  const rows = dbData.channels || [];
  bot.sendMessage(msg.chat.id, rows.length ? rows.map(x => `${x.title} | ${x.chatId}`).join("\n") : "Kanal yo'q.");
});

bot.onText(/^\/movies$/i, async msg => {
  if (!isAdmin(msg.from.id, admins)) return;
  const dbData = readData();
  const rows = (dbData.movies || []).slice(-50).reverse();
  bot.sendMessage(msg.chat.id, rows.length ? rows.map(x => `${x.code} — ${x.title}`).join("\n") : "Kino yo'q.");
});

bot.on("callback_query", async q => {
  const chatId = q.message.chat.id;
  const userId = q.from.id;
  const data = q.data;
  await bot.answerCallbackQuery(q.id).catch(() => {});

  const dbData = readData();
  const u = dbData.users?.find(user => user.telegramId === userId) || await getUser(q);

  if (data === "check_sub") {
    const premium = u?.premiumUntil && new Date(u.premiumUntil) > new Date();
    if (premium || await isSubscribed(bot, userId)) {
      await bot.sendMessage(chatId, "✅ Obuna tasdiqlandi!\n\nKino botga xush kelibsiz 🎬");
      return welcome(bot, chatId);
    }
    return bot.sendMessage(chatId, "❌ Hali barcha kanallarga obuna bo'lmagansiz.");
  }

  if (data === "menu") return welcome(bot, chatId);
  if (data === "support") return bot.sendMessage(chatId, `☎️ Support: @${support}`);
  
  if (data === "code") {
    u.step = "movie_search";
    writeData(dbData);
    return bot.sendMessage(chatId, "🔢 Kino kodini yuboring. Masalan: 5");
  }

  if (data === "more") {
    return bot.sendMessage(chatId, "🎬 Ko'proq kinolar uchun bizning kanalimizga qo'shiling.");
  }

  if (data === "saved") return savedMovies(bot, chatId, userId);

  if (data === "vip") {
    return bot.sendMessage(chatId, "💎 Premium tarifni tanlang:", { reply_markup: { inline_keyboard: kb.vip } });
  }

  if (["buy_1","buy_3","buy_12"].includes(data)) {
    const plan = data === "buy_1" ? 1 : data === "buy_3" ? 3 : 12;
    const price = dbData.settings?.[`price_${plan}`] || ({1:10000, 3:25000, 12:75000}[plan]);
    u.temp = { plan, amount: price };
    writeData(dbData);
    return bot.sendMessage(chatId, `💳 ${plan === 12 ? "1 yillik" : plan + " oylik"} Premium — ${price.toLocaleString("ru-RU")} so'm\n\n💳 To'lov usulini tanlang:`, { reply_markup: { inline_keyboard: kb.payment } });
  }

  if (["pay_hazna","pay_payme","pay_click"].includes(data)) {
    const provider = data.replace("pay_", "");
    const plan = u.temp?.plan || 1;
    const amount = u.temp?.amount || 10000;
    const p = await createPayment(provider, userId, amount);
    const rows = [];
    if (p.paymentUrl) rows.push([{ text: "💳 To'lov qilish", url: p.paymentUrl }]);
    rows.push([{ text: "✅ Tekshirish", callback_data: `verify_${provider}_${p.externalId}` }]);
    return bot.sendMessage(chatId,
      `🚀 ${amount.toLocaleString("ru-RU")} so'm to'lov qilish uchun quyidagi tugmani bosing.\n\nTo'lovdan so me ✅ Tekshirish tugmasini bosing.`,
      { reply_markup: { inline_keyboard: rows } });
  }

  if (data.startsWith("verify_")) {
    const [, provider, ...idParts] = data.split("_");
    const externalId = idParts.join("_");
    const result = await verifyPayment(provider, externalId);
    if (!result.paid) return bot.sendMessage(chatId, "❌ To'lov topilmadi yoki hali tasdiqlanmagan.");
    
    const months = u.temp?.plan || 1;
    const base = (u.premiumUntil && new Date(u.premiumUntil) > new Date()) ? new Date(u.premiumUntil) : new Date();
    base.setMonth(base.getMonth() + months);
    u.premiumUntil = base;
    u.temp = {};
    writeData(dbData);
    return bot.sendMessage(chatId, "✅ To'lov tasdiqlandi! Premium faollashtirildi.");
  }

  if (data.startsWith("save_")) {
    const code = data.replace("save_", "");
    if (!u.savedMovies) u.savedMovies = [];
    if (!u.savedMovies.includes(code)) u.savedMovies.push(code);
    writeData(dbData);
    return bot.sendMessage(chatId, "💾 Kino saqlandi.");
  }

  if (data.startsWith("comment_")) {
    const code = data.replace("comment_", "");
    u.step = "comment";
    u.temp = { code };
    writeData(dbData);
    return bot.sendMessage(chatId, "💬 Izohingizni yozing:");
  }

  if (data.startsWith("comments_")) {
    return comments(bot, chatId, data.replace("comments_", ""));
  }
});

bot.on("message", async msg => {
  if (!msg.from || msg.text?.startsWith("/")) return;
  const u = await getUser(msg);

  if (isAdmin(msg.from.id, admins) && u.step) {
    return handleAdminStep(bot, msg, u);
  }

  if (u.step === "comment") {
    const code = u.temp?.code;
    if (msg.text?.trim()) {
      const dbData = readData();
      if (!dbData.comments) dbData.comments = [];
      dbData.comments.push({
        movieCode: code,
        userId: msg.from.id,
        username: msg.from.username || msg.from.first_name,
        text: msg.text.trim(),
        createdAt: new Date()
      });

      const movie = dbData.movies?.find(m => m.code === code);
      if (movie) movie.commentsCount = (movie.commentsCount || 0) + 1;

      u.step = null;
      u.temp = {};
      writeData(dbData);
      return bot.sendMessage(msg.chat.id, "✅ Izoh qabul qilindi.");
    }
  }

  if (u.step === "movie_search" && msg.text?.trim()) {
    u.step = null;
    const dbData = readData();
    const idx = dbData.users.findIndex(user => user.telegramId === msg.from.id);
    if (idx !== -1) {
      dbData.users[idx].step = null;
      writeData(dbData);
    }
    if (!(await gate(bot, msg))) return;
    return searchMovie(bot, msg, msg.text.trim());
  }

  if (msg.text?.trim()) {
    if (!(await gate(bot, msg))) return;
    return searchMovie(bot, msg, msg.text.trim());
  }
});

console.log("Kino bot ishga tushdi...");
