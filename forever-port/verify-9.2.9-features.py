"""Exercise new flight lifecycle and explicit renderer/prediction ownership."""
from pathlib import Path
from lupa.lua51 import LuaRuntime
import runpy

ROOT=Path(__file__).resolve().parents[2]
def source(name): return (ROOT/name).read_text(encoding='utf-8-sig')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
EUI_FOREVER=true; EllesmereUIDB={activeProfile='Personal',profiles={Personal={sentinel=42}}}
SlashCmdList={}; messages={}; function print(s) messages[#messages+1]=s end
function InCombatLockdown() return combat end
''')
lua.execute(source('EllesmereUI/EllesmereUI_CustomControls.lua'))
lua.execute('''
assert(EllesmereUIDB.foreverGroupRenderer==nil)
SlashCmdList.EUIFOREVERGROUPS(''); assert(EllesmereUIDB.foreverGroupRenderer==nil)
combat=true; SlashCmdList.EUIFOREVERGROUPS('official'); assert(EllesmereUIDB.foreverGroupRenderer==nil)
combat=false; SlashCmdList.EUIFOREVERGROUPS('official'); assert(EllesmereUIDB.foreverGroupRenderer=='official')
assert(EllesmereUIDB.profiles.Personal.sentinel==42)
''')
# The actual native adapter must exit before even asking for native frames.
lua.execute(source('EllesmereUIRaidFrames/EllesmereUIRaidFrames_Forever.lua'))
lua.execute('assert(not EUI_FOREVER_NATIVE_GROUPS); SlashCmdList.EUIFOREVERGROUPS("native"); assert(EllesmereUIDB.foreverGroupRenderer=="native")')
for p in (ROOT/'EllesmereUIRaidFrames').glob('*.lua'):
    if p.name=='EllesmereUIRaidFrames_Forever.lua': continue
    lua.execute('EUI_FOREVER_NATIVE_GROUPS=true')
    lua.execute(p.read_text(encoding='utf-8-sig'))
print('PASS: explicit group renderer selection, combat refusal, unchanged profile and all custom-engine chunks inert under native ownership')

flight=source('EllesmereUIForeverEssentials/EllesmereUIForeverEssentials_FlightTimer.lua')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
EllesmereUI={IS_FOREVER=true,BuildBarTextureTables=function() return {},{},{} end,
    _FlightTimerRoutes={[10002]=3040,[20003]=1520}}
EllesmereUIDB={}; clock=0; taxi=false; perk=false; hooks={}; frames={}
function GetTime() return clock end
function UnitOnTaxi() return taxi end
function GetTaxiMapID() return map end; map=1
C_TaxiMap={GetAllTaxiNodes=function() return {{slotIndex=1,nodeID=1},{slotIndex=2,nodeID=2},{slotIndex=3,nodeID=3}} end}
function GetNumRoutes(slot) return slot-1 end
function TaxiGetNodeSlot(slot,hop,from) return from and hop or hop+1 end
function TaxiNodeName() return 'Destination' end
C_Traits={GetConfigIDByTreeID=function() return 1 end,GetNodeInfo=function() return {activeRank=perk and 1 or 0} end}
C_Timer={NewTicker=function(_,fn) return {callback=fn,Cancel=function(self) self.cancelled=true end} end}
C_DurationUtil={CreateDuration=function() return {SetTimeFromStart=function(self,start,duration) self.duration=duration end} end}
Enum={StatusBarInterpolation={Immediate=0},StatusBarTimerDirection={ElapsedTime=0}}
function hooksecurefunc(name,fn) hooks[name]=fn end
function CreateFrame()
 local f={events={}}; frames[#frames+1]=f
 function f:SetScript(_,fn) self.event=fn end
 function f:RegisterEvent(e) self.events[e]=true end
 function f:UnregisterAllEvents() self.events={} end
 return f
end
''')
prefix=flight[:flight.index('local function ApplyPosition()')]
logic=flight[flight.index('local function EndFlight()'):flight.index('-- Options-page entry points.')]
lua.execute(prefix+'''
local function CreateBar()
 if bar then return end
 local function label() return {SetText=function(self,t) self.text=t end} end
 bar={dest=label(),time=label(),Show=function(self) self.shown=true end,
      Hide=function(self) self.shown=false end,
      SetTimerDuration=function(self,duration) self.duration=duration.duration end}
end
local function ApplyFillColor() end
'''+logic+'''
T={Route=RouteYards,Apply=Apply,Event=OnEvent,
 State=function() return flight,bar,ticker,pending end}
''')
lua.execute('''
assert(T.Route(3)==4560); map=nil; assert(T.Route(3)==nil); map=1
EllesmereUI._FlightTimerRoutes[20003]=nil; assert(T.Route(3)==nil)
EllesmereUI._FlightTimerRoutes[20003]=1520
T.Apply(); assert(next(hooks)==nil and EllesmereUIDB.flightTimer==nil)
EllesmereUIDB.flightTimer={enabled=true}; T.Apply()
assert(hooks.TakeTaxiNode and hooks.TaxiRequestEarlyLanding)
hooks.TakeTaxiNode(2); T.Event(nil,'PLAYER_CONTROL_LOST'); assert(T.State()==nil,'stun started taxi')
taxi=true; clock=1; T.Event(nil,'PLAYER_CONTROL_LOST')
local f,b=T.State(); assert(f.eta==100 and b.shown and b.duration==100)
clock=101;taxi=false;T.Event(nil,'PLAYER_CONTROL_GAINED'); assert(T.State()==nil and not b.shown)
assert(math.abs(EllesmereUIDB.flightTimer.speed-30.4)<.00001)
perk=true;hooks.TakeTaxiNode(2);taxi=true;T.Event(nil,'PLAYER_CONTROL_LOST')
f,b=T.State(); assert(math.abs(f.eta-100/1.2)<.00001)
hooks.TaxiRequestEarlyLanding();clock=120;taxi=false;T.Event(nil,'PLAYER_CONTROL_GAINED')
assert(EllesmereUIDB.flightTimer.speed==30.4,'early landing trained speed')
hooks.TakeTaxiNode(2);clock=130;taxi=true;T.Event(nil,'PLAYER_CONTROL_LOST');assert(T.State()==nil,'stale click started flight')
map=nil;hooks.TakeTaxiNode(2);T.Event(nil,'PLAYER_CONTROL_LOST');f,b=T.State();assert(f and f.eta==nil and b.shown)
EllesmereUIDB.flightTimer.enabled=false;T.Apply();assert(T.State()==nil and not b.shown)
for _,f in ipairs(frames) do assert(next(f.events)==nil) end
''')
print('PASS: actual flight route aggregation, missing routes, disabled default, taxi-vs-stun, stale click, ETA, Frequent Flier, normal/early landing calibration and disable cleanup')

test=runpy.run_path(str(ROOT/'EllesmereUI/forever-port/verify-heal-prediction.py'))
lua=test['lua']
# Use the same real production geometry fixture after all existing regressions.
lua.execute('''
local f=OWNERSHIP_FRAME
units.geometry={maximum=100,current=50,incoming=20,healAbsorb=0}
ns.ForeverSetPredictionOwner(f,true)
assert(f.ForeverIncomingHeal.value==0)
ns.ForeverRefreshHealPrediction(f,'geometry','Official');assert(f.ForeverIncomingHeal.value==0)
ns.ForeverSetPredictionOwner(f,false)
ns.ForeverRefreshHealPrediction(f,'geometry','Local');assert(f.ForeverIncomingHeal.value==20)
''')
print('PASS: explicit official heal opt-in suppresses local drawing and switching back restores local prediction')
