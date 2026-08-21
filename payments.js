// Haqiqiy auto-payment API ma'lumotlari sizdagi mavjud koddan qo'shiladi.
// Hozircha bu modul pending order yaratish uchun interfeys beradi.

const { Setting } = require("../models");

async function createPayment(provider, userId, amount) {
  // Bu yerga sizning Hazna/Payme/Click API kodingiz ulanadi.
  // Natija: { paymentUrl, externalId }
  const setting = await Setting.findOne({ key: `payment_url_${provider}` });
  const baseUrl = setting?.value || process.env[`${provider.toUpperCase()}_PAYMENT_URL`] || "";
  return {
    paymentUrl: baseUrl,
    externalId: `${provider}_${userId}_${Date.now()}`
  };
}

async function verifyPayment(provider, externalId) {
  // Provider API bilan tekshirish shu yerda qilinadi.
  // Siz mavjud auto-payment kodini yuborsangiz, aynan shu joyga moslab beriladi.
  return { paid: false, externalId, provider };
}

module.exports = { createPayment, verifyPayment };
