const mongoose = require("mongoose");

async function connect(uri) {
  if (!uri) throw new Error("MONGODB_URI topilmadi");
  await mongoose.connect(uri);
  console.log("MongoDB ulandi");
}

module.exports = { connect };
