// Telegram custom emoji IDs.
// Text xabarlarida HTML orqali ishlatiladi:
// <tg-emoji emoji-id="ID">🎬</tg-emoji>
const IDS = {
  odam: "5271829423899845716",
  qol: "5271765841203995324",
  pul: "5271857409906745357",
  support: "5271586238556574482",
  id: "5271628651358622439",
  back: "5271512047291507931",
  qolBosish: "5271857014769754460",
  lupa: "5272013068111485452",
  dollar: "5271739719212901906",
  kashlok: "5271739719212901906",
  ok: "5271507881173227410",
  card: "5271907450570709756",
  warning: "5271535227230028862",
  dot: "5274239519028191789"
};

function ce(id, fallback = "✨") {
  return `<tg-emoji emoji-id="${id}">${fallback}</tg-emoji>`;
}

module.exports = { IDS, ce };
