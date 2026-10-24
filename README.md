<div align="center">

# 🇨🇳 BeamNG.drive 世界编辑器简体中文

**把 World Editor 的界面变成中文 —— 纯 Mod 运行时注入，不改游戏文件一个字节**

🎯 6,567 条词条 ｜ 🧩 54 个接管点 ｜ 🛡 零侵入 ｜ 🔤 字体缺失自动降级 ｜ 🆓 MIT

</div>

---

## 🎬 这个 Mod 做了什么

BeamNG 的 **世界编辑器（World Editor）** 是 Lua 驱动的 ImGui 手绘界面，界面文字全部写死在 Lua 里，
官方翻译系统（`locales/translations/`）管不到 —— 即使游戏切成简体中文，编辑器里依然是满屏英文
（编辑器内只有 80 处 `_tr()` 调用，且早已翻译完毕）。

本 Mod 在运行时接管 `ui_imgui` 的文本接口，命中词表就换中文渲染，未命中则原样透传，**行为零变化**。

| 位置 | 原版 | 装了本 Mod |
|---|---|---|
| 窗口标题 | `Material Editor` | 🀄 `材质编辑器` |
| 检查器字段 | `Pitch Jitter` | 🀄 `俯仰抖动` |
| 偏好说明 | `Check full filepath when searching…` | 🀄 `搜索资源时检查完整文件路径…` |
| 可视化类名 | `TSStatic` | 🀄 `静态模型（TSStatic）` |
| 状态行 | `EditMode: Manipulate Object(s)` | 🀄 `编辑模式：物体操作` |
| 底部快捷键条 | `Ctrl  Fine Rotation/Scale` | 🀄 `Ctrl 精细旋转/缩放` |

---

## 🚀 安装

### 方式一：下载发行版（推荐）

去 [Releases](../../releases) 下载 `BeamNG_WorldEditor_ZH_CN_v1.0.2.zip`，放进：

```
文档\BeamNG.drive\<版本号>\mods\
```

重启游戏 → 按 **F11** 进入世界编辑器 → 界面即为中文。

> 也可以直接在游戏内「模组管理器」把 zip 拖进去。

### 方式二：从源码构建

```bash
git clone https://github.com/xiaoweo233/BeamNG-Editor-ZH-CN.git
cd BeamNG-Editor-ZH-CN
python tools/build_zip.py          # 产物在 dist/
```

构建脚本会读 `mod/mod_info/ZHCNEditorLoc/info.json` 的版本号自动命名，并把 `mod/` 打成
**根目录无套层**的 zip（游戏只认这种结构）。

---

## ✅ 怎么确认生效

1. 编辑器里任意面板出现中文（最快：看右侧「检查器」标题、底部快捷键条）。
2. `beamng.log` 里搜 `zhcn_editorLoc`，应有：

```
GELua.zhcn_editorLoc| 世界编辑器汉化已启用：6567 条词条
```

3. 控制台可查看运行统计：

```lua
extensions.editor_zhcnLocalization.stats()   -- calls/hit/dictSize/ruleHit/composeHit
```

---

## 🧠 原理

### 1. 接管 `ui_imgui`

编辑器所有模块都写 `local imgui = ui_imgui`（表引用），所以替换表里的函数字段即可全量生效。
按「标签是否兼作控件 ID」分两组：

| 组 | 接口 | 输出 |
|---|---|---|
| 纯文本 | `Text` `TextUnformatted` `TextWrapped` `TextDisabled` `BulletText` `SetTooltip` `SeparatorText` `HeaderText` `LabelText` `TableSetupColumn` | 直接中文，**绝不追加 `##`** |
| 控件 | `Button` `SmallButton` `Checkbox` `MenuItem1` `MenuItem` `Selectable1` `Selectable` `RadioButton2` `RadioButton` `InputText` `InputFloat` `InputInt` `InputFloat3` `SliderFloat` `SliderInt` `DragFloat` `Combo1` `Combo` `Combo2` `BeginCombo` `CollapsingHeader*` `TreeNode*` `TreeNodeEx*` `BeginTabItem` `BeginMenu` `ListBox` | `中文##英文原文` |

另有 `TextColored`（标签在第 2 参）与 `Begin`（窗口标题，兼作窗口 ID）。

### 2. `##` ID 保护

ImGui 用 label 计算控件 ID。控件组输出 `中文##英文原文`：只显示 `##` 前的中文，ID 仍按整串哈希 ——
不同英文标签映射到同一中文时 ID 依然唯一，**不会串号、不会勾选错位**。
纯文本组绝不能加（否则 `##` 会被当普通字符画出来）。

### 3. 四级匹配

| 级别 | 手段 | 例子 |
|---|---|---|
| 1 | 精确词表（6,567 条） | `Apply` → `应用` |
| 2 | 动态规则（21 条 Lua pattern） | `Path: a.b.c` → `路径： a.b.c` |
| 3 | 快捷键拼接 | `Ctrl  Fine Rotation/Scale` → `Ctrl 精细旋转/缩放` |
| 4 | 术语组合（214 词，≤5 词才拼） | `Sidewalk Corner Radius` → `人行道转角半径` |

多行文本（`说明\nPath: …\nType: …\nDefault Value: …`）会**按行拆开分别翻译**。

### 4. 字体保护

`cairo_regular_medium` / `cairo_bold` / `robotomono_regular` 没有烘焙中文字形，用其中文会显示 `????`。
模块包装 `PushFont3` / `PopFont` 维护字体栈，这些字体激活期间直接返回原文。

### 5. 加载链路（关键坑）

官方 `scripts/modScript.lua` 在 **0.40.3 上读不了 zip 内文件**（`dofile` 报 `Result too large`），
因此主加载点改为**编辑器自带的目录扫描**：

```
editor/main.lua: loadAllEditorExtensions()
  → FS:findFiles('/lua/ge/extensions/editor/', '*.lua', 0, false, false)
  → 文件含 "M.onEditor" / "M.onExtension" 即视为编辑器扩展
  → extensions.load('editor_' .. 文件名)
```

所以汉化层放在 `lua/ge/extensions/editor/zhcnLocalization.lua`；词表用 `loadfile` 直读
（`require` 有模块缓存，换词表后热更新会读到旧内容）。`scripts/modScript.lua` 仅作解包安装时的兜底。

### 6. 性能

- 首次查表后全部命中一级缓存，单帧上万次调用只是哈希查表
- 词表 ~328K 字符，仅进编辑器时解析一次
- 编辑器内实测 **196–330 FPS**，无可测掉帧
- 卸载即恢复英文，零残留

---

## 📊 覆盖范围

| 区域 | 状态 |
|---|---|
| 主菜单栏「文件/编辑/视角/对象/视图/窗口/帮助」 | 官方语言包提供（非本 Mod） |
| 状态行 `关卡：`/`编辑模式：`/`尺寸：`/`帧率：` | ✅ |
| 场景树、检查器（全部字段名）、对象类名 195 个 | ✅ |
| 材质编辑器（贴图槽、光照/动画参数） | ✅ |
| 可视化窗口（调试/可见/可选择） | ✅ |
| 首选项 22 个分类 + 全部开关 + 悬停长说明 | ✅ |
| 贴花 / 森林 / 地表植被 / 地形 / 道路建筑师 / 生物群系 / 资源浏览器 / 任务·竞速·拉力 / 信号灯 | ✅ |
| 底部快捷键条 | ✅ |

---

## ⚠️ 已知限制

| 限制 | 说明 |
|---|---|
| 数据内容不翻 | 车辆名、关卡名、材质名、场景对象名属于用户数据，翻了反而找不到 |
| `Layer 0` 这类「标签+序号」 | 运行时拼接，仅标签部分可翻 |
| `cairo_*` 字体标题 | 字形缺失，保持英文而非显示 `????` |
| 下拉框内建项 | `Combo1(label, items)` 的选项是 C 侧 `char*` 数组，Lua 层拿不到 |
| 非编辑器界面 | 主菜单/HUD 等由官方 `_tr` 翻译系统负责，本 Mod 不干预 |

---

## ✍️ 参与翻译

词条都在 `translations/` 下：`*.json` 是人工整理批次，`agent/*.json` 是分片翻译结果。
格式就是 `{"英文原文": "中文译文"}`。

改完两步：

```bash
python tools/gen_dict.py    # 合并所有批次 → mod/lua/ge/extensions/zhcn/dictionary.lua
python tools/build_zip.py   # 打包 → dist/
```

游戏内即时生效（不用重启）：

```lua
extensions.editor_zhcnLocalization.reload()   -- 重新读词表
```

> 键必须与游戏里的可见文本**逐字符一致**（含尾随空格、冒号）。
> `dictionary.lua` 是生成物，**不要手改**，改了会被下次生成覆盖。
> 术语组合兜底用的词根在 `tools/gen_dict.py` 的 `terms` 里，拼不通的短标签加词根比加整条更划算。

`translations/` 里还有各批次的分工说明，见 [HANDOVER.md](HANDOVER.md)（面向后续维护者 / AI 的完整交接文档：
环境、踩坑、缺口扫描脚本、游戏更新适配流程）。

---

## 📁 目录说明

```
BeamNG_WorldEditor_ZH_CN/
├── mod/                                                ← 直接对应模组 zip 的根目录
│   ├── lua/ge/extensions/editor/zhcnLocalization.lua   ← 汉化层本体（约 380 行）
│   ├── lua/ge/extensions/zhcn/dictionary.lua           ← 词表（6,567 条，由工具生成）
│   ├── scripts/modScript.lua                           ← 兜底加载入口
│   └── mod_info/ZHCNEditorLoc/info.json                ← 模组元信息（名称/版本/简介）
├── translations/                                       ← 词条源文件（人写的那一层）
│   ├── batch1~4.json                                   高频通用词条（按钮/字段/对话框）
│   ├── batch5_windows.json                             60+ 窗口标题
│   ├── batch6~11_*.json                                检查器字段/工具名/偏好分类/菜单/贴图槽
│   ├── batch12_desc.json                               偏好设置长说明（人工精修）
│   └── agent/*.json                                    17 个分片的翻译结果（UI 字面量/类名/长句）
├── tools/                                              ← 构建与开发工具
│   ├── gen_dict.py                                     合并 translations/ → dictionary.lua
│   ├── build_zip.py                                    打包 mod/ → dist/*.zip
│   ├── mcp.py                                          游戏内 MCP 客户端（进游戏验证/取日志）
│   ├── qa_capture.py                                   运行时捕获未翻译文字 + 与词表比对
│   ├── extract.py / extract_extra.py                   静态扫描编辑器 Lua 里的界面字符串
│   ├── analyze_tr.py                                   分析官方 zh_Hans 语言包覆盖情况
│   └── cap3.ps1                                        Windows 下截取含 ImGui 层的真实画面
├── dist/BeamNG_WorldEditor_ZH_CN_v1.0.2.zip            ← 已构建好的成品（可直接安装）
├── .github/workflows/release.yml                       推 tag 即构建 zip 并发布 Release
├── .github/release-notes.md                            Release 说明模板
├── HANDOVER.md                                         完整交接文档（环境/踩坑/更新适配）
├── LICENSE                                             MIT
└── README.md
```

### 每个关键文件负责什么

| 文件 | 职责 | 改它的场景 |
|---|---|---|
| `mod/lua/ge/extensions/editor/zhcnLocalization.lua` | 运行时翻译层：包裹 `ui_imgui` 的 24 个文本接口、`##` ID 处理、四级匹配、字体栈保护、缓存 | 要新增接管点 / 修 `##` 残留 / 调规则时 |
| `mod/lua/ge/extensions/zhcn/dictionary.lua` | 词表：`M.words`（6,567 条）+ `M.terms`（214 术语）+ `M.rules`（21 条动态规则） | **不要手改**，改 `translations/` 后重新生成 |
| `mod/scripts/modScript.lua` | 兜底加载：解包安装（`mods/unpacked/`）时由游戏启动脚本加载 | 一般不用动 |
| `mod/mod_info/ZHCNEditorLoc/info.json` | 模组名/版本/简介，`version_string` 决定 zip 文件名与 Release tag | 发新版本时改这里 |
| `translations/**/*.json` | 词条的**唯一真源**，`{"英文原文": "中文译文"}` | 补翻译时只改这里 |
| `tools/gen_dict.py` | 合并全部批次 → 生成 `dictionary.lua`（含术语表与动态规则） | 要加术语根 / 加动态规则时 |
| `tools/build_zip.py` | 读版本号 → 打 zip（根目录无套层、`modScript.lua` 用 STORED） | 改打包规则时 |

### 实现索引（想知道某段逻辑在哪）

| 机制 | 位置 |
|---|---|
| 接管 `ui_imgui` 的接口清单 | `zhcnLocalization.lua` 的 `TEXT_FNS` / `WIDGET_FNS` 两个表 |
| `中文##英文原文` 的 ID 保护 | `translateLabel()` 里 `isWidget` 分支 |
| 四级匹配（词表→规则→快捷键拼接→术语组合） | `translateLabel()` → `lookup()` / `applyRule()` / `translateHint()` / `composeTranslate()` |
| 多行提示按行翻译 | `translateLabel()` 开头的 `s:find('\n')` 分支 |
| 缺字形字体跳过 | `wrapFonts()` + `M.config.cjklessFonts` + `translateLabel()` 首行判断 |
| 缓存与上限 | `cache` 表 + `M.config.cacheLimit` |
| 加载与自愈 | `M.onEditorInitialized` / `M.onEditorGui`（每帧幂等补装） |


---

## 🧪 版本与兼容

| 项 | 说明 |
|---|---|
| 实测游戏版本 | BeamNG.drive **0.40.3.0.290897**（Direct3D12） |
| 依赖 | 无。不需要额外字体、不需要联网、不需要 Lua 扩展 |
| 构建依赖 | Python 3.8+ |
| 设计原则 | **宁可少翻，不可报错**：任何异常都只退化成英文，编辑器功能保持完整 |

游戏大版本更新后，按 [HANDOVER.md](HANDOVER.md) 第 8 节的 checklist 回归：
确认 `editor/main.lua` 的扫描逻辑与 `ui_imgui` 接口未变 → 跑缺口扫描 → 补词条 → 重新打包。

---

## 📜 许可

[MIT](LICENSE) © xiaoweo233

本项目与 BeamNG GmbH 无关，仅为社区汉化补丁。游戏本体版权归 BeamNG GmbH 所有。
