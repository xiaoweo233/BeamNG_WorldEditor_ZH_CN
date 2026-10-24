#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并 translations/ 下的全部词条批次，生成 mod/lua/ge/extensions/zhcn/dictionary.lua。

用法：python tools/gen_dict.py

批次来源（自动 glob）：
    translations/*.json         人工整理的批次（batch1..batch12 等）
    translations/agent/*.json   子 agent 分片翻译结果
冲突策略：同名 key 保留**先出现的**译文（按文件名排序），不覆盖。
"""
import json, io, os, re, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'mod', 'lua', 'ge', 'extensions', 'zhcn')

merged = {}
dups = 0
for p in (sorted(glob.glob(os.path.join(ROOT, 'translations', '*.json'))) +
          sorted(glob.glob(os.path.join(ROOT, 'translations', 'agent', '*.json')))):
    d = json.load(io.open(p, encoding='utf-8'))
    for k, v in d.items():
        if not isinstance(v, str) or not v.strip():
            continue
        if k in merged and merged[k] != v:
            dups += 1
            continue
        merged[k] = v

# 基本校验（可选：如果本地有 items.json 就做覆盖率比对）
print('合并条目:', len(merged), '冲突忽略:', dups)
cjk = re.compile(r'[\u4e00-\u9fff]')
no_cjk = [k for k, v in merged.items() if not cjk.search(v)]
if no_cjk:
    print('提示：译文无中文的 key（多为专有名词/占位符）:', len(no_cjk), no_cjk[:5])

# 补充：去掉尾随空格/前后空白的等价 key，提升命中率
extra = {}
for k, v in merged.items():
    ks = k.strip()
    if ks != k and ks and ks not in merged and ks not in extra:
        extra[ks] = v.rstrip()
for k, v in extra.items():
    merged.setdefault(k, v)

# 额外手工补充：截图/实测中发现的动态或遗漏文字
manual = {
    'SceneTree': '场景树',
    'Scene Tree': '场景树',
    'Tree': '树',
    '<no selection>': '‹未选择›',
    '-no selection-': '‹未选择›',
    'EditMode: ': '编辑模式： ',
    'Level: ': '关卡： ',
    'Fine Rotation/Scale': '精细旋转/缩放',
    'Align object to surfaces on LMB down + Wheel (rotates around up axis)': '左键按下对齐对象到表面 + 滚轮（绕上轴旋转）',
    'Copy objects': '复制对象',
    'Duplicate': '复制',
    'Duplicate at cam pos': '在镜头位置复制',
    'Delete objects': '删除对象',
    'Duplicate objects': '复制对象',
    'Duplicate at camera position': '在摄像机位置复制',
    'Align object to surface': '对齐对象到表面',
    'Fine Rotation': '精细旋转',
    'Fine Scale': '精细缩放',
}
for k, v in manual.items():
    merged.setdefault(k, v)

print('最终词条:', len(merged))

# 生成 Lua 词表
def lua_escape(s):
    s = s.replace('\r', ' ').replace('\n', '\\n').replace('\t', '\\t')
    return s.replace('\\', '\\\\').replace("'", "\\'")

lines = []
lines.append('-- 自动生成：世界编辑器中文词表')
lines.append('-- 生成来源: BeamNG.drive 0.40 世界编辑器 Lua 源码静态提取 + 人工翻译')
lines.append('local M = {}')
lines.append('M.words = {')
for k in sorted(merged):
    lines.append("  ['%s'] = '%s'," % (lua_escape(k), lua_escape(merged[k])))
lines.append('}')

# 术语表（组合式兜底用）
terms = {
    'lane': '车道', 'lanes': '车道', 'width': '宽度', 'height': '高度', 'length': '长度',
    'road': '道路', 'roads': '道路', 'sidewalk': '人行道', 'crossing': '交叉口',
    'overlay': '覆盖层', 'overlays': '覆盖层', 'traffic': '交通', 'sign': '标志', 'signs': '标志',
    'random': '随机', 'seed': '种子', 'value': '值', 'number': '数量', 'count': '数量',
    'inner': '内侧', 'outer': '外侧', 'front': '前', 'rear': '后', 'left': '左', 'right': '右',
    'central': '中央', 'default': '默认', 'auto': '自动', 'custom': '自定义', 'current': '当前',
    'new': '新建', 'old': '原', 'add': '添加', 'remove': '移除', 'delete': '删除',
    'enable': '启用', 'disable': '禁用', 'show': '显示', 'hide': '隐藏', 'use': '使用',
    'min': '最小', 'max': '最大', 'size': '尺寸', 'scale': '缩放', 'offset': '偏移',
    'position': '位置', 'rotation': '旋转', 'angle': '角度', 'radius': '半径',
    'spacing': '间距', 'distance': '距离', 'density': '密度', 'strength': '强度',
    'influence': '影响', 'slope': '坡度', 'row': '行', 'edge': '边缘', 'field': '田地',
    'area': '区域', 'zone': '区域', 'brush': '笔刷', 'mask': '遮罩', 'layer': '图层',
    'terrain': '地形', 'forest': '森林', 'material': '材质', 'texture': '贴图',
    'mesh': '网格', 'object': '对象', 'objects': '对象', 'node': '节点', 'nodes': '节点',
    'camera': '摄像机', 'vehicle': '车辆', 'speed': '速度', 'tilt': '倾斜',
    'type': '类型', 'name': '名称', 'label': '标签', 'path': '路径', 'file': '文件',
    'folder': '文件夹', 'level': '关卡', 'mission': '任务', 'prefab': '预制体',
    'prefabs': '预制体', 'index': '索引', 'order': '顺序', 'tiling': '平铺',
    'alpha': '透明', 'color': '颜色', 'normal': '法线', 'diffuse': '漫反射',
    'roughness': '粗糙度', 'metallic': '金属度', 'blend': '混合', 'mode': '模式',
    'channel': '通道', 'intensity': '强度', 'thickness': '厚度', 'softness': '柔和度',
    'outline': '描边', 'distribution': '分布', 'source': '来源', 'target': '目标',
    'selection': '选择', 'selected': '所选', 'option': '选项', 'options': '选项',
    'star': '星级', 'progress': '进度', 'notes': '笔记', 'clip': '裁剪',
    'horizontal': '水平', 'vertical': '垂直', 'start': '起点', 'end': '终点',
    'preview': '预览', 'display': '显示', 'view': '视图', 'general': '常规',
    'advanced': '高级', 'properties': '属性', 'settings': '设置', 'list': '列表',
    'bake': '烘焙', 'generate': '生成', 'regenerate': '重新生成', 'clear': '清除',
    'reset': '重置', 'apply': '应用', 'save': '保存', 'load': '加载', 'export': '导出',
    'import': '导入', 'browse': '浏览', 'select': '选择', 'create': '创建',
    'of': '的', 'to': '到', 'in': '于', 'for': '用于', 'with': '带', 'and': '和',
    'corner': '转角', 'side': '侧', 'top': '顶部', 'bottom': '底部', 'depth': '深度',
    'begin': '起点', 'finish': '终点', 'curve': '曲线', 'spline': '样条',
    'decal': '贴花', 'decals': '贴花', 'glyph': '字形', 'font': '字体', 'line': '线',
    'inspector': '检查器', 'tree': '树', 'toolbar': '工具栏', 'browser': '浏览器',
    'selector': '选择器', 'history': '历史', 'editor': '编辑器', 'tool': '工具',
    'tools': '工具', 'panel': '面板', 'legend': '图例', 'library': '库',
    'manager': '管理器', 'checker': '检查器', 'validator': '验证器', 'importer': '导入器',
    'exporter': '导出器', 'viewer': '查看器', 'painter': '画笔', 'window': '窗口',
    'windows': '窗口', 'dialog': '对话框', 'table': '表', 'column': '列',
    'header': '表头', 'entry': '条目', 'item': '项目', 'items': '项目', 'data': '数据',
    'paint': '绘制', 'build': '构建', 'sample': '采样', 'snap': '吸附',
    'record': '记录', 'play': '播放', 'stop': '停止', 'pause': '暂停',
    'hide': '隐藏', 'show': '显示', 'lock': '锁定', 'unlock': '解锁',
    'group': '分组', 'groups': '分组', 'parent': '父级', 'child': '子级',
    'transform': '变换', 'position': '位置', 'axis': '轴', 'axes': '轴',
    'grid': '网格', 'snapping': '吸附', 'rotation': '旋转', 'pivot': '轴心',
    'zone': '区域', 'zones': '区域', 'section': '区段', 'segment': '段',
    'node': '节点', 'vertex': '顶点', 'vertices': '顶点', 'edge': '边缘',
    'faces': '面', 'polygon': '多边形', 'width': '宽度', 'thickness': '厚度',
}
lines.append('M.terms = {')
for k in sorted(terms):
    lines.append("  ['%s'] = '%s'," % (k, terms[k]))
lines.append('}')

# 动态前缀规则（拼接出来的文字，如 "Level: xxx"）
lines.append('M.rules = {')
for pat, repl in [
    ('^Level:%s*(.*)$', '关卡： %1'),
    ('^EditMode:%s*(.*)$', '编辑模式： %1'),
    ('^File:%s*(.*)$', '文件： %1'),
    ('^Total:%s*(.*)$', '总计： %1'),
    ('^Type:%s*(.*)$', '类型： %1'),
    ('^TypeName:%s*(.*)$', '类型名： %1'),
    ('^Size:%s*(.*)$', '尺寸： %1'),
    ('^Class:%s*(.*)$', '类： %1'),
    ('^Parent:%s*(.*)$', '父级： %1'),
    ('^Path:%s*(.*)$', '路径： %1'),
    ('^FPS:%s*(.*)$', '帧率： %1'),
    ('^VRAM:%s*(.*)$', '显存： %1'),
    ('^RAM:%s*(.*)$', '内存： %1'),
    ('^GpuWait:%s*(.*)$', 'GPU 等待： %1'),
    ('^Scene Vehicles:%s*$', '场景车辆：'),
    ('^Default Value:%s*(.*)$', '默认值： %1'),
    ('^Description:%s*(.*)$', '描述： %1'),
    ('^Variable:%s*(.*)$', '变量： %1'),
    ('^Value:%s*(.*)$', '值： %1'),
    ('^Min Value:%s*(.*)$', '最小值： %1'),
    ('^Max Value:%s*(.*)$', '最大值： %1'),
]:
    lines.append("  {pattern = '%s', repl = '%s'}," % (pat, repl))
lines.append('}')
lines.append('return M')

out = '\n'.join(lines) + '\n'
out_path = os.path.join(MOD, 'dictionary.lua')
os.makedirs(MOD, exist_ok=True)
io.open(out_path, 'w', encoding='utf-8', newline='\n').write(out)
print('写入', os.path.relpath(out_path, ROOT), '字符数', len(out), '词条', len(merged))
