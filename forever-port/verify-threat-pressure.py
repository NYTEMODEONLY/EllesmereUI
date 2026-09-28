"""Official threat handoff: replaces the retired badge's behavior contract.
Original badge source/tests are retained in the complete external before backup.
No WoW input or execution of saved Lua; synthetic profiles only.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2]
def source(n): return (ROOT/n).read_text(encoding='utf-8-sig')
lua=LuaRuntime(unpack_returned_tuples=True)
handoff=source('EllesmereUINameplates/EllesmereUINameplates_ThreatPressure.lua')
lua.execute(r"""
EUI_FOREVER=true; EllesmereUI={IS_FOREVER=true}
function CreateFrame() error('retired badge allocated a frame') end
function hooksecurefunc() error('retired badge hooked a frame') end
C_Timer=setmetatable({}, {__index=function() error('retired badge started a timer') end})
SlashCmdList={}; ns={defaults={}}
on={threatPressureEnabled=true,threatPctSize=14,threatPctPosition='LEFT'}
off={threatPressureEnabled=false}; explicitOff={threatPctEnabled=false}
officialOn={threatPctEnabled=true,threatPressureEnabled=false}
legacyDefault={}; fresh={addons={}}
EllesmereUIDB={profiles={on={addons={EllesmereUINameplates=on}},off={addons={EllesmereUINameplates=off}},
 explicitOff={addons={EllesmereUINameplates=explicitOff}},officialOn={addons={EllesmereUINameplates=officialOn}},
 legacy={addons={EllesmereUINameplates=legacyDefault}},fresh=fresh}}
""")
lua.execute(handoff,'Nameplates',lua.globals().ns)
lua.execute("assert(on.threatPctEnabled and not off.threatPctEnabled and not explicitOff.threatPctEnabled and officialOn.threatPctEnabled and legacyDefault.threatPctEnabled); assert(on.threatPctSize==14 and on.threatPctPosition=='LEFT' and on.threatPressureEnabled); assert(fresh.addons.EllesmereUINameplates==nil); on.threatPctEnabled=false")
lua.execute(handoff,'Nameplates',lua.globals().ns)
lua.execute("assert(on.threatPctEnabled==false); assert(next(SlashCmdList)==nil and next(ns.defaults)==nil)")
print('PASS: one-time handoff, explicit false/layout preservation, later OFF, no badge allocations/hooks/timers/commands')
main=source('EllesmereUINameplates/EllesmereUINameplates.lua')
options=source('EllesmereUIOptions/EUI_Nameplates_Options.lua')
assert 'ThreatPressure' not in main and 'BuildThreatPressureOptions' not in options
assert options.count('text="Show Threat % on Nameplates"')==1
start=main.index('ns._npTptOn = false')
end=main.index('ns.EnsureHoverOverlay',start)
# Run the real official painter and nameplate lifecycle, with an opaque numeric
# token. Only native mock sinks unwrap it; Lua math/comparison/stringify fail.
lua.execute(r"""
local baseType=type
secret=setmetatable({}, {__tostring=function() error('secret stringify') end,
 __lt=function() error('secret compare') end,__le=function() error('secret compare') end,
 __add=function() error('secret arithmetic') end})
function type(v) if rawequal(v,secret) then return 'number' end; return baseType(v) end
function issecretvalue(v) return rawequal(v,secret) end
function GetThreatStatusColor(status) return status/3,0.5,0 end
C_CurveUtil={EvaluateColorValueFromBoolean=function(b,t,f) return b and t or f end}
ns={plates={}}; p={threatPctEnabled=true,threatPctColorByThreat=true}
defaults={threatPctPosition='CENTER',threatPctSize=10,threatPctXOffset=0,threatPctYOffset=0}
HP_BAR_SLOTS={{anchor='RIGHT',point='LEFT',xOff=-5},{anchor='LEFT',point='RIGHT',xOff=5},{anchor='CENTER'}}
function GetFont() return 'font' end; function GetNPOutline() return 'outline' end
function SetFSFont(fs,size) fs.size=size end
PP={Point=function(fs,...) fs:SetPoint(...) end}
queries=0; pct=75; status=1; tank=false
function UnitDetailedThreatSituation() queries=queries+1; return tank,status,pct end
allocations=0
function fsNew()
 allocations=allocations+1
 return {SetWordWrap=function() end,Hide=function(s) s.shown=false end,
 SetShown=function(s,v) s.shown=v end,ClearAllPoints=function() end,
 SetPoint=function(s,...) s.point={...} end,SetJustifyH=function() end,
 SetFormattedText=function(s,format,v) s.value=v end,
 SetTextColor=function(s,...) s.color={...} end}
end
plate={health={},unit='nameplate1',healthTextFrame={CreateFontString=fsNew}};ns.plates[1]=plate
""")
paint=source('EllesmereUI/EllesmereUI_UICore.lua')
startp=paint.index('if EllesmereUI.IS_FOREVER then',paint.index('--  Threat % text paint'))
endp=paint.index('end -- IS_FOREVER',startp)+len('end -- IS_FOREVER')
lua.execute(paint[startp:endp]);lua.execute(main[start:end])
lua.execute(r"""
ns.RefreshThreatPct(); assert(plate.threatPctText.shown and plate.threatPctText.value==75 and allocations==1)
pct=secret;status=secret;tank=true; ns.RefreshThreatPct();assert(rawequal(plate.threatPctText.value,secret))
p.threatPctColorByThreat=false;ns.RefreshThreatPct();assert(plate.threatPctText.color[1]==1)
p.threatPctEnabled=false; local count=queries;ns.RefreshThreatPct();assert(not plate.threatPctText.shown and queries==count)
p.threatPctEnabled=true;pct=nil;ns.RefreshThreatPct();assert(not plate.threatPctText.shown)
pct=55;p.threatPctPosition='RIGHT';p.threatPctSize=16;ns.RefreshThreatPct();assert(plate.threatPctText.size==16 and allocations==1)
plate.unit='nameplate2';pct=20;ns.RefreshThreatPct();assert(plate.threatPctText.value==20 and allocations==1)
EllesmereUI.IS_FOREVER=false;ns.RefreshThreatPct();assert(not plate.threatPctText.shown)
""")
assert 'if self._tptShown then self.threatPctText:Hide() end' in main
print('PASS: official painter, opaque percentage sink, toggles, missing data, profile layout, pooled reuse and retail gate')

# Exercise actual cast layout and its existing show/hide callback: positioning
# must follow resolved geometry immediately, without a second threat query/loop.
assert 'BELOW = "Below Health Bar"' in options
cast_start=main.index('function ns.LayoutCastBar(')
cast_end=main.index('-- Size + anchor the cast spell icon',cast_start)
callback_start=main.index('local function OnCastVisibilityChanged(self)')
callback_end=main.index('    plate.cast:HookScript("OnShow"',callback_start)
lua.execute(r"""
EllesmereUI.IS_FOREVER=true;pct=50;p.threatPctPosition='BELOW'
p.threatPctXOffset=4;p.threatPctYOffset=-2
classic=false
ns.NP_Classic=function() return classic end
ns.NP_ClassicCastLayout=function(w,h,ch) return 9,w+8,-5 end
ns.NP_ApplyClassicCastArt=function() end
ns.GetWrapBorderCastbar=function() return false end
function GetHealthBarHeight() return 20 end
function GetShowCastIcon() return false end
defaults.castBarOffsetY=0
PP.perfect=1
plate.GetEffectiveScale=function() return 1 end
plate.cast={shown=false,_timerPlate=plate,IsShown=function(s) return s.shown end,
 ClearAllPoints=function() end,SetSize=function(s,w,h) s.height=h end,
 SetPoint=function(s,...) s.point={...} end}
""")
lua.execute(main[cast_start:cast_end])
lua.execute(main[callback_start:callback_end]+'\nCastVisibilityChanged=OnCastVisibilityChanged')
lua.execute(r"""
ns.LayoutCastBar(plate,150,17);ns.RefreshThreatPct()
local fs=plate.threatPctText
assert(fs.point[1]=='TOP' and fs.point[2]==plate.health and fs.point[3]=='BOTTOM')
assert(fs.point[4]==4 and fs.point[5]==-5 and allocations==1)
local count=queries
plate.cast.shown=true;CastVisibilityChanged(plate.cast);assert(fs.point[5]==-22)
p.castBarOffsetY=-6;ns.LayoutCastBar(plate,150,25);assert(fs.point[5]==-36)
classic=true;ns.LayoutCastBar(plate,150,25);assert(fs.point[5]==-41)
plate.cast.shown=false;CastVisibilityChanged(plate.cast);assert(fs.point[5]==-5)
assert(queries==count and allocations==1)
-- Cast above health must never pull the text into the health bar.
classic=false;p.castBarOffsetY=40;plate.cast.shown=true
ns.LayoutCastBar(plate,150,17);assert(fs.point[5]==-5)
plate.cast.shown=secret;CastVisibilityChanged(plate.cast);assert(fs.point[5]==-5)
plate.cast.shown=false;p.threatPctSize=20;p.threatPctXOffset=-7;p.threatPctYOffset=8
ns.RefreshThreatPct();assert(fs.size==20 and fs.point[4]==-7 and fs.point[5]==5)
for _,position in ipairs({'LEFT','RIGHT','CENTER'}) do
 p.threatPctPosition=position;ns.RefreshThreatPct()
 assert(fs.point[1]==position and fs.point[5]==8)
end
p.threatPctEnabled=false;ns.RefreshThreatPct();assert(not fs.shown)
plate.unit='nameplate3';p.threatPctPosition='BELOW';p.threatPctEnabled=true
pct=secret;ns.RefreshThreatPct();assert(rawequal(fs.value,secret) and allocations==1 and fs.point[1]=='TOP')
""")
print('PASS: Below option, offsets/font size, cast start/end/layout/Classic/focus clearance, opaque state, all inside positions and pooled reuse')
