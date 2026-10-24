import json, io, re, sys

def strip_comments(s):
    out = []
    i = 0
    n = len(s)
    in_str = False
    esc = False
    while i < n:
        c = s[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == '/' and i + 1 < n and s[i+1] == '/':
            while i < n and s[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and s[i+1] == '*':
            i += 2
            while i + 1 < n and not (s[i] == '*' and s[i+1] == '/'):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    txt = ''.join(out)
    # remove trailing commas
    txt = re.sub(r',(\s*[}\]])', r'\1', txt)
    return txt

def load(p):
    with io.open(p, encoding='utf-8') as f:
        return json.loads(strip_comments(f.read()))

base = 'E:/SteamLibrary/steamapps/common/BeamNG.drive/locales/translations/'
en = load(base + 'en-US/main.translation.json')
zh = load(base + 'zh_Hans/main.translation.json')
print('en keys:', len(en), ' zh keys:', len(zh))
missing = [k for k in en if k not in zh]
print('missing:', len(missing))
cjk = re.compile(r'[\u4e00-\u9fff]')
untrans = []
for k, v in en.items():
    if not isinstance(v, str):
        continue
    zv = zh.get(k)
    if zv is None:
        continue
    # has latin words but no chinese => likely untranslated
    if len(v.strip()) > 2 and re.search(r'[A-Za-z]{3,}', v) and not cjk.search(str(zv)):
        untrans.append((k, v, zv))
print('likely untranslated (en text, zh has no CJK):', len(untrans))
prefix = {}
for k in missing:
    p = '.'.join(k.split('.')[:2])
    prefix[p] = prefix.get(p, 0) + 1
for p, c in sorted(prefix.items(), key=lambda x: -x[1])[:20]:
    print('  missing', p, c)
for k, v, zv in untrans[:15]:
    print('  UNTR', k, '|', str(v)[:60])
