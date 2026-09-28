"""Native layout persistence regression, including actual Forever stack methods.

Offline tests cannot establish the client's secure/taint boundary or rendering.
"""
import os
from pathlib import Path
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
source = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns'))
native = (source / 'Blizzard_EditMode/Shared/EditModeManager.lua').read_text(encoding='utf-8-sig')
start = native.index('function EditModeManagerFrameMixin:UpdateRightActionBarPositions()')
end = native.index('function EditModeManagerFrameMixin:UpdateTopFramePositions()', start)
methods = native[start:end]
script = (root.parent / 'EllesmereUIActionBars/EllesmereUIActionBars_ForeverCombatLayout.lua').read_text()
setup = r'''
EUI_FOREVER=true; EUI_FOREVER_STATUS={}; combat=false; editing=false; dirty=false
saves=0; activates=0; added=0; messages={}; timers={}; callbacks={}; SlashCmdList={}
function GetBuildInfo() return '1.60.1','69913' end
function InCombatLockdown() return combat end
function print(text) messages[#messages+1]=text end
function issecretvalue() return false end
function copy(x) if type(x)~='table' then return x end local o={} for k,v in pairs(x) do o[k]=copy(v) end return o end
function equal(a,b)
 if type(a)~=type(b) then return false end
 if type(a)~='table' then return a==b end
 for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
 for k in pairs(b) do if a[k]==nil then return false end end return true
end
function A(x,y) return {point='CENTER',relativePoint='CENTER',relativeTo='UIParent',offsetX=x,offsetY=y} end
function S(id,index) return {system=id,systemIndex=index,anchorInfo=A(0,0),isInDefaultPosition=true,settings={{setting=100,value=42}}} end
function L(name,kind) return {layoutName=name,layoutType=kind,systems={S(0,1),S(0,2),S(0,3),S(12),S(400,99)}} end
Enum={EditModeLayoutType={Preset=0,Account=1,Character=2}}
Constants={EditModeConsts={EditModeMaxLayoutsPerType=5}}
presets={L('Modern',0),L('Classic',0),L('Gamepad',0)}
db={activeLayout=2,layouts={L('Account A',1),L('Character A',2)}}
original=copy(db)
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function flush() local n=0 while #timers>0 do n=n+1; assert(n<30,'timer loop'); table.remove(timers,1)() end end
EventRegistry={RegisterCallback=function(_,event,fn) callbacks[event]=fn end}
function CreateFrame() local f={} function f:RegisterEvent() end function f:SetScript(_,fn) self.event=fn end driver=f return f end
EditModeManagerFrameMixin={}
EditModeManagerFrame={}
setmetatable(EditModeManagerFrame,{__index=EditModeManagerFrameMixin})
function EditModeManagerFrame:IsInitialized() return true end
function EditModeManagerFrame:IsEditModeActive() return editing end
function EditModeManagerFrame:HasActiveChanges() return dirty end
EditModePresetLayoutManager={GetCopyOfPresetLayouts=function() return copy(presets) end}
UIParent={}
function Frame(name,index)
 local f={system=0,systemIndex=index,name=name,point={'CENTER',UIParent,'CENTER',0,0}}
 function f:IsShown() return true end
 function f:IsInDefaultPosition() return self.systemInfo.isInDefaultPosition end
 function f:GetHeight() return 40 end
 function f:GetWidth() return 560 end
 function f:SetScale(s) self.scale=s end
 function f:ClearAllPoints() self.point={} end
 function f:SetPoint(...) self.point={...} end
 function f:BreakFromFrameManager() error('addon must not call manager mutation') end
 return f
end
MainActionBar=Frame('MainActionBar',1); MultiBarBottomLeft=Frame('MultiBarBottomLeft',2); MultiBarRight=Frame('MultiBarRight',3)
ObjectiveTrackerFrame=Frame('ObjectiveTrackerFrame'); ObjectiveTrackerFrame.system=12
frames={MainActionBar,MultiBarBottomLeft,MultiBarRight,ObjectiveTrackerFrame}
function nativeApply()
 local layout=db.activeLayout<=3 and presets[db.activeLayout] or db.layouts[db.activeLayout-3]
 for _,f in ipairs(frames) do
  for _,s in ipairs(layout.systems) do
   if s.system==f.system and s.systemIndex==f.systemIndex then f.systemInfo=copy(s) end
  end
 end
end
nativeApply()
function EditModeManagerFrame:GetRightActionBars() return {MultiBarRight} end
function EditModeManagerFrame:GetRightActionBarTopLimit() return 1000 end
function EditModeManagerFrame:GetRightActionBarBottomLimit() return 0 end
EditModeUtil={GetBottomActionBars=function() return {MainActionBar,MultiBarBottomLeft} end,
 IsCenterManagedFrame=function() return false end}
function EditModeManagerFrame:GetDefaultAnchor() return {} end
function EditModeManagerFrame:SetToLayoutAnchor(bar)
 bar:SetPoint('BOTTOMRIGHT','MicroMenuContainer','BOTTOMLEFT',-4.5,-4)
end
function ManageFramePositions() end
ACTION_BARS_RELATIVE_TO_BASE_POSITIONING=true -- actual Camelot default
RIGHT_ACTION_BAR_DEFAULT_OFFSET_X=-5; RIGHT_ACTION_BAR_DEFAULT_OFFSET_Y=0; RIGHT_ACTION_BAR_DEFAULT_PADDING_X=0
MAIN_ACTION_BAR_OFFSET_X=0; MAIN_ACTION_BAR_OFFSET_Y=0; BOTTOM_ACTION_BARS_SPACER_Y=5
encoded={}
C_EditMode={
 GetLayouts=function() return copy(db) end,
 IsValidLayoutName=function() return true end,
 ConvertLayoutInfoToString=function(layout) encoded=copy(layout); return 'serialized' end,
 ConvertStringToLayoutInfo=function() return copy(encoded) end,
 SaveLayouts=function(info)
  assert(not combat and not editing and not dirty,'unsafe save')
  saves=saves+1
  db={activeLayout=info.activeLayout,layouts={}}
  for _,v in ipairs(info.layouts) do if v.layoutType~=0 then db.layouts[#db.layouts+1]=copy(v) end end
  if corrupt then db.layouts[#db.layouts].systems[1].isInDefaultPosition=true end
  if quantize then
   for _,s in ipairs(db.layouts[#db.layouts].systems) do
    s.anchorInfo.offsetX=math.floor(s.anchorInfo.offsetX*1000+0.5)/1000
    s.anchorInfo.offsetY=math.floor(s.anchorInfo.offsetY*1000+0.5)/1000
   end
  end
  nativeApply(); driver.event()
 end,
 OnLayoutAdded=function(index,activate,imported) assert(index==#db.layouts+3 and not activate and imported); added=added+1 end,
 SetActiveLayout=function(index)
  assert(not combat and not editing,'unsafe activation'); activates=activates+1; db.activeLayout=index; nativeApply(); driver.event()
 end,
}
function register()
 EUI_FOREVER_CombatLayout.Register(MainActionBar,{x=0,y=-500})
 EUI_FOREVER_CombatLayout.Register(MultiBarBottomLeft,{x=0,y=-450})
 EUI_FOREVER_CombatLayout.Register(MultiBarRight,{x=800,y=-25})
 EUI_FOREVER_CombatLayout.Register(ObjectiveTrackerFrame,{point='RIGHT',relPoint='RIGHT',x=-109,y=-16},0.8)
end
'''

def fresh():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(setup)
    lua.execute(methods)
    lua.execute(script)
    return lua

lua = fresh()
lua.execute(r'''
-- Reproduce using Blizzard's actual code, without addon repair callbacks.
MainActionBar.point={'CENTER',UIParent,'CENTER',0,-500}
EditModeManagerFrame:UpdateBottomActionBarPositions()
assert(MainActionBar.point[1]=='BOTTOMRIGHT' and MainActionBar.point[2]=='MicroMenuContainer','pre-fix Camelot stack did not move the bar to the right-side menu')
register(); flush()
assert(saves==1 and added==1 and activates==1)
assert(db.activeLayout==6 and #db.layouts==3,'three presets must precede custom indices')
assert(equal(original.layouts[1],db.layouts[1]) and equal(original.layouts[2],db.layouts[2]))
assert(equal(presets[2].systems[5],db.layouts[3].systems[5]),'unowned future system changed')
assert(db.layouts[3].systems[4].anchorInfo.offsetX==-109*0.8,'native stored scale lost')
for _,f in ipairs(frames) do assert(not f:IsInDefaultPosition()) end
MainActionBar.point={'CENTER',UIParent,'CENTER',0,-500}
MultiBarBottomLeft.point={'CENTER',UIParent,'CENTER',0,-450}
MultiBarRight.point={'CENTER',UIParent,'CENTER',800,-25}
local points={copy(MainActionBar.point),copy(MultiBarBottomLeft.point),copy(MultiBarRight.point)}
-- UIParent references are copied too, so compare the meaningful coordinates.
combat=true
for i=1,10 do EditModeManagerFrame:UpdateBottomActionBarPositions(); EditModeManagerFrame:UpdateRightActionBarPositions() end
for i,f in ipairs({MainActionBar,MultiBarBottomLeft,MultiBarRight}) do
 assert(f.point[1]==points[i][1] and f.point[4]==points[i][4] and f.point[5]==points[i][5], 'combat native stack moved custom bar')
end
EUI_FOREVER_CombatLayout.Queue(); flush(); assert(saves==1)
combat=false; driver.event(); flush(); assert(saves==1,'unchanged native layout saved again')
EUI_FOREVER_CombatLayout.Register(MainActionBar,{x=50,y=-510}); flush()
assert(saves==2 and activates==1 and #db.layouts==3,'slider edit created another layout')
assert(#messages==0,'position synchronization failed verification')
assert(db.layouts[3].systems[1].anchorInfo.offsetX==50)
SlashCmdList.EUIFOREVERCOMBATLAYOUT('restore'); flush()
assert(db.activeLayout==2 and EUIForeverCombatLayoutState.disabled)
assert(equal(original.layouts[1],db.layouts[1]) and equal(original.layouts[2],db.layouts[2]))
''')
print('PASS: native combat stack reproduction, additive migration, scale, sync, idempotence, rollback')

for field in ['combat', 'editing', 'dirty']:
    lua=fresh()
    lua.execute(f'register(); {field}=true; flush(); assert(saves==0); {field}=false; driver.event(); flush(); assert(saves==1)')
lua=fresh()
lua.execute('EditModeManagerFrame.overrideLayoutInfo={}; register(); flush(); assert(saves==0); EditModeManagerFrame.overrideLayoutInfo=nil; driver.event(); flush(); assert(saves==1)')
lua=fresh()
lua.execute('callbacks["EditMode.Enter"](); register(); flush(); assert(saves==0); callbacks["EditMode.Exit"](); register(); flush(); assert(saves==1)')
print('PASS: combat, Edit Mode, pending changes, override layout, exit latch deferral')

lua=fresh()
lua.execute(r'''
for i=2,5 do db.layouts[#db.layouts+1]=L('Character '..i,2) end
register(); flush(); assert(saves==0 and #messages==1)
for i=1,10 do driver.event(); flush() end
assert(#messages==1,'failure repeated on every event')
table.remove(db.layouts); SlashCmdList.EUIFOREVERCOMBATLAYOUT('retry'); flush(); assert(saves==1)
''')
lua=fresh()
lua.execute('corrupt=true; register(); flush(); assert(saves==1 and activates==0 and #messages==1); corrupt=false; SlashCmdList.EUIFOREVERCOMBATLAYOUT("retry"); flush(); assert(saves==2 and activates==1 and #db.layouts==3 and EUIForeverCombatLayoutState.pending==nil)')
lua=fresh()
lua.execute('db.layouts[#db.layouts+1]=L("Ellesmere Forever Combat",2); register(); flush(); assert(db.layouts[4].layoutName=="Ellesmere Forever Combat 2")')
lua=fresh()
lua.execute('register(); flush(); C_EditMode.SetActiveLayout(1); flush(); assert(saves==1 and activates==2 and db.activeLayout==1)')
lua=fresh()
lua.execute('C_EditMode.SaveLayouts=nil; register(); flush(); assert(saves==0 and activates==0)')
print('PASS: full slots, bounded failure, retry, corrupted persistence, duplicate name, deliberate selection, missing API')

lua=fresh()
lua.execute('quantize=true; register(); EUI_FOREVER_CombatLayout.Register(MainActionBar,{x=0.000030517578,y=-512.50002574921}); flush(); assert(saves==1 and activates==1); driver.event(); flush(); assert(saves==1)')
# Reload the module with persisted native/character data, rebuilding registrations.
lua.execute(script)
lua.execute('register(); EUI_FOREVER_CombatLayout.Register(MainActionBar,{x=0.000030517578,y=-512.50002574921}); flush(); assert(saves==1 and activates==1 and #db.layouts==3)')
print('PASS: native float rounding and reload without duplicate layout/save')

# Native layouts survive even when the beta loses the per-character identity.
lua=fresh()
lua.execute('register(); flush(); db.layouts[3].layoutName="Ellesmere Forever Combat 4"; for i=1,3 do db.layouts[#db.layouts+1]=L("Other "..i,2) end; EUIForeverCombatLayoutState={}; saves=0; activates=0; added=0')
lua.execute(script)
lua.execute('register(); flush(); assert(saves==0 and activates==0 and added==0 and #db.layouts==6); assert(EUIForeverCombatLayoutState.name=="Ellesmere Forever Combat 4" and EUIForeverCombatLayoutState.previous==nil); assert(#messages==0); driver.event(); flush(); assert(saves==0)')
print('PASS: lost identity recovered from matching active layout with full slots and no native writes')

for variation in [
    'db.layouts[3].systems[1].anchorInfo.offsetX=77',
    'db.layouts[3].layoutName="My layout"',
    'db.activeLayout=2',
    'EUIForeverCombatLayoutState={disabled=true}',
]:
    lua=fresh()
    lua.execute('register(); flush(); for i=1,3 do db.layouts[#db.layouts+1]=L("Other "..i,2) end; EUIForeverCombatLayoutState={}; saves=0; activates=0; added=0; '+variation)
    lua.execute(script)
    lua.execute('register(); flush(); assert(saves==0 and activates==0 and added==0 and #db.layouts==6); assert(EUIForeverCombatLayoutState.name==nil)')
print('PASS: recovery respects mismatched anchors, user layout names, active selection and disabled state')

lua=fresh()
lua.execute(r'''
register(); local savedPosition={x=0,y=-500}
EUI_FOREVER_CombatLayout.Register(MainActionBar,savedPosition); flush()
callbacks['EditMode.Enter'](); editing=true
local anchor=db.layouts[3].systems[1].anchorInfo
anchor.point='TOP'; anchor.relativePoint='BOTTOM'; anchor.relativeTo='MultiBarBottomLeft'; anchor.offsetX=25; anchor.offsetY=-50
callbacks['EditMode.SavedLayouts']()
assert(savedPosition.point=='TOP' and savedPosition.relPoint=='BOTTOM' and savedPosition.relativeTo=='MultiBarBottomLeft' and savedPosition.x==25 and savedPosition.y==-50)
editing=false; callbacks['EditMode.Exit']()
EUI_FOREVER_CombatLayout.Register(MainActionBar,savedPosition); flush()
assert(saves==1,'native saved drag was overwritten')
callbacks['EditMode.Enter'](); editing=true
-- A cancelled visual drag never saves new native anchors/profile coordinates.
MainActionBar.point={'CENTER',UIParent,'CENTER',100,100}
editing=false; callbacks['EditMode.Exit'](); flush()
assert(savedPosition.x==25 and saves==1)
local adopted
EUI_FOREVER_CombatLayout.Register(ObjectiveTrackerFrame,{x=-109,y=-16},0.8,function(p) adopted=p end)
flush(); callbacks['EditMode.Enter'](); editing=true
db.layouts[3].systems[4].anchorInfo.offsetX=80
callbacks['EditMode.SavedLayouts']()
assert(adopted.x==100,'scale-aware native save callback failed')
''')
print('PASS: saved native drag/snap adoption, cancelled drag preservation, scaled HUD callback')
