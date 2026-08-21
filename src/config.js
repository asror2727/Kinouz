require("dotenv").config();

module.exports = {
  token: process.env.BOT_TOKEN,
  mongo: process.env.MONGODB_URI,
  port: Number(process.env.PORT || 3000),
  admins: (process.env.ADMIN_IDS || "")
    .split(",").map(x => Number(x.trim())).filter(Boolean),
  support: process.env.SUPPORT_USERNAME || "x7fan"
};
