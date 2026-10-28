import assert from 'node:assert/strict';
import fs from 'node:fs';
const directory = '/tmp/browser-artifacts';
const results = JSON.parse(fs.readFileSync(`${directory}/results.json`, 'utf8'));
assert.equal(results.length, 9);
assert.ok(results.every(result => result.passed === true));
const page = fs.readFileSync(`${directory}/page.png`);
assert.ok(page.length > 100 && page.length < 4 * 1024 * 1024);
console.log('ENCLAVE_BROWSER_RESULTS=' + JSON.stringify({ results, screenshot: page.toString('base64') }));
