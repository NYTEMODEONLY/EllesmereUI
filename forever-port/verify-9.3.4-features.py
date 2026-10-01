"""v9.3.4 actual combat queue and official optional group-buff painter gates.

Offline state checks; no live secure execution, aura access or rendering claim.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
def source(name): return (ROOT/name).read_text(encoding='utf-8-sig')

text=source('EllesmereUI/EllesmereUI_Ticker.lua')
chunk=text[text.index('local function QueueErrorHandler'):text.index('-- The shared driver:')]
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
EllesmereUI={}; frames={}; errors={}; runs={}
function geterrorhandler() return function(e) errors[#errors+1]=e end end
function CreateFrame()
 local f={events={}}; frames[#frames+1]=f
 function f:SetScript(_,fn) self.fn=fn end
 function f:RegisterEvent(e) self.events[e]=true end
 function f:UnregisterEvent(e) self.events[e]=nil end
 return f
end
''')
lua.execute(chunk)
lua.execute('''
local q=EllesmereUI.CombatQueue; local f=frames[1]
assert(not f.events.PLAYER_REGEN_ENABLED)
q.Defer('layout',function() runs[#runs+1]='old' end)
q.Defer('other',function() runs[#runs+1]='other' end)
q.Defer('layout',function()
 runs[#runs+1]='latest'
 q.Defer('next',function() runs[#runs+1]='next' end)
end)
q.Defer('failure',function() error('queue diagnostic') end)
q.Defer('tail',function() runs[#runs+1]='tail' end)
assert(q.Has('layout') and f.events.PLAYER_REGEN_ENABLED and #runs==0)
f.fn(f)
assert(runs[1]=='latest' and runs[2]=='other' and runs[3]=='tail')
assert(#errors==1 and errors[1]:find('queue diagnostic',1,true))
assert(not q.Has('layout') and q.Has('next') and f.events.PLAYER_REGEN_ENABLED)
f.fn(f); assert(runs[4]=='next' and not f.events.PLAYER_REGEN_ENABLED)
''')
print('PASS: official core combat queue deduplicates current state, preserves FIFO/errors and defers requeued work')

text=source('EllesmereUIRaidFrames/EUI_RaidFrames_ForeverMissingBuffs.lua')
chunk=text[text.index('local paintList = {}'):text.index('local function PaintUnit(unit)')]
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
enabled=true; settings={}; state={party1={fort=false}}; provider={fort=true}
NUM_FAMILIES=1; FAMILIES={{key='fort'}}; ns={LVL_MARKER=4}; allocations=0
function SettingsFor() return settings end
function HideOverlay(o) o.hidden=true end
function FamOn() return true end
function Overlay() allocations=allocations+1; return {} end
function Layout(o,s,h,list,n) o.hidden=false; o.count=n end
btn={GetAttribute=function() return 'party1' end,GetFrameLevel=function() return 1 end}
data={health={}}
''')
lua.execute(chunk+'\nPaint=PaintButton')
lua.execute('''
Paint(btn,data); assert(allocations==0,'unset new display changed existing appearance')
settings.showMissingBuffs=false; Paint(btn,data); assert(allocations==0)
settings.showMissingBuffs=true; Paint(btn,data); assert(allocations==1 and data.fvMissing.count==1)
settings.showMissingBuffs=false; Paint(btn,data); assert(data.fvMissing.hidden and allocations==1)
settings.showMissingBuffs=true; enabled=false; Paint(btn,data); assert(data.fvMissing.hidden)
enabled=true; state.party1.fort=true; Paint(btn,data); assert(data.fvMissing.count==0)
''')
print('PASS: official group missing-buff painter is opt-in, honors OFF/provider state and reuses its overlay')

toc=source('EllesmereUI/EllesmereUI.toc')
for owner in ('EllesmereUI_PixelPerfect.lua','EllesmereUI_Popups.lua','EllesmereUI_Fonts.lua','EllesmereUI_VisibilityRules.lua','EllesmereUI_SharedHelpers.lua','EllesmereUI_ProfileSync.lua','EllesmereUI_SpellCostPrediction.lua'):
    assert owner in toc and (ROOT/'EllesmereUI'/owner).is_file(),owner
assert toc.index('EllesmereUI_ClientGate.lua')<toc.index('EllesmereUI_Forever.lua')<toc.index('EllesmereUI.lua')
assert 'local function WirePopupEscape(' not in source('EllesmereUI/EllesmereUI.lua')
assert 'opts.allowWorldInput' in source('EllesmereUI/EllesmereUI_Popups.lua')
assert 'ns.RF_LEVEL_DEFAULT = "none"' in source('EllesmereUIRaidFrames/EllesmereUIRaidFrames.lua')
print('PASS: upstream split owners execute through the manifest; custom popup contract moved and optional group level text stays off')
