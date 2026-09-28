"""Forever prediction: production engine + painter, guarded native API sinks.

The calculator is a C++ API; the mock models its documented contract, not its
implementation. Geometry assertions cover four orientations. No live WoW access.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime
root=Path(__file__).resolve().parents[2]
folder=root/'EllesmereUIUnitFrames'
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(r"""
EUI_FOREVER=true; EllesmereUI={}; ns={}; allFrames={}; timers={}; now=1; settings={}
local function forbidden() error('protected value used by Lua') end
local mt={__eq=forbidden,__lt=forbidden,__le=forbidden,__add=forbidden,__sub=forbidden,
 __mul=forbidden,__div=forbidden,__tostring=forbidden,__concat=forbidden}
function secret() return setmetatable({secret=true},mt) end
function issecretvalue(v) return type(v)=='table' and rawget(v,'secret')==true end
function wipe(t) for k in pairs(t) do t[k]=nil end end
function GetTime() return now end
function UnitExists(u) return units[u]~=nil end
function UnitGUID(u) return u end
function RegisterStateDriver() end
function SecureButton_GetUnit(f) return f._euiBaseUnit end
function SecureButton_GetModifiedUnit(f) return f._euiUnit end
function CreateFrame(kind,name,parent)
 local f={kind=kind,parent=parent,events={},scripts={},points={},width=232,height=48,level=2,shown=true}
 function f:RegisterEvent(e) self.events[e]=true end
 function f:RegisterUnitEvent(e,...) self.events[e]={...} end
 function f:SetScript(e,fn) self.scripts[e]=fn end
 function f:HookScript(e,fn)
  local old=self.scripts[e]; self.scripts[e]=function(...) if old then old(...) end; fn(...) end
 end
 function f:SetAllPoints(other) self.allPoints=other end
 function f:SetClipsChildren(v) self.clips=v end
 function f:SetAlpha(v) self.alpha=v end
 function f:Show() self.shown=true; if self.scripts.OnShow then self.scripts.OnShow(self) end end
 function f:Hide() self.shown=false; if self.scripts.OnHide then self.scripts.OnHide(self) end end
 function f:IsShown() return self.shown end
 function f:GetWidth() return self.width end
 function f:GetHeight() return self.height end
 function f:SetSize(w,h) assert(not issecretvalue(w) and not issecretvalue(h)); self.width=w; self.height=h end
 function f:SetWidth(w) self.width=w end
 function f:SetHeight(h) self.height=h end
 function f:GetFrameLevel() return self.level end
 function f:SetFrameLevel(v) self.level=v end
 function f:SetStatusBarTexture(path) self.fill=self.fill or CreateFrame('Texture',nil,self); self.fill.path=path end
 function f:SetStatusBarColor(...) self.color={...} end
 function f:GetStatusBarTexture() return self.fill end
 function f:SetMinMaxValues(a,b) assert(a==0); self.maximum=b end
 function f:SetValue(v) self.value=v end
 function f:CreateMaskTexture() return CreateFrame('Mask',nil,self) end
 function f:AddMaskTexture(mask) self.mask=mask end
 function f:SetTexture(path) self.path=path end
 function f:SetOrientation(v) self.orientation=v end
 function f:SetReverseFill(v) self.reverse=v end
 function f:ClearAllPoints() self.points={} end
 function f:SetPoint(...) self.points[#self.points+1]={...} end
 function f:SetAttribute() error('protected click attribute changed') end
 function f:SetParent() error('native frame parent changed') end
 allFrames[#allFrames+1]=f; return f
end
UIParent=CreateFrame('Frame')
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function flush() local t=timers; timers={}; for _,fn in ipairs(t) do fn() end end
Enum={UnitMaximumHealthMode={Default=0},UnitIncomingHealClampMode={MissingHealth=0},UnitHealAbsorbMode={ReducedByIncomingHeals=0}}
units={player={maximum=442,current=313,incoming=100,healAbsorb=0},target={maximum=500,current=200,incoming=80,healAbsorb=0},vehicle={maximum=1000,current=500,incoming=140,healAbsorb=0}}
calculators={}; reads=0
function CreateUnitHealPredictionCalculator()
 local c={}
 function c:SetMaximumHealthMode(v) assert(v==0); self.mode=v end
 function c:SetIncomingHealClampMode(v) assert(v==0); self.clamp=v end
 function c:SetIncomingHealOverflowPercent(v) assert(v==1); self.overflow=v end
 function c:SetHealAbsorbMode(v) assert(v==0); self.absorbMode=v end
 function c:GetMaximumHealth() return self.maximum end
 function c:GetIncomingHeals() return self.incoming end
 calculators[#calculators+1]=c; return c
end
calculatorFactory=CreateUnitHealPredictionCalculator
function UnitGetDetailedHealPrediction(unit,healer,c)
 assert(healer=='player' and c.mode==0 and c.clamp==0 and c.overflow==1 and c.absorbMode==0)
 reads=reads+1
 if rejected then error('restricted API read') end
 local u=units[unit] or {maximum=1,incoming=0,current=0,healAbsorb=0}
 c.maximum=u.maximum
 if issecretvalue(u.incoming) then c.incoming=u.incoming
 else c.incoming=math.min(math.max(0,u.maximum-u.current),math.max(0,u.incoming-u.healAbsorb)) end
end
function event(name,unit)
 -- Dispatch the engine's real per-unit registrations, including vehicle alias.
 for _,f in ipairs(allFrames) do
  local match=f.events[name]
  if type(match)=='table' then
   local found=false; for _,v in ipairs(match) do if v==unit then found=true end end
   match=found
  end
  if match and f.scripts.OnEvent then f.scripts.OnEvent(f,name,unit) end
 end
end
function newunit(unit)
 local f=CreateFrame('Button');f._euiBaseUnit=unit;f._euiUnit=unit
 f.Health=CreateFrame('StatusBar',nil,f); f.Health:SetStatusBarTexture('health')
 ns.ForeverCreateHealPrediction(f,unit,function() return settings end)
 ns.Engine.Attach(f,unit,{'incomingHeal'})
 ns.Engine.RepaintAll(f,'Spawn')
 return f
end
""")
for name in ['EUI_UnitFrames_Engine.lua','EUI_UnitFrames_ForeverPrediction.lua']:
 lua.execute((folder/name).read_text(encoding='utf-8-sig'),'EllesmereUIUnitFrames',lua.globals().ns)
# Execute the original layout and raw-shield value block too: this verifies
# integration with original styles/overflow rather than a duplicate adapter.
original=(folder/'EllesmereUIUnitFrames.lua').read_text(encoding='utf-8-sig')
start=original.index('local function UpdateAbsorbBarReverseFill(')
end=original.index('-- Absorb / Heal Absorb strip-bar',start)
lua.execute('ns.ApplyFillRotation=function() end\n'+original[start:end]+'\nOriginalAbsorbLayout=UpdateAbsorbBarReverseFill')
# The extracted block also declares upstream's supported-unit set. This harness
# exercises the extension's generic event/vehicle/geometry contracts in isolation;
# verify-native-ownership.py tests the real supported set and rejects allocation.
lua.execute('ns.UF_HEAL_PRED_UNITS = {}')
start=original.index('                local abValue = absorbAmt')
end=original.index('            -- Heal absorb: overlay',start)
# The final end belongs to the enclosing shieldOff branch, which this harness
# deliberately replaces with explicit arguments for enabled shield styles.
value_block=original[start:end].rstrip()
assert value_block.endswith('end')
value_block=value_block[:-3]
lua.execute('function OriginalShieldValues(ab,fw,absorbAmt,maxHealth,osMode,absorbMode)\n'+value_block+'\nend')
lua.execute(r"""
player=newunit('player'); bar=player.ForeverIncomingHeal
assert(bar.maximum==442 and bar.value==100)
assert(bar.color[2]==1 and bar.color[4]==.7 and bar.parent.clips)
assert(bar.fill.mask.allPoints==player.Health)
assert(bar.width==232 and bar.height==48)
assert(bar.points[1][1]=='TOPLEFT' and bar.points[1][2]==player.Health.fill and bar.points[1][3]=='TOPRIGHT')
-- 70.8% HP plus100 heal: 22.6% of the full232px bar, not of the empty segment.
assert(math.abs(bar.width*bar.value/bar.maximum-52.48868778)<.00001)
local made=#allFrames
ns.ForeverCreateHealPrediction(player,'player',function() return settings end);assert(#allFrames==made)
-- Source-provided total can include other healers; no spell-rank estimates.
units.player.incoming=180;event('UNIT_HEAL_PREDICTION','player');assert(bar.value==129)
units.player.incoming=0;event('UNIT_HEAL_PREDICTION','player');assert(bar.value==0,'same-frame cancellation dropped')
units.player.incoming=180;event('UNIT_HEAL_PREDICTION','player');assert(bar.value==129)
units.player.current=400;event('UNIT_HEALTH','player');assert(bar.value==42,'missing-health clamp stale')
units.player.current=442;event('UNIT_HEALTH','player');assert(bar.value==0,'full health shows overheal')
units.player.current=313;units.player.incoming=100;units.player.healAbsorb=40
event('UNIT_HEAL_ABSORB_AMOUNT_CHANGED','player');assert(bar.value==60)
units.player.healAbsorb=150;event('UNIT_HEAL_ABSORB_AMOUNT_CHANGED','player');assert(bar.value==0)
units.player.healAbsorb=0;units.player.maximum=500
event('UNIT_MAXHEALTH','player');assert(bar.maximum==500 and bar.value==100);flush()
units.player.current=490;event('UNIT_MAX_HEALTH_MODIFIERS_CHANGED','player');assert(bar.value==10);flush()
-- No new timers/frame allocations or protected operations for repeated casts.
for i=1,10 do event('UNIT_HEAL_PREDICTION','player') end
assert(#allFrames==made and #timers==0)
-- Resize and all fill directions; only custom prediction geometry is changed.
for _,vertical in ipairs({false,true}) do
 for _,reverse in ipairs({false,true}) do
  settings.healthVerticalFill=vertical;settings.healthReverseFill=reverse
  ns.Engine.RepaintAll(player,'ForceUpdate')
  assert(bar.orientation==(vertical and 'VERTICAL' or 'HORIZONTAL') and bar.reverse==reverse)
  local p=bar.points[1]
  assert(p[1]==(vertical and (reverse and 'TOPLEFT' or 'BOTTOMLEFT') or (reverse and 'TOPRIGHT' or 'TOPLEFT')))
  assert(p[3]==(vertical and (reverse and 'BOTTOMLEFT' or 'TOPLEFT') or (reverse and 'TOPLEFT' or 'TOPRIGHT')))
 end
end
player.Health.width=260;player.Health.height=52
player.Health.scripts.OnSizeChanged(player.Health);assert(bar.width==260 and bar.height==52)
-- Secret data reaches only engine sinks, including diagnostics while in combat.
units.player.incoming=secret();units.player.maximum=secret()
event('UNIT_HEAL_PREDICTION','player')
assert(rawequal(bar.value,units.player.incoming) and rawequal(bar.maximum,units.player.maximum))
local lines={}; local before=reads;ns.ForeverPredictionEvidence(lines)
assert(reads==before and lines[1]:find('protected value rendered',1,true))
-- A rejected read clears an old heal; the next readable event recovers.
rejected=true;event('UNIT_HEAL_PREDICTION','player');assert(bar.value==0)
rejected=false;units.player={maximum=442,current=313,incoming=50,healAbsorb=0}
event('UNIT_HEAL_PREDICTION','player');assert(bar.value==50)
-- Vehicle remap inherits both registered tokens. Target identity/hidden-show
-- refreshes discard old results even without a new incoming-heal event.
player._euiUnit='vehicle';event('UNIT_HEAL_PREDICTION','vehicle');assert(bar.value==140 and bar.maximum==1000)
local target=newunit('target');assert(target.ForeverIncomingHeal.value==80)
units.target={maximum=100,current=90,incoming=0,healAbsorb=0};event('PLAYER_TARGET_CHANGED')
assert(target.ForeverIncomingHeal.value==0 and target.ForeverIncomingHeal.maximum==100)
target:Hide();units.target.incoming=7;event('UNIT_HEAL_PREDICTION','target');assert(target.ForeverIncomingHeal.value==0)
target:Show();assert(target.ForeverIncomingHeal.value==7)
-- Eventless target-of-target uses the existing engine's shared tick.
units.targettarget={maximum=100,current=40,incoming=20,healAbsorb=0}
local tot=CreateFrame('Button');tot._euiUnit='targettarget';tot._euiBaseUnit='targettarget'
tot.Health=CreateFrame('StatusBar',nil,tot);tot.Health:SetStatusBarTexture('health')
ns.ForeverCreateHealPrediction(tot,'targettarget',function() return {} end)
ns.Engine.AttachPolled(tot,'targettarget',{'incomingHeal'})
for _,f in ipairs(allFrames) do if f.scripts.OnUpdate then f.scripts.OnUpdate(f,.5) end end
assert(tot.ForeverIncomingHeal.value==20)
units.targettarget.incoming=0
for _,f in ipairs(allFrames) do if f.scripts.OnUpdate then f.scripts.OnUpdate(f,.5) end end
assert(tot.ForeverIncomingHeal.value==0)
-- Unavailable beta capability leaves no stale or fabricated heal.
CreateUnitHealPredictionCalculator=nil
local pet=newunit('pet');assert(pet.ForeverIncomingHeal.value==0)
""")
lua.execute(r"""
CreateUnitHealPredictionCalculator=calculatorFactory
-- Migration is attached to actual settings, not frame lifetime. A new frame
-- after an explicit user opt-out must retain none, while custom styles survive.
local appearance={showPlayerAbsorb='none'}
local function geometryFrame()
 local f=CreateFrame('Button');f._euiUnit='geometry';f._euiBaseUnit='geometry'
 local hp=CreateFrame('StatusBar',nil,f);f.Health=hp;hp:SetStatusBarTexture('health')
 local cur=CreateFrame('Frame',nil,hp);cur:SetClipsChildren(true)
 local miss=CreateFrame('Frame',nil,hp);miss:SetClipsChildren(true)
 local ab=CreateFrame('StatusBar',nil,cur);ab:SetStatusBarTexture('shield')
 local fw=CreateFrame('StatusBar',nil,miss);fw:SetStatusBarTexture('shield')
 ab._hpBar=hp;ab._forward=fw;ab._curClip=cur;ab._missClip=miss
 f.HealthPrediction={damageAbsorb=ab}
 ns.ForeverCreateHealPrediction(f,'geometry',function() return appearance end)
 return f,ab,fw
end
units.geometry={maximum=100,current=50,incoming=20,healAbsorb=0}
local f,ab,fw=geometryFrame()
OWNERSHIP_FRAME=f
assert(appearance.showPlayerAbsorb=='clean' and appearance.foreverHealingDisplayMigrated)
appearance.showPlayerAbsorb='none';geometryFrame();assert(appearance.showPlayerAbsorb=='none','later opt-out overwritten')
appearance={showPlayerAbsorb='striped'};geometryFrame();assert(appearance.showPlayerAbsorb=='striped','custom shield style overwritten')
appearance.showPlayerAbsorb='clean'
local pred=f.ForeverIncomingHeal
local function carrierFor(frame)
 for _,candidate in ipairs(allFrames) do
  if candidate.kind=='StatusBar' and candidate.parent==frame.Health and candidate.alpha==0 then return candidate end
 end
 error('carrier missing')
end
local carrier=carrierFor(f)
assert(carrier:IsShown() and carrier.allPoints==f.Health)
-- Resolve the production anchor graph along the active fill axis. Texture
-- rectangles model documented native StatusBar clamping; no production Lua
-- computes these widths. Both corners are used for dynamically sized clips.
local function edge(point,vertical)
 if vertical then return point:find('TOP',1,true) and 1 or 0 end
 return point:find('RIGHT',1,true) and 1 or 0
end
local bounds
bounds=function(obj,vertical)
 if obj.kind=='Texture' and obj.parent.kind=='StatusBar' then
  local bar=obj.parent;local lo,hi=bounds(bar,vertical)
  local fraction=bar.maximum and bar.maximum>0 and math.max(0,math.min(1,(bar.value or 0)/bar.maximum)) or 0
  local length=(hi-lo)*fraction
  if bar.reverse then return hi-length,hi end
  return lo,lo+length
 end
 if obj.allPoints then return bounds(obj.allPoints,vertical) end
 local span=vertical and obj.height or obj.width
 local first=obj.points[1]
 if not first then return 0,span end
 local function coordinate(p)
  local lo,hi=bounds(p[2],vertical)
  return (edge(p[3],vertical)==1 and hi or lo)+(p[vertical and 5 or 4] or 0)
 end
 local a=coordinate(first);local own=edge(first[1],vertical)
 for i=2,#obj.points do
  local p=obj.points[i]
  if edge(p[1],vertical)~=own then
   local b=coordinate(p)
   if own==0 then return a,b else return b,a end
  end
 end
 if own==1 then return a-span,a else return a,a+span end
end
local function visible(bar,vertical)
 if not bar:IsShown() then return 0 end
 local a,b=bounds(bar.fill,vertical);local c,d=bounds(bar.parent,vertical)
 return math.max(0,math.min(100,b,d)-math.max(0,a,c))
end
local cases=0
for _,vertical in ipairs({false,true}) do
 for _,reverse in ipairs({false,true}) do
  appearance.healthVerticalFill=vertical;appearance.healthReverseFill=reverse
  f.Health:SetSize(vertical and 20 or 100,vertical and 100 or 20)
  f.Health:SetOrientation(vertical and 'VERTICAL' or 'HORIZONTAL');f.Health:SetReverseFill(reverse)
  ab:SetSize(f.Health.width,f.Health.height);fw:SetSize(f.Health.width,f.Health.height)
  for _,mode in ipairs({'always','fromleft','never'}) do
   appearance.absorbEdgeMode='overlay';appearance.overshieldMode=mode
   for _,health in ipairs({0,20,50,80,100}) do
    for _,fraction in ipairs({0,.5,1}) do
     local incoming=(100-health)*fraction
     units.geometry.current=health;units.geometry.incoming=incoming
     f.Health:SetMinMaxValues(0,100);f.Health:SetValue(health)
     ns.ForeverRefreshHealPrediction(f,'geometry','Regression')
     -- Actual original routine invokes the production helper after restoring
     -- native EUI anchors, including its separate vertical return branch.
     OriginalAbsorbLayout(f,reverse,appearance)
     assert(carrier.reverse==not reverse and carrier.orientation==pred.orientation)
     assert(carrier.value==incoming and carrier.maximum==100)
     local source=mode=='fromleft' and pred.fill or carrier.fill
     assert(ab.points[1][2]==source and fw.points[1][2]==pred.fill)
     for _,shield in ipairs({0,10,40,80,120}) do
      OriginalShieldValues(ab,fw,shield,100,mode,'overlay')
      local capped=math.min(100,shield)
      local empty=100-health-incoming
      local expectedForward=math.min(capped,empty)
      local expectedBack=mode=='never' and 0 or math.min(health,math.max(0,capped-empty))
      assert(math.abs(visible(fw,vertical)-expectedForward)<.00001,'forward shield overlaps/mis-sizes incoming')
      assert(math.abs(visible(ab,vertical)-expectedBack)<.00001,'shield overflow changed')
      cases=cases+1
     end
    end
   end
  end
  -- Other styles retain their original anchor/visibility contract; the new
  -- overlay helper must not override the intentional full-bar/reverse modes.
  for _,mode in ipairs({'left','right','overlayReverse'}) do
   appearance.absorbEdgeMode=mode
   OriginalAbsorbLayout(f,reverse,appearance)
   local beforeAb,beforeFw=ab.points,fw.points
   ns.ForeverLayoutPredictionShields(f,appearance)
   assert(ab.points==beforeAb and fw.points==beforeFw,'non-overlay geometry modified')
   OriginalShieldValues(ab,fw,40,100,'always',mode)
   assert(not fw:IsShown() and ab.value==40)
  end
 end
end
assert(cases==900)
-- Secret values and failed/no-unit updates must move/reset both carriers.
units.geometry.incoming=secret();units.geometry.maximum=secret()
ns.ForeverRefreshHealPrediction(f,'geometry','Secret')
assert(rawequal(pred.value,carrier.value) and rawequal(pred.maximum,carrier.maximum))
rejected=true;ns.ForeverRefreshHealPrediction(f,'geometry','Rejected')
assert(pred.value==0 and carrier.value==0)
rejected=false;units.geometry={maximum=100,current=50,incoming=20,healAbsorb=0}
ns.ForeverRefreshHealPrediction(f,'geometry','Recovery');assert(carrier.value==20)
ns.ForeverRefreshHealPrediction(f,nil,'NoUnit');assert(pred.value==0 and carrier.value==0)
CreateUnitHealPredictionCalculator=nil
local absent=geometryFrame();local absentCarrier=carrierFor(absent)
ns.ForeverRefreshHealPrediction(absent,'geometry','Unavailable')
assert(absent.ForeverIncomingHeal.value==0 and absentCarrier.value==0)
""")
print('PASS incoming heals: production event engine/painter, same-frame cancellation, health/max/absorb changes, overfill clamp, four orientations, resize, protected data sinks, identity/vehicle/show/poll lifecycles, missing/rejected API recovery and cached evidence')
print('PASS combined heals/shields: actual original layout/value blocks and prediction helper, 900 anchor-resolved cases across four directions, default/fromleft/never overflow, preserved other styles, secret/zero/error carriers and one-time shield opt-in respecting later choices')
