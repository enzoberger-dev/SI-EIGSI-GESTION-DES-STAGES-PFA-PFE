const fs = require('node:fs');
const path = require('node:path');
const Database = require('better-sqlite3');

const dataDirectory = path.join(__dirname, '..', '..', 'data');
const databasePath = path.join(dataDirectory, 'stages.sqlite');

fs.mkdirSync(dataDirectory, { recursive: true });

const database = new Database(databasePath);
database.pragma('foreign_keys = ON');

module.exports = database;
