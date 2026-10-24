--[[
  BeamNG.drive 世界编辑器深度汉化 / World Editor Deep Chinese Localization
  ---------------------------------------------------------------------------
  实现原理：
    世界编辑器的界面由 Lua 驱动 ImGui 即时渲染，所有文字最终都会经过全局表
    ui_imgui 的文本类接口。本模块在运行时为这些接口套一层翻译，把英文标签
    换成中文，从而在不修改任何游戏原文件的前提下完成汉化。

  安全设计：
    1. 控件类接口（Button/Checkbox/MenuItem/TreeNode/Begin...）的标签会输出为
       「中文##英文原文」：ImGui 只显示 ## 之前的部分，而控件 ID 仍按整串计算，
       因此不同英文标签对应的控件 ID 依然互不相同，不会串号。
    2. 纯文本类接口（Text/TextUnformatted/SetTooltip/TextColored...）不追加 ##，
       否则 ## 会被当作普通字符显示出来。
    3. 原始函数被完整保留，uninstall() 可 100% 还原；卸载 mod 即恢复英文。
    4. 翻译结果一律走缓存，单帧上万次调用也只做哈希查表，对帧率无影响。
    5. 弹窗类接口（OpenPopup/BeginPopupModal）不做替换，避免弹窗 ID 失配。

  控制台开关：extensions.zhcn_editorLocalization.setEnabled(false)
]]

local M = {}

M.version = '1.0.1'

M.config = {
  translateWindowTitles = true,   -- Begin() 的窗口标题
  translateTextColored = true,    -- TextColored() 的第二个参数
  translateHints = true,          -- 「快捷键  +  说明文字」这类拼接串
  cacheLimit = 20000,
  -- 这些字体没有烘焙中文字形，用到它们时跳过翻译，避免出现「?????」
  cjklessFonts = {
    cairo_regular_medium = true,
    cairo_bold = true,
    robotomono_regular = true,
  },
}

local imgui = nil
local dict = nil
local terms = nil
local rules = nil
local cache = {}
local installed = false
local enabled = true
local wrapped = {}

local stats = {calls = 0, hit = 0, dictSize = 0, ruleHit = 0, composeHit = 0, hintHit = 0}

-- 字体栈：某些字体没有中文字形，激活期间跳过翻译（否则会显示 ??）
local fontStack = {}
local cjklessDepth = 0

-- 纯文本接口：只显示文字，不参与控件 ID，绝不能追加 ##
local TEXT_FNS = {
  'Text', 'TextUnformatted', 'TextWrapped', 'TextDisabled', 'BulletText', 'SetTooltip',
  'SeparatorText', 'HeaderText', 'LabelText', 'TableSetupColumn',
}

-- 控件接口：标签同时是控件 ID，追加 ## 原文可保证 ID 唯一
local WIDGET_FNS = {
  'Button', 'SmallButton', 'Checkbox', 'MenuItem1', 'MenuItem', 'Selectable1', 'Selectable',
  'RadioButton2', 'RadioButton', 'InputText', 'InputFloat', 'InputInt', 'InputFloat3',
  'SliderFloat', 'SliderInt', 'DragFloat', 'Combo1', 'Combo', 'Combo2', 'BeginCombo',
  'CollapsingHeader1', 'CollapsingHeader', 'TreeNode1', 'TreeNode', 'TreeNodeEx1', 'TreeNodeEx',
  'BeginTabItem', 'BeginMenu', 'ListBox',
}

local DICT_PATH = '/lua/ge/extensions/zhcn/dictionary.lua'

-- 直接按虚拟路径加载词表：不经过 require 的模块缓存，
-- 这样升级词表后 reload() 能立刻生效，不需要重启游戏。
local function loadFromFile()
  local ok, chunk = pcall(loadfile, DICT_PATH)
  if not ok or type(chunk) ~= 'function' then return nil end
  local ok2, d = pcall(chunk)
  if ok2 and type(d) == 'table' then return d end
  return nil
end

local function loadDictionary()
  if type(rawget(_G, '__zhcnEditorDict')) == 'table' then
    dict, terms, rules = _G.__zhcnEditorDict, _G.__zhcnEditorTerms, _G.__zhcnEditorRules
  else
    local d = loadFromFile()
    if not d then
      local ok, res = pcall(require, 'zhcn/dictionary')
      if ok and type(res) == 'table' then d = res end
    end
    if d then
      dict = d.words or d
      terms = d.terms
      rules = d.rules
    else
      dict, terms, rules = {}, nil, nil
      log('E', 'zhcn_editorLoc', '词表加载失败: ' .. DICT_PATH)
    end
  end
  local n = 0
  for _ in pairs(dict or {}) do n = n + 1 end
  stats.dictSize = n
end

local function splitLabel(s)
  local vis, tail = s:match('^(.-)(##.*)$')
  if vis then return vis, tail end
  return s, nil
end

local function applyRule(v)
  if not rules then return nil end
  for i = 1, #rules do
    local r = rules[i]
    if v:find(r.pattern) then
      local ok, res = pcall(string.gsub, v, r.pattern, r.repl)
      if ok and res then
        stats.ruleHit = stats.ruleHit + 1
        return res
      end
      return nil
    end
  end
  return nil
end

-- 组合式兜底：整条标签由已知术语组成时按术语拼接（仅短标签，避免出现半句翻译）
local function composeTranslate(vis)
  if not terms then return nil end
  local out, count = {}, 0
  for w in vis:gmatch('[%w%./%+%-]+') do
    local t = terms[w:lower()]
    if not t then return nil end
    count = count + 1
    if count > 5 then return nil end
    out[#out + 1] = t
  end
  if count == 0 then return nil end
  return table.concat(out)
end

-- 「Ctrl  Fine Rotation/Scale」这类拼接串：只翻译后半段说明文字，快捷键部分保留
local function translateHint(v)
  if not M.config.translateHints then return nil end
  local pos
  local i = 1
  while true do
    local a, b = v:find('%s%s+', i)
    if not a then break end
    pos = a
    i = b + 1
  end
  if not pos then return nil end
  local head = v:sub(1, pos - 1)
  local sep = v:match('%s+', pos)
  local tail = v:sub(pos + #sep)
  local zh = dict and dict[tail]
  if not zh then
    local t = tail:match('^%s*(.-)%s*$')
    zh = dict and dict[t]
  end
  if zh then
    stats.hintHit = stats.hintHit + 1
    return head .. sep .. zh
  end
  return nil
end

-- 查词：支持前后空白（如 "\tLevel: "）
local function lookup(v)
  local zh = dict and dict[v]
  if zh then return zh end
  local lead, core, trail = v:match('^(%s*)(.-)(%s*)$')
  if core and core ~= v and core ~= '' then
    zh = dict and dict[core]
    if not zh then zh = applyRule(core) end
    if zh then
      -- 避免译文自带尾随空格与原标签尾随空格叠加成双空格
      if trail ~= '' and zh:sub(-1) == ' ' then zh = zh:sub(1, -2) end
      return lead .. zh .. trail
    end
  end
  return nil
end

local function translateLabel(s, isWidget)
  if cjklessDepth > 0 then return s end
  local cached = cache[s]
  if cached then return cached end
  stats.calls = stats.calls + 1

  local cap = rawget(_G, '__zhcnCapture')
  if cap and #cap < 5000 then cap[#cap + 1] = s end

  -- 多行文本（如偏好设置提示：说明 + Path + Type + Default Value）按行分别翻译
  if s:find('\n', 1, true) then
    local parts = {}
    for line in (s .. '\n'):gmatch('(.-)\n') do
      parts[#parts + 1] = translateLabel(line, false)
    end
    local joined = table.concat(parts, '\n')
    cache[s] = joined
    return joined
  end

  local vis, tail = splitLabel(s)
  local out = s

  if vis ~= '' and vis:sub(1, 1) ~= '#' then
    local zh = lookup(vis)

    if not zh then zh = applyRule(vis) end

    if not zh then
      zh = translateHint(vis)
      if not zh and #vis <= 40 and not vis:find('[%.:%?!]%s') and not vis:find('%s%s') then
        zh = composeTranslate(vis)
        if zh then stats.composeHit = stats.composeHit + 1 end
      end
    end

    if zh then
      stats.hit = stats.hit + 1
      if isWidget then
        out = zh .. (tail or ('##' .. s))
      else
        out = zh
      end
    end
  end

  if stats.calls > M.config.cacheLimit then
    cache = {}
    stats.calls = 0
  end
  cache[s] = out
  return out
end

local function wrapArg1(name, isWidget)
  if wrapped[name] then return end
  local orig = imgui[name]
  if not orig then return end
  wrapped[name] = orig
  imgui[name] = function(a, ...)
    if enabled and type(a) == 'string' then a = translateLabel(a, isWidget) end
    return orig(a, ...)
  end
end

local function wrapArg2(name, isWidget)
  if wrapped[name] then return end
  local orig = imgui[name]
  if not orig then return end
  wrapped[name] = orig
  imgui[name] = function(a, b, ...)
    if enabled and type(b) == 'string' then b = translateLabel(b, isWidget) end
    return orig(a, b, ...)
  end
end

-- 跟踪字体切换：激活缺少中文字形的字体时，暂停翻译
local function wrapFonts()
  local push = imgui.PushFont3
  if push and not wrapped.PushFont3 then
    wrapped.PushFont3 = push
    imgui.PushFont3 = function(name, ...)
      local skip = (type(name) == 'string' and M.config.cjklessFonts[name]) and true or false
      fontStack[#fontStack + 1] = skip
      if skip then cjklessDepth = cjklessDepth + 1 end
      return push(name, ...)
    end
  end
  local pop = imgui.PopFont
  if pop and not wrapped.PopFont then
    wrapped.PopFont = pop
    imgui.PopFont = function(...)
      local top = table.remove(fontStack)
      if top then cjklessDepth = math.max(0, cjklessDepth - 1) end
      return pop(...)
    end
  end
  -- 兜底：万一 push/pop 不平衡，避免永久停译
  if #fontStack > 64 then
    fontStack = {}
    cjklessDepth = 0
  end
end

function M.install()
  if installed then return true end
  if not ui_imgui then return false end
  imgui = ui_imgui
  loadDictionary()

  for _, name in ipairs(TEXT_FNS) do wrapArg1(name, false) end
  for _, name in ipairs(WIDGET_FNS) do wrapArg1(name, true) end
  if M.config.translateTextColored then wrapArg2('TextColored', false) end
  -- 窗口标题：Begin(name, ...) 的 name 兼作 ImGui 窗口 ID，按控件处理
  if M.config.translateWindowTitles then wrapArg1('Begin', true) end
  wrapFonts()

  installed = true
  log('I', 'zhcn_editorLoc', string.format('世界编辑器汉化已启用：%d 条词条', stats.dictSize))
  return true
end

function M.uninstall()
  if not installed or not imgui then return end
  for name, orig in pairs(wrapped) do imgui[name] = orig end
  wrapped = {}
  cache = {}
  fontStack = {}
  cjklessDepth = 0
  installed = false
  log('I', 'zhcn_editorLoc', '世界编辑器汉化已停用，界面已还原为英文')
end

function M.setEnabled(v)
  enabled = v and true or false
  return enabled
end

function M.isEnabled() return enabled end

function M.reload()
  cache = {}
  loadDictionary()
  return stats.dictSize
end

function M.stats() return stats, installed end

-- 调试/质检辅助：查看某段文字会被翻译成什么；开启/关闭原始文字捕获
function M.debugTranslate(s) return translateLabel(s, true) end

function M.capture(on)
  if on == false then
    _G.__zhcnCapture = nil
    return false
  end
  cache = {}
  _G.__zhcnCapture = {}
  return true
end

function M.captured()
  local cap = rawget(_G, '__zhcnCapture')
  return cap or {}
end

function M.onExtensionLoaded()
  M.install()
end

-- 编辑器扩展回调：进入世界编辑器时安装汉化层
function M.onEditorInitialized()
  M.install()
end

-- 每帧兜底：ui_imgui 或扩展加载顺序有变化时也能补装
function M.onEditorGui()
  if not installed then M.install() end
end

function M.onUpdate()
  if not installed then M.install() end
end

function M.onClientPreRender()
  if not installed then M.install() end
end

function M.onExtensionUnloaded()
  M.uninstall()
end

return M
