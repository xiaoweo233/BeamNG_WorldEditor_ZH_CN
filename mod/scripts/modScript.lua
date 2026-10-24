-- BeamNG.drive 世界编辑器深度汉化 —— 备用自动加载入口
-- 说明：世界编辑器启动时会自动扫描 lua/ge/extensions/editor/*.lua 并加载
-- （本 mod 的主加载方式）。此脚本是第二道保险：BeamNG 启动时还会执行 mod 内
-- /scripts/modScript.lua，两者任一成功即可生效，重复加载是安全的（幂等）。
local extName = 'editor_zhcnLocalization'

if setExtensionUnloadMode then
  pcall(setExtensionUnloadMode, extName, 'manual')
end

if extensions and extensions.load then
  pcall(extensions.load, extName)
end
