"""No competing threat-window/settings owner; fallback still works."""
from pathlib import Path
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2]
def source(n):return (ROOT/n).read_text(encoding='utf-8-sig')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute("EllesmereUI={_ModuleNS={},Lite={NewAddon=function() return {} end}}; ns={}")
lua.execute(source('EllesmereUIForeverEssentials/EllesmereUIForeverEssentials.lua'),'EllesmereUIForeverEssentials',lua.globals().ns)
lua.execute("assert(not EllesmereUI.ForeverEmbeddedThreatOwnsDisplay()); EllesmereUI._ModuleNS.EllesmereUIDamageMeters={Threat={}};assert(EllesmereUI.ForeverEmbeddedThreatOwnsDisplay())")
tm=source('EllesmereUIForeverEssentials/EllesmereUIForeverEssentials_ThreatMeter.lua')
begin=tm.index('Get = function(key)');end=tm.index('function ns.GetStyleValue',begin)
lua.execute("EUI=EllesmereUI; cfg={enabled=true,position={x=1,y=2}}; function Read() return cfg end;LEGACY={};DEFAULTS={enabled=false}")
lua.execute(tm[begin:end]);lua.execute("assert(Get('enabled')==false and cfg.enabled==true and cfg.position.x==1); EllesmereUI._ModuleNS.EllesmereUIDamageMeters=nil;assert(Get('enabled')==true)")
bootstrap=tm[tm.index('boot:SetScript("OnEvent", function(self)'):tm.index('--  /euitm')]
lua.execute("boot={SetScript=function(_,_,fn) bootFn=fn end};EllesmereUI._ModuleNS.EllesmereUIDamageMeters={Threat={}}")
lua.execute(bootstrap)
lua.execute("bootFn({UnregisterAllEvents=function() end})") # no window, seed, unlock or listeners
slash=tm[tm.index('SlashCmdList.ELLESMEREUITHREAT = function(input)'):]
lua.execute("SlashCmdList={};function Say(s) said=s end");lua.execute(slash)
lua.execute("SlashCmdList.ELLESMEREUITHREAT('show');assert(cfg.enabled==true and said:find('Damage Meters'))")
opt=source('EllesmereUIOptions/EUI_ForeverEssentials_Options.lua')
lua.execute(r"""
EllesmereUI._ModuleNS.EllesmereUIForeverEssentials={}
EllesmereUIDB={threatMeter={enabled=true},unlockAnchors={EUI_ThreatMeter={x=3}},flightTimer={enabled=true}}
function CreateFrame() return {RegisterEvent=function() end,UnregisterEvent=function() end,
 SetScript=function(s,k,v) s[k]=v end,GetScript=function(s,k) return s[k] end} end
function IsLoggedIn() return true end
function EllesmereUI:RegisterModule(_,v) registered=v end
function EllesmereUI:InvalidatePageCache() end
""")
lua.execute(opt)
lua.execute("assert(#registered.pages==2 and registered.pages[1]=='Travel' and registered.pages[2]=='Loot');assert(registered.buildPage('Threat',{},0)==nil); registered.onReset();assert(EllesmereUIDB.threatMeter.enabled and EllesmereUIDB.unlockAnchors.EUI_ThreatMeter.x==3);EllesmereUI._ModuleNS.EllesmereUIDamageMeters=nil")
lua.execute(opt);lua.execute("assert(#registered.pages==3 and registered.pages[2]=='Threat' and registered.pages[3]=='Loot')")
style=source('EllesmereUIOptions/EUI_Style_Options.lua')
start=style.index('if EllesmereUI.IS_FOREVER and not (EllesmereUI.ForeverEmbeddedThreatOwnsDisplay')
end=style.index('Register("questtracker"',start)
lua.execute("EllesmereUI.IS_FOREVER=true;EllesmereUI._ModuleNS.EllesmereUIDamageMeters={Threat={}}; function Register() error('duplicate style row') end")
lua.execute(style[start:end])
assert 'Register("charsheet"' not in style, 'upstream removed the ineffective style row; do not restore it'
print('PASS: runtime owner gate independent of module file order, no standalone boot/window/unlock/command, settings/style suppression, dormant data and disabled-module fallback')
