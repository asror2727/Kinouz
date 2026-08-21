const { Channel } = require("../models");

async function getChannels() {
  return Channel.find({ enabled: true }).sort({ createdAt: 1 });
}

async function isSubscribed(bot, userId) {
  const channels = await getChannels();
  for (const ch of channels) {
    try {
      const member = await bot.getChatMember(ch.chatId, userId);
      const ok = ["creator", "administrator", "member"].includes(member.status);
      if (!ok) return false;
    } catch {
      return false;
    }
  }
  return true;
}

module.exports = { getChannels, isSubscribed };
