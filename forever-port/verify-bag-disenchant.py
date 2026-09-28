"""Offline button lifecycle checks; actual protected execution needs an in-game check."""
from pathlib import Path
import os
import re
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
source = (root.parent / 'EllesmereUIBags/EllesmereUIBags.lua').read_text(encoding='utf-8-sig')
helper = re.search(r'local function CreateDisenchantButton\(header, bagsBtn\).*?\nend\n', source, re.S).group()
lua = LuaRuntime()
lua.execute('assert(loadstring(...))', source)
native_root = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns'))
restricted = (native_root / 'Blizzard_RestrictedAddOnEnvironment/RestrictedExecution.lua').read_text()
compiler = re.search(r'local function BuildRestrictedClosure\(body, env, signature\).*?\nend\n', restricted, re.S).group()
# Reproduce this client's missing restricted compiler using Blizzard's function.
# Regular loadstring still exists in Lua; it is not the function at fault.
lua.execute(compiler + '\nCompileSnippet = BuildRestrictedClosure')
ok, error = lua.eval('pcall(CompileSnippet, \'if newstate == "hide" then self:Hide() end\', {}, "self,newstate")')
assert not ok and 'loadstring_untainted' in error and 'nil value' in error
print('PASS: reproduced restricted-handler compilation failure with missing loadstring_untainted')
lua.execute('''
combat, known, secureExecution = false, true, false
frames = {}
local methods = {}
local function check(self)
    assert(not (self.protected and combat and not secureExecution), "protected write during combat")
end
function methods:SetScript(k, v) self.scripts[k] = v end
function methods:Hide()
    check(self)
    local wasShown = self.shown
    self.shown = false
    if wasShown and self.scripts.OnHide then self.scripts.OnHide(self) end
end
function methods:Show() check(self); self.shown = true end
function methods:SetShown(v) if v then self:Show() else self:Hide() end end
function methods:IsShown() return self.shown end
function methods:IsVisible() return self.shown and (not self.parent or self.parent:IsVisible()) end
function methods:SetAttribute(k,v)
    check(self)
    local old = self.attrs[k]
    self.attrs[k] = v
    if old == v then return end
    if self.scripts.OnAttributeChanged then self.scripts.OnAttributeChanged(self,k,v) end
    if k:sub(1,6) == "state-" and self.attrs["_onstate-" .. k:sub(7)] then
        CompileSnippet(self.attrs["_onstate-" .. k:sub(7)], {}, "self,newstate")
    end
end
function methods:GetAttribute(k) return self.attrs[k] end
function methods:SetPoint(...) check(self); self.point = {...}; self.moves = (self.moves or 0) + 1 end
function methods:ClearAllPoints() check(self); self.point = nil end
function methods:SetSize(w,h) check(self); self.w,self.h = w,h end
function methods:GetCenter() return self.x or 200,self.y or 300 end
function methods:GetEffectiveScale() return self.scale or (self.parent and self.parent:GetEffectiveScale()) or 1 end
function methods:GetFrameLevel() return self.level or 100 end
function methods:SetFrameLevel(v) check(self); self.level = v end
function methods:GetFrameStrata() return self.strata or "HIGH" end
function methods:SetFrameStrata(v) check(self); self.strata = v end
function methods:RegisterForClicks(...) check(self); self.clicks = {...} end
function methods:CreateTexture() return CreateFrame("Texture",nil,self) end
function methods:CreateMaskTexture() return CreateFrame("MaskTexture",nil,self) end
function methods:SetDesaturated(v) self.desaturated = v end
for _, key in ipairs({"EnableMouse", "SetAllPoints", "SetTexture", "SetTexCoord", "SetAlpha", "RegisterEvent", "AddMaskTexture"}) do
    methods[key] = function() end
end
function CreateFrame(kind,name,parent,template)
    local f = setmetatable({name=name,parent=parent,shown=true,scripts={},attrs={},
        protected=template ~= nil}, {__index=methods})
    assert(not (f.protected and combat), "secure frame created during combat")
    frames[#frames+1] = f
    if name then _G[name] = f end
    return f
end
function InCombatLockdown() return combat end
strmatch = string.match
table.wipe = function(t) for k in pairs(t) do t[k] = nil end end
function SecureCmdOptionParse(condition)
    if combat and condition:find("[combat] hide", 1, true) then return "hide" end
    if condition:find("; show", 1, true) then return "show" end
    return nil
end
function TickStateDrivers()
    secureExecution = true
    SecureStateDriverManager.scripts.OnUpdate(SecureStateDriverManager, 1)
    secureExecution = false
end
function IsPlayerSpell(id) assert(id == 13262); return known end
C_SpellBook = {IsSpellKnown=IsPlayerSpell}
EllesmereUI = {L=function(s) return s end}
GameTooltip = {SetOwner=function() end,SetSpellByID=function() end,AddLine=function() end,
    Show=function() end,Hide=function() end}
UIParent = CreateFrame("Frame")
EUI_Bags = CreateFrame("Frame",nil,UIParent)
header = CreateFrame("Frame",nil,EUI_Bags)
bagsBtn = CreateFrame("Button",nil,header)
''')
lua.execute((native_root / 'Blizzard_RestrictedAddOnEnvironment/SecureStateDriver.lua').read_text())
lua.execute(helper + '\nCreateForTest = CreateDisenchantButton')
lua.execute('''
local anchorIndex = #frames + 1
CreateForTest(header,bagsBtn)
local anchor = frames[anchorIndex]
local button = EUI_Bags._disenchantBtn
assert(anchor.point[2] == bagsBtn and anchor.point[3] == "LEFT")
assert(button:IsShown() and button.parent == UIParent)
assert(button.point[2] == UIParent and button.attrs.type1 == "spell" and button.attrs.spell1 == 13262)
assert(button.clicks[1] == "LeftButtonUp" and button.attrs.useOnKeyDown == false)
assert(not button.scripts.OnClick, "must preserve inherited secure OnClick")
local moves = button.moves
anchor.scripts.OnUpdate()
assert(button.moves == moves, "stationary bags should not rewrite geometry")
anchor.x,anchor.y,anchor.scale = 500,250,0.8
anchor.scripts.OnUpdate()
assert(button.point[4] == 400 and button.point[5] == 200 and math.abs(button.w - 19.2) < 0.0001)
EUI_Bags:Hide(); anchor.scripts.OnHide()
assert(not button:IsShown())
EUI_Bags:Show(); anchor.scripts.OnShow()
assert(button:IsShown())
combat = true
-- Run Blizzard's state driver, including its special visibility path.
TickStateDrivers()
anchor.scripts.OnEvent(); anchor.scripts.OnUpdate()
assert(not button:IsShown() and anchor.icon.desaturated)
EUI_Bags:Hide(); anchor.scripts.OnHide()
EUI_Bags:Show(); anchor.scripts.OnShow(); EUI_Bags:Hide()
combat = false; TickStateDrivers(); anchor.scripts.OnEvent()
assert(not button:IsShown(), "must not reappear after closing bags in combat")
TickStateDrivers()
assert(not button:IsShown(), "periodic driver scans must not show closed bags' button")
EUI_Bags:Show(); anchor.scripts.OnShow()
assert(button:IsShown() and not anchor.icon.desaturated)
known = false; anchor.scripts.OnEvent()
TickStateDrivers()
assert(not anchor:IsShown() and not button:IsShown())
known = true; anchor.scripts.OnEvent()
assert(anchor:IsShown() and button:IsShown())
C_SpellBook = nil; anchor.scripts.OnEvent()
assert(button:IsShown(), "legacy spell-known fallback")
-- Reload/open in combat: defer creating a secure button until combat ends.
combat = true
local first = #frames + 1
CreateForTest(header,bagsBtn)
local deferred = frames[first]
local beforeRegen = #frames
for i = first,beforeRegen do assert(not frames[i].protected, "only unprotected visuals created in combat") end
combat = false; deferred.scripts.OnEvent()
assert(#frames == beforeRegen + 1 and EUI_Bags._disenchantBtn:IsShown())
''')

native = (Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_FrameXML/SecureTemplates.lua').read_text()
spell_action = re.search(r'SECURE_ACTIONS.spell =.*?\n    end;', native, re.S).group()
lua.execute('''
SECURE_ACTIONS = {}
function SecureButton_GetModifiedAttribute(self, name, button) return self.attrs[name .. "1"] end
function CastSpellByID(id, unit) castID, castUnit = id, unit end
''')
lua.execute(spell_action)
lua.execute('''
SECURE_ACTIONS.spell(EUI_Bags._disenchantBtn, nil, "LeftButton")
assert(castID == 13262 and castUnit == nil, "native action must cast untargeted Disenchant")
''')
print('PASS: Lua 5.1 syntax; header placement; native state driver and spell dispatch; visibility; movement/scale; cached geometry; combat lifecycle; profession changes; combat initialization')
