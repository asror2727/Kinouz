const { Channel, Movie, Setting, User } = require("../models");
const { ce } = require("../emoji");

function isAdmin(id, admins) { return admins.includes(Number(id)); }

async function adminPanel(bot, msg) {
  await bot.sendMessage(msg.chat.id,
`🛠 <b>ADMIN PANEL</b>

Kino:
➕ /addmovie — kino qo'shish
📋 /movies — kinolar

Kanallar:
📢 /addchannel — kanal qo'shish
🗑 /delchannel — kanal o'chirish
📋 /channels — kanallar

Premium:
💎 /prices — narxlarni ko'rish
✏️ /setprice — narx o'zgartirish

Emoji:
✨ /emoji — emoji ID sozlash

📊 /stats — statistika`,
  { parse_mode: "HTML" });
}

async function addMovie(bot, msg, user) {
  user.step = "movie_code";
  user.temp = {};
  await user.save();
  bot.sendMessage(msg.chat.id, "🔢 Kino kodini yuboring. Masalan: 123");
}

async function handleAdminStep(bot, msg, user) {
  if (user.step === "movie_code") {
    user.temp.code = msg.text.trim();
    user.step = "movie_title";
    await user.save();
    return bot.sendMessage(msg.chat.id, "🎬 Kino nomini yuboring.");
  }
  if (user.step === "movie_title") {
    user.temp.title = msg.text.trim();
    user.step = "movie_file";
    await user.save();
    return bot.sendMessage(msg.chat.id, "📤 Kino videosini yoki faylini yuboring.");
  }
  if (user.step === "movie_file") {
    let fileId, fileType;
    if (msg.video) { fileId = msg.video.file_id; fileType = "video"; }
    else if (msg.document) { fileId = msg.document.file_id; fileType = "document"; }
    else if (msg.photo?.length) { fileId = msg.photo[msg.photo.length-1].file_id; fileType = "photo"; }
    else return bot.sendMessage(msg.chat.id, "❌ Video/fayl yuboring.");

    user.temp.fileId = fileId;
    user.temp.fileType = fileType;
    user.step = "movie_description";
    await user.save();
    return bot.sendMessage(msg.chat.id, "📝 Tavsif yuboring yoki /skip yozing.");
  }
  if (user.step === "movie_description") {
    const desc = msg.text === "/skip" ? "" : (msg.text || "");
    const t = user.temp;
    await Movie.findOneAndUpdate(
      { code: t.code },
      { $set: { title: t.title, fileId: t.fileId, fileType: t.fileType, description: desc } },
      { upsert: true }
    );
    user.step = null; user.temp = {};
    await user.save();
    return bot.sendMessage(msg.chat.id, "✅ Kino saqlandi.");
  }

  if (user.step === "channel_chatid") {
    user.temp.chatId = msg.text.trim();
    user.step = "channel_username";
    await user.save();
    return bot.sendMessage(msg.chat.id, "📢 Kanal username yuboring. Masalan: @mychannel");
  }
  if (user.step === "channel_username") {
    user.temp.username = msg.text.trim();
    user.step = "channel_title";
    await user.save();
    return bot.sendMessage(msg.chat.id, "📝 Kanal nomi?");
  }
  if (user.step === "channel_title") {
    user.temp.title = msg.text.trim();
    user.step = "channel_link";
    await user.save();
    return bot.sendMessage(msg.chat.id, "🔗 Obuna qilish linkini yuboring.");
  }
  if (user.step === "channel_link") {
    const t = user.temp;
    await Channel.findOneAndUpdate(
      { chatId: t.chatId },
      { $set: { username: t.username, title: t.title, inviteLink: msg.text.trim(), enabled: true } },
      { upsert: true }
    );
    user.step = null; user.temp = {};
    await user.save();
    return bot.sendMessage(msg.chat.id, "✅ Kanal saqlandi.");
  }

  if (user.step === "price") {
    const [plan, amount] = (msg.text || "").split(/\s+/);
    if (!["1","3","12"].includes(plan) || !Number(amount)) {
      return bot.sendMessage(msg.chat.id, "Format: 1 10000\n3 25000\n12 75000");
    }
    await Setting.findOneAndUpdate({ key: `price_${plan}` }, { value: Number(amount) }, { upsert: true });
    user.step = null; await user.save();
    return bot.sendMessage(msg.chat.id, "✅ Narx saqlandi.");
  }

  if (user.step === "emoji") {
    const [button, id] = (msg.text || "").split(/\s+/);
    if (!button || !id) return bot.sendMessage(msg.chat.id, "Format: menu 527...");
    const current = await Setting.findOne({ key: "emoji_buttons" });
    const value = current?.value || {};
    value[button] = id;
    await Setting.findOneAndUpdate({ key: "emoji_buttons" }, { value }, { upsert: true });
    user.step = null; await user.save();
    return bot.sendMessage(msg.chat.id, `✅ ${button} tugmasiga emoji ID biriktirildi.`);
  }
}

async function addChannel(bot, msg, user) {
  user.step = "channel_chatid"; user.temp = {}; await user.save();
  bot.sendMessage(msg.chat.id, "📢 Kanal chat ID yuboring.\nMasalan: -1001234567890");
}

async function setPrice(bot, msg, user) {
  user.step = "price"; await user.save();
  bot.sendMessage(msg.chat.id, "Format yuboring:\n1 10000\n3 25000\n12 75000");
}

async function showPrices(bot, chatId) {
  const get = async p => (await Setting.findOne({ key: `price_${p}` }))?.value || ({1:10000,3:25000,12:75000}[p]);
  bot.sendMessage(chatId, `💎 Premium narxlari:\n1 oy — ${await get(1)} so'm\n3 oy — ${await get(3)} so'm\n1 yil — ${await get(12)} so'm`);
}

async function emojiPanel(bot, msg, user) {
  user.step = "emoji"; await user.save();
  bot.sendMessage(msg.chat.id,
`✨ Custom emoji sozlash

Format:
button_id emoji_id

Masalan:
menu 5271829423899845716

Button ID ni o'zingiz tanlaysiz.
Keyin kodda o'sha ID ga emoji qo'yiladi.`);
}

async function stats(bot, chatId) {
  const users = await User.countDocuments();
  const movies = await Movie.countDocuments();
  bot.sendMessage(chatId, `📊 Statistika\n\n👥 Userlar: ${users}\n🎬 Kinolar: ${movies}`);
}

module.exports = { isAdmin, adminPanel, addMovie, addChannel, setPrice, showPrices, emojiPanel, stats, handleAdminStep };
