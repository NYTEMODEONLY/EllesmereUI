"""Load actual FT UI/config/skin with mocked frames; exercise lifecycle and controls."""
from pathlib import Path
import sys
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2] / 'ForeverThreat'
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().lateSkin = '--late' in sys.argv
lua.execute(r'''
FT={}; SlashCmdList={}; RAID_CLASS_COLORS={WARRIOR={r=.78,g=.61,b=.43}}
function GetLocale() return 'enUS' end
function issecretvalue() return false end
function UnitAffectingCombat() return false end
function GetTime() return 0 end
DEFAULT_CHAT_FRAME={AddMessage=function() end}
local methods={}
function methods:IsObjectType(k) return self.kind==k or k=='Button' and self.kind=='CheckButton' end
function methods:SetSize(w,h) self.w=w; self.h=h end
function methods:SetWidth(w) self.w=w end
function methods:SetHeight(h) self.h=h end
function methods:GetWidth() return self.w or 274 end
function methods:GetHeight() return self.h or 140 end
function methods:SetFont(p,s,f)
 assert(type(s)=='number' and s>0 and s<math.huge, 'Invalid font height: height must be > 0')
 self.font={p,s,f}
end
function methods:GetFont() if self.font then return unpack(self.font) end; return nil,0,'' end
function methods:SetText(s) self.text=s; if self.label then self.label:SetText(s) end end
function methods:GetText() return self.text end
function methods:SetTextColor(...) self.color={...} end
function methods:GetTextColor() return unpack(self.color or {1,1,1,1}) end
function methods:SetColorTexture(...) self.color={...} end
function methods:SetVertexColor(...) self.color={...} end
function methods:SetStatusBarColor(...) self.barColor={...} end
function methods:SetStatusBarTexture(v) self.texture=v end
function methods:SetValue(v) self.value=v; if self.scripts.OnValueChanged then self.scripts.OnValueChanged(self,v) end end
function methods:SetChecked(v) self.checked=v end
function methods:GetChecked() return self.checked end
function methods:SetPoint(...) self.point={...} end
function methods:GetPoint() return 'CENTER',nil,'CENTER',30,40 end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:SetShown(v) self.shown=v end
function methods:IsShown() return self.shown end
function methods:GetFrameLevel() return 1 end
function methods:SetScript(k,fn) self.scripts[k]=fn end
function methods:GetChildren() return unpack(self.children) end
function methods:GetRegions() return unpack(self.regions) end
function methods:GetFontString() return self.label end
function methods:SetThumbTexture() self.thumb=self.thumb or self:CreateTexture() end
function methods:GetThumbTexture() return self.thumb end
function methods:CreateFontString(name,layer,template)
 local f=New('FontString'); if template then f:SetFont('stock',12,'') end
 self.regions[#self.regions+1]=f; return f
end
function methods:CreateTexture()
 local f=New('Texture'); self.regions[#self.regions+1]=f; return f
end
for _,k in ipairs({'SetAllPoints','ClearAllPoints','SetJustifyH','SetJustifyV','SetWordWrap','SetBackdrop',
 'SetBackdropColor','SetBackdropBorderColor','SetAlpha','SetScale','SetFrameStrata','SetFrameLevel',
 'SetClampedToScreen','SetResizable','SetResizeBounds','SetMovable','EnableMouse','RegisterForDrag',
 'StartMoving','StopMovingOrSizing','StartSizing','RegisterEvent','SetNormalTexture','SetHighlightTexture',
 'SetPushedTexture','SetMinMaxValues','SetShadowOffset','SetShadowColor','SetValueStep','SetObeyStepOnDrag',
 'SetTexture','LockHighlight','UnlockHighlight','Raise'}) do methods[k]=function() end end
function New(kind) return setmetatable({kind=kind,shown=true,children={},regions={},scripts={}}, {__index=methods}) end
function CreateFrame(kind,name,parent,template)
 local f=New(kind or 'Frame')
 if parent then parent.children[#parent.children+1]=f end
 if name then _G[name]=f end
 if template and template:find('ButtonTemplate') then f.label=f:CreateFontString(nil,'OVERLAY','GameFontNormal') end
 return f
end
UIParent=CreateFrame('Frame')
GameTooltip={SetOwner=function() end,AddLine=function() end,Show=function() end,Hide=function() end}
function hooksecurefunc(t,k,fn)
 local old=t[k]; assert(type(old)=='function',k)
 t[k]=function(...) local out={old(...)}; fn(...); return unpack(out) end
end
local ar,ag,ab=.72,.52,.31
function setAccent(r,g,b) ar,ag,ab=r,g,b end
S={}
for _,k in ipairs({'Shell','CloseButton','Button','StateButtonLabel','Checkbox'}) do
 S[k]=function(f) assert(f,k..' missing frame'); f['skin'..k]=true end
end
function S.Font(f,r,g,b) f:SetFont('EUI-font',select(2,f:GetFont())); if r then f:SetTextColor(r,g,b) end end
function S.GetFont() return 'EUI-font','OUTLINE' end
function S.GetAccentColor() return ar,ag,ab end
function S.FadeRegions(f) for _,r in ipairs(f.regions) do r:SetAlpha(0) end end
function S.ApplyBarFill(f) f:SetStatusBarColor(ar,ag,ab,.8) end
function S.OnLooksChanged(fn) looksChanged=fn end
EllesmereUI={RegisterSkin=function(name,fn) assert(name=='ForeverThreat'); registerSkin=fn end}
''')
compile_lua = lua.eval('function(s,n) local f,e=loadstring(s,n); assert(f,e); return f end')
for name in ('Core.lua','Localization.lua','Threat.lua','UI.lua','Config.lua','EllesmereSkin.lua'):
    compile_lua((root/name).read_text(encoding='utf-8-sig'), name)('ForeverThreat',lua.globals().FT)
lua.execute(r'''
FT.db={}; for k,v in pairs(FT.defaults) do FT.db[k]=v end
samples={{name='Tank',classToken='WARRIOR',isPlayer=true,isAggroHolder=true,isTanking=true,
 scaled=100,rawThreat=243,threatDelta=0,connected=true},
 {name='DPS',classToken='WARRIOR',scaled=52,rawThreat=140,threatDelta=-103,connected=true}}
function FT:GetThreatData() return samples,'Spider' end
-- Skin registration before lazy UI creation must work.
if lateSkin then FT:CreateUI(); FT:OpenConfig('display'); registerSkin(S)
else registerSkin(S); FT:CreateUI() end
FT:Refresh()
assert(FT.frame.skinShell and FT.frame.closeButton.skinCloseButton and FT.configButton.skinButton)
assert(FT.frame.title.text=='ForeverThreat' and FT.frame.title.font[1]=='EUI-font')
assert(FT.rows[1].value==100 and FT.rows[2].value==52)
assert(FT.rows[2].threat.text=='140' and FT.rows[2].delta.text=='-103')
assert(FT.rows[1].texture=='Interface\\Buttons\\WHITE8X8')
assert(FT.rows[1].name.text:find('|cffffd200',1,true)==nil)
assert(FT.rows[1].barColor[1]==.78, 'Class colors must remain available')
FT.db.useClassColors=false; FT:Refresh(); assert(FT.rows[1].barColor[1]==.72)
FT.db.fontSize=15; FT:RefreshLayout(); assert(FT.rows[1].name.font[2]==15)
samples[2].scaled=80; FT:Refresh(); assert(FT.rows[2].percent.color[2]==.82)
samples[2].scaled=95; FT:Refresh(); assert(FT.rows[2].percent.color[2]==.35)
FT:OpenConfig('display')
assert(FT.configFrame.skinShell and FT.configFrame.closeButton.skinCloseButton)
assert(FT.configFrame.tabs.display._euiActiveLine.shown)
assert(not FT.configFrame.tabs.warnings._euiActiveLine.shown)
local check=FT.configFrame.pages.display.controls.showPets
assert(check.skinCheckbox); check:SetChecked(true); check.scripts.OnClick(check); assert(FT.db.showPets)
local slider=FT.configFrame.pages.display.controls.fontSize
assert(slider.thumb and slider.thumb.w==8 and slider.thumb.h==14)
slider:SetValue(13); assert(FT.db.fontSize==13)
FT:SelectConfigTab('warnings'); assert(FT.configFrame.tabs.warnings._euiActiveLine.shown)
FT.frame.scripts.OnDragStop(FT.frame); assert(FT.db.x==30 and FT.db.y==40)
FT.configButton.scripts.OnClick(); assert(FT.db.configLastTab=='display')
setAccent(.2,.7,.5); looksChanged(); assert(FT.rows[1].barColor[1]==.2)
assert(FT.configFrame.title.color[1]==.2 and slider.thumb.color[1]==.2)
samples={}; FT:Refresh(); assert(FT.rows[1]._ellesmereEntry==nil and not FT.rows[2].shown)
FT.frame.closeButton.scripts.OnClick(); assert(not FT.db.visible and not FT.frame.shown)
print('PASS: native FT UI + theme lifecycle, values/class colors, font/column preferences, lazy config, checkbox/slider/tab controls, drag/close, accent refresh and empty-state cleanup.')
''')
for toc in root.glob('*.toc'):
    content = toc.read_text()
    assert '## OptionalDeps: EllesmereUI' in content and content.count('EllesmereSkin.lua') == 1
print('PASS: both installed TOCs load the optional EllesmereUI skin.')
