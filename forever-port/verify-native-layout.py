"""Offline candidate tests; no client calls, saves, imports, or activation.

Uses Lupa Lua 5.1 and the actual downloaded Forever ApplySystemAnchor body.
Override EUI_FOREVER_SOURCE to select another authoritative source directory.
"""
import os
from pathlib import Path
from lupa.lua51 import LuaRuntime, LuaError

folder = Path(__file__).resolve().parent
source = Path(os.environ.get("EUI_FOREVER_SOURCE", str(
    Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["LOCALAPPDATA"]) / "Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns"))
)))
native_text = (source / "Blizzard_EditMode/Shared/EditModeSystemTemplates.lua").read_text(encoding="utf-8-sig")
start = native_text.index("function EditModeSystemMixin:ApplySystemAnchor()")
end = native_text.index("function EditModeSystemMixin:UpdateSystem(systemInfo)", start)
native = native_text[start:end]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().Candidate = lua.execute((folder / "native-layout-candidate.lua").read_text(encoding="utf-8-sig"))
lua.execute(r'''
local function forbidden() error('secret value was operated on') end
local secretMT={__eq=forbidden,__lt=forbidden,__le=forbidden,__add=forbidden,
 __sub=forbidden,__mul=forbidden,__div=forbidden,__mod=forbidden,__tostring=forbidden,
 __concat=forbidden,__index=forbidden}
function secret() return setmetatable({_secret=true},secretMT) end
function detector(v) return type(v)=='table' and rawget(v,'_secret')==true end
function copy(v)
 if type(v)~='table' then return v end
 local r={}; for k,x in pairs(v) do r[k]=copy(x) end; return r
end
function equal(a,b)
 if type(a)~=type(b) then return false end
 if type(a)=='number' and a~=a then return b~=b end
 if type(a)~='table' then return a==b end
 for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
 for k in pairs(b) do if a[k]==nil then return false end end
 return true
end
function detached(a,b)
 if type(a)~='table' or type(b)~='table' then return end
 assert(not rawequal(a,b),'shared input/candidate table')
 for k,v in pairs(a) do detached(v,b[k]) end
end
function A(x,y,point,relativePoint,relativeTo)
 return {point=point or 'CENTER',relativeTo=relativeTo or 'UIParent',
 relativePoint=relativePoint or 'CENTER',offsetX=x or 0,offsetY=y or 0}
end
active={layoutName='Native existing',layoutType=0,unknownRoot={version=7,flags={true,false}},systems={
 {system=77,systemIndex=4,anchorInfo=A(11,22),anchorInfo2=A(-33,-44,'BOTTOMRIGHT'),
  isInDefaultPosition=true,settings={{setting=5001,value=19,unknown={future='retain'}}},extra={1,2,3}},
 {system=77,systemIndex=5,anchorInfo=A(88,99),isInDefaultPosition=true,settings={}},
 {system=78001,anchorInfo=A(-50,75,'RIGHT','LEFT','FutureFrame'),anchorInfo2=A(30,40),
  isInDefaultPosition=true,settings={{setting=8123123,value=1}},unknownSystem={enabled=true}},
 {system=77,anchorInfo=A(1,1),settings={}},
 {system=77,systemIndex=-1,anchorInfo=A(2,2),settings={}}
}}
owned={{system=77,systemIndex=4,anchorInfo=A(250,-120,'TOPRIGHT','BOTTOMLEFT')}}
local original,originalOwned=copy(active),copy(owned)
result=Candidate.Build(active,owned,'Ellesmere Forever - Pickme',1,detector)
assert(result.layoutName=='Ellesmere Forever - Pickme' and result.layoutType==1)
assert(result.systems[1].isInDefaultPosition==false)
assert(equal(result.systems[1].anchorInfo,owned[1].anchorInfo))
assert(equal(result.systems[1].anchorInfo2,active.systems[1].anchorInfo2))
local expected=copy(active)
expected.layoutName=result.layoutName; expected.layoutType=1
expected.systems[1].anchorInfo=copy(owned[1].anchorInfo)
expected.systems[1].isInDefaultPosition=false
assert(equal(result,expected),'unknown/untouched native fields changed')
assert(equal(active,original) and equal(owned,originalOwned),'inputs mutated')
detached(active,result); detached(owned[1].anchorInfo,result.systems[1].anchorInfo)
result.systems[3].unknownSystem.enabled=false
result.systems[1].settings[1].unknown.future='mutated candidate'
assert(equal(active,original),'candidate writes leaked into source')

local remove=copy(owned); remove[1].anchorInfo2=false
assert(Candidate.Build(active,remove,'Remove second',1,detector).systems[1].anchorInfo2==nil)
remove[1].anchorInfo2=A(500,-700,'BOTTOM','TOP')
local replaced=Candidate.Build(active,remove,'Replace second',1,detector)
assert(equal(replaced.systems[1].anchorInfo2,remove[1].anchorInfo2))
detached(replaced.systems[1].anchorInfo2,remove[1].anchorInfo2)
local distinct={{system=77,anchorInfo=A(90,90)},{system=77,systemIndex=-1,anchorInfo=A(80,80)}}
local separate=Candidate.Build(active,distinct,'Distinct indices',1,detector)
assert(separate.systems[4].anchorInfo.offsetX==90 and separate.systems[5].anchorInfo.offsetX==80)
assert(separate.systems[1].anchorInfo.offsetX==11)

local rejected=0
function rejects(label,change)
 local a,o,n,t,d=copy(active),copy(owned),'Reviewed copy',1,detector
 local args={a,o,n,t,d}; change(args)
 local aBefore,oBefore=copy(args[1]),copy(args[2])
 local ok,err=pcall(Candidate.Build,unpack(args,1,5))
 assert(not ok,label..' unexpectedly accepted')
 assert(type(err)=='string' and err:find('native layout candidate:',1,true),label..': '..tostring(err))
 if label:find('secret',1,true) then
  assert(err:find('secret input',1,true),label..' was not rejected by the secret guard')
 end
 -- Generic clone cannot compare opaque values; clean failure cases checked here.
 if label:find('secret',1,true)==nil then
  assert(equal(args[1],aBefore) and equal(args[2],oBefore),label..' mutated source')
 end
 rejected=rejected+1
end
rejects('missing source system',function(a) a[1].systems[1].system=nil end)
rejects('invalid source identity',function(a) a[1].systems[1].system='77' end)
rejects('fractional identity',function(a) a[2][1].systemIndex=4.5 end)
rejects('missing owned identity',function(a) a[2][1].system=nil end)
rejects('unknown owned identity',function(a) a[2][1].system=9999 end)
rejects('duplicate source identity',function(a) table.insert(a[1].systems,copy(a[1].systems[1])) end)
rejects('duplicate owned identity',function(a) table.insert(a[2],copy(a[2][1])) end)
rejects('missing systems',function(a) a[1].systems=nil end)
rejects('empty systems',function(a) a[1].systems={} end)
rejects('empty owned',function(a) a[2]={} end)
rejects('source holes',function(a) a[1].systems[2]=nil end)
rejects('owned holes',function(a) a[2][3]=a[2][1] end)
rejects('unsupported owned field',function(a) a[2][1].settings={} end)
rejects('missing coordinate',function(a) a[2][1].anchorInfo.offsetX=nil end)
rejects('string coordinate',function(a) a[2][1].anchorInfo.offsetX='10' end)
rejects('nan coordinate',function(a) a[2][1].anchorInfo.offsetY=0/0 end)
rejects('infinite coordinate',function(a) a[2][1].anchorInfo.offsetX=math.huge end)
rejects('negative infinite coordinate',function(a) a[2][1].anchorInfo.offsetX=-math.huge end)
rejects('unknown source point',function(a) a[1].systems[3].anchorInfo.point='MIDDLE' end)
rejects('unknown owned point',function(a) a[2][1].anchorInfo.point='MIDDLE' end)
rejects('lowercase point',function(a) a[2][1].anchorInfo.relativePoint='right' end)
rejects('relative frame object',function(a) a[2][1].anchorInfo.relativeTo={} end)
rejects('empty relative frame',function(a) a[2][1].anchorInfo.relativeTo='' end)
rejects('second anchor invalid',function(a) a[2][1].anchorInfo2=A(0,0,'MIDDLE') end)
rejects('same copy name',function(a) a[3]=a[1].layoutName end)
rejects('blank name',function(a) a[3]=' \t ' end)
rejects('control name',function(a) a[3]='Copy\nname' end)
rejects('invalid type',function(a) a[4]='Character' end)
rejects('missing detector',function(a) a[5]=nil end)
rejects('secret offset',function(a) a[2][1].anchorInfo.offsetX=secret() end)
rejects('secret source offset',function(a) a[1].systems[3].anchorInfo.offsetY=secret() end)
rejects('secret identity',function(a) a[2][1].systemIndex=secret() end)
rejects('secret unknown setting',function(a) a[1].systems[3].settings[1].value=secret() end)
rejects('secret name',function(a) a[3]=secret() end)
rejects('secret type',function(a) a[4]=secret() end)
rejects('secret unknown key',function(a) a[1].unknownRoot[secret()]=1 end)
rejectionCount=rejected

-- Serialization data cannot contain cycles, metatables, or callbacks.
local cyclic=copy(active); cyclic.unknownRoot.self=cyclic
assert(not pcall(Candidate.Build,cyclic,owned,'Cycle',1,detector))
local meta=copy(active); setmetatable(meta.unknownRoot,{})
assert(not pcall(Candidate.Build,meta,owned,'Meta',1,detector))
local callable=copy(active); callable.unknownRoot.callback=function() end
assert(not pcall(Candidate.Build,callable,owned,'Callback',1,detector))

EditModeSystemMixin={}
EditModeUtil={IsRightAnchoredActionBar=function() error('default layout path entered') end,
 IsBottomAnchoredActionBar=function() error('default layout path entered') end}
UIParent={}
EditModeManagerFrame={UpdateActionBarLayout=function(self,frame) frame.layoutCalls=frame.layoutCalls+1 end}
function CheckNativeAnchors()
 for _,scale in ipairs({0.64,0.8,1,1.25,2}) do
  local frameX,frameY=231.75,-127.125
  -- The builder deliberately expects stored offsets; reviewed conversion occurs
  -- at its caller, using the target frame scale rather than a guessed UI scale.
  local changes={{system=77,systemIndex=4,
   anchorInfo=A(frameX*scale,frameY*scale,'RIGHT','LEFT','FutureFrame'),
   anchorInfo2=A(-42.25*scale,91.5*scale,'BOTTOM','TOP')}}
  local candidate=Candidate.Build(active,changes,'Scale copy',1,detector)
  local f={systemInfo=candidate.systems[1],points={},layoutCalls=0}
  function f:GetManagedFrameContainer() return nil end
  function f:IsInDefaultPosition() return self.systemInfo.isInDefaultPosition end
  function f:ClearAllPoints() self.points={}; self.cleared=true end
  function f:GetScale() return scale end
  function f:SetPoint(...) table.insert(self.points,{...}) end
  EditModeSystemMixin.ApplySystemAnchor(f)
  assert(f.cleared and #f.points==2 and f.layoutCalls==1)
  local p,q=f.points[1],f.points[2]
  assert(p[1]=='RIGHT' and p[2]=='FutureFrame' and p[3]=='LEFT')
  assert(math.abs(p[4]-frameX)<1e-9 and math.abs(p[5]-frameY)<1e-9,'native scale conversion mismatch')
  assert(q[1]=='BOTTOM' and q[2]=='UIParent' and q[3]=='TOP')
  assert(math.abs(q[4]+42.25)<1e-9 and math.abs(q[5]-91.5)<1e-9,'native second-anchor scale mismatch')
  changes[1].anchorInfo2=false
  f.systemInfo=Candidate.Build(active,changes,'Single scale copy',1,detector).systems[1]
  EditModeSystemMixin.ApplySystemAnchor(f)
  assert(#f.points==1,'removed second anchor still applied')
 end
end
''')
lua.execute(native)
lua.globals().CheckNativeAnchors()
# Prove that the native-body test detects incorrect scale conversion.
assert native.count(" / scale") == 4, "native anchor implementation changed; review extraction"
lua.execute(native.replace(" / scale", " * scale"))
try:
    lua.globals().CheckNativeAnchors()
except LuaError as error:
    assert "scale conversion mismatch" in str(error)
else:
    raise AssertionError("scale mutation unexpectedly passed")
lua.execute(native)
lua.globals().CheckNativeAnchors()
print(f"PASS: independent layout copy, untouched native data, {lua.globals().rejectionCount} rejection cases, native scaling at five scales and negative control")
