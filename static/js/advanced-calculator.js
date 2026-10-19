/* ==========================================================================
   Advanced Calculator — engine + UI
   --------------------------------------------------------------------------
   • Safe expression evaluator (tokenize → shunting-yard → RPN). No eval().
   • Live preview while typing, calculation history, memory keys, ANS recall.
   • DEG/RAD trig, factorial, percent (smart A+B%), implicit multiplication.
   • Unit converter (length / mass / volume / area) and stock tools.
   • Full keyboard support with visual key feedback.
   ========================================================================== */
(function () {
    'use strict';

    /* ---------------------------------------------------------------------
       1. Expression engine
       --------------------------------------------------------------------- */

    var FUNCS = {
        sqrt: 1, cbrt: 1, sin: 1, cos: 1, tan: 1,
        asin: 1, acos: 1, atan: 1, log: 1, ln: 1,
        abs: 1, exp: 1
    };

    var CONSTANTS = { pi: Math.PI, e: Math.E };

    var engineState = {
        angle: 'DEG',   // DEG | RAD
        ans: 0
    };

    function normalizeExpr(raw) {
        return String(raw)
            .replace(/[×∙⋅]/g, '*')
            .replace(/[÷]/g, '/')
            .replace(/[−–—]/g, '-')
            .replace(/，/g, ',')
            .replace(/√/g, 'sqrt')
            .replace(/∛/g, 'cbrt')
            .replace(/π/g, 'pi')
            .replace(/,/g, '')            // strip display thousand separators
            .replace(/\s+/g, ' ')
            .trim();
    }

    /* Smart percent: "200+10%" → "200+(200*10/100)" (= 220), same for −.
       Lone "10%" falls through as postfix /100. */
    function rewritePercent(expr) {
        var pattern = /(\d*\.?\d+)\s*([+-])\s*(\d*\.?\d+)\s*%/g;
        var prev;
        do {
            prev = expr;
            expr = expr.replace(pattern, function (_m, a, op, b) {
                return a + op + '(' + a + '*' + b + '/100)';
            });
        } while (expr !== prev);
        return expr;
    }

    function tokenize(expr) {
        var tokens = [];
        var i = 0;
        var n = expr.length;

        function push(type, value) { tokens.push({ t: type, v: value }); }

        while (i < n) {
            var ch = expr[i];

            if (ch === ' ') { i++; continue; }

            // number (incl. 1.5e-3)
            if (/[0-9.]/.test(ch)) {
                var start = i;
                i++;
                while (i < n && /[0-9]/.test(expr[i])) i++;
                if (expr[i] === '.' ) { i++; while (i < n && /[0-9]/.test(expr[i])) i++; }
                if (expr[i] === 'e' || expr[i] === 'E') {
                    var save = i;
                    i++;
                    if (expr[i] === '+' || expr[i] === '-') i++;
                    if (/[0-9]/.test(expr[i] || '')) {
                        while (i < n && /[0-9]/.test(expr[i])) i++;
                    } else {
                        i = save; // bare "e" is Euler's number → fall through
                    }
                }
                var numStr = expr.slice(start, i);
                if (numStr === '.') throw new Error('Invalid number');
                push('num', parseFloat(numStr));
                continue;
            }

            // identifier: function / constant / ANS
            if (/[a-z]/i.test(ch)) {
                var s = i;
                while (i < n && /[a-z0-9]/i.test(expr[i])) i++;
                var word = expr.slice(s, i).toLowerCase();
                if (word === 'ans') { push('const', engineState.ans); continue; }
                if (Object.prototype.hasOwnProperty.call(CONSTANTS, word)) {
                    push('const', CONSTANTS[word]);
                    continue;
                }
                if (Object.prototype.hasOwnProperty.call(FUNCS, word)) {
                    push('func', word);
                    continue;
                }
                if (word === 'e') { push('const', Math.E); continue; }
                throw new Error('Unknown symbol: ' + word);
            }

            if (ch === '(' ) { push('lparen', '('); i++; continue; }
            if (ch === ')' ) { push('rparen', ')'); i++; continue; }
            if (ch === '%' ) { push('postfix', '%'); i++; continue; }
            if (ch === '!' ) { push('postfix', '!'); i++; continue; }
            if (ch === '^' ) { push('op', '^'); i++; continue; }
            if (ch === '+' || ch === '-' || ch === '*' || ch === '/') {
                push('op', ch); i++; continue;
            }
            throw new Error('Unexpected character: ' + ch);
        }
        return tokens;
    }

    /* Insert implicit multiplication: 2pi, 3(4+1), 2sqrt(9), )( */
    function insertImplicitMul(tokens) {
        var out = [];
        for (var i = 0; i < tokens.length; i++) {
            var cur = tokens[i];
            var prev = out[out.length - 1];
            if (prev) {
                var prevEndsValue =
                    prev.t === 'num' || prev.t === 'const' ||
                    prev.t === 'rparen' || prev.t === 'postfix';
                var curStartsValue =
                    cur.t === 'num' || cur.t === 'const' ||
                    cur.t === 'func' || cur.t === 'lparen';
                if (prevEndsValue && curStartsValue) {
                    out.push({ t: 'op', v: '*' });
                }
            }
            out.push(cur);
        }
        return out;
    }

    function factorial(n) {
        if (n < 0 || Math.abs(n % 1) > 1e-9) throw new Error('Factorial needs a whole number ≥ 0');
        if (n > 170) throw new Error('Factorial too large (max 170!)');
        var r = 1;
        for (var i = 2; i <= n; i++) r *= i;
        return r;
    }

    function applyFunc(name, x) {
        var toRad = engineState.angle === 'DEG' ? Math.PI / 180 : 1;
        var fromRad = engineState.angle === 'DEG' ? 180 / Math.PI : 1;
        switch (name) {
            case 'sqrt':
                if (x < 0) throw new Error('√ of a negative number');
                return Math.sqrt(x);
            case 'cbrt': return Math.cbrt(x);
            case 'sin': return Math.sin(x * toRad);
            case 'cos': return Math.cos(x * toRad);
            case 'tan': {
                if (engineState.angle === 'DEG') {
                    var m = ((x % 180) + 180) % 180;
                    if (Math.abs(m - 90) < 1e-9) throw new Error('tan is undefined here');
                }
                return Math.tan(x * toRad);
            }
            case 'asin':
                if (x < -1 || x > 1) throw new Error('asin needs a value between −1 and 1');
                return Math.asin(x) * fromRad;
            case 'acos':
                if (x < -1 || x > 1) throw new Error('acos needs a value between −1 and 1');
                return Math.acos(x) * fromRad;
            case 'atan': return Math.atan(x) * fromRad;
            case 'log':
                if (x <= 0) throw new Error('log needs a value greater than 0');
                return Math.log10(x);
            case 'ln':
                if (x <= 0) throw new Error('ln needs a value greater than 0');
                return Math.log(x);
            case 'abs': return Math.abs(x);
            case 'exp': return Math.exp(x);
            default: throw new Error('Unknown function');
        }
    }

    var PREC = { '+': 1, '-': 1, '*': 2, '/': 2, 'neg': 3, '^': 4 };

    function toRPN(tokens) {
        var output = [];
        var stack = [];      // operators
        var expectOperand = true;

        for (var i = 0; i < tokens.length; i++) {
            var tk = tokens[i];

            if (tk.t === 'num' || tk.t === 'const') {
                output.push(tk);
                expectOperand = false;
                continue;
            }
            if (tk.t === 'func') {
                stack.push(tk);
                expectOperand = true;
                continue;
            }
            if (tk.t === 'postfix') {
                if (expectOperand) throw new Error('Misplaced "' + tk.v + '"');
                output.push(tk);
                continue;
            }
            if (tk.t === 'lparen') {
                stack.push(tk);
                expectOperand = true;
                continue;
            }
            if (tk.t === 'rparen') {
                while (stack.length && stack[stack.length - 1].t !== 'lparen') {
                    output.push(stack.pop());
                }
                if (!stack.length) throw new Error('Mismatched parentheses');
                stack.pop(); // lparen
                if (stack.length && stack[stack.length - 1].t === 'func') {
                    output.push(stack.pop());
                }
                expectOperand = false;
                continue;
            }
            if (tk.t === 'op') {
                var op = tk.v;
                if (op === '-' && expectOperand) {
                    // unary minus
                    while (stack.length) {
                        var top = stack[stack.length - 1];
                        if (top.t === 'op' && (top.v === '^' || PREC[top.v] > PREC.neg)) {
                            output.push(stack.pop());
                        } else break;
                    }
                    stack.push({ t: 'op', v: 'neg', unary: true });
                    expectOperand = true;
                    continue;
                }
                if (expectOperand) throw new Error('Misplaced operator');
                while (stack.length) {
                    var t2 = stack[stack.length - 1];
                    if (t2.t === 'func') {
                        output.push(stack.pop());
                        continue;
                    }
                    if (t2.t === 'op') {
                        var pTop = PREC[t2.v];
                        var pCur = PREC[op];
                        if (pTop > pCur || (pTop === pCur && op !== '^')) {
                            output.push(stack.pop());
                            continue;
                        }
                    }
                    break;
                }
                stack.push({ t: 'op', v: op });
                expectOperand = true;
            }
        }
        while (stack.length) {
            var rest = stack.pop();
            if (rest.t === 'lparen') throw new Error('Mismatched parentheses');
            output.push(rest);
        }
        if (expectOperand && output.length) throw new Error('Expression is incomplete');
        return output;
    }

    function evalRPN(rpn) {
        var st = [];
        for (var i = 0; i < rpn.length; i++) {
            var tk = rpn[i];
            if (tk.t === 'num' || tk.t === 'const') {
                st.push(tk.v);
            } else if (tk.t === 'postfix') {
                if (!st.length) throw new Error('Expression is incomplete');
                var a = st.pop();
                st.push(tk.v === '%' ? a / 100 : factorial(a));
            } else if (tk.t === 'func') {
                if (!st.length) throw new Error('Expression is incomplete');
                st.push(applyFunc(tk.v, st.pop()));
            } else if (tk.t === 'op') {
                if (tk.v === 'neg') {
                    if (!st.length) throw new Error('Expression is incomplete');
                    st.push(-st.pop());
                    continue;
                }
                if (st.length < 2) throw new Error('Expression is incomplete');
                var b = st.pop();
                var a2 = st.pop();
                switch (tk.v) {
                    case '+': st.push(a2 + b); break;
                    case '-': st.push(a2 - b); break;
                    case '*': st.push(a2 * b); break;
                    case '/':
                        if (b === 0) throw new Error('Cannot divide by zero');
                        st.push(a2 / b);
                        break;
                    case '^': {
                        var p = Math.pow(a2, b);
                        if (isNaN(p)) throw new Error('Invalid power');
                        st.push(p);
                        break;
                    }
                    default: throw new Error('Unknown operator');
                }
            }
        }
        if (st.length !== 1) throw new Error('Expression is incomplete');
        var result = st[0];
        if (typeof result !== 'number' || isNaN(result)) throw new Error('Result is not a number');
        return result;
    }

    /**
     * Evaluate a display expression.
     * @param {string} raw       what the user sees (×, ÷, π, %, …)
     * @param {object} [opts]    { preview: true } → tolerant of incomplete input
     *                           (returns null instead of throwing when trailing
     *                           operators / unclosed parens remain)
     */
    function evaluate(raw, opts) {
        var preview = opts && opts.preview;
        var expr = normalizeExpr(raw);
        if (!expr) return preview ? null : 0;

        expr = rewritePercent(expr);

        // Auto-close unbalanced parens for live preview only
        if (preview) {
            var opens = (expr.match(/\(/g) || []).length;
            var closes = (expr.match(/\)/g) || []).length;
            if (opens > closes) expr += ')'.repeat(opens - closes);
            if (/[+\-*/^]$/.test(expr) || /neg$/.test(expr)) {
                expr = expr.replace(/[+\-*/^]+$/, '');
            }
            if (!expr) return null;
        }

        var tokens = insertImplicitMul(tokenize(expr));
        if (!tokens.length) return preview ? null : 0;
        return evalRPN(toRPN(tokens));
    }

    /* ---------------------------------------------------------------------
       2. Number formatting
       --------------------------------------------------------------------- */

    var groupFmt = null;
    try {
        groupFmt = new Intl.NumberFormat('en-ZA', { maximumFractionDigits: 10 });
    } catch (err) {
        groupFmt = null;
    }

    function formatNumber(x, opts) {
        if (!isFinite(x)) return x > 0 ? '∞' : (x < 0 ? '−∞' : 'Error');
        var grouped = opts && opts.grouped;
        var abs = Math.abs(x);

        // clean float noise
        var cleaned = parseFloat(x.toPrecision(12));
        if (Object.is(cleaned, -0)) cleaned = 0;

        if (abs !== 0 && (abs >= 1e15 || abs < 1e-9)) {
            return cleaned.toExponential(8).replace(/\.?0+e/, 'e').replace('-', '−');
        }
        if (grouped && groupFmt) {
            return groupFmt.format(cleaned).replace(/-/g, '−');
        }
        return String(cleaned).replace('-', '−');
    }

    /* Machine-friendly (no minus sign swap, no grouping) for chaining results */
    function toRawNumber(x) {
        var cleaned = parseFloat(x.toPrecision(12));
        return String(cleaned);
    }

    /* ---------------------------------------------------------------------
       3. UI controller
       --------------------------------------------------------------------- */

    var els = {};
    var history = [];
    var memory = 0;
    var STORAGE_HISTORY = 'advCalcHistory';
    var STORAGE_MEMORY = 'advCalcMemory';
    var STORAGE_ANGLE = 'advCalcAngle';

    function $(id) { return document.getElementById(id); }

    function init() {
        els.expression = $('calc-expression');
        els.preview = $('calc-preview');
        els.memoryFlag = $('calc-memory-flag');
        els.angleBtn = $('calc-angle-btn');
        els.historyList = $('calc-history-list');
        els.historyEmpty = $('calc-history-empty');
        els.clearHistory = $('calc-history-clear');
        els.copyResult = $('calc-copy-result');
        els.toast = $('calc-toast');

        if (!els.expression) return; // script loaded on the wrong page

        restoreState();
        renderMemoryFlag();
        renderHistory();
        updatePreview();

        // --- mode tabs ---
        document.querySelectorAll('.calc-mode-btn').forEach(function (btn) {
            btn.addEventListener('click', function () { switchMode(btn.dataset.mode); });
        });

        // --- keypad + sci keys (event delegation) ---
        var pad = $('calc-keypad');
        if (pad) {
            pad.addEventListener('click', function (e) {
                var btn = e.target.closest('[data-action]');
                if (!btn) return;
                handleAction(btn.dataset.action, btn.dataset.value);
            });
        }
        var sci = $('calc-sci-keys');
        if (sci) {
            sci.addEventListener('click', function (e) {
                var btn = e.target.closest('[data-action]');
                if (!btn) return;
                handleAction(btn.dataset.action, btn.dataset.value);
            });
        }
        var memRow = $('calc-memory-keys');
        if (memRow) {
            memRow.addEventListener('click', function (e) {
                var btn = e.target.closest('[data-action]');
                if (!btn) return;
                handleAction(btn.dataset.action, btn.dataset.value);
            });
        }

        // --- expression input ---
        els.expression.addEventListener('input', function () {
            normalizeDisplay();
            updatePreview();
        });
        els.expression.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === '=') {
                e.preventDefault();
                commit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                clearAll();
            }
        });

        // --- keyboard (visual feedback + fast entry) ---
        document.addEventListener('keydown', handleGlobalKey);

        // --- history ---
        if (els.clearHistory) {
            els.clearHistory.addEventListener('click', function () {
                history = [];
                saveHistory();
                renderHistory();
                showToast('History cleared');
            });
        }

        // --- copy ---
        if (els.copyResult) {
            els.copyResult.addEventListener('click', copyCurrentResult);
        }

        // --- memory / angle live in handleAction ---

        // --- converter ---
        initConverter();

        // --- stock tools ---
        initStockTools();

        // welcome toast hint
        setTimeout(function () {
            showToast('Tip: type on your keyboard — Enter = equals, Esc = clear');
        }, 600);
    }

    /* ---------------- display helpers ---------------- */

    function normalizeDisplay() {
        var el = els.expression;
        var pos = el.selectionStart;
        var before = el.value;
        var after = before
            .replace(/\*/g, '×')
            .replace(/\//g, '÷')
            .replace(/(^|[^0-9)])\.(?=[0-9])/g, '$1.'); // keep decimals
        // only rewrite when it changed something meaningful
        if (after !== before) {
            el.value = after;
            try { el.setSelectionRange(pos, pos); } catch (e) { /* ignore */ }
        }
    }

    function insertAtCaret(text) {
        var el = els.expression;
        var start = el.selectionStart || el.value.length;
        var end = el.selectionEnd || el.value.length;
        var val = el.value;
        el.value = val.slice(0, start) + text + val.slice(end);
        var caret = start + text.length;
        el.focus();
        try { el.setSelectionRange(caret, caret); } catch (e) { /* ignore */ }
        normalizeDisplay();
        updatePreview();
    }

    function backspace() {
        var el = els.expression;
        var start = el.selectionStart;
        var end = el.selectionEnd;
        if (start === end) {
            if (start === 0) return;
            el.value = el.value.slice(0, start - 1) + el.value.slice(end);
            start -= 1;
        } else {
            el.value = el.value.slice(0, start) + el.value.slice(end);
        }
        el.focus();
        try { el.setSelectionRange(start, start); } catch (e) { /* ignore */ }
        updatePreview();
    }

    function clearAll() {
        els.expression.value = '';
        els.preview.textContent = '';
        els.preview.classList.remove('is-error');
        els.expression.focus();
        updatePreview();
    }

    function updatePreview() {
        var raw = els.expression.value.trim();
        if (!raw) {
            els.preview.textContent = '0';
            els.preview.classList.remove('is-error');
            return;
        }
        try {
            var result = evaluate(raw, { preview: true });
            if (result === null || result === undefined) {
                els.preview.textContent = '';
                els.preview.classList.remove('is-error');
                return;
            }
            els.preview.textContent = '= ' + formatNumber(result, { grouped: true });
            els.preview.classList.remove('is-error');
        } catch (err) {
            els.preview.textContent = '';
            els.preview.classList.remove('is-error');
        }
    }

    function commit() {
        var raw = els.expression.value.trim();
        if (!raw) return;
        try {
            var result = evaluate(raw);
            engineState.ans = result;
            var pretty = formatNumber(result, { grouped: true });
            pushHistory(raw, pretty);
            els.expression.value = toRawNumber(result).replace('-', '−');
            els.preview.textContent = '= ' + pretty;
            els.preview.classList.remove('is-error');
        } catch (err) {
            els.preview.textContent = err.message || 'Invalid expression';
            els.preview.classList.add('is-error');
        }
    }

    function copyCurrentResult() {
        var text = els.preview.textContent.replace(/^=\s*/, '') || els.expression.value;
        if (!text) { showToast('Nothing to copy yet'); return; }
        copyText(text).then(function () {
            showToast('Copied: ' + text);
        });
    }

    function copyText(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).catch(function () {
                return legacyCopy(text);
            });
        }
        return legacyCopy(text);
    }

    function legacyCopy(text) {
        return new Promise(function (resolve) {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand('copy'); } catch (e) { /* ignore */ }
            document.body.removeChild(ta);
            resolve();
        });
    }

    var toastTimer = null;
    function showToast(msg) {
        if (!els.toast) return;
        els.toast.textContent = msg;
        els.toast.classList.add('is-visible');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            els.toast.classList.remove('is-visible');
        }, 2400);
    }

    /* ---------------- actions ---------------- */

    function handleAction(action, value) {
        switch (action) {
            case 'insert': insertAtCaret(value); break;
            case 'func': insertAtCaret(value + '('); break;
            case 'clear': clearAll(); break;
            case 'back': backspace(); break;
            case 'equals': commit(); break;
            case 'negate': toggleSign(); break;
            case 'ans': insertAtCaret('ans'); break;
            case 'angle': toggleAngle(); break;
            case 'mem-clear': memory = 0; saveMemory(); renderMemoryFlag(); showToast('Memory cleared'); break;
            case 'mem-recall': insertAtCaret(String(memory).replace('-', '−')); break;
            case 'mem-add': memory += currentOrZero(); saveMemory(); renderMemoryFlag(); showToast('Added to memory'); break;
            case 'mem-sub': memory -= currentOrZero(); saveMemory(); renderMemoryFlag(); showToast('Subtracted from memory'); break;
            case 'mem-store': memory = currentOrZero(); saveMemory(); renderMemoryFlag(); showToast('Stored in memory'); break;
            default: break;
        }
    }

    function currentOrZero() {
        try {
            var raw = els.expression.value.trim();
            if (!raw) return engineState.ans;
            return evaluate(raw, { preview: true }) || 0;
        } catch (e) {
            return 0;
        }
    }

    function toggleSign() {
        var el = els.expression;
        var val = el.value.trim();
        if (!val) {
            insertAtCaret('−');
            return;
        }
        if (val.startsWith('−')) {
            el.value = val.slice(1);
        } else {
            el.value = '−(' + val + ')';
        }
        el.focus();
        updatePreview();
    }

    function toggleAngle() {
        engineState.angle = engineState.angle === 'DEG' ? 'RAD' : 'DEG';
        if (els.angleBtn) {
            els.angleBtn.textContent = engineState.angle;
            els.angleBtn.setAttribute('aria-label',
                'Angle mode: ' + engineState.angle + ' (click to switch)');
        }
        try { localStorage.setItem(STORAGE_ANGLE, engineState.angle); } catch (e) { /* ignore */ }
        updatePreview();
        showToast('Trigonometry: ' + engineState.angle);
    }

    /* ---------------- memory + history persistence ---------------- */

    function renderMemoryFlag() {
        if (!els.memoryFlag) return;
        els.memoryFlag.textContent = memory !== 0 ? 'M' : '';
        els.memoryFlag.title = memory !== 0 ? 'Memory: ' + formatNumber(memory) : 'Memory empty';
    }

    function saveMemory() {
        try { localStorage.setItem(STORAGE_MEMORY, String(memory)); } catch (e) { /* ignore */ }
    }

    function saveHistory() {
        try { localStorage.setItem(STORAGE_HISTORY, JSON.stringify(history)); } catch (e) { /* ignore */ }
    }

    function pushHistory(expr, result) {
        history.unshift({ e: expr, r: result, t: Date.now() });
        if (history.length > 50) history = history.slice(0, 50);
        saveHistory();
        renderHistory();
    }

    function renderHistory() {
        if (!els.historyList) return;
        els.historyList.innerHTML = '';
        if (!history.length) {
            if (els.historyEmpty) els.historyEmpty.style.display = 'block';
            if (els.clearHistory) els.clearHistory.disabled = true;
            return;
        }
        if (els.historyEmpty) els.historyEmpty.style.display = 'none';
        if (els.clearHistory) els.clearHistory.disabled = false;

        history.forEach(function (item, idx) {
            var li = document.createElement('li');
            li.className = 'calc-history-item';
            li.tabIndex = 0;
            li.setAttribute('role', 'button');
            li.setAttribute('aria-label', 'Reuse result ' + item.r);

            var exprSpan = document.createElement('span');
            exprSpan.className = 'calc-history-expr';
            exprSpan.textContent = item.e;

            var resSpan = document.createElement('span');
            resSpan.className = 'calc-history-res';
            resSpan.textContent = '= ' + item.r;

            li.appendChild(exprSpan);
            li.appendChild(resSpan);

            function reuse() {
                els.expression.value = item.r.replace(/,/g, '');
                els.expression.focus();
                updatePreview();
                showToast('Result restored');
            }
            li.addEventListener('click', reuse);
            li.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    reuse();
                }
            });
            els.historyList.appendChild(li);
            // entrance animation only for the newest item
            if (idx === 0) li.classList.add('is-new');
        });
    }

    function restoreState() {
        try {
            var h = JSON.parse(localStorage.getItem(STORAGE_HISTORY) || '[]');
            if (Array.isArray(h)) history = h;
            var m = parseFloat(localStorage.getItem(STORAGE_MEMORY));
            if (!isNaN(m)) memory = m;
            var angle = localStorage.getItem(STORAGE_ANGLE);
            if (angle === 'DEG' || angle === 'RAD') {
                engineState.angle = angle;
                if (els.angleBtn) els.angleBtn.textContent = angle;
            }
        } catch (e) { /* corrupted storage → start fresh */ }
    }

    /* ---------------- keyboard ---------------- */

    var KEY_MAP = {
        '0': '[data-key="0"]', '1': '[data-key="1"]', '2': '[data-key="2"]',
        '3': '[data-key="3"]', '4': '[data-key="4"]', '5': '[data-key="5"]',
        '6': '[data-key="6"]', '7': '[data-key="7"]', '8': '[data-key="8"]',
        '9': '[data-key="9"]', '.': '[data-key="."]', ',': '[data-key="."]',
        '+': '[data-key="+"]', '-': '[data-key="-"]', '*': '[data-key="×"]',
        '/': '[data-key="÷"]', '(': '[data-key="("]', ')': '[data-key=")"]',
        '%': '[data-key="%"]', '^': '[data-key="^"]', '!': '[data-key="!"]',
        '=': '[data-action="equals"]', 'Enter': '[data-action="equals"]',
        'Backspace': '[data-action="back"]', 'Escape': '[data-action="clear"]'
    };

    function flashKey(selector) {
        var btn = document.querySelector('#calc-keypad ' + selector) ||
                  document.querySelector('#calc-sci-keys ' + selector);
        if (!btn) return;
        btn.classList.add('is-pressed');
        setTimeout(function () { btn.classList.remove('is-pressed'); }, 120);
    }

    function handleGlobalKey(e) {
        // only when the calculator panel is on screen
        var panel = document.querySelector('.calc-view[data-view="calculator"]');
        if (!panel || panel.hidden) return;

        // never hijack typing in other inputs (converter / stock tools)
        var tag = (e.target.tagName || '').toLowerCase();
        if ((tag === 'input' || tag === 'textarea' || tag === 'select') &&
            e.target !== els.expression) {
            return;
        }
        if (e.ctrlKey || e.metaKey || e.altKey) return;

        var selector = KEY_MAP[e.key];
        if (!selector) return;

        // expression input handles its own characters natively — just flash
        if (e.target === els.expression &&
            !['Enter', '=', 'Escape', 'Backspace'].includes(e.key)) {
            flashKey(selector);
            return;
        }

        e.preventDefault();
        flashKey(selector);

        if (e.key === 'Enter' || e.key === '=') {
            commit();
        } else if (e.key === 'Escape') {
            clearAll();
        } else if (e.key === 'Backspace') {
            backspace();
        } else {
            var insertMap = { '*': '×', '/': '÷', '-': '−', ',': '.' };
            insertAtCaret(insertMap[e.key] || e.key);
        }
    }

    /* ---------------- modes ---------------- */

    function switchMode(mode) {
        document.querySelectorAll('.calc-mode-btn').forEach(function (btn) {
            var active = btn.dataset.mode === mode;
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        document.querySelectorAll('.calc-view').forEach(function (view) {
            var show = view.dataset.view === mode;
            view.hidden = !show;
        });
        // scientific & standard share the calculator view
        var calculatorView = document.querySelector('.calc-view[data-view="calculator"]');
        if (calculatorView && (mode === 'standard' || mode === 'scientific')) {
            calculatorView.hidden = false;
            calculatorView.classList.toggle('is-scientific', mode === 'scientific');
            if (mode === 'standard' || mode === 'scientific') {
                els.expression.focus();
            }
        }
    }

    /* ---------------- unit converter ---------------- */

    var UNIT_TABLE = {
        length: {
            label: 'Length',
            units: {
                'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
                'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144
            },
            defaultFrom: 'mm', defaultTo: 'm'
        },
        mass: {
            label: 'Mass / Weight',
            units: { 'g': 0.001, 'kg': 1, 't': 1000, 'oz': 0.028349523, 'lb': 0.45359237 },
            defaultFrom: 'kg', defaultTo: 'g'
        },
        volume: {
            label: 'Volume',
            units: { 'ml': 0.001, 'l': 1, 'kl': 1000, 'gal (US)': 3.785411784, 'fl oz (US)': 0.0295735296 },
            defaultFrom: 'l', defaultTo: 'ml'
        },
        area: {
            label: 'Area',
            units: { 'mm²': 0.000001, 'cm²': 0.0001, 'm²': 1, 'km²': 1000000, 'in²': 0.00064516, 'ft²': 0.09290304 },
            defaultFrom: 'm²', defaultTo: 'mm²'
        }
    };

    function initConverter() {
        var catWrap = $('conv-categories');
        var fromVal = $('conv-from-value');
        var toVal = $('conv-to-value');
        var fromUnit = $('conv-from-unit');
        var toUnit = $('conv-to-unit');
        var swapBtn = $('conv-swap');
        if (!catWrap) return;

        var currentCat = 'length';

        function fillUnits() {
            var cfg = UNIT_TABLE[currentCat];
            [fromUnit, toUnit].forEach(function (sel) {
                sel.innerHTML = '';
                Object.keys(cfg.units).forEach(function (u) {
                    var opt = document.createElement('option');
                    opt.value = u;
                    opt.textContent = u;
                    sel.appendChild(opt);
                });
            });
            fromUnit.value = cfg.defaultFrom;
            toUnit.value = cfg.defaultTo;
        }

        function convertForward() {
            var cfg = UNIT_TABLE[currentCat];
            var v = parseFloat(fromVal.value);
            if (isNaN(v)) {
                toVal.value = '';
                return;
            }
            var base = v * cfg.units[fromUnit.value];
            var result = base / cfg.units[toUnit.value];
            toVal.value = formatNumber(result, { grouped: false }).replace('−', '-');
        }

        function convertBackward() {
            var cfg = UNIT_TABLE[currentCat];
            var v = parseFloat(toVal.value);
            if (isNaN(v)) {
                fromVal.value = '';
                return;
            }
            var base = v * cfg.units[toUnit.value];
            var result = base / cfg.units[fromUnit.value];
            fromVal.value = formatNumber(result, { grouped: false }).replace('−', '-');
        }

        catWrap.addEventListener('click', function (e) {
            var chip = e.target.closest('[data-category]');
            if (!chip) return;
            currentCat = chip.dataset.category;
            catWrap.querySelectorAll('.calc-chip').forEach(function (c) {
                c.classList.toggle('is-active', c === chip);
                c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
            });
            fillUnits();
            convertForward();
        });

        fromVal.addEventListener('input', convertForward);
        toVal.addEventListener('input', convertBackward);
        fromUnit.addEventListener('change', convertForward);
        toUnit.addEventListener('change', convertForward);

        if (swapBtn) {
            swapBtn.addEventListener('click', function () {
                var u = fromUnit.value;
                fromUnit.value = toUnit.value;
                toUnit.value = u;
                var v = fromVal.value;
                fromVal.value = toVal.value;
                toVal.value = v;
                convertForward();
            });
        }

        fillUnits();
        convertForward();
    }

    /* ---------------- stock tools ---------------- */

    function initStockTools() {
        bindLive([
            'tape-rolls', 'tape-width', 'piece-length', 'piece-wastage',
            'kit-items', 'kit-count', 'kit-spare'
        ], updateStockTools);
        updateStockTools();
    }

    function bindLive(ids, fn) {
        ids.forEach(function (id) {
            var el = $(id);
            if (el) {
                el.addEventListener('input', fn);
                el.addEventListener('change', fn);
            }
        });
    }

    function readNum(id) {
        var el = $(id);
        var v = el ? parseFloat(el.value) : NaN;
        return isNaN(v) ? 0 : v;
    }

    function setOut(id, text) {
        var el = $(id);
        if (el) el.textContent = text;
    }

    function updateStockTools() {
        // 1. Tape / VHB rolls → total length + area
        var rolls = readNum('tape-rolls');
        var widthMm = readNum('tape-width');
        var rollLengthM = 33; // standard VHB roll
        var totalLen = rolls * rollLengthM;
        var totalArea = totalLen * (widthMm / 1000);
        setOut('tape-length-out', formatNumber(totalLen, { grouped: true }) + ' m');
        setOut('tape-area-out', formatNumber(totalArea, { grouped: true }) + ' m²');

        // 2. Pieces from a roll
        var pieceLenMm = readNum('piece-length');
        var wastePct = readNum('piece-wastage');
        var usableMm = totalLen * 1000 * (1 - Math.min(Math.max(wastePct, 0), 100) / 100);
        var pieces = pieceLenMm > 0 ? Math.floor(usableMm / pieceLenMm) : 0;
        setOut('pieces-out', formatNumber(pieces, { grouped: true }));

        // 3. Kit builder
        var itemsPerKit = readNum('kit-items');
        var kitCount = readNum('kit-count');
        var sparePct = readNum('kit-spare');
        var baseTotal = itemsPerKit * kitCount;
        var total = Math.ceil(baseTotal * (1 + Math.min(Math.max(sparePct, 0), 100) / 100));
        setOut('kit-out', formatNumber(total, { grouped: true }));
        setOut('kit-base-out', formatNumber(baseTotal, { grouped: true }) + ' base');
    }

    /* ---------------------------------------------------------------------
       boot
       --------------------------------------------------------------------- */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
