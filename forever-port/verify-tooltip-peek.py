"""Exercise the real tooltip-peek walker with a modeled native text status bar.

The model reproduces the persistent lockShow mutation and later close failure;
it does not emulate WoW's secure execution engine.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT.parent / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin.lua").read_text(encoding="utf-8-sig")
start = source.index("    local function IsFrameForbidden(frame)")
end = source.index('    local modWatcher = CreateFrame("Frame")', start)
walker = source[start:end] + "\nreturn FireHoveredOnEnter"

fixture = r'''
WorldFrame = {}; UIParent = {}; EllesmereUI = {}
GameTooltip = {shown=false}
function GameTooltip:IsShown() return self.shown end
function GameTooltip:SetUnit(unit) assert(unit=='mouseover'); self.unit=unit end
function GameTooltip:Show() self.shown=true end
function GameTooltip_SetDefaultAnchor(_, frame) GameTooltip.anchor=frame end
function UnitExists(unit) assert(unit=='mouseover'); return mouseover end
function GetMouseFoci() return foci end
function GetMouseFocus() return foci[1] end
function Frame(parent, enter)
    local f = {parent=parent, enter=enter, calls=0}
    function f:IsForbidden() return self.forbidden end
    function f:IsProtected() return self.protected end
    function f:GetParent() assert(not self.forbidden); return self.parent end
    function f:GetScript(script)
        assert(not self.forbidden and not self.protected)
        assert(script=='OnEnter'); return self.enter
    end
    return f
end
function Reset()
    GameTooltip.shown=false; GameTooltip.unit=nil; GameTooltip.anchor=nil
    mouseover=false; addonCall=false
    owner=Frame(UIParent, function(self) self.calls=self.calls+1 end)
    bar=Frame(owner)
    bar.lockShow=1; bar.counterTainted=false; bar.formatCalls=0
    function bar:UpdateTextString()
        self.formatCalls=self.formatCalls+1
        assert(not self.counterTainted, 'secret number comparison after tainted lockShow')
    end
    function bar:ShowStatusBarText()
        self.lockShow=self.lockShow+1
        self.counterTainted=self.counterTainted or addonCall
        self:UpdateTextString()
    end
    function bar:HideStatusBarText()
        if self.lockShow>0 then self.lockShow=self.lockShow-1 end
        self:UpdateTextString()
    end
    function bar:OnStatusBarEnter() self:ShowStatusBarText(); self:UpdateTextString() end
    bar.enter=bar.OnStatusBarEnter
    foci={bar}
end
function Peek()
    addonCall=true; peek(); addonCall=false
end
'''

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(fixture)
# Demonstrate that the previous walker changes lockShow even though pcall
# swallows the formatter error; a later native CharacterFrame close still fails.
lua.globals().peek = lua.execute(walker.replace('if IsTextStatusBar(frame) then break end', ''))
lua.execute('''
Reset(); Peek()
assert(bar.lockShow==2 and bar.counterTainted)
assert(not pcall(bar.HideStatusBarText,bar))
''')
print('PASS: previous peek reproduces persistent counter mutation and later close failure')

lua.globals().peek = lua.execute(walker)
lua.execute('''
Reset(); Peek(); Peek()
assert(bar.lockShow==1 and not bar.counterTainted and bar.formatCalls==0)
assert(owner.calls==0, 'walk escaped the status-bar boundary')
bar:HideStatusBarText()
assert(bar.lockShow==0 and bar.formatCalls==1)

-- An overlay without a handler must not lead to a native status-bar replay.
Reset(); foci={Frame(bar)}; Peek()
assert(bar.lockShow==1 and bar.formatCalls==0 and owner.calls==0)

-- Still reveal a mouseover unit tooltip without running any status-text code.
Reset(); mouseover=true; Peek()
assert(GameTooltip.shown and GameTooltip.unit=='mouseover')
assert(bar.lockShow==1 and not bar.counterTainted and bar.formatCalls==0)

-- Module-built tooltip handlers continue to work, including parent walks.
Reset()
local addon=Frame(UIParent, function(self) self.calls=self.calls+1; GameTooltip:Show() end)
foci={bar,Frame(addon)}; Peek()
assert(addon.calls==1 and GameTooltip.shown and bar.lockShow==1)

Reset(); bar.forbidden=true; Peek(); assert(bar.lockShow==1)
Reset(); local protected=Frame(UIParent, function() error('protected handler replayed') end)
protected.protected=true; foci={protected}; Peek()

-- The legacy focus API gets the same guard.
Reset(); GetMouseFoci=nil; Peek(); assert(bar.lockShow==1 and bar.formatCalls==0)
''')
print('PASS: text-bar counters/formatters untouched; parent boundary, module tips, unit fallback, forbidden/protected frames and legacy focus preserved')
