"""Execute real resource update functions with values that reject Lua operations."""
from pathlib import Path
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2]
resource = (root / "EllesmereUIResourceBars/EllesmereUIResourceBars.lua").read_text(encoding="utf-8-sig")
unit = (root / "EllesmereUIUnitFrames/EllesmereUIUnitFrames.lua").read_text(encoding="utf-8-sig")
# Keep complete production function bodies; provide only their external APIs and
# configuration. The unit builder prefix isolates max selection before widgets.
bands = resource[resource.index("local function BuildBandStops("):resource.index("-- per-element scale, border, colors, text, alerts")]
updates = resource[resource.index("local function UpdateHealthBar()"):resource.index("-- Pre-allocated rune sorting buffers")]
pip_prefix = unit[unit.index("local function CreateCustomClassPower("):unit.index('    local isModern = (style == "modern")', unit.index("local function CreateCustomClassPower("))]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
local function forbidden() error('secret used by Lua comparison/arithmetic/formatting') end
local secretMT={__le=forbidden,__lt=forbidden,__eq=forbidden,__add=forbidden,__sub=forbidden,
 __mul=forbidden,__div=forbidden,__mod=forbidden,__pow=forbidden,__unm=forbidden,__tostring=forbidden,__concat=forbidden}
function secret() return setmetatable({secret=true},secretMT) end
function issecretvalue(v) return type(v)=='table' and rawget(v,'secret')==true end
cur=25; maximum=100; rangeCalls=0; valueCalls=0
function UnitHealth() return cur end
function UnitHealthMax() return maximum end
function UnitPower() return cur end
function UnitPowerMax() return maximum end
function UnitHealthPercent() return 25 end
function UnitPowerPercent() return 25 end
CurveConstants={ScaleTo100={}}
healthCfg={textFormat='none',customColored=true}
powerCfg={textFormat='none',customColored=true}
function _ERB_ResolveHealthCfg() return healthCfg end
function _ERB_ResolvePowerCfg() return powerCfg end
function _ERB_TextHiddenByForm() return false end
function ResolveThresholdSpecEntry() return nil end
function ResolveBandConfig() return false,nil,'percent',false end
function GetPrimaryPowerType() return 0 end
function makebar()
 local b={_text={Hide=function() end}}
 function b:IsShown() return true end
 function b:GetStatusBarTexture() return nil end
 function b:SetMinMaxValues(low,high) assert(low==0); self.max=high; rangeCalls=rangeCalls+1 end
 function b:SetValue(value,smoothing) self.value=value; self.smoothing=smoothing; valueCalls=valueCalls+1 end
 return b
end
healthBar=makebar(); primaryBar=makebar()
ns={CfgGen=1,EASE='easing',PPC={gen=1,pp=powerCfg,primary=0},PowTracks=function() return false end}
function CreateColor(r,g,b,a) return {r=r,g=g,b=b,a=a} end
C_CurveUtil={CreateColorCurve=function()
 local c={points={}}
 function c:AddPoint(x,color) assert(type(x)=='number'); table.insert(self.points,{x,color}) end
 return c
end}
format=string.format
CLASS_POWER_TYPES={PALADIN=9}; EllesmereUI={IS_FOREVER=false}; Enum={PowerType={ComboPoints=4}}
function UnitClass() return 'Paladin','PALADIN' end
''')
lua.execute("local _bandCurveCache={}\n" + bands + updates + unit[unit.index("local FOREVER_CLASS_POWER ="):unit.index("-- Combo points exist only")] + pip_prefix + "\nreturn maxPower\nend\n" +
            "TestHealth=UpdateHealthBar; TestPower=UpdatePrimaryBar; TestBands=GetBarBandCurve; TestStops=BuildBandStops; TestPips=CreateCustomClassPower")
lua.execute(r'''
-- Clean values preserve normal rendering and reject zero/nil maximums.
TestHealth(); TestPower()
assert(healthBar.max==100 and healthBar.value==25 and primaryBar.value==25)
assert(healthBar.smoothing=='easing' and primaryBar.smoothing=='easing')
local ranges,values=rangeCalls,valueCalls
maximum=0; TestHealth(); TestPower(); assert(rangeCalls==ranges and valueCalls==values)
maximum=nil; TestHealth(); TestPower(); assert(rangeCalls==ranges and valueCalls==values)
maximum=100; cur=-5; TestPower(); assert(primaryBar.value==0)
-- Both current and maximum may be opaque: pass exact objects to native sinks.
cur=secret(); maximum=secret(); TestHealth(); TestPower()
assert(rawequal(healthBar.max,maximum) and rawequal(primaryBar.max,maximum))
assert(rawequal(healthBar.value,cur) and rawequal(primaryBar.value,cur))
assert(healthBar.smoothing==nil and primaryBar.smoothing==nil)
-- The legacy fallback must not divide clean current health by a secret max.
local percent=UnitHealthPercent; UnitHealthPercent=nil; cur=25
TestHealth(); assert(rawequal(healthBar.max,maximum) and healthBar.value==25)
UnitHealthPercent=percent
local bands={{to=50,r=1,g=0,b=0,a=1},{to=100,r=0,g=1,b=0,a=1}}
-- Percent colors have no dependency on maximum: clean/secret max use one curve.
local curve=TestBands('test',bands,'percent',100,1,1,1,false)
assert(curve and #curve.points>0)
local sameCurve=TestBands('test',bands,'percent',maximum,1,1,1,false)
assert(rawequal(curve,sameCurve),'percent band cache depended on secret max')
assert(TestStops(bands,'value',maximum)==nil and TestBands('absolute',bands,'value',maximum,1,1,1,false)==nil)
assert(TestBands('absolute',bands,'value',200,1,1,1,false),'clean value bands stopped rendering')
-- Secret pip counts cannot be compared, allocated or looped over. Defer a
-- first display; reuse only a previously observed clean maximum thereafter.
ns._classPowerMaxCache=nil; maximum=secret(); assert(TestPips({},'modern')==nil)
maximum=3; assert(TestPips({},'modern')==3)
maximum=secret(); assert(TestPips({},'modern')==3)
local count=TestPips({},'modern'); local pips={}; for i=1,count do pips[i]=true end
assert(#pips==3)
maximum=5; assert(TestPips({},'modern')==5)
maximum=0; assert(TestPips({},'modern')==5,'existing clean zero fallback changed')
EllesmereUI.IS_FOREVER=true; maximum=5; assert(TestPips({},'modern')==nil, 'Forever Paladin has no Holy Power bar')
''')
print("PASS resource secrets: production health/power updates, opaque current/max native sinks, clean zero/nil guards, legacy percentage fallback, percent-band cache/value-band deferral, clean cached pip counts without secret allocation")
