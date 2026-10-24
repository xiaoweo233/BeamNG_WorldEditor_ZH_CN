import os, re, json, collections, io

EDITOR = 'E:/SteamLibrary/steamapps/common/BeamNG.drive/lua/ge/extensions/editor'
OUT = 'D:/Documents/Beamng/current/mods/_work'

# functions whose FIRST string arg is a user-visible label
LABEL_FN = set("""Button Text TextUnformatted TextWrapped TextDisabled BulletText Checkbox
MenuItem1 MenuItem Selectable1 Selectable RadioButton2 RadioButton InputText InputFloat InputInt
SliderFloat SliderInt InputFloat3 DragFloat Combo1 Combo Combo2 BeginCombo TableSetupColumn
BeginTabItem BeginMenu HeaderText SmallButton CollapsingHeader1 TreeNode1 TreeNodeEx1 Begin
SetTooltip TextColored SeparatorText BeginPopupModal ListBox LabelText""".split())

pat = re.compile(r'\b(?:imgui|im)\.(\w+)\(\s*"([^"\\]{1,160})"')
counts = collections.Counter()
fns = collections.defaultdict(set)

for root, dirs, files in os.walk(EDITOR):
    for fn in files:
        if not fn.endswith('.lua'):
            continue
        p = os.path.join(root, fn)
        txt = io.open(p, encoding='utf-8', errors='replace').read()
        for m in pat.finditer(txt):
            name, s = m.group(1), m.group(2)
            if name not in LABEL_FN:
                continue
            if not re.search(r'[A-Za-z]', s):
                continue
            if '%' in s or '{{' in s:
                continue
            if s.startswith('/') or re.match(r'^[a-z0-9_]+\.(lua|json|png|dds|jpg)$', s):
                continue
            counts[s] += 1
            fns[s].add(name)

items = [{"en": s, "n": c, "fn": sorted(fns[s])} for s, c in counts.most_common()]
with io.open(OUT + '/items.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=0)

tot = sum(counts.values())
print('unique:', len(items), 'uses:', tot)
for it in items[:70]:
    print(it['n'], repr(it['en']))
