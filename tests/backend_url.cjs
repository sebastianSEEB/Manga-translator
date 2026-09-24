const assert=require('node:assert/strict');
const {normalizeBackendUrl:n}=require('../extension/backend-url.js');
assert.equal(n('https://manga.example.com/'),'https://manga.example.com');
assert.equal(n('http://127.0.0.1:8000'),'http://127.0.0.1:8000');
for(const bad of ['http://manga.example.com','https://user:pass@example.com','https://example.com/path','https://example.com?token=secret','javascript:alert(1)'])assert.throws(()=>n(bad));
console.log('Backend URL validation passed');
