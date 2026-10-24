# BeamNG.drive 世界编辑器汉化 · 交接文档

> 给接手这个项目的 AI / 人看的操作手册。读完这一份就能继续补汉化、适配游戏更新。
> 最后更新：2026-10-24 · 对应产物 **v1.0.2**（6,567 条词条）

---

## 0. 一句话现状

已经做完：**世界编辑器（World Editor）**的界面汉化，通过运行时拦截 `ui_imgui` 实现，不改游戏任何原文件。
产物是 `mods/BeamNG_WorldEditor_ZH_CN_v1.0.2.zip`，已在游戏内冷启动 + 热重载双重验证通过。
还没做完：长尾词条（少量工具面板深层参数）、游戏更新后新增的字符串。

---

## 1. 环境事实（改之前先确认这些）

| 项 | 值 |
|---|---|
| 游戏版本 | BeamNG.drive **0.40.3.0.290897** RELEASE Direct3D12 |
| 游戏安装目录 | `E:\SteamLibrary\steamapps\common\BeamNG.drive` |
| 用户数据目录（= mods 所在） | `D:\Documents\Beamng\current` |
| 模组安装目录 | `D:\Documents\Beamng\current\mods` |
| 编辑器扩展源码（读参考用） | `E:\...\BeamNG.drive\lua\ge\extensions\editor`（154 个文件） |
| 工程/工作目录 | `D:\Documents\Beamng\current\mods\_work` |
| 游戏内 MCP 服务 | `http://127.0.0.1:29292/mcp`（**端口会自动顺延**，29292→29293→…见 §7.1） |
| MCP 开关 | 游戏内 选项 → 启用 MCP 服务器（已开） |
| 运行环境 | Python `C:\Users\feng\.workbuddy\binaries\python\versions\3.13.12\python.exe` |

**重要前提**：游戏窗口**失焦时 ImGui 不重绘**，此时 MCP 会超时、运行时捕获抓不到东西。
需要画面/捕获时，先用 `_work/cap3.ps1` 把窗口调前台再操作。

---

## 2. 产物结构与每个文件的作用

zip 内（**必须文件在根目录，不能套一层文件夹**）：

```
lua/ge/extensions/editor/zhcnLocalization.lua   汉化层本体（主加载点，~380 行）
lua/ge/extensions/zhcn/dictionary.lua           词表（自动生成，勿手改，改批次 JSON）
scripts/modScript.lua                           备用加载入口（解包安装 / 其他版本兜底）
mod_info/ZHCNEditorLoc/info.json                模组信息（文件夹名必须纯字母数字！）
README.md                                        给玩家看的说明
```

- `mod_info/<ID>/info.json` 的 `<ID>` 会被 `modmanager.lua:121` 用 `^/?mod_info/([0-9a-zA-Z]*)/info%.json` 匹配，
  **只能用字母数字**（当前 `ZHCNEditorLoc`），否则模组信息读不到。
- 模组在 modmanager 里的 key 是**zip 文件名小写**：`beamng_worldeditor_zh_cn_v1.0.2`（重命名 zip 会变！）。

---

## 3. 工作原理（为什么这么设计）

### 3.1 为什么必须拦截
世界编辑器的 UI 是 **Lua 驱动的 ImGui 即时渲染**。全编辑器只有 80 处 `_tr()` 调用且官方中文包早已翻好，
剩下 6000+ 条界面文字是**硬编码在 Lua 里直接丢给 ImGui** 的，因此只能运行时拦截文本接口。

### 3.2 拦截点：全局表 `ui_imgui`
所有编辑器模块都写 `local imgui = ui_imgui`（表引用，不是函数引用），所以**替换表里的函数字段**就能
全量生效，无需改任何游戏文件。分两组处理：

| 组 | 函数 | 输出格式 |
|---|---|---|
| `TEXT_FNS`（纯文本） | Text / TextUnformatted / TextWrapped / TextDisabled / BulletText / SetTooltip / SeparatorText / HeaderText / LabelText / TableSetupColumn | 直接输出中文，**绝不追加 `##`** |
| `WIDGET_FNS`（控件） | Button / SmallButton / Checkbox / MenuItem1 / MenuItem / Selectable1 / Selectable / RadioButton2 / RadioButton / InputText / InputFloat / InputInt / InputFloat3 / SliderFloat / SliderInt / DragFloat / Combo1 / Combo / Combo2 / BeginCombo / CollapsingHeader1 / CollapsingHeader / TreeNode1 / TreeNode / TreeNodeEx1 / TreeNodeEx / BeginTabItem / BeginMenu / ListBox | `中文##英文原文` |

另外两个特例：`TextColored`（标签在第 2 个参数）、`Begin`（窗口标题，兼作 ImGui 窗口 ID）。

> **为什么控件要加 `##英文原文`**：ImGui 只显示 `##` 之前的内容，但控件 ID 按整串哈希。
> 这样既显示中文，又保证「两个不同英文标签 → 同一个中文」时 ID 依然不同，不会串号。
> **为什么纯文本不能加**：Text 类接口会把 `##` 当普通字符画出来（曾经的 `删除##Delete` 事故）。

### 3.3 四种匹配手段（按优先级）
1. **精确词表**：`M.words['英文'] = '中文'`
2. **动态规则**：`M.rules`，共 **21** 条 Lua pattern，处理拼接出来的文字
   （`^Path:%s*(.*)$`、`^Level:%s*(.*)$`、`^EditMode:%s*(.*)$`、`^Size:%s*(.*)$`、`^Default Value:%s*(.*)$`、`^FPS:%s*(.*)$` …）
3. **快捷键拼接**：`"Ctrl  Fine Rotation/Scale"` 这种「按键 + 双空格 + 说明」只翻后半段
4. **术语组合兜底**：`M.terms` 里 **214** 个单词级术语（lane=车道、width=宽度…），
   词表未命中且 ≤5 个词的短标签按术语拼接，如 `Sidewalk Corner Radius` → `人行道转角半径`

> 兜底只在「整条都由已知术语组成」时才用，避免产出半中半英的垃圾。

### 3.4 两个必须知道的特殊处理
- **多行文本按行翻译**：偏好设置提示是 `说明\nPath: …\nType: …\nDefault Value: …` 的单串，
  先按 `\n` 拆行，逐行翻译再拼回（见 `translateLabel` 开头）。
- **缺字形字体跳过**：`cairo_regular_medium` / `cairo_bold` / `robotomono_regular` 这三个字体
  **没有烘焙中文字形**，用于其中文字会显示 `????`。做法是包装 `PushFont3` / `PopFont` 维护字体栈，
  这些字体激活期间直接返回原文（`M.config.cjklessFonts`）。代价：极少数标题保持英文。

### 3.5 加载链路（这里踩过大坑，务必理解）
BeamNG 官方机制 `scripts/modScript.lua` 在 0.40.3 里**读不了 zip 内文件**：
`dofile('/scripts/modScript.lua')` 报 `cannot open …: Result too large / No error`。
（`loadfile` 和 `require` 读 zip 内文件都正常，唯独 `dofile` 不行。）

所以主加载点改为**编辑器自带的目录扫描**：

```
lua/ge/extensions/editor/main.lua: loadAllEditorExtensions()
  → FS:findFiles('/lua/ge/extensions/editor/', '*.lua', 0, false, false)
  → 文件内容含 "M.onEditor" 或 "M.onExtension" 才算编辑器扩展
  → extensions.load('editor_' .. 文件名)
```

因此汉化层放在 `lua/ge/extensions/editor/zhcnLocalization.lua`，扩展名 `editor_zhcnLocalization`，
里面提供 `M.onEditorInitialized` / `M.onEditorGui`（后者每帧幂等补装，防加载顺序问题）。

同理**词表用 `loadfile` 直读**而不是 `require`：`require` 有模块缓存，换词表后 `reload()` 读到旧内容
（这个坑导致过「明明改了词表却没生效」）。

---

## 4. 工程目录清单（`mods/_work`）

| 文件 | 作用 | 用不用 |
|---|---|---|
| `mod/` | **打包源目录**（改这里，`build.py` 从这里打 zip） | ✅ 手改 |
| `batch1~12_*.json` | 我逐批人工翻译的词条（按主题分） | ✅ 可增补 |
| `agent/*.json` | 子 agent 分片翻译结果（part/ui/gap/sent/classes/extra） | 只读 |
| `gen_dict.py` | **合并所有批次 → 生成 `dictionary.lua`**（含术语表、规则、手工补丁） | ✅ 必跑 |
| `build.py` | 打包成 zip（含 README、清理旧版本、modScript 用 STORED 存档） | ✅ 必跑 |
| `mcp.py` | 游戏 MCP 客户端（自动选端口、自动重试） | ✅ 常用 |
| `cap3.ps1` | 截取游戏窗口真实画面（含 ImGui 层，**引擎自带截图不含 ImGui**） | ✅ 常用 |
| `analyze_tr.py` | 分析官方 zh_Hans 覆盖情况（历史用途） | 备用 |
| `extract.py` | 扫 `im.*` 首参字面量 → `items.json` | 备用 |
| `extract_extra.py` | 扫 `displayName/iconTooltip/auxShortcuts` | 备用 |
| `qa_capture.py` | 遍历所有编辑模式做运行时捕获 + 缺口比对 | ✅ 常用 |
| `mkdev.py` / `dev_reload.lua` | 生成单文件热重载版（历史用途，现用 §6.5 的方式） | 备用 |
| `slices/` | 待翻译分片（送 agent 的输入） | 临时 |
| `items.json` | 全部 UI 字面量 + 出现次数（词表校验基准） | 只读 |

---

## 5. 词表是怎么攒起来的（批次对照）

| 批次 | 内容 | 条数 |
|---|---|---|
| `batch1~4` | 高频通用：按钮/字段/对话框/面板（人工逐条） | ~620 |
| `agent/part0~3.json` | 全量 UI 字面量分片（4 个 agent 并行） | 2,195 |
| `batch5_windows` | 60+ 个窗口标题 | 78 |
| `batch6_ui` / `batch7_extra` / `batch8_prefs` | 检查器字段、工具名、偏好分类 | ~90 |
| `agent/extra.json` | 工具栏名称/tooltip/快捷键说明 | 204 |
| `agent/gap0~1.json` | 全模式运行时捕获的缺口 | 279 |
| `batch9~11` | 窗口菜单、贴图槽、杂项 | ~60 |
| `batch12_desc` | 偏好设置长说明（人工） | 60 |
| `agent/ui0~3.json` | 放宽提取范围后的材质/工具面板标签 | 1,554 |
| `agent/classes.json` | **195 个 SimObject 类名** → `中文（English）` | 195 |
| `agent/sent0~2.json` | 句子级提示/警告/说明 | 859 |

合计 **6,567** 条（`gen_dict.py` 输出会打印实际数字）。

---

## 6. 标准工作流：补一批新的汉化

### 6.1 三种找缺口的方法

**A. 静态扫描（覆盖最全，推荐先做）**
```bash
cd D:/Documents/Beamng/current/mods/_work
# 扫「任意函数调用的第一个字符串参数」+ 句子级字面量
"C:/Users/feng/.workbuddy/binaries/python/versions/3.13.12/python.exe" - <<'PY'
import os, re, io, glob, json
EDITOR='E:/SteamLibrary/steamapps/common/BeamNG.drive/lua/ge/extensions/editor'
known=set()
for p in glob.glob('batch*.json')+glob.glob('agent/*.json'):
    known |= set(json.load(io.open(p,encoding='utf-8')).keys())
cand={}
for root,d,fs in os.walk(EDITOR):
    for fn in fs:
        if not fn.endswith('.lua'): continue
        t=io.open(os.path.join(root,fn),encoding='utf-8',errors='replace').read()
        for m in re.finditer(r'\b\w+\s*\(\s*"([^"\\\n]{2,120})"', t):      # 任意调用首参
            s=m.group(1)
            if re.search('[A-Za-z]',s) and '%' not in s and not s.startswith('/'): cand[s]=1
        for m in re.finditer(r'"([^"\\\n]{25,400})"', t):                   # 句子级
            s=m.group(1)
            if s.count(' ')>=2 and '%' not in s and '..' not in s: cand[s]=1
todo=sorted({s.split('##')[0].strip() for s in cand} - known)
io.open('slices/new_gap.txt','w',encoding='utf-8').write('\n'.join(todo))
print('待翻', len(todo))
PY
```

**B. 运行时捕获（最贴近实际显示）**
```bash
# 1) 打开捕获（会清缓存，让所有字符串重新走一遍）
python mcp.py run_lua "{\"code\":\"local m=extensions.editor_zhcnLocalization m.capture(true) return 1\"}"
# 2) 用 cap3.ps1 把游戏调前台，手动/用 set_edit_mode 切几个面板，等 2~3 秒
powershell -File cap3.ps1
# 3) 取回并和词表比对
python qa_capture.py     # 已封装：输出 missing*.txt
```
> 缓存机制：`translateLabel` 命中缓存就不再记录，所以 `capture(true)` 会先清缓存。

**C. 看截图**：用户给截图时，直接 `m.debugTranslate('看到的英文')` 判断是否命中，没命中就补词表。

### 6.2 分片翻译（用子 agent 并行）

把 `slices/new_gap.txt` 按 300~450 条切片，每个 agent 一份，输出到 `agent/xxxN.json`。
**prompt 模板**（照抄，术语表按主题改）：

```
把 BeamNG.drive 世界编辑器界面英文字符串翻译成简体中文，输出 JSON。
输入：<绝对路径>/slices/xxx0.txt（每行一个）
输出：<绝对路径>/agent/xxx0.json
格式：JSON 对象，key=原文（逐字符一致，含尾随空格），value=简体中文。
要求：
1. 术语统一：terrain 地形、road 道路、lane 车道、spline 样条、decal 贴花、prefab 预制体、
   forest 森林、mesh 网格、material 材质、texture 贴图、node 节点、gizmo 操作手柄、
   asset 资源、thumbnail 缩略图、mission 任务、level 关卡、navgraph 导航图。
2. 保留尾随空格/冒号/省略号；保留 %s %d {{x}} 占位符。
3. 长句通顺翻译，不要逐词硬译。
4. 纯标识符/路径/正则 跳过不输出。
执行：用 Python(路径见上) 写 JSON（ensure_ascii=False, indent=1）并 json.load 校验。
只回报：路径、行数、key 数、跳过数。不要回 JSON 内容。
```

### 6.3 合并 + 打包
```bash
cd D:/Documents/Beamng/current/mods/_work
"C:/Users/feng/.workbuddy/binaries/python/versions/3.13.12/python.exe" gen_dict.py   # 打印最终条数
"C:/Users/feng/.workbuddy/binaries/python/versions/3.13.12/python.exe" build.py      # 生成 zip
```
- `gen_dict.py` 会自动：合并 → 去重（冲突保留先出现的）→ 补 `strip()` 变体键 → 注入手写补丁 → 转义 → 写 `dictionary.lua`
- **改版本号要同时改 3 处**：`build.py` 的 `NAME`/README 文本、`mod_info/.../info.json` 的 `version_string`/`filename`
- `build.py` 会删掉旧版本 zip（注意：删正在被挂载的 zip 会让游戏报 `Invalid ZIP file`，见 §7.4）

### 6.4 热验证（不重启游戏，30 秒见效）
```bash
python mcp.py run_lua "{\"code\":\"local ok,d=pcall(dofile,'/mods/_work/mod/lua/ge/extensions/zhcn/dictionary.lua') if not ok then return 'FAIL '..tostring(d) end _G.__zhcnEditorDict,_G.__zhcnEditorTerms,_G.__zhcnEditorRules=d.words,d.terms,d.rules local m=extensions.editor_zhcnLocalization m.uninstall() local n=m.reload() m.install() return 'dict='..n\"}"
```
> `/mods/_work/...` 是 VFS 路径（用户数据目录 = VFS 根），`dofile` 对**散装文件**是可用的。
> 用 `_G.__zhcnEditorDict` 注入会**跳过读文件**，所以验证「打包后的 zip 是否正常」时**必须先清掉这三个全局**。

### 6.5 让运行中的游戏用上新 zip（免重启）
```lua
local mm = extensions.core_modmanager
mm.deactivateMod('beamng_worldeditor_zh_cn_v1.0.2', true, true)
mm.activateMod('beamng_worldeditor_zh_cn_v1.0.2')
-- 然后 reload 词表（此时要清掉 __zhcnEditorDict 等全局，才会读 zip 里的新文件）
```
key = zip 文件名小写；换新版本号后 key 也要改。

### 6.6 冷启动验证（最终验收）
重启游戏 → 进编辑器 → 检查三件事：
1. 日志里有 `GELua.zhcn_editorLoc | 世界编辑器汉化已启用：6567 条词条`
   ```bash
   python mcp.py get_logs '{"lines":200}'   # 或直接看 D:/Documents/Beamng/current/beamng.log
   ```
2. `extensions.editor_zhcnLocalization` 存在且 `stats().dictSize == 期望条数`
3. 截图确认（`cap3.ps1`）菜单栏中文、场景树/检查器中文、底部快捷键条中文

---

## 7. 踩过的坑（照这个排查，能省几小时）

### 7.1 MCP 连不上 / 超时
- 端口会顺延：`29292` 被占后游戏会绑 `29293`、`29294`…（看日志 `MCP listening on http://127.0.0.1:XXXX/mcp`）
- 旧端口 socket 可能仍 LISTENING 但已死，表现就是「连上但不回包」→ `mcp.py` 已实现逐端口尝试
- **游戏窗口失焦时 Lua/ImGui 不跑，MCP 会超时**——不是服务挂了，先 `cap3.ps1` 调前台

### 7.2 引擎自带截图不含 ImGui 层
`mcp screenshot` / `screenshot_image` 只截 3D 画面，编辑器面板一个都看不到。
必须用 `cap3.ps1`（EnumWindows 找进程最大窗口 → 置前 → CopyFromScreen）。
若返回 `160x28` 说明窗口最小化/句柄刚重建，重跑一次即可。

### 7.3 界面出现 `中文##英文` 后缀
两种原因：
1. 该字符串走的是**纯文本接口**却被当成控件处理 → 把它加进 `TEXT_FNS` 而不是 `WIDGET_FNS`
   （已踩：`TableSetupColumn` 是表头，原样显示 `##`；`LabelText` 同理）
2. **多层包装**：反复 `install()` 没 `uninstall()`，外层翻完内层再翻一次，后缀就暴露了。
   规范做法：`m.uninstall(); m.reload(); m.install()`，或直接 `reload_lua`。

### 7.4 `Invalid ZIP file: /mods/xxx.zip`
把**正在挂载**的 zip 删了/改了。解决：`initDB()` 重扫或重启游戏；`build.py` 删旧版本前最好先 `deactivateMod`。

### 7.5 改了词表但界面没变
`require` 模块缓存（`package.loaded['zhcn/dictionary']`）会返回旧表。
现在代码已改成 `loadfile` 直读，但如果你在 Lua 里手动 `require` 就会复现。用 `m.reload()` 而不是 `require`。

### 7.6 标题变成 `???????`
该文字用 `cairo_regular_medium`（无中文字形）。已由字体栈机制自动跳过 → 保持英文是正确的，
**不要**为了「全中文」强行翻译，否则只会有乱码。

### 7.7 `modScript.lua` 一直报 `cannot open … Result too large`
zip 内 `dofile` 不可用（0.40.3 特性）。不用管，主加载走编辑器目录扫描；`modScript.lua` 只是兜底。

### 7.8 词典 Lua 语法错误 `unfinished string near '<eof>'`
翻译结果里混进了换行/制表符。`gen_dict.py` 的 `lua_escape()` 已处理 `\r \n \t \\ '`，
新增批次若手工写 JSON 也要保证是合法 JSON（换个行就会炸）。

### 7.9 类名/对象名被误翻
词表是**按字符串全局匹配**的，如果某个英文单词恰好也是数据值（车辆名、材质名），也会被翻。
目前已知无害；若出现「对象名被翻」投诉，把该词从 `M.words` 移除，改用只在该上下文出现的长字符串。

---

## 8. 游戏更新后要做什么（版本升级 checklist）

1. **确认版本**：`tasklist` / `get_logs` 里看 `BeamNG.drive - 0.xx.x.x`；用户数据目录可能新增 `0.xx` 层（本例是 `D:\Documents\Beamng\current`）。
2. **看编辑器源码有没有大改**：
   ```bash
   cd E:/SteamLibrary/steamapps/common/BeamNG.drive
   ls lua/ge/extensions/editor/ | wc -l          # 0.40.3 是 154 个文件
   grep -c "M.onEditor" lua/ge/extensions/editor/main.lua
   ```
   重点确认 `editor/main.lua` 里 `loadAllEditorExtensions()` 的扫描逻辑和 `isFileAnEditorExtension` 的判定关键字是否还是 `M.onEditor`。
3. **确认 `ui_imgui` 仍是同一套接口**：`grep -c "ui_imgui" -r lua/ge/extensions/editor | head`
   以及几个关键函数是否还在：`im.Text` / `im.Checkbox` / `im.MenuItem1` / `im.Begin`。
4. **跑一次缺口扫描**（§6.1A）→ 通常更新会新增几十~几百条 → 分片翻译 → 合并打包。
5. **回归测试**（§6.6）：日志无 error、菜单/场景树/检查器/偏好设置四处截图确认、FPS 无异常下降。
6. **升版本号**：`v1.0.x → v1.1.0`，三处同步改（`build.py`、`info.json`、文档）。

---

## 9. 已知未覆盖 / 下一步可做

- **长尾词条**：工具面板深层参数（拉力赛笔记本、脚本 AI、部分调试窗口）仍有英文，用 §6.1B 捕获法批量补。
- **`Layer 0` / `Object 3` 这类「标签+序号」**：规则里可加 `^Layer %d+$` 之类。
- **窗口菜单的「最近窗口」条目**：存的是 key（`Gameplay > Script AI Manager`）而不是标签，需在 `mainMenu.lua` 层面处理，不建议动。
- **动态命名对象**（材质名、车辆名）：属于数据，**不要翻**。
- **`cairo_*` 字体标题**：无解（字形缺失），除非改游戏字体。
- **CEF/Vue 那部分 UI**（`ui/modules/**`）不属于本 mod 范围，走游戏官方翻译表。

---

## 10. 性能与安全边界

- 词表 6,567 条 ≈ 328 KB Lua 文本，**只在进入编辑器时解析一次**（进编辑器会多 ~50–100ms）
- 运行期：首次查表后全部命中缓存，单帧上万次调用只是哈希查表；实测编辑器内 **196–330 FPS**
- 缓存上限 `M.config.cacheLimit = 20000`，超了清空重来，不会无限增长
- **零文件修改**：不改游戏目录任何文件，卸载 = 删 zip
- 兜底开关：
  ```lua
  extensions.editor_zhcnLocalization.setEnabled(false)   -- 立刻回英文
  extensions.editor_zhcnLocalization.uninstall()         -- 彻底还原（含字体/包裹函数）
  extensions.editor_zhcnLocalization.stats()             -- {calls,hit,dictSize,ruleHit,...}
  extensions.editor_zhcnLocalization.debugTranslate('Text')  -- 测单条
  extensions.editor_zhcnLocalization.capture(true/false)     -- 开/关缺口捕获
  ```

---

## 11. 命令速查

```bash
# 路径变量
PY="C:/Users/feng/.workbuddy/binaries/python/versions/3.13.12/python.exe"
cd /d/Documents/Beamng/current/mods/_work

$PY gen_dict.py                     # 合并词表
$PY build.py                        # 打包 zip
$PY qa_capture.py                   # 运行时捕获 + 缺口比对
$PY mcp.py run_lua "{\"code\":\"return 1+1\"}"      # 探活
$PY mcp.py get_logs '{"lines":150}'                 # 看日志
$PY mcp.py set_editor_active '{"active":true}'      # 进编辑器
$PY mcp.py list_editor_classes '{"pattern":""}'     # 全部类名（译类名用）
powershell -File cap3.ps1                            # 截真实画面

# 重新挂载 + 刷新词表（免重启）
$PY mcp.py run_lua "{\"code\":\"local mm=extensions.core_modmanager pcall(function() mm.deactivateMod('beamng_worldeditor_zh_cn_v1.0.2',true,true) end) pcall(function() mm.activateMod('beamng_worldeditor_zh_cn_v1.0.2') end) _G.__zhcnEditorDict=nil return 'ok'\"}"
$PY mcp.py run_lua "{\"code\":\"local m=extensions.editor_zhcnLocalization m.uninstall() local n=m.reload() m.install() return n\"}"
```

---

## 12. 交接 checklist

- [x] mod 能在**冷启动**自动加载（编辑器目录扫描）
- [x] 卸载/开关/热更新接口可用
- [x] 6,567 条词条已生效，四处关键界面中文确认
- [x] FPS 无异常（196–330）
- [x] 旧版本 zip 已清理（`mods/` 下只剩 v1.0.2）
- [ ] 长尾词条继续补（可选）
- [ ] 游戏更新后按 §8 回归
