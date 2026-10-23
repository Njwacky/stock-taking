// Install test dependency: npm install --prefix .cache/ui-tests jsdom@26
// Run with: node scripts/test_add_stock_ui.cjs
const { JSDOM } = require('../.cache/ui-tests/node_modules/jsdom');
const { execFileSync } = require('node:child_process');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const html = execFileSync('.venv/bin/python', ['-c', `
import os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
import django
django.setup()
from django.template.loader import render_to_string
from stockT.models import User, KitType
user = User(id=1, username='UI tester', role='user')
kit = KitType(id=1, name='VHB Tape 18mm', code='TAPE')
print(json.dumps([render_to_string('add_items.html', {
    'user': user, 'can_select_user': manager, 'target_users': [user],
    'kit_types': [kit],
}) for manager in (False, True)]))
`], { encoding: 'utf8' });
(async () => {
    for (const [index, markup] of JSON.parse(html).entries()) {
        const dom = new JSDOM(markup, { runScripts: 'outside-only', url: 'http://testserver/add-items/' });
        const { window } = dom;
        const errors = [];
        window.addEventListener('error', e => errors.push(e.error));
        let fetches = 0;
        window.fetch = async () => { fetches++; return { json: async () => ({ success: true, kits: [] }) }; };
        window.eval(fs.readFileSync('static/js/add_items.js', 'utf8'));
        await new Promise(resolve => window.document.addEventListener('DOMContentLoaded', resolve));
        const doc = window.document;
        const checkbox = doc.querySelector('.modern-checkbox');
        const quantity = doc.querySelector('.quantity-input');
        const submit = doc.querySelector('#submitBtn');
        assert.equal(submit.disabled, true);
        checkbox.checked = true;
        checkbox.dispatchEvent(new window.Event('change'));
        assert.equal(quantity.disabled, false);
        assert.equal(doc.querySelector('.kit-details').classList.contains('show'), true);
        for (const [value, disabled] of [['0', true], ['1.5', true], ['3', false]]) {
            quantity.value = value;
            quantity.dispatchEvent(new window.Event('input'));
            assert.equal(submit.disabled, disabled, `quantity ${value}`);
        }
        assert.ok(doc.querySelector('.tape-calculation'));
        checkbox.checked = false;
        checkbox.dispatchEvent(new window.Event('change'));
        assert.equal(quantity.disabled, true);
        assert.equal(submit.disabled, true);
        checkbox.checked = true;
        checkbox.dispatchEvent(new window.Event('change'));
        assert.equal(doc.querySelector('.detail-select').value, 'new');
        doc.querySelector('#user').dispatchEvent(new window.Event('change'));
        assert.equal(errors.length, 0, errors.map(String).join('\n'));
        assert.equal(fetches > 0, index === 1);
        console.log(`PASS: ${index ? 'manager' : 'regular user'} selection, validation, tape calculation, reset and initialization`);
        window.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
