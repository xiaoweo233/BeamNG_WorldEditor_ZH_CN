#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 mod/ 目录打包成可分发的 BeamNG 模组 zip。

用法：
    python tools/build_zip.py            # 输出到 dist/
    python tools/build_zip.py out.zip    # 指定输出路径

规则（和游戏实际加载强相关，勿随意改）：
  * zip 内**不能有顶层文件夹**，lua/ scripts/ mod_info/ 必须在根。
  * mod_info/<ID>/info.json 的 <ID> 只能含字母数字（游戏用正则 ^mod_info/([0-9a-zA-Z]*)/info.json 匹配）。
  * scripts/modScript.lua 用 STORED（不压缩）：部分环境下 dofile 无法流式解压 zip 条目。
"""
import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'mod')
INFO = os.path.join(MOD, 'mod_info', 'ZHCNEditorLoc', 'info.json')

README = """# 世界编辑器深度汉化包 v{ver}

BeamNG.drive 世界编辑器（World Editor）简体中文汉化，运行时替换，不修改游戏原文件。

## 安装
1. 把本 zip 放入 `.../BeamNG.drive/0.xx/mods/`（或游戏内 模组管理器 → 拖入）
2. 重启游戏
3. 按 F11 进入世界编辑器，界面即为中文

## 特性
- {count} 条界面文本翻译：菜单、工具面板、检查器字段、悬停说明、快捷键条
- 采用 `中文##英文原文` 标签方案，控件 ID 保持唯一，不会串号
- 纯文本接口不追加 ##；缺中文字形的字体自动跳过，不出现乱码
- 翻译结果缓存，对帧率无可测影响
- 卸载即恢复英文；控制台可随时开关：
  `extensions.editor_zhcnLocalization.setEnabled(false)`

## 结构
```
lua/ge/extensions/editor/zhcnLocalization.lua   主加载点：编辑器启动时自动扫描加载
lua/ge/extensions/zhcn/dictionary.lua           词表（可自行增补）
scripts/modScript.lua                           备用加载入口（解包安装时生效）
mod_info/ZHCNEditorLoc/info.json                模组信息
```

## 自行增补词条
编辑 `dictionary.lua` 的 `M.words`，加上 `['英文原文'] = '中文',`，
然后在游戏控制台执行 `extensions.editor_zhcnLocalization.reload()` 即可热更新。

## 已知边界
- 菜单栏「文件/编辑/视角/对象/视图/窗口/帮助」来自游戏内置语言包，不是本 mod
- 车辆名、关卡名、材质名等数据内容不翻译
- 少数使用 `cairo_regular_medium` 等无中文字形字体的标题保持英文，避免出现「????」
- 动态拼接串（含路径的如 `Level: /levels/...`）按前缀规则翻译
"""


def count_words(dict_path):
    n = 0
    with io.open(dict_path, encoding='utf-8') as f:
        for line in f:
            if "'] = '" in line:
                n += 1
    return n


def main():
    with io.open(INFO, encoding='utf-8') as f:
        info = json.load(f)
    ver = info.get('version_string', '0.0.0')
    name = info.get('filename') or ('BeamNG_WorldEditor_ZH_CN_v%s.zip' % ver)
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', name)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)

    dict_path = os.path.join(MOD, 'lua', 'ge', 'extensions', 'zhcn', 'dictionary.lua')
    readme = README.format(ver=ver, count='{:,}'.format(count_words(dict_path)))

    files = []
    for root, dirs, fs in os.walk(MOD):
        for f in sorted(fs):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, MOD).replace('\\', '/')
            files.append((full, rel))

    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for full, rel in files:
            if rel == 'scripts/modScript.lua':
                z.write(full, rel, compress_type=zipfile.ZIP_STORED)
            else:
                z.write(full, rel)
        z.writestr('README.md', readme)

    size = os.path.getsize(out)
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        n = len(z.namelist())
    print('打包完成: %s' % out)
    print('大小: %.1f KB  条目数: %d  完整性: %s' % (size / 1024.0, n, 'OK' if bad is None else bad))
    return 0 if bad is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
