#!/usr/bin/env node

// Split monolithic quotes.js into 24 hourly JSON files for async loading.
// Usage: node scripts/split-quotes.js
// Output: data/quotes-00.json through data/quotes-23.json

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const QUOTES_FILE = path.join(ROOT, 'quotes.js');
const DATA_DIR = path.join(ROOT, 'data');

// Evaluate quotes.js to extract the QUOTES object (handles trailing commas)
const vm = require('vm');
const raw = fs.readFileSync(QUOTES_FILE, 'utf-8');

// Replace "const QUOTES =" with "this.QUOTES =" so it attaches to the context
const modified = raw.replace(/^const QUOTES\s*=/m, 'this.QUOTES =');
const context = {};
vm.createContext(context);
vm.runInContext(modified, context);

if (!context.QUOTES) {
    console.error('Could not find QUOTES object in quotes.js');
    process.exit(1);
}

const quotes = context.QUOTES;

// Create output directory
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Group quotes by hour and write 24 files
let totalQuotes = 0;
for (let hour = 0; hour < 24; hour++) {
    const hourStr = hour.toString().padStart(2, '0');
    const hourData = {};

    for (let minute = 0; minute < 60; minute++) {
        const key = `${hourStr}:${minute.toString().padStart(2, '0')}`;
        if (quotes[key]) {
            hourData[key] = quotes[key];
            totalQuotes += quotes[key].length;
        }
    }

    const outFile = path.join(DATA_DIR, `quotes-${hourStr}.json`);
    fs.writeFileSync(outFile, JSON.stringify(hourData));

    const size = (fs.statSync(outFile).size / 1024).toFixed(0);
    const keys = Object.keys(hourData).length;
    console.log(`  ${path.basename(outFile)}  ${keys} time slots  ${size} KB`);
}

console.log(`\nDone: 24 files written to data/, ${totalQuotes} total quotes.`);
