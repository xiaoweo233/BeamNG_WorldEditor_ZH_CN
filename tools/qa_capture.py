import mcp, time, io, re, json

MODES = ["createObject", "decalEditMode", "forestToolsEditMode", "terrainToolsEditMode",
         "roadArchitectEditMode", "roadEditMode", "meshRoadEditMode", "riverEditMode",
         "biomeEditMode", "assetBrowserEditMode", "drivePathSplineEditMode", "trailEditMode",
         "pathEditMode", "boundaryEditMode", "sitesEditMode", "raceEditMode",
         "biomeEditMode", "barriersSelection", "signalsEditMode", "notebookEditMode"]

for m in MODES:
    try:
        mcp.call('set_edit_mode', {'name': m}, timeout=20)
        print('->', m, flush=True)
    except Exception as e:
        print('skip', m, type(e).__name__, flush=True)
    time.sleep(1.1)

r = mcp.call('run_lua', {'code': "return table.concat(_G.__zhcnCapture or {}, '||')"}, timeout=30)
raw = r['result']['content'][0]['text']
items = [s for s in raw.split('||') if s]
print('captured raw:', len(items))

uniq = []
seen = set()
for s in items:
    if s not in seen:
        seen.add(s)
        uniq.append(s)
print('unique:', len(uniq))
io.open('D:/Documents/Beamng/current/mods/_work/captured_strings.txt', 'w', encoding='utf-8').write('\n'.join(uniq))

# 与词表比对
dictsrc = io.open('D:/Documents/Beamng/current/mods/_work/mod/lua/ge/extensions/zhcn/dictionary.lua', encoding='utf-8').read()
keys = set()
for mm in re.finditer(r"\['((?:[^'\\]|\\.)*)'\] = '", dictsrc):
    keys.add(mm.group(1))

missing = []
for s in uniq:
    vis = s.split('##')[0]
    if not vis or vis.startswith('#') or vis.strip() == '':
        continue
    if vis in keys:
        continue
    core = vis.strip()
    if core in keys:
        continue
    if not re.search('[A-Za-z]', vis):
        continue
    if '%' in vis or '{{' in vis:
        continue
    missing.append(vis)

print('字典未覆盖的可见文字:', len(missing))
io.open('D:/Documents/Beamng/current/mods/_work/missing.txt', 'w', encoding='utf-8').write('\n'.join(missing))
cjk = re.compile(r'[\u4e00-\u9fff]')
for s in missing[:45]:
    print('  ', repr(s))
