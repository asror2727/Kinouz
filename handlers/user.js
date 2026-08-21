const { User, Movie, Comment } = require("../models");
const { getChannels, isSubscribed } = require("../services/channels");
const { ce, IDS } = require("../emoji");

const kb = {
  check: [[{ text: "✅ Tekshirish", callback_data: "check_sub" }], [{ text: "💎 PREMIUM", callback_data: "vip" }]],
  main: [
    [{ text: "🔎 Kod kiritish", callback_data: "code" }, { text: "☎️ Support", callback_data: "support" }],
    [{ text: "🎬 Ko'proq kino", callback_data: "more" }, { text: "💾 Saqlangan kino", callback_data: "saved" }]
  ],
  vip: [
    [{ text: "1 oylik — 10 000 so'm", callback_data: "buy_1" }],
    [{ text: "3 oylik — 25 000 so'm", callback_data: "buy_3" }],
    [{ text: "1 yillik — 75 000 so'm", callback_data: "buy_12" }],
    [{ text: "⬅️ Menu", callback_data: "menu" }]
  ],
  payment: [
    [{ text: "💳 Hazna auto", callback_data: "pay_hazna" }],
    [{ text: "💳 Payme auto", callback_data: "pay_payme" }],
    [{ text: "💳 Click auto", callback_data: "pay_click" }],
    [{ text: "⬅️ Orqaga", callback_data: "vip" }]
  ]
};

async function getUser(msg) {
  return User.findOneAndUpdate(
    { telegramId: msg.from.id },
    {
      $set: { firstName: msg.from.first_name, username: msg.from.username || "" },
      $setOnInsert: { telegramId: msg.from.id }
    },
    { upsert: true, new: true }
  );
}

async function sendSubscribe(bot, chatId) {
  const channels = await getChannels();
  if (!channels.length) return false;

  const rows = [];
  for (const c of channels) {
    rows.push([{ text: `📢 ${c.title || c.username || "Kanal"}`, url: c.inviteLink || (c.username ? `https://t.me/${String(c.username).replace("@","")}` : "https://t.me/") }]);
  }
  rows.push(...kb.check);

  await bot.sendMessage(chatId,
    "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling.\n\nObuna bo'lgach, «Tekshirish» tugmasini bosing.",
    { reply_markup: { inline_keyboard: rows } }
  );
  return true;
}

async function gate(bot, msg) {
  const u = await getUser(msg);
  if (u.premiumUntil && u.premiumUntil > new Date()) return true;
  return !(await sendSubscribe(bot, msg.chat.id)) || await isSubscribed(bot, msg.from.id);
}

async function welcome(bot, chatId) {
  const text =
`👋 Salom!

/rand - 🔄 Random kino
/top - 🏆 Top kino
/last - 📽️ Oxirgi yuklangan
/help - ☎️ Qo'llab quvvatlash
/vip - 💎 Premium
/dev - 🧑‍💻 Dasturchi
/liv - 💬 Izoh

🍿 Kino kodi yoki nomini yuboring:`;

  await bot.sendMessage(chatId, text, { reply_markup: { inline_keyboard: kb.main } });
}

async function sendMovie(bot, chatId, movie) {
  await Movie.updateOne({ _id: movie._id }, { $inc: { views: 1 } });
  const caption = `🎬 <b>${escapeHtml(movie.title)}</b>\n\n${escapeHtml(movie.description || "")}\n\n🔢 Kod: <code>${movie.code}</code>`;
  const options = {
    caption,
    parse_mode: "HTML",
    reply_markup: {
      inline_keyboard: [
        [
          { text: "💬 Izoh yozish", callback_data: `comment_${movie.code}` },
          { text: "💾 Saqlash", callback_data: `save_${movie.code}` }
        ],
        [{ text: "💬 Izohlar", callback_data: `comments_${movie.code}` }]
      ]
    }
  };

  if (movie.fileType === "video") return bot.sendVideo(chatId, movie.fileId, options);
  if (movie.fileType === "document") return bot.sendDocument(chatId, movie.fileId, options);
  return bot.sendPhoto(chatId, movie.fileId, options);
}

function escapeHtml(s) {
  return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function searchMovie(bot, msg, code) {
  const movie = await Movie.findOne({ code: String(code).trim() });
  if (!movie) {
    return bot.sendMessage(msg.chat.id, "❌ Bunday koddagi kino topilmadi.");
  }
  return sendMovie(bot, msg.chat.id, movie);
}

async function randomMovie(bot, chatId) {
  const arr = await Movie.aggregate([{ $sample: { size: 1 } }]);
  if (!arr.length) return bot.sendMessage(chatId, "❌ Hozircha kino yo'q.");
  return sendMovie(bot, chatId, arr[0]);
}

async function topMovies(bot, chatId) {
  const movies = await Movie.find().sort({ views: -1 }).limit(10);
  if (!movies.length) return bot.sendMessage(chatId, "❌ Hozircha kino yo'q.");
  return bot.sendMessage(chatId, movies.map((m, i) => `${i+1}. ${m.title} — ${m.views} ko'rish`).join("\n"));
}

async function lastMovies(bot, chatId) {
  const movies = await Movie.find().sort({ createdAt: -1 }).limit(10);
  if (!movies.length) return bot.sendMessage(chatId, "❌ Hozircha kino yo'q.");
  return bot.sendMessage(chatId, movies.map(m => `🎬 ${m.title} — ${m.code}`).join("\n"));
}

async function savedMovies(bot, chatId, userId) {
  const u = await User.findOne({ telegramId: userId });
  if (!u?.savedMovies?.length) return bot.sendMessage(chatId, "💾 Saqlangan kinolar yo'q.");
  const movies = await Movie.find({ code: { $in: u.savedMovies } });
  if (!movies.length) return bot.sendMessage(chatId, "💾 Saqlangan kinolar yo'q.");
  return bot.sendMessage(chatId, movies.map(m => `🎬 ${m.title} — ${m.code}`).join("\n"));
}

async function comments(bot, chatId, code) {
  const rows = await Comment.find({ movieCode: code }).sort({ createdAt: -1 }).limit(30);
  if (!rows.length) return bot.sendMessage(chatId, "💬 Hozircha izoh yo'q.");
  return bot.sendMessage(chatId, rows.map(x => `👤 ${x.username || x.userId}: ${x.text}`).join("\n\n"));
}

module.exports = {
  kb, getUser, gate, welcome, searchMovie, randomMovie, topMovies, lastMovies,
  savedMovies, comments, sendMovie, IDS
};
