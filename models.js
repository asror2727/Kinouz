const mongoose = require("mongoose");

const channelSchema = new mongoose.Schema({
  chatId: { type: String, required: true, unique: true },
  username: String,
  title: String,
  inviteLink: String,
  enabled: { type: Boolean, default: true }
}, { timestamps: true });

const movieSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true, index: true },
  title: { type: String, default: "Nomsiz kino" },
  description: { type: String, default: "" },
  fileId: { type: String, required: true },
  fileType: { type: String, default: "video" },
  views: { type: Number, default: 0 },
  likes: { type: Number, default: 0 },
  commentsCount: { type: Number, default: 0 }
}, { timestamps: true });

const userSchema = new mongoose.Schema({
  telegramId: { type: Number, required: true, unique: true, index: true },
  firstName: String,
  username: String,
  premiumUntil: { type: Date, default: null },
  savedMovies: [{ type: String }],
  step: { type: String, default: null },
  temp: { type: mongoose.Schema.Types.Mixed, default: {} }
}, { timestamps: true });

const commentSchema = new mongoose.Schema({
  movieCode: { type: String, index: true },
  userId: Number,
  username: String,
  text: String
}, { timestamps: true });

const settingsSchema = new mongoose.Schema({
  key: { type: String, unique: true },
  value: mongoose.Schema.Types.Mixed
});

module.exports = {
  Channel: mongoose.model("Channel", channelSchema),
  Movie: mongoose.model("Movie", movieSchema),
  User: mongoose.model("User", userSchema),
  Comment: mongoose.model("Comment", commentSchema),
  Setting: mongoose.model("Setting", settingsSchema)
};
