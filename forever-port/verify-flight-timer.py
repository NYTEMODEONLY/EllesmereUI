"""Execute the full flight-timer chunk with scheduled taxi-state transitions.

Offline lifecycle regression only; does not prove rendering or live event order.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'EllesmereUIForeverEssentials/EllesmereUIForeverEssentials_FlightTimer.lua').read_text(encoding='utf-8-sig')
SETUP = r'''
clock=0; taxi=false; frames={}; timers={}; hooks={}; bars={}; hookCounts={}
UIParent={}; Enum={StatusBarInterpolation={Immediate=0},StatusBarTimerDirection={ElapsedTime=0}}
EllesmereUIDB={flightTimer={enabled=true}}
EllesmereUI={IS_FOREVER=true, _FlightTimerRoutes={[10002]=3040},
 BuildBarTextureTables=function() return {},{},{} end,
 ELLESMERE_GREEN={r=0,g=1,b=0}, L=function(s) return s end,
 GetFontPath=function() return 'font' end, GetFontOutlineFlag=function() return '' end,
 PrimeFontShadow=function() end, ResolveTexturePath=function() return 'texture' end,
 MakeUnlockElement=function(t) return t end, RegisterUnlockElements=function() end,
 PP={CreateBorder=function() end,UpdateBorder=function() end,ShowBorder=function() end,HideBorder=function() end}}
function GetTime() return clock end
function UnitOnTaxi() return taxi end
function GetTaxiMapID() return 1 end
C_TaxiMap={GetAllTaxiNodes=function() return {{slotIndex=1,nodeID=1},{slotIndex=2,nodeID=2}} end}
function GetNumRoutes() return 1 end
function TaxiGetNodeSlot(_,_,from) return from and 1 or 2 end
function TaxiNodeName() return 'Crossroads' end
C_Traits={GetConfigIDByTreeID=function() return nil end}
C_DurationUtil={CreateDuration=function() return {SetTimeFromStart=function(self,s,d) self.start=s;self.duration=d end} end}
function hooksecurefunc(name,fn) hooks[name]=fn; hookCounts[name]=(hookCounts[name] or 0)+1 end
C_Timer={NewTicker=function(interval,fn)
 local t={interval=interval,callback=fn,due=clock+interval,Cancel=function(self) self.cancelled=true end}
 timers[#timers+1]=t; return t
end}
function Advance(seconds)
 local stop=clock+seconds
 while true do
  local nextTimer
  for _,t in ipairs(timers) do
   if not t.cancelled and t.due<=stop and (not nextTimer or t.due<nextTimer.due) then nextTimer=t end
  end
  if not nextTimer then break end
  clock=nextTimer.due; nextTimer.due=clock+nextTimer.interval; nextTimer.callback()
 end
 clock=stop
end
function ActiveTimers()
 local n=0; for _,t in ipairs(timers) do if not t.cancelled then n=n+1 end end; return n
end
local function region()
 local r={}
 for _,name in ipairs({'SetAllPoints','SetColorTexture','SetFont','ClearAllPoints','SetPoint','SetJustifyH','SetWordWrap','SetWidth'}) do r[name]=function() end end
 function r:Show() self.shown=true end
 function r:Hide() self.shown=false end
 function r:SetText(s) self.text=s end
 return r
end
function CreateFrame(kind)
 local f=region(); frames[#frames+1]=f; f.events={}; f.scripts={}
 if kind=='StatusBar' then bars[#bars+1]=f end
 for _,name in ipairs({'SetMinMaxValues','SetValue','SetSize','SetStatusBarTexture','SetStatusBarColor'}) do f[name]=function() end end
 function f:SetScript(k,fn) self.scripts[k]=fn end
 function f:RegisterEvent(e) self.events[e]=true end
 function f:UnregisterAllEvents() self.events={} end
 function f:CreateTexture() return region() end
 function f:CreateFontString() return region() end
 function f:SetTimerDuration(d) self.duration=d; self.durationCalls=(self.durationCalls or 0)+1 end
 return f
end
function Fire(e)
 for _,f in ipairs(frames) do if f.events[e] then f.scripts.OnEvent(f,e) end end
end
function Visible() return bars[1] and bars[1].shown end
'''

CASES = {
    'normal event, duplicate prevention, landing and calibration': '''
hooks.TakeTaxiNode(2); taxi=true; Fire('PLAYER_CONTROL_LOST')
assert(Visible()); assert(bars[1].duration.duration==100)
Fire('PLAYER_CONTROL_LOST'); Advance(.5)
assert(bars[1].durationCalls==1, 'duplicate takeoff restarted timer')
Advance(99.5); taxi=false; Fire('PLAYER_CONTROL_GAINED')
assert(not Visible() and ActiveTimers()==0)
assert(math.abs(EllesmereUIDB.flightTimer.speed-30.4)<.00001)
''',
    'taxi state delayed until after control-lost event': '''
hooks.TakeTaxiNode(2); Fire('PLAYER_CONTROL_LOST'); assert(not Visible())
Advance(.2); taxi=true; Advance(.2)
assert(Visible(), 'delayed taxi state never started timer')
assert(bars[1].dest.text=='Crossroads' and bars[1].duration.duration==100)
''',
    'takeoff without control-lost event': '''
hooks.TakeTaxiNode(2); Advance(.2); taxi=true; Advance(.2)
assert(Visible(), 'taxi without control event never started timer')
''',
    'synchronous taxi state at post-hook': '''
taxi=true; hooks.TakeTaxiNode(2); Advance(.2)
assert(Visible(), 'already-active taxi at post-hook never started timer')
''',
    'refused click expires, stun cannot start taxi': '''
hooks.TakeTaxiNode(2); Fire('PLAYER_CONTROL_LOST'); Advance(6)
assert(not Visible() and ActiveTimers()==0)
taxi=true; Fire('PLAYER_CONTROL_LOST'); Advance(.2)
assert(not Visible(), 'expired click started unrelated flight')
''',
    'disable cancels takeoff watcher and late callbacks': '''
hooks.TakeTaxiNode(2); EllesmereUIDB.flightTimer.enabled=false; EllesmereUI._FlightTimer.Apply()
taxi=true; Advance(6); assert(not Visible() and ActiveTimers()==0)
for _,f in ipairs(frames) do assert(next(f.events)==nil) end
''',
    'enable during flight recovers elapsed-only without calibration': '''
EllesmereUIDB.flightTimer.enabled=false; EllesmereUI._FlightTimer.Apply()
taxi=true; EllesmereUIDB.flightTimer.enabled=true; EllesmereUI._FlightTimer.Apply()
assert(Visible(), 'enabling during flight never started timer')
assert(bars[1].duration==nil)
Advance(10); taxi=false; Fire('PLAYER_CONTROL_GAINED')
assert(not Visible() and EllesmereUIDB.flightTimer.speed==nil)
assert(hookCounts.TakeTaxiNode==1 and ActiveTimers()==0)
''',
    'entering world in flight recovers without invented destination or ETA': '''
taxi=true; Fire('PLAYER_ENTERING_WORLD'); assert(Visible(), 'world-entry recovery missing')
assert(bars[1].duration==nil and bars[1].dest.text~='Crossroads')
Fire('PLAYER_ENTERING_WORLD'); Advance(3)
assert(bars[1].time.text=='0:03', 'world event reset elapsed timer')
''',
    'preview is replaced by a real taxi and landing fallback ends it': '''
EllesmereUI._FlightTimer.Preview(); assert(Visible())
hooks.TakeTaxiNode(2); taxi=true; Advance(.2)
assert(bars[1].dest.text=='Crossroads')
taxi=false; Advance(4); assert(not Visible() and ActiveTimers()==0)
assert(EllesmereUIDB.flightTimer.speed==nil)
''',
}

failures = []
for name, test in CASES.items():
    lua = LuaRuntime(unpack_returned_tuples=True)
    try:
        lua.execute(SETUP)
        lua.execute(SOURCE)
        lua.execute("Fire('PLAYER_LOGIN')")
        lua.execute(test)
        print('PASS:', name)
    except Exception as error:
        failures.append(name)
        print('FAIL:', name, str(error))
assert not failures, failures
print('PASS: full flight module lifecycle (offline; live taxi acceptance pending)')
