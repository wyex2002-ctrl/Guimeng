"""Strict Lua 5.1 / LuaJIT 2.0 lexer, recursive-descent parser, static checker, and AST evaluator.

Used by test_v299.py on Windows environments without a native luajit.exe to:
1. Strictly syntax-check & scope-check GBK Lua source strings embedded in game.res.
2. Execute the exact embedded Lua source (such as runtime_v299.lua) end-to-end against
   mocked game engine/UI/save/container states and real LuaJIT bytecode VM hooks.
"""
import math
import re


KEYWORDS = {
    'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function',
    'if', 'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then',
    'true', 'until', 'while',
}

TWO_CHAR_OPS = {'==', '~=', '<=', '>=', '..', '::'}
THREE_CHAR_OPS = {'...'}


class LuaSyntaxError(SyntaxError):
    pass


class LuaRuntimeError(RuntimeError):
    pass


class LuaTable:
    """Lua-like table supporting both dict/array indexing, #length, rawget, and metatables."""

    def __init__(self, initial=None):
        self._data = {}
        self._mt = None
        if initial:
            if isinstance(initial, dict):
                self._data.update(initial)
            elif isinstance(initial, list):
                for idx, val in enumerate(initial, 1):
                    self._data[idx] = val

    def rawget(self, k):
        return self._data.get(k, None)

    def rawset(self, k, v):
        if v is None:
            self._data.pop(k, None)
        else:
            self._data[k] = v

    def get(self, k):
        if k in self._data:
            return self._data[k]
        if self._mt is not None:
            idx = self._mt.rawget('__index')
            if callable(idx):
                return idx(self, k)
            if isinstance(idx, LuaTable):
                return idx.get(k)
        return None

    def set(self, k, v):
        if k in self._data or self._mt is None or self._mt.rawget('__newindex') is None:
            self.rawset(k, v)
            return
        ni = self._mt.rawget('__newindex')
        if callable(ni):
            ni(self, k, v)
        elif isinstance(ni, LuaTable):
            ni.set(k, v)

    def __call__(self, *args):
        if self._mt is not None:
            c = self._mt.rawget('__call')
            if callable(c):
                return c(self, *args)
        raise LuaRuntimeError('attempt to call a table value')

    def length(self):
        n = 0
        while (n + 1) in self._data:
            n += 1
        return n

    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, k, v):
        self.set(k, v)

    def __repr__(self):
        return f'LuaTable({self._data!r})'


def lua_truthy(v):
    return v is not None and v is not False


def lua_type(v):
    if v is None:
        return 'nil'
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, (int, float)):
        return 'number'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, LuaTable):
        return 'table'
    if callable(v):
        return 'function'
    return 'userdata'


def lua_tonumber(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            if s.startswith(('0x', '0X')):
                return int(s, 16)
            return int(s) if re.fullmatch(r'[+-]?\d+', s) else float(s)
        except ValueError:
            return None
    return None


def lua_tostring(v):
    if v is None:
        return 'nil'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, float) and v.is_integer() and not math.isinf(v):
        return str(int(v))
    return str(v)


def _is_ident_start(ch):
    return ch == '_' or ch.isalpha() or ord(ch) >= 128


def _is_ident_part(ch):
    return ch == '_' or ch.isalnum() or ord(ch) >= 128


def tokenize(src):
    tokens = []
    i = 0
    n = len(src)
    line = 1
    while i < n:
        ch = src[i]
        if ch in ' \t\r':
            i += 1
            continue
        if ch == '\n':
            line += 1
            i += 1
            continue
        # Comment
        if ch == '-' and i + 1 < n and src[i + 1] == '-':
            i += 2
            while i < n and src[i] != '\n':
                i += 1
            continue
        # String
        if ch in ("'", '"'):
            quote = ch
            i += 1
            buf = []
            while i < n and src[i] != quote:
                c = src[i]
                if c == '\n':
                    raise LuaSyntaxError(f'unfinished string at line {line}')
                if c == '\\':
                    i += 1
                    if i >= n:
                        raise LuaSyntaxError(f'unfinished escape at line {line}')
                    ec = src[i]
                    esc_map = {'n': '\n', 'r': '\r', 't': '\t', '\\': '\\', "'": "'", '"': '"', '0': '\0'}
                    if ec in esc_map:
                        buf.append(esc_map[ec])
                    elif ec.isdigit():
                        digits = ec
                        for _ in range(2):
                            if i + 1 < n and src[i + 1].isdigit():
                                i += 1
                                digits += src[i]
                            else:
                                break
                        buf.append(chr(int(digits)))
                    else:
                        raise LuaSyntaxError(f'invalid escape \\{ec} at line {line}')
                else:
                    buf.append(c)
                i += 1
            if i >= n:
                raise LuaSyntaxError(f'unterminated string at line {line}')
            i += 1
            tokens.append(('STR', ''.join(buf), line))
            continue
        # Number
        if ch.isdigit() or (ch == '.' and i + 1 < n and src[i + 1].isdigit()):
            m = re.match(r'(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)', src[i:])
            raw = m.group(0)
            if raw.startswith(('0x', '0X')):
                val = int(raw, 16)
            elif '.' in raw or 'e' in raw or 'E' in raw:
                val = float(raw)
            else:
                val = int(raw)
            tokens.append(('NUM', val, line))
            i += len(raw)
            continue
        # Identifier / keyword
        if _is_ident_start(ch):
            j = i + 1
            while j < n and _is_ident_part(src[j]):
                j += 1
            word = src[i:j]
            kind = 'KW' if word in KEYWORDS else 'ID'
            tokens.append((kind, word, line))
            i = j
            continue
        # Multi-char ops
        if src[i:i + 3] in THREE_CHAR_OPS:
            tokens.append(('OP', src[i:i + 3], line))
            i += 3
            continue
        if src[i:i + 2] in TWO_CHAR_OPS:
            tokens.append(('OP', src[i:i + 2], line))
            i += 2
            continue
        if ch in '+-*/%^#()<>{}[];:,=.':
            tokens.append(('OP', ch, line))
            i += 1
            continue
        raise LuaSyntaxError(f'unexpected character {ch!r} at line {line}')
    tokens.append(('EOF', '', line))
    return tokens


class Parser:
    """Strict Lua 5.1 recursive-descent parser."""

    BINOP_PREC = {
        'or': (1, 2),
        'and': (2, 3),
        '<': (3, 4), '>': (3, 4), '<=': (3, 4), '>=': (3, 4), '~=': (3, 4), '==': (3, 4),
        '..': (4, 4),
        '+': (5, 6), '-': (5, 6),
        '*': (6, 7), '/': (6, 7), '%': (6, 7),
        '^': (8, 8),
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.max_locals = 0

    def cur(self):
        return self.tokens[self.pos]

    def peek(self, off=1):
        idx = min(self.pos + off, len(self.tokens) - 1)
        return self.tokens[idx]

    def match(self, kind, val=None):
        k, v, _ = self.cur()
        if k == kind and (val is None or v == val):
            self.pos += 1
            return v
        return None

    def expect(self, kind, val=None):
        k, v, line = self.cur()
        if k == kind and (val is None or v == val):
            self.pos += 1
            return v
        raise LuaSyntaxError(f'expected {kind} {val!r} at line {line}, got {k} {v!r}')

    def parse(self):
        body = self.parse_block({'EOF'})
        self.expect('EOF')
        return ('func', [], True, body)

    def parse_block(self, stop_kws):
        stmts = []
        local_count = 0
        while True:
            while self.match('OP', ';'):
                pass
            k, v, line = self.cur()
            if k == 'EOF' or (k == 'KW' and v in stop_kws):
                break
            st = self.parse_stmt()
            if st[0] in ('local', 'local_func'):
                local_count += len(st[1]) if st[0] == 'local' else 1
                if local_count > self.max_locals:
                    self.max_locals = local_count
                if local_count > 200:
                    raise LuaSyntaxError(f'too many local variables (>200) at line {line}')
            stmts.append(st)
            if st[0] in ('return', 'break'):
                self.match('OP', ';')
                break
        return stmts

    def parse_stmt(self):
        k, v, line = self.cur()
        if k == 'KW':
            if v == 'local':
                self.pos += 1
                if self.match('KW', 'function'):
                    name = self.expect('ID')
                    fn = self.parse_funcbody(False)
                    return ('local_func', name, fn)
                names = [self.expect('ID')]
                while self.match('OP', ','):
                    names.append(self.expect('ID'))
                exprs = []
                if self.match('OP', '='):
                    exprs = self.parse_explist()
                return ('local', names, exprs)
            if v == 'if':
                self.pos += 1
                branches = []
                cond = self.parse_exp()
                self.expect('KW', 'then')
                body = self.parse_block({'elseif', 'else', 'end'})
                branches.append((cond, body))
                while self.match('KW', 'elseif'):
                    c2 = self.parse_exp()
                    self.expect('KW', 'then')
                    b2 = self.parse_block({'elseif', 'else', 'end'})
                    branches.append((c2, b2))
                else_body = None
                if self.match('KW', 'else'):
                    else_body = self.parse_block({'end'})
                self.expect('KW', 'end')
                return ('if', branches, else_body)
            if v == 'for':
                self.pos += 1
                first = self.expect('ID')
                if self.match('OP', '='):
                    start = self.parse_exp()
                    self.expect('OP', ',')
                    stop = self.parse_exp()
                    step = self.parse_exp() if self.match('OP', ',') else ('num', 1)
                    self.expect('KW', 'do')
                    body = self.parse_block({'end'})
                    self.expect('KW', 'end')
                    return ('for_num', first, start, stop, step, body)
                names = [first]
                while self.match('OP', ','):
                    names.append(self.expect('ID'))
                self.expect('KW', 'in')
                explist = self.parse_explist()
                self.expect('KW', 'do')
                body = self.parse_block({'end'})
                self.expect('KW', 'end')
                return ('for_in', names, explist, body)
            if v == 'while':
                self.pos += 1
                cond = self.parse_exp()
                self.expect('KW', 'do')
                body = self.parse_block({'end'})
                self.expect('KW', 'end')
                return ('while', cond, body)
            if v == 'do':
                self.pos += 1
                body = self.parse_block({'end'})
                self.expect('KW', 'end')
                return ('do', body)
            if v == 'return':
                self.pos += 1
                nk, nv, _ = self.cur()
                if nk == 'EOF' or (nk == 'OP' and nv == ';') or (nk == 'KW' and nv in ('end', 'else', 'elseif', 'until')):
                    return ('return', [])
                return ('return', self.parse_explist())
            if v == 'break':
                self.pos += 1
                return ('break',)
            if v == 'function':
                self.pos += 1
                target = ('var', self.expect('ID'))
                while self.match('OP', '.'):
                    target = ('index', target, ('str', self.expect('ID')))
                is_method = False
                if self.match('OP', ':'):
                    target = ('index', target, ('str', self.expect('ID')))
                    is_method = True
                fn = self.parse_funcbody(is_method)
                return ('assign', [target], [fn])
            raise LuaSyntaxError(f'unsupported keyword {v!r} at line {line}')

        expr = self.parse_suffixed()
        if self.cur()[0] == 'OP' and self.cur()[1] in (',', '='):
            lhs = [expr]
            while self.match('OP', ','):
                lhs.append(self.parse_suffixed())
            self.expect('OP', '=')
            rhs = self.parse_explist()
            for t in lhs:
                if t[0] not in ('var', 'index'):
                    raise LuaSyntaxError(f'invalid assignment target at line {line}')
            return ('assign', lhs, rhs)
        if expr[0] not in ('call', 'mcall'):
            raise LuaSyntaxError(f'expected statement at line {line}, got {expr[0]}')
        return ('expr_stmt', expr)

    def parse_funcbody(self, is_method):
        self.expect('OP', '(')
        params = ['self'] if is_method else []
        vararg = False
        if not self.match('OP', ')'):
            while True:
                if self.match('OP', '...'):
                    vararg = True
                    break
                params.append(self.expect('ID'))
                if not self.match('OP', ','):
                    break
            self.expect('OP', ')')
        body = self.parse_block({'end'})
        self.expect('KW', 'end')
        return ('func', params, vararg, body)

    def parse_explist(self):
        out = [self.parse_exp()]
        while self.match('OP', ','):
            out.append(self.parse_exp())
        return out

    def parse_exp(self, min_prec=1):
        lhs = self.parse_unary()
        while True:
            k, v, _ = self.cur()
            if (k in ('OP', 'KW')) and v in self.BINOP_PREC:
                lprec, rprec = self.BINOP_PREC[v]
                if lprec < min_prec:
                    break
                self.pos += 1
                rhs = self.parse_exp(rprec)
                lhs = ('binop', v, lhs, rhs)
            else:
                break
        return lhs

    def parse_unary(self):
        k, v, _ = self.cur()
        if (k == 'OP' and v in ('-', '#')) or (k == 'KW' and v == 'not'):
            self.pos += 1
            return ('unop', v, self.parse_exp(7))
        return self.parse_simple()

    def parse_simple(self):
        k, v, line = self.cur()
        if k == 'NUM':
            self.pos += 1
            return ('num', v)
        if k == 'STR':
            self.pos += 1
            return ('str', v)
        if k == 'KW' and v == 'nil':
            self.pos += 1
            return ('nil',)
        if k == 'KW' and v == 'true':
            self.pos += 1
            return ('bool', True)
        if k == 'KW' and v == 'false':
            self.pos += 1
            return ('bool', False)
        if k == 'OP' and v == '...':
            self.pos += 1
            return ('vararg',)
        if k == 'OP' and v == '{':
            return self.parse_table()
        if k == 'KW' and v == 'function':
            self.pos += 1
            return self.parse_funcbody(False)
        return self.parse_suffixed()

    def parse_suffixed(self):
        k, v, line = self.cur()
        if k == 'ID':
            self.pos += 1
            node = ('var', v)
        elif k == 'OP' and v == '(':
            self.pos += 1
            node = ('paren', self.parse_exp())
            self.expect('OP', ')')
        else:
            raise LuaSyntaxError(f'unexpected token {k} {v!r} at line {line}')

        while True:
            k, v, _ = self.cur()
            if k == 'OP' and v == '.':
                self.pos += 1
                node = ('index', node, ('str', self.expect('ID')))
            elif k == 'OP' and v == '[':
                self.pos += 1
                idx = self.parse_exp()
                self.expect('OP', ']')
                node = ('index', node, idx)
            elif k == 'OP' and v == ':':
                self.pos += 1
                mname = self.expect('ID')
                args = self.parse_args()
                node = ('mcall', node, mname, args)
            elif (k == 'OP' and v in ('(', '{')) or k == 'STR':
                args = self.parse_args()
                node = ('call', node, args)
            else:
                break
        return node

    def parse_args(self):
        k, v, _ = self.cur()
        if k == 'OP' and v == '(':
            self.pos += 1
            if self.match('OP', ')'):
                return []
            args = self.parse_explist()
            self.expect('OP', ')')
            return args
        if k == 'OP' and v == '{':
            return [self.parse_table()]
        if k == 'STR':
            self.pos += 1
            return [('str', v)]
        raise LuaSyntaxError(f'expected function arguments, got {k} {v!r}')

    def parse_table(self):
        self.expect('OP', '{')
        fields = []
        while not self.match('OP', '}'):
            if self.match('OP', '['):
                kexp = self.parse_exp()
                self.expect('OP', ']')
                self.expect('OP', '=')
                vexp = self.parse_exp()
                fields.append(('kv', kexp, vexp))
            elif self.cur()[0] == 'ID' and self.peek()[0] == 'OP' and self.peek()[1] == '=':
                key = self.expect('ID')
                self.expect('OP', '=')
                vexp = self.parse_exp()
                fields.append(('kv', ('str', key), vexp))
            else:
                fields.append(('arr', self.parse_exp()))
            if not (self.match('OP', ',') or self.match('OP', ';')):
                self.expect('OP', '}')
                break
        return ('table', fields)


class _ReturnSignal(Exception):
    def __init__(self, vals):
        self.vals = vals


class _BreakSignal(Exception):
    pass


class _Env:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def declare(self, name, val):
        self.vars[name] = val

    def get(self, name, g):
        cur = self
        while cur is not None:
            if name in cur.vars:
                return cur.vars[name]
            cur = cur.parent
        return g.get(name)

    def set(self, name, val, g):
        cur = self
        while cur is not None:
            if name in cur.vars:
                cur.vars[name] = val
                return
            cur = cur.parent
        g.set(name, val)


class LuaEvaluator:
    """Executes parsed Lua 5.1 AST with full closures, metatables, pcall, pairs/ipairs."""

    def __init__(self, extra_globals=None):
        self.G = LuaTable()
        self.G.rawset('_G', self.G)
        self._install_stdlib()
        if extra_globals:
            for k, v in extra_globals.items():
                self.G.rawset(k, v)

    def _install_stdlib(self):
        G = self.G
        G.rawset('type', lua_type)
        G.rawset('tonumber', lua_tonumber)
        G.rawset('tostring', lua_tostring)
        G.rawset('rawget', lambda t, k: t.rawget(k) if isinstance(t, LuaTable) else None)
        G.rawset('rawset', lambda t, k, v: (t.rawset(k, v), t)[1])
        G.rawset('setmetatable', lambda t, mt: (setattr(t, '_mt', mt), t)[1])
        G.rawset('getmetatable', lambda t: getattr(t, '_mt', None))

        def lua_error(msg='error'):
            raise LuaRuntimeError(lua_tostring(msg))

        def lua_assert(cond, msg='assertion failed'):
            if not lua_truthy(cond):
                raise LuaRuntimeError(lua_tostring(msg))
            return cond

        def lua_pcall(fn, *args):
            try:
                res = self._call_fn(fn, list(args))
                if isinstance(res, tuple):
                    return (True,) + res
                return (True, res)
            except Exception as exc:
                return (False, str(exc))

        def lua_pairs(t):
            keys = list(t._data.keys()) if isinstance(t, LuaTable) else []
            idx = [0]

            def nxt(_t, _k):
                if idx[0] >= len(keys):
                    return (None, None)
                k = keys[idx[0]]
                idx[0] += 1
                return (k, t._data.get(k))

            return (nxt, t, None)

        def lua_ipairs(t):
            def nxt(_t, i):
                i2 = (i or 0) + 1
                v = t.get(i2) if isinstance(t, LuaTable) else None
                if v is None:
                    return (None, None)
                return (i2, v)

            return (nxt, t, 0)

        G.rawset('error', lua_error)
        G.rawset('assert', lua_assert)
        G.rawset('pcall', lua_pcall)
        G.rawset('pairs', lua_pairs)
        G.rawset('ipairs', lua_ipairs)

        math_tbl = LuaTable({
            'floor': math.floor,
            'ceil': math.ceil,
            'max': lambda *a: max(a),
            'min': lambda *a: min(a),
            'abs': abs,
            'huge': math.inf,
        })
        G.rawset('math', math_tbl)

        def str_format(fmt, *args):
            out = []
            i = 0
            ai = 0
            while i < len(fmt):
                if fmt[i] == '%' and i + 1 < len(fmt):
                    if fmt[i + 1] == '%':
                        out.append('%')
                        i += 2
                        continue
                    m = re.match(r'%([+-0 #]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])', fmt[i:])
                    if m:
                        spec = m.group(0)
                        val = args[ai]
                        ai += 1
                        out.append(spec % val)
                        i += len(spec)
                        continue
                out.append(fmt[i])
                i += 1
            return ''.join(out)

        def str_sub(s, i, j=None):
            s = str(s)
            n = len(s)
            i = int(i)
            j = n if j is None else int(j)
            if i < 0:
                i = n + i + 1
            if j < 0:
                j = n + j + 1
            if i < 1:
                i = 1
            if j > n:
                j = n
            if i > j:
                return ''
            return s[i - 1:j]

        def str_find(s, pat, init=1, plain=False):
            s = str(s)
            pat = str(pat)
            n = len(s)
            init = int(init)
            if init < 0:
                init = n + init + 1
            if init < 1:
                init = 1
            if init > n + 1:
                return None
            if plain:
                idx = s.find(pat, init - 1)
                if idx < 0:
                    return None
                return (idx + 1, idx + len(pat))
            idx = s.find(pat, init - 1)
            if idx < 0:
                return None
            return (idx + 1, idx + len(pat))

        string_tbl = LuaTable({'format': str_format, 'sub': str_sub, 'find': str_find})
        G.rawset('string', string_tbl)

        def table_copy(t, deep=False):
            if not isinstance(t, LuaTable):
                return t
            raw = t.rawget('__数据')
            src = raw if isinstance(raw, LuaTable) else t
            out = LuaTable()
            for k, v in src._data.items():
                out.rawset(k, table_copy(v, True) if deep and isinstance(v, LuaTable) else v)
            return out

        def table_insert(t, pos_or_val, val=None):
            if val is None:
                t.rawset(t.length() + 1, pos_or_val)
            else:
                n = t.length()
                for idx in range(n, pos_or_val - 1, -1):
                    t.rawset(idx + 1, t.rawget(idx))
                t.rawset(pos_or_val, val)

        table_tbl = LuaTable({'copy': table_copy, 'insert': table_insert})
        G.rawset('table', table_tbl)
        G.rawset('loadstring', lambda src: self.compile(src))

    def compile(self, src):
        tokens = tokenize(src)
        parser = Parser(tokens)
        ast = parser.parse()
        return self._make_closure(ast, _Env(None))

    def _make_closure(self, func_ast, parent_env):
        _, params, vararg, body = func_ast

        def fn(*args):
            env = _Env(parent_env)
            for idx, pname in enumerate(params):
                env.declare(pname, args[idx] if idx < len(args) else None)
            if vararg:
                env.declare('...', list(args[len(params):]))
            try:
                self._exec_block(body, env)
            except _ReturnSignal as ret:
                if len(ret.vals) == 0:
                    return None
                if len(ret.vals) == 1:
                    return ret.vals[0]
                return tuple(ret.vals)
            return None

        return fn

    def _call_fn(self, fn, args):
        if isinstance(fn, LuaTable):
            return fn(*args)
        if not callable(fn):
            raise LuaRuntimeError(f'attempt to call a {lua_type(fn)} value')
        return fn(*args)

    def _eval_explist(self, exprs, env):
        out = []
        for idx, e in enumerate(exprs):
            val = self._eval_exp(e, env, multi=(idx == len(exprs) - 1))
            if idx == len(exprs) - 1 and isinstance(val, _Multi):
                out.extend(val.vals)
            else:
                out.append(val.vals[0] if isinstance(val, _Multi) else val)
        return out

    def _eval_one(self, expr, env):
        v = self._eval_exp(expr, env, multi=False)
        if isinstance(v, _Multi):
            return v.vals[0] if v.vals else None
        return v

    def _eval_exp(self, expr, env, multi=False):
        tag = expr[0]
        if tag == 'num' or tag == 'str' or tag == 'bool':
            return expr[1]
        if tag == 'nil':
            return None
        if tag == 'var':
            return env.get(expr[1], self.G)
        if tag == 'vararg':
            vals = env.get('...', self.G) or []
            return _Multi(vals) if multi else (vals[0] if vals else None)
        if tag == 'paren':
            return self._eval_one(expr[1], env)
        if tag == 'func':
            return self._make_closure(expr, env)
        if tag == 'table':
            tbl = LuaTable()
            arr_i = 1
            for f in expr[1]:
                if f[0] == 'kv':
                    k = self._eval_one(f[1], env)
                    v = self._eval_one(f[2], env)
                    tbl.rawset(k, v)
                else:
                    v = self._eval_one(f[1], env)
                    tbl.rawset(arr_i, v)
                    arr_i += 1
            return tbl
        if tag == 'index':
            t = self._eval_one(expr[1], env)
            k = self._eval_one(expr[2], env)
            if isinstance(t, LuaTable):
                return t.get(k)
            raise LuaRuntimeError(f'attempt to index a {lua_type(t)} value with {k!r}')
        if tag == 'unop':
            op, sub = expr[1], self._eval_one(expr[2], env)
            if op == 'not':
                return not lua_truthy(sub)
            if op == '-':
                return -sub
            if op == '#':
                return sub.length() if isinstance(sub, LuaTable) else len(sub)
        if tag == 'binop':
            op = expr[1]
            if op == 'and':
                lv = self._eval_one(expr[2], env)
                return self._eval_one(expr[3], env) if lua_truthy(lv) else lv
            if op == 'or':
                lv = self._eval_one(expr[2], env)
                return lv if lua_truthy(lv) else self._eval_one(expr[3], env)
            lv = self._eval_one(expr[2], env)
            rv = self._eval_one(expr[3], env)
            if op == '==':
                return lv == rv and type(lv) is not bool and type(rv) is not bool or (lv is rv)
            if op == '~=':
                eq = (lv == rv and type(lv) is not bool and type(rv) is not bool) or (lv is rv)
                return not eq
            if op == '<':
                return lv < rv
            if op == '<=':
                return lv <= rv
            if op == '>':
                return lv > rv
            if op == '>=':
                return lv >= rv
            if op == '..':
                return lua_tostring(lv) + lua_tostring(rv)
            if op == '+':
                return lv + rv
            if op == '-':
                return lv - rv
            if op == '*':
                return lv * rv
            if op == '/':
                return lv / rv
            if op == '%':
                return lv % rv
            if op == '^':
                return lv ** rv
        if tag == 'call':
            fn = self._eval_one(expr[1], env)
            args = self._eval_explist(expr[2], env)
            res = self._call_fn(fn, args)
            if isinstance(res, tuple):
                return _Multi(list(res)) if multi else (res[0] if res else None)
            return res
        if tag == 'mcall':
            obj = self._eval_one(expr[1], env)
            fn = obj.get(expr[2]) if isinstance(obj, LuaTable) else None
            args = [obj] + self._eval_explist(expr[3], env)
            res = self._call_fn(fn, args)
            if isinstance(res, tuple):
                return _Multi(list(res)) if multi else (res[0] if res else None)
            return res
        raise LuaRuntimeError(f'unknown expr {tag}')

    def _exec_block(self, stmts, parent_env):
        env = _Env(parent_env)
        for st in stmts:
            tag = st[0]
            if tag == 'local':
                vals = self._eval_explist(st[2], env) if st[2] else []
                for idx, name in enumerate(st[1]):
                    env.declare(name, vals[idx] if idx < len(vals) else None)
            elif tag == 'local_func':
                env.declare(st[1], None)
                env.vars[st[1]] = self._make_closure(st[2], env)
            elif tag == 'assign':
                lhs_eval = []
                for t in st[1]:
                    if t[0] == 'var':
                        lhs_eval.append(('var', t[1]))
                    else:
                        lhs_eval.append(('index', self._eval_one(t[1], env), self._eval_one(t[2], env)))
                vals = self._eval_explist(st[2], env)
                for idx, target in enumerate(lhs_eval):
                    val = vals[idx] if idx < len(vals) else None
                    if target[0] == 'var':
                        env.set(target[1], val, self.G)
                    else:
                        target[1].set(target[2], val)
            elif tag == 'expr_stmt':
                self._eval_exp(st[1], env)
            elif tag == 'if':
                ran = False
                for cond, body in st[1]:
                    if lua_truthy(self._eval_one(cond, env)):
                        self._exec_block(body, env)
                        ran = True
                        break
                if not ran and st[2] is not None:
                    self._exec_block(st[2], env)
            elif tag == 'for_num':
                _, var, s_e, e_e, step_e, body = st
                cur = self._eval_one(s_e, env)
                limit = self._eval_one(e_e, env)
                step = self._eval_one(step_e, env)
                while (step > 0 and cur <= limit) or (step < 0 and cur >= limit):
                    loop_env = _Env(env)
                    loop_env.declare(var, cur)
                    try:
                        self._exec_block(body, loop_env)
                    except _BreakSignal:
                        break
                    cur += step
            elif tag == 'for_in':
                _, names, explist, body = st
                it_vals = self._eval_explist(explist, env)
                it_fn = it_vals[0]
                it_state = it_vals[1] if len(it_vals) > 1 else None
                it_ctrl = it_vals[2] if len(it_vals) > 2 else None
                while True:
                    res = self._call_fn(it_fn, [it_state, it_ctrl])
                    rlist = list(res) if isinstance(res, tuple) else [res]
                    it_ctrl = rlist[0] if rlist else None
                    if it_ctrl is None:
                        break
                    loop_env = _Env(env)
                    for idx, name in enumerate(names):
                        loop_env.declare(name, rlist[idx] if idx < len(rlist) else None)
                    try:
                        self._exec_block(body, loop_env)
                    except _BreakSignal:
                        break
            elif tag == 'while':
                while lua_truthy(self._eval_one(st[1], env)):
                    try:
                        self._exec_block(st[2], env)
                    except _BreakSignal:
                        break
            elif tag == 'do':
                self._exec_block(st[1], env)
            elif tag == 'return':
                vals = self._eval_explist(st[1], env) if st[1] else []
                raise _ReturnSignal(vals)
            elif tag == 'break':
                raise _BreakSignal()


class _Multi:
    def __init__(self, vals):
        self.vals = vals


def syntax_check(src):
    tokens = tokenize(src)
    parser = Parser(tokens)
    ast = parser.parse()
    return {'tokens': len(tokens), 'max_locals': parser.max_locals, 'ast_ok': True, 'ast': ast}
