# 世界编辑器深度汉化包 v1.0.2

把 BeamNG.drive **世界编辑器（World Editor）** 的界面完整汉化：**6,567 条**界面文本，
覆盖主菜单、场景树、检查器、材质编辑器、可视化、首选项、贴花/森林/地形/道路建筑师/资源浏览器等全部工具面板。

**纯运行时替换，不修改游戏任何文件**，卸载即恢复英文。

---

## 📦 安装

1. 下载本页下方 **Assets** 里的 `BeamNG_WorldEditor_ZH_CN_v1.0.2.zip`
2. 放进 `文档\BeamNG.drive\<版本号>\mods\`（或游戏内「模组管理器」拖入）
3. 重启游戏 → 按 **F11** 进入世界编辑器，界面即为中文

卸载：删掉 zip 重启即可，零残留。

---

## ✨ 本次更新（v1.0.2）

- 补齐 **195 个 SimObject 对象类名** → `静态模型（TSStatic）`、`地形块（TerrainBlock）`…
- 补齐**材质编辑器**属性名（不透明度贴图 / 像素高光 / 粗糙度系数 / 自发光强度 / 辉光系数 / 各向异性过滤 / 波形与振幅…）与 16 个贴图槽名称
- 新增**多行提示按行翻译**：偏好设置悬停说明现在连 `路径 / 类型 / 默认值` 一起中文化
- 补齐工具栏悬停提示（曝光设置等）、窗口菜单项、偏好分类、贴图槽
- 修复 `已锁定##locked` 这类 `##` 后缀残留

词条规模：3,687 → **6,567**。

---

## 🔧 特性

- **零侵入**：不改游戏原文件，游戏完整性校验永远通过
- **控件 ID 安全**：采用 `中文##英文原文` 标签，不会出现选项串号 / 勾选错位
- **字体保护**：遇到没有中文字形的字体（`cairo_*`）自动跳过，不显示 `????`
- **可热更新**：控制台 `extensions.editor_zhcnLocalization.reload()` 即可重载词表，不用重启
- **可随时开关**：`extensions.editor_zhcnLocalization.setEnabled(false)`
- **性能无感**：查表全缓存，编辑器内实测 196–330 FPS

---

## ⚠️ 已知边界

- 车辆名、关卡名、材质名、场景对象名等**数据内容不翻译**
- `Layer 0` 这类「标签+序号」运行时拼接，仅标签可翻
- 少数使用 `cairo_regular_medium` 字体的标题保持英文（该字体无中文字形）
- 主菜单/HUD 等非编辑器界面由游戏官方翻译系统负责

---

## 🧩 从源码构建

```bash
python tools/gen_dict.py    # 合并 translations/ → mod/lua/ge/extensions/zhcn/dictionary.lua
python tools/build_zip.py   # 打包 → dist/BeamNG_WorldEditor_ZH_CN_v1.0.2.zip
```

维护/二次开发请看仓库里的 [HANDOVER.md](https://github.com/xiaoweo233/BeamNG-Editor-ZH-CN/blob/main/HANDOVER.md)。

---

**兼容性**：BeamNG.drive 0.40.3 实测通过（Direct3D12）。游戏大版本更新后若出现英文回退，欢迎提 Issue 附截图。
