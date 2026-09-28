"""Tracker import, base anchoring and native Edit Mode save/cancel lifecycle."""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

source = (Path(__file__).resolve().parents[2] / "EllesmereUIQuestTracker/EllesmereUIQuestTracker_Forever.lua").read_text(encoding="utf-8-sig")
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
EUI_FOREVER=true; EUI_CLIENT_BLOCKED=false; combat=false; nativeEditing=false; nativeReset=false
mutations=0; geometry=0
EllesmereUIDB={activeProfile='Pickme - Forever'}
profiles={['Pickme - Forever']={forceOnScreen=true},Other={forceOnScreen=false}}
ns={EQT={}}
function ns.EQT.DB() return profiles[EllesmereUIDB.activeProfile] end
function ns.EQT.Cfg(k) return ns.EQT.DB()[k] end
function GetBuildInfo() return '1.60.1','69913' end
function InCombatLockdown() return combat end
UIParent={w=1920,h=1080,GetName=function() return 'UIParent' end,GetHeight=function(self) return self.h end}
Minimap={GetName=function() return 'Minimap' end}
trackerState={point={'CENTER',UIParent,'CENTER',0,0},w=235,h=800,clamped=false}
local function mutate()
 assert(not combat,'tracker changed in combat')
 assert(not nativeEditing,'tracker changed in Edit Mode')
 assert(not nativeReset,'tracker changed during native exit reset')
 mutations=mutations+1
end
ObjectiveTrackerFrame={scripts={OnClick='nativeQuestClick',OnEvent='nativeQuestEvents'},attributes={unit='player'}}
local f=ObjectiveTrackerFrame
function f:ClearAllPointsBase() mutate(); geometry=geometry+1; trackerState.point={} end
function f:SetPointBase(...) mutate(); geometry=geometry+1; trackerState.point={...} end
function f:GetPoint() return unpack(trackerState.point) end
function f:SetClampedToScreen(v) mutate(); trackerState.clamped=v end
function f:SetPoint() error('native Edit Mode anchor override invoked') end
function f:ClearAllPoints() error('native snap state changed') end
function f:SetParent() error('native tracker reparented') end
function f:SetAttribute() error('native secure attributes changed') end
function f:Update() error('native quest refresh invoked by addon') end
function f:UpdateHeight()
 assert(nativeContext,'native height refresh invoked by addon')
 nativeHeightPoint={unpack(trackerState.point)}
 nativeHeightCalls=(nativeHeightCalls or 0)+1
end
function f:IsShown() return true end
function f:SetSize() error('native tracker resized') end
function f:SetHeight() error('native tracker resized') end
function f:Show() error('native tracker visibility overridden') end
function f:Hide() error('native tracker visibility overridden') end
function f:BreakFromFrameManager() error('native manager state changed') end
function f:OnSystemPositionChange() assert(nativeContext,'addon invoked native position change') end
function f:ResetToDefaultPosition() assert(nativeContext,'addon invoked native reset') end
function f:ApplySystemAnchor() assert(nativeContext,'addon invoked native anchor dispatch') end
function f:HookScript(event,fn) self.scripts[event]=fn end
setmetatable(f,{__newindex=function(_,key) error('native Lua field written: '..key) end})
function nativePlace(point,relative,relPoint,x,y,explicitChange)
 trackerState.point={point,relative,relPoint,x,y}
 nativeContext=true; f:ApplySystemAnchor()
 if explicitChange then f:OnSystemPositionChange() end
 nativeContext=false
end
function nativeDefault(point,relative,relPoint,x,y)
 nativePlace(point,relative,relPoint,x,y)
 nativeContext=true; f:ResetToDefaultPosition(); nativeContext=false
end
function hooksecurefunc(target,key,fn)
 if type(target)=='string' then target,key,fn=_G,target,key end
 local original=target[key]
 target[key]=function(...) local r={original(...)}; fn(...); return unpack(r) end
end
EditModeManagerFrame={}
function EditModeManagerFrame:IsEditModeActive() return nativeEditing end
EventRegistry={callbacks={}}
function EventRegistry:RegisterCallback(event,fn) self.callbacks[event]=fn end
function EventRegistry:TriggerEvent(event) self.callbacks[event]() end
timers={}; C_Timer={After=function(_,fn) table.insert(timers,fn) end}
function flush()
 local n=0; while #timers>0 do n=n+1; assert(n<10,'tracker anchoring loop'); table.remove(timers,1)() end
end
events={}
function CreateFrame()
 local e={registered={}}
 function e:RegisterEvent(event) self.registered[event]=true end
 function e:SetScript(_,fn) self.handler=fn end
 table.insert(events,e); return e
end
function fire(event) for _,e in ipairs(events) do if e.registered[event] then e.handler(e,event) end end end
function at(point,relative,relPoint,x,y)
 local p=trackerState.point
 return p[1]==point and p[2]==relative and p[3]==relPoint and p[4]==x and p[5]==y
end
function savedAt(point,relative,relPoint,x,y)
 local p=ns.EQT.DB().foreverPosition
 return p and p.point==point and p.relativeTo==relative and p.relPoint==relPoint and p.x==x and p.y==y
end
''')
# Run the actual native global dispatch, mainline override and right-container
# method. Only C frame/layout primitives are mocks; the addon never calls this
# native chain itself. This verifies repair happens after native height work and
# before the completed caller can render, without flushing C_Timer.
native_root = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["LOCALAPPDATA"]) / "Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns"))
panel = (native_root / "Blizzard_UIParentPanelManager/Shared/UIParentPanelManager.lua").read_text(encoding="utf-8-sig")
dispatch = panel[panel.index("function ManageFramePositions()"):panel.index("function ToggleFrame(frame)")]
right = panel[panel.index("function FramePositionDelegate:ManageRightFrameContainer()"):panel.index("-- Call this function to update the positions", panel.index("function FramePositionDelegate:ManageRightFrameContainer()"))]
override = (native_root / "Blizzard_UIParentPanelManager/Mainline/UIParentPanelManagerOverrides.lua").read_text(encoding="utf-8-sig")
lua.execute(r'''
nativePanel={}
FramePositionDelegate={}
function FramePositionDelegate:SetAttribute(key,value)
 assert(nativeContext and key=='manage-frame-positions' and value==true)
 nativePanel.ManageFramePositions(self)
end
function FramePositionDelegate:ManageBottomFrameContainer() assert(nativeContext) end
MinimapCluster={GetHeight=function() return 160 end}
nativeRightContainer={BottomManagedLayoutContainer={Layout=function() assert(nativeContext) end}}
function nativeRightContainer:ClearAllPoints() assert(nativeContext) end
function nativeRightContainer:Layout()
 assert(nativeContext)
 trackerState.point={'TOPRIGHT',UIParent,'TOPRIGHT',-10,-200}
end
function GetRightManagedFrameContainer() return nativeRightContainer end
EditModeUtil={GetRightContainerAnchor=function()
 return {SetPoint=function(_,container,clear) assert(container==nativeRightContainer and clear and nativeContext) end}
end}
function nativeManagedReset()
 nativeContext=true; ManageFramePositions(); nativeContext=false
end
''')
lua.execute('assert(loadstring(...))("native-panel",nativePanel)', override)
lua.execute(right + dispatch)
lua.execute('assert(loadstring(...))("EllesmereUIQuestTracker",ns)', source)
lua.execute(r'''
ns.EQT.InitForeverPosition(); flush()
assert(at('RIGHT',UIParent,'RIGHT',-109,-16),'named Retail Pickme tracker anchor not imported')
assert(savedAt('RIGHT','UIParent','RIGHT',-109,-16) and trackerState.clamped)
assert(ObjectiveTrackerFrame.scripts.OnClick=='nativeQuestClick' and ObjectiveTrackerFrame.attributes.unit=='player')
assert(trackerState.w==235 and trackerState.h==800,'native dimensions changed')
-- Completed native anchor calls restore immediately, before a timer/render tick.
nativePlace('CENTER',UIParent,'CENTER',0,0)
assert(at('RIGHT',UIParent,'RIGHT',-109,-16),'native anchor call leaked intermediate position')
flush(); assert(at('RIGHT',UIParent,'RIGHT',-109,-16))
local beforeNativeHeight=nativeHeightCalls or 0
nativeManagedReset()
assert(nativeHeightCalls==beforeNativeHeight+1)
assert(nativeHeightPoint[1]=='TOPRIGHT' and nativeHeightPoint[5]==-200,'addon anchor changed native height calculation')
assert(at('RIGHT',UIParent,'RIGHT',-109,-16),'managed layout leaked intermediate position before timer flush')
flush(); assert(at('RIGHT',UIParent,'RIGHT',-109,-16))
-- RIGHT remains tied to the current screen, with exact saved offsets retained.
UIParent.w=1360; UIParent.h=768; fire('DISPLAY_SIZE_CHANGED'); flush()
assert(at('RIGHT',UIParent,'RIGHT',-109,-16) and UIParent.w+trackerState.point[4]==1251)
UIParent.w=1920; UIParent.h=1080; fire('UI_SCALE_CHANGED'); flush()
assert(at('RIGHT',UIParent,'RIGHT',-109,-16) and savedAt('RIGHT','UIParent','RIGHT',-109,-16))
-- Pending paint before entering Edit Mode cannot run while native UI is active.
fire('PLAYER_ENTERING_WORLD'); nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
local before=mutations
nativePlace('TOPLEFT',UIParent,'TOPLEFT',50,-80,true); fire('DISPLAY_SIZE_CHANGED'); flush()
assert(mutations==before and savedAt('RIGHT','UIParent','RIGHT',-109,-16))
nativeManagedReset(); assert(mutations==before and at('TOPRIGHT',UIParent,'TOPRIGHT',-10,-200))
-- Cancel/close clears Blizzard's active flag BEFORE restoring its own layout.
nativeEditing=false; nativeReset=true
nativePlace('CENTER',UIParent,'CENTER',0,0); flush(); assert(mutations==before)
nativeManagedReset(); assert(mutations==before,'managed posthook bypassed Edit Mode exit latch')
nativeReset=false; EventRegistry:TriggerEvent('EditMode.Exit')
assert(mutations==before,'exit event applied anchor synchronously')
flush(); assert(at('RIGHT',UIParent,'RIGHT',-109,-16))
-- Saving another system must not adopt the native default tracker position.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
nativePlace('CENTER',UIParent,'CENTER',0,0)
EventRegistry:TriggerEvent('EditMode.SavedLayouts')
assert(savedAt('RIGHT','UIParent','RIGHT',-109,-16))
nativeEditing=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush()
-- Deliberate saved tracker drag is persisted in addon-owned configuration.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
before=mutations; nativePlace('TOPRIGHT',UIParent,'TOPRIGHT',-70,-120,true)
EventRegistry:TriggerEvent('EditMode.SavedLayouts')
assert(savedAt('TOPRIGHT','UIParent','TOPRIGHT',-70,-120) and mutations==before)
nativeEditing=false; nativeReset=true
nativePlace('CENTER',UIParent,'CENTER',0,0); flush(); assert(mutations==before)
nativeReset=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush()
assert(at('TOPRIGHT',UIParent,'TOPRIGHT',-70,-120))
-- Native named-frame snaps and explicit reset-to-default are retained on Save.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
nativeDefault('TOPRIGHT',Minimap,'BOTTOMRIGHT',0,-10)
EventRegistry:TriggerEvent('EditMode.SavedLayouts')
nativeEditing=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush()
assert(savedAt('TOPRIGHT','Minimap','BOTTOMRIGHT',0,-10) and at('TOPRIGHT',Minimap,'BOTTOMRIGHT',0,-10))
-- Later canceled changes do not undo the previously saved tracker location.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
nativePlace('CENTER',UIParent,'CENTER',20,30,true)
nativeEditing=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush()
assert(at('TOPRIGHT',Minimap,'BOTTOMRIGHT',0,-10))
-- Combat and a missing named relative frame defer safely until their events.
combat=true; before=mutations; nativePlace('CENTER',UIParent,'CENTER',0,0)
nativeManagedReset(); assert(mutations==before,'managed posthook moved tracker during combat')
fire('DISPLAY_SIZE_CHANGED'); flush(); assert(mutations==before)
combat=false; fire('PLAYER_REGEN_ENABLED'); flush(); assert(at('TOPRIGHT',Minimap,'BOTTOMRIGHT',0,-10))
local realMinimap=Minimap; Minimap=nil; before=mutations
nativePlace('CENTER',UIParent,'CENTER',0,0); flush(); assert(mutations==before)
Minimap=realMinimap; fire('ADDON_LOADED'); flush(); assert(at('TOPRIGHT',Minimap,'BOTTOMRIGHT',0,-10))
-- Other profiles retain their native position; their existing clamp option works.
EllesmereUIDB.activeProfile='Other'; nativePlace('CENTER',UIParent,'CENTER',10,20)
local beforeGeometry=geometry; ns.EQT.QueueForeverPosition(); flush()
assert(geometry==beforeGeometry and at('CENTER',UIParent,'CENTER',10,20))
assert(not trackerState.clamped and profiles.Other.foreverPosition==nil)
EllesmereUIDB.activeProfile='Pickme - Forever'; ns.EQT.QueueForeverPosition(); flush()
assert(at('TOPRIGHT',Minimap,'BOTTOMRIGHT',0,-10) and trackerState.clamped)
assert(ObjectiveTrackerFrame.ignoreFramePositionManager==nil and ObjectiveTrackerFrame.editModeHeight==nil)
assert(ObjectiveTrackerFrame.scripts.OnEvent=='nativeQuestEvents')
''')
retail = LuaRuntime()
retail.execute('EUI_FOREVER=false; ns={EQT={}}')
retail.execute('assert(loadstring(...))("test",ns)', source)
assert retail.globals().ns.EQT.InitForeverPosition is None
print("PASS quest tracker: sourced Pickme import, synchronous completed native anchor/managed-layout repair before timers, native height ordering, deferred events, resolution changes, native size/actions preserved, Edit Mode cancel/save/other-system/reset/snap behavior, exit latch, combat/late relative frame, profile isolation, Retail gate")
