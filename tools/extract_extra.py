import os, re, io, json, collections

EDITOR = 'E:/SteamLibrary/steamapps/common/BeamNG.drive/lua/ge/extensions/editor'
WORK = 'D:/Documents/Beamng/current/mods/_work'

# 已在词表中的条目
known = set()
import glob
for p in glob.glob(WORK + '/batch*.json') + glob.glob(WORK + '/agent/part*.json'):
    known |= set(json.load(io.open(p, encoding='utf-8')).keys())
zh_src = io.open(WORK + '/mod/lua/ge/extensions/zhcn/dictionary.lua', encoding='utf-8').read()
for m in re.finditer(r"\['((?:[^'\\]|\\.)*)'\] = '", zh_src):
    known.add(m.group(1))

PATTERNS = [
    r'displayName\s*=\s*"([^"\\]{2,80})"',
    r'displayName\s*=\s*\'([^\'\\]{2,80})\'',
    r'iconTooltip\s*=\s*"([^"\\]{2,90})"',
    r'iconTooltip\s*=\s*\'([^\'\\]{2,90})\'',
    r'auxShortcuts\[[^\]]*\]\s*=\s*"([^"\\]{2,90})"',
    r'auxShortcuts\[[^\]]*\]\s*=\s*\'([^\'\\]{2,90})\'',
    r'\bdescription\s*=\s*"([^"\\]{3,110})"',
    r'\btooltip\s*=\s*"([^"\\]{3,110})"',
]

found = collections.Counter()
for root, dirs, files in os.walk(EDITOR):
    for fn in files:
        if not fn.endswith('.lua'):
            continue
        txt = io.open(os.path.join(root, fn), encoding='utf-8', errors='replace').read()
        for pat in PATTERNS:
            for m in re.finditer(pat, txt):
                s = m.group(1).strip()
                if len(s) < 2 or '%' in s or s.startswith('#'):
                    continue
                if re.fullmatch(r'[a-z][A-Za-z0-9_]*', s):
                    continue
                found[s] += 1

new = [s for s in found if s not in known]
new.sort(key=lambda s: (-found[s], s))
print('总命中:', len(found), '新增待翻:', len(new))
io.open(WORK + '/slices/extra.txt', 'w', encoding='utf-8').write('\n'.join(new))
for s in new[:40]:
    print(' ', found[s], s)
