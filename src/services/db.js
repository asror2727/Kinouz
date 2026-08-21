const fs = require('fs');
const path = require('path');

const dbPath = path.join(__dirname, '../../data.json');

// Fayl bo'lmasa yaratib oladi
if (!fs.existsSync(dbPath)) {
    fs.writeFileSync(dbPath, JSON.stringify({ users: [], movies: [] }, null, 2));
}

const readData = () => JSON.parse(fs.readFileSync(dbPath, 'utf8'));
const writeData = (data) => fs.writeFileSync(dbPath, JSON.stringify(data, null, 2));

module.exports = { readData, writeData };
