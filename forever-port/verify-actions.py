"""Run the native action adapter with guarded frames and native Edit Mode ordering."""
from pathlib import Path
import os
import re
from lupa.lua51 import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
EUI_FOREVER=true; EUI_FOREVER_STATUS={}; combat=false; nativeEditing=false; nativeReset=false
mutations=0; borders=0; hudCalls=0
function GetBuildInfo() return '1.60.1','69913' end
function InCombatLockdown() return combat end
function geterrorhandler() return function(err) error(err,0) end end
local function mutate()
 assert(not combat,'protected mutation in combat')
 assert(not nativeEditing,'mutation during native Edit Mode')
 assert(not nativeReset,'mutation during native exit reset')
 mutations=mutations+1
end
function frame(label,parent)
 local f={label=label,parent=parent,points={},shown=true,scripts={},attributes={action=7,type='action',unit='player'}}
 setmetatable(f,{__newindex=function(t,k,v)
  assert(k~='ignoreFramePositionManager','native manager flag tainted')
  rawset(t,k,v)
 end})
 function f:GetName() return self.label end
 function f:GetParent() return self.parent end
 function f:SetParent(p) mutate(); assert(not self.actionButton,'native button reparented'); self.parent=p end
 function f:SetSize(w,h) mutate(); self.w=w; self.h=h end
 function f:GetWidth() return self.w or 100 end
 function f:GetHeight() return self.h or 40 end
 function f:GetEffectiveScale() return 1 end
 function f:SetScale(s) mutate(); self.scale=s end
 function f:SetPoint(...) mutate(); self.points={{...}} end
 function f:ClearAllPoints() mutate(); self.points={} end
 function f:GetPoint() return unpack(self.points[1] or {}) end
 function f:Show() mutate(); self.shown=true; self.baseShowCalls=(self.baseShowCalls or 0)+1 end
 function f:Hide() mutate(); self.shown=false; self.baseHideCalls=(self.baseHideCalls or 0)+1 end
 function f:IsShown() return self.shown end
 function f:HookScript(event,fn) self.scripts[event]=fn end
 function f:SetScript() error('native handler replaced') end
 function f:SetAttribute() error('secure action/unit attribute changed') end
 function f:RegisterForClicks() error('native click registration changed') end
 function f:BreakFromFrameManager() error('native manager bookkeeping tainted') end
 function f:SetAlpha(a) mutate(); self.alpha=a end
 function f:SetColorTexture(...) mutate(); self.color={...} end
 function f:SetDrawLayer(...) mutate(); self.layer={...} end
 function f:SetTexCoord(...) mutate(); self.crop={...} end
 function f:RemoveMaskTexture(mask) mutate(); self.removedMask=mask end
 function f:GetNormalTexture() return self.normal end
 return f
end
UIParent=frame('UIParent'); UIParent.w=1920; UIParent.h=1080
function system(label)
 local f=frame(label,UIParent)
 f.SetPointBase=f.SetPoint; f.ClearAllPointsBase=f.ClearAllPoints
 f.SetScaleBase=f.SetScale; f.HideBase=f.Hide; f.ShowBase=f.Show; f.IsShownBase=f.IsShown
 function f:SetPoint() error('native Edit Mode anchor wrapper invoked') end
 function f:ClearAllPoints() error('native Edit Mode snap wrapper invoked') end
 function f:SetScale() error('native Edit Mode scale wrapper invoked') end
 -- ActionBarMixin's visibility wrappers touch native isShownExternal and
 -- dispatch managed Edit Mode layout. The adapter must use frame base methods.
 function f:Show() error('native ShowOverride tainted isShownExternal and dispatched Edit Mode layout') end
 function f:Hide() error('native HideOverride tainted external visibility') end
 function f:IsShown() error('native IsShownOverride queried managed visibility') end
 function f:ApplySystemAnchor() end
 function f:UpdateGridLayout() end
 return f
end
barNames={'MainActionBar','MultiBarBottomLeft','MultiBarBottomRight','MultiBarRight','MultiBarLeft','MultiBar5','MultiBar6','MultiBar7'}
for _,name in ipairs(barNames) do
 local bar=system(name); _G[name]=bar; bar.actionButtons={}
 bar.BorderArt=frame('borderArt',bar); bar.EndCaps=frame('endCaps',bar)
 for i=1,4 do
  local container=frame(name..'Container'..i,bar)
  local b=frame(name..'Button'..i,container); b.actionButton=true; b.container=container
  b.scripts.OnClick='native-click'; b.scripts.OnEvent='native-events'
  b.icon=frame('icon',b); b.IconMask=frame('mask',b); b.SlotArt=frame('slot',b)
  b.SlotBackground=frame('background',b); b.normal=frame('normal',b)
  b.HotKey=frame('hotkey',b); b.Name=frame('name',b)
  bar.actionButtons[i]=b
 end
end
MainActionBar.shown=false; MultiBar5.shown=false
MicroMenuContainer=system('MicroMenuContainer'); MicroMenu=frame('MicroMenu',MicroMenuContainer)
function MicroMenuContainer:Layout() error('addon invoked taint-sensitive native menu layout') end
function MicroMenu:Layout() error('addon invoked taint-sensitive native menu layout') end
BagsBar=system('BagsBar')
EditModeManagerFrame={}
function EditModeManagerFrame:IsEditModeActive() return nativeEditing end
EventRegistry={callbacks={}}
function EventRegistry:RegisterCallback(event,fn) self.callbacks[event]=fn end
function EventRegistry:TriggerEvent(event) self.callbacks[event]() end
timers={}; C_Timer={After=function(delay,fn) table.insert(timers,{delay,fn}) end}
function flush()
 local n=0
 while #timers>0 do n=n+1; assert(n<30,'queued layout loop'); table.remove(timers,1)[2]() end
end
function hooksecurefunc(target,key,fn)
 local original=target[key]
 target[key]=function(...) local r={original(...)}; fn(...); return unpack(r) end
end
profile={bars={
 MainBar={buttonWidth=30,buttonHeight=24,buttonPadding=3,numIcons=3,numRows=2,iconOrder='reversed',iconZoom=8,hideKeybind=true,hideMacroText=true},
 Bar2={buttonWidth=22,buttonHeight=16,numIcons=4,numRows=2,orientation='vertical'},
 Bar3={enabled=false}, Bar4={barVisibility='never'}, Bar5={alwaysHidden=true},
},barPositions={MainBar={point='CENTER',relPoint='CENTER',x=-300,y=75},Bar2={point='BOTTOM',relPoint='BOTTOM',x=24,y=38}}}
addon={events={}}
function addon:RegisterEvent(event,fn) self.events[event]=fn end
function fire(event) addon.events[event or 'PLAYER_ENTERING_WORLD']() end
EllesmereUI={Lite={}}
function EllesmereUI.Lite.NewAddon() return addon end
function EllesmereUI.Lite.NewDB() return {profile=profile} end
function EllesmereUI.MakeBorder(button) mutate(); borders=borders+1; return {button=button} end
function EllesmereUI:RegisterModule(_,def) self.module=def end
function EUI_FOREVER_StyleHUD(p,queue) mutate(); assert(p==profile); hudCalls=hudCalls+1 end
''')
path = Path(__file__).resolve().parents[2] / "EllesmereUIActionBars/EllesmereUIActionBars_Forever.lua"
source = path.read_text(encoding="utf-8-sig")
lua.execute('assert(loadstring(...))("EllesmereUIActionBars")', source)
lua.execute(r'''
addon:OnInitialize(); addon:OnEnable(); flush()
assert(EUI_FOREVER_NATIVE_ACTIONS and hudCalls>0)
local main=MainActionBar; local b=main.actionButtons[1]
assert(main.shown and main.baseShowCalls==1,'initially hidden enabled main bar did not use native ShowBase')
assert(MultiBar5.shown and MultiBar5.baseShowCalls==1,'initially hidden enabled secondary bar did not use ShowBase')
assert(main.w==63 and main.h==51 and main.scale==1)
assert(main.points[1][4]==-300 and main.points[1][5]==75)
assert(b.w==30 and b.h==24 and b.container.points[1][4]==0 and b.container.points[1][5]==-27)
assert(main.actionButtons[2].container.points[1][4]==33)
assert(main.actionButtons[3].container.points[1][5]==0 and not main.actionButtons[4].container.shown)
assert(b.icon.crop[1]==.08 and b.icon.crop[2]==.92 and b.icon.removedMask==b.IconMask)
assert(b.SlotArt.alpha==0 and b.normal.alpha==0 and b.HotKey.alpha==0 and b.Name.alpha==0)
assert(b.SlotBackground.layer[1]=='BACKGROUND' and b.SlotBackground.color[4]==.85)
assert(not MultiBarBottomRight.shown and not MultiBarRight.shown and not MultiBarLeft.shown)
assert(MultiBarBottomRight.baseHideCalls==1 and MultiBarRight.baseHideCalls==1 and MultiBarLeft.baseHideCalls==1)
assert(MultiBarBottomLeft.actionButtons[2].container.points[1][5]==-18)
assert(MultiBarBottomLeft.actionButtons[3].container.points[1][4]==24)
assert(MicroMenuContainer.points[1][4]==-12 and MicroMenuContainer.points[1][5]==6)
assert(BagsBar.points[1][4]==-6 and BagsBar.points[1][5]==54)
local originalBorders=borders
fire(); flush(); assert(borders==originalBorders,'duplicate border creation')
-- Native anchoring/grid hooks queue restoration rather than paint reentrantly.
main.points={{'CENTER',UIParent,'CENTER',999,999}}
local before=mutations; main:ApplySystemAnchor()
assert(mutations==before and main.points[1][4]==999)
flush(); assert(main.points[1][4]==-300)
-- Pending work must be canceled by the active Edit Mode gate, then stay paused
-- through the native exit interval after Blizzard clears its active flag.
fire(); before=mutations; local beforeHUD=hudCalls
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
profile.barPositions.MainBar.x=-410; profile.bars.MainBar.buttonWidth=32
main:UpdateGridLayout(); main:ApplySystemAnchor(); main.scripts.OnShow(); fire(); flush()
assert(mutations==before and hudCalls==beforeHUD and main.w==63)
nativeEditing=false; nativeReset=true
main:UpdateGridLayout(); main:ApplySystemAnchor(); _EAB_Apply(); fire(); flush()
assert(mutations==before and hudCalls==beforeHUD,'paint resumed before native exit reset completed')
nativeReset=false; EventRegistry:TriggerEvent('EditMode.Exit')
assert(mutations==before,'Exit callback painted synchronously')
flush(); assert(main.points[1][4]==-410 and main.w==67 and hudCalls>beforeHUD)
-- Combat freezes layout and secure buttons; regen applies the latest settings.
before=mutations; combat=true; profile.barPositions.MainBar.y=91
main:UpdateGridLayout(); main:ApplySystemAnchor(); fire(); flush()
assert(mutations==before and main.points[1][5]==75)
combat=false; fire('PLAYER_REGEN_ENABLED'); flush()
assert(main.points[1][5]==91)
-- Exit during combat also defers to regen, with no settings or native fields changed.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
combat=true; before=mutations; nativeEditing=false
EventRegistry:TriggerEvent('EditMode.Exit'); flush(); assert(mutations==before)
combat=false; fire('PLAYER_REGEN_ENABLED'); flush()
for _,name in ipairs(barNames) do
 local bar=_G[name]; assert(bar.ignoreFramePositionManager==nil)
 for _,button in ipairs(bar.actionButtons) do
  assert(button.attributes.action==7 and button.attributes.type=='action' and button.attributes.unit=='player')
  assert(button.scripts.OnClick=='native-click' and button.scripts.OnEvent=='native-events')
  assert(button.parent==button.container and button.container.parent==bar)
 end
end
''')
print("PASS actions: real adapter, saved grid/crop and anchors, base visibility, Edit Mode ordering, combat/resize deferral, native manager/menu protection, secure actions retained")

# Native availability logic is used directly, including pet spacer containers.
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_ActionBar/Shared'
lua.execute('function tInvert(t) local r={} for k,v in pairs(t) do r[v]=k end return r end')
lua.execute((native / 'ActionBar.lua').read_text())
lua.execute((native / 'StanceBar.lua').read_text())
lua.execute((native / 'PetActionBar.lua').read_text())
lua.execute(r'''
function table.wipe(t) for k in pairs(t) do t[k]=nil end end
forms=1; hasPet=false
function GetNumShapeshiftForms() return forms end
function GetShapeshiftFormInfo(i) return 'native-form-'..i,i==1,i~=2,100+i end
function GetShapeshiftFormCooldown(i) return 10,3,1 end
function CooldownFrame_Set(f,start,duration,enabled) f.cooldownData={start,duration,enabled} end
function PetHasActionBar() return hasPet end
function ActionBarBusy() return false end
C_ActionBar={IsPossessBarVisible=function() return false end}
InputUtil={IsMKBUIEnabled=function() return true end}
function ActionBarController_GetCurrentActionBarState() return 0 end
LE_ACTIONBAR_STATE_OVERRIDE=1
function SharedActionButton_RefreshSpellHighlight(button,active) end
EllesmereUI.ELLESMERE_GREEN={r=.2,g=.8,b=.5}
function conditionalBar(name,stance)
 local bar=system(name); _G[name]=bar
 bar.shown=false; bar.actionButtons={}; bar.shownButtonContainers={}
 bar.numButtons=10; bar.numButtonsShowable=10; bar.noSpacers=stance or nil
 bar.UpdateShownButtons=ActionBarMixin.UpdateShownButtons
 function bar:SetShown(shown) self.shown=shown end
 for i=1,10 do
  local container=frame(name..'Container'..i,bar)
  function container:SetShown(shown) self.shown=shown end
  local b=frame(name..'Button'..i,container); b.actionButton=true; b.container=container; b.index=i
  b.scripts.OnClick='native-click'; b.scripts.OnEvent='native-events'
  b.icon=frame('icon',b); b.IconMask=frame('mask',b); b.normal=frame('normal',b)
  b.cooldown=frame('cooldown',b); b.checked=false
  b.AutoCastOverlay=frame('autocast',b); b.AutoCastOverlay.autoCastEnabled=true
  b.AutoCastOverlay.Shine={playing=true}; b.AutoCastOverlay.shown=i~=2
  b.CheckedTexture=frame('checked',b); b.PushedTexture=frame('pushed',b); b.HighlightTexture=frame('highlight',b)
  b.attributes.statehidden=stance and i==2 or false
  function b:GetAttribute(key) return self.attributes[key] end
  function b:GetShowGrid() return stance end
  function b:HasAction() return self.index<=3 end
  function b:SetShown(shown) self.shown=shown end
  function b:GetID() return self.index end
  function b:SetChecked(checked) self.checked=checked end
  function b.icon:SetTexture(texture) self.texture=texture end
  function b.icon:SetVertexColor(...) self.vertex={...} end
  function b:UpdateButtonState() self.nativeUpdates=(self.nativeUpdates or 0)+1 end
  bar.actionButtons[i]=b
 end
 if stance then
  bar.Update=StanceBarMixin.Update; bar.UpdateState=StanceBarMixin.UpdateState; bar.ShouldShow=StanceBarMixin.ShouldShow
  function bar:UpdateBackgroundArt() end
 else
  bar.Update=PetActionBarMixin.Update
  function bar:UpdateCooldowns() self.actionButtons[1].cooldown.cooldownData={1,9,1} end
  -- Only native PetActionBar.Update owns this availability change.
  function bar:Hide() self.shown=false end
 end
 bar:UpdateShownButtons(); bar:Update()
 return bar
end
local stance=conditionalBar('StanceBar',true)
local pet=conditionalBar('PetActionBar',false)
profile.bars.StanceBar={buttonWidth=45,buttonHeight=45,overrideNumRows=1,alwaysShowButtons=true,overrideNumIcons=10}
profile.barPositions.StanceBar={x=417,y=-512.5}
profile.bars.PetBar={buttonWidth=40,buttonHeight=40,orientation='vertical',overrideNumRows=1,overrideNumIcons=1,alwaysShowButtons=true}
profile.barPositions.PetBar={x=856,y=-28}
fire(); flush()
assert(stance.w==45 and stance.h==45 and stance.shown,'single aura dimensions/native visibility changed')
assert(stance.points[1][4]==417 and stance.points[1][5]==-512.5,'stance imported anchor missed')
assert(stance.actionButtons[1].w==45 and stance.actionButtons[1].checked and stance.actionButtons[1].cooldown.cooldownData[2]==3,'stance state or cooldown altered')
assert(not stance.actionButtons[2].container.shown and not stance.actionButtons[2].shown,'unavailable stance exposed')
assert(pet.w==40 and pet.h==418 and not pet.shown,'pet layout/count/native availability changed')
assert(pet.points[1][4]==856 and pet.points[1][5]==-28 and pet.actionButtons[10].container.points[1][5]==-378,'vertical pet grid/anchor wrong')
assert(not pet.actionButtons[4].shown and pet.actionButtons[4].container.shown,'native empty pet slot spacer changed')
for _,bar in ipairs({stance,pet}) do
 assert(not bar.baseShowCalls and not bar.baseHideCalls,'adapter changed conditional bar visibility')
 for _,button in ipairs(bar.actionButtons) do
  assert(not button.baseShowCalls and not button.baseHideCalls and not button.container.baseShowCalls and not button.container.baseHideCalls,'adapter changed conditional button/container visibility')
  assert(button.AutoCastOverlay.autoCastEnabled and button.AutoCastOverlay.Shine.playing,'native autocast state changed')
  assert(button.scripts.OnClick=='native-click' and button.attributes.action==7,'native conditional action replaced')
 end
end
assert(pet.actionButtons[1].AutoCastOverlay.w==40 and pet.actionButtons[1].CheckedTexture.color[4]==.25,'pet state artwork not sized/themed')
-- A native form change includes a statehidden form: do not expose it or reserve its slot.
forms=3; stance:Update(); flush()
assert(stance.w==92 and #stance.shownButtonContainers==2 and stance.numButtonsShowable==3,'native form policy overwritten')
assert(stance.actionButtons[3].container.points[1][4]==47 and not stance.actionButtons[2].container.shown,'new forms not compacted safely')
assert(stance.actionButtons[2].icon.vertex[1]==.4,'uncastable native tint changed')
forms=0; stance:Update(); flush(); assert(not stance.shown,'zero-form stance bar exposed')
pet.shown=true; hasPet=true; pet:Update(); pet:UpdateShownButtons(); flush()
assert(pet.shown and pet.w==40 and pet.actionButtons[1].cooldown.cooldownData[2]==9,'native pet summon state lost')
-- Native code can reveal forms in combat; styling must wait for regen.
forms=4; combat=true
-- UpdateState normally performs protected native work; exercise its posthook
-- through UpdateShownButtons after preparing the native availability snapshot.
stance.numButtonsShowable=4; stance:UpdateShownButtons()
local before=mutations; flush(); assert(mutations==before,'conditional bar styling ran in combat')
combat=false; fire('PLAYER_REGEN_ENABLED'); flush()
assert(stance.actionButtons[4].w==45 and stance.w==139,'deferred form layout missed regen')
assert(not stance.shown,'restyling forced a hidden conditional bar visible')
local pages=EllesmereUI.module.pages
assert(pages[9]=='StanceBar' and pages[10]=='PetBar','conditional geometry options missing')
''')
print('PASS conditional bars: native form availability/statehidden, pet spacers, imported stance/pet geometry, checked/cooldown/autocast preservation, no availability mutations and combat deferral')

# Execute the actual manager methods without loading unrelated Edit Mode UI.
manager_source = (native.parents[1] / 'Blizzard_EditMode/Shared/EditModeManager.lua').read_text()
lua.execute('EditModeManagerFrameMixin={}')
for method in ('UpdateActionBarLayout', 'UpdateBottomActionBarPositions', 'UpdateRightActionBarPositions'):
    match = re.search(r'function EditModeManagerFrameMixin:' + method + r'\([^\n]*\).*?\nend\n', manager_source, re.S)
    assert match, method
    lua.execute(match.group())
lua.execute(r'''
nativeLayoutCalls=0; nativeWrapperCalls=0; inNativeChain=false
local manager=EditModeManagerFrame
manager.UpdateActionBarLayout=EditModeManagerFrameMixin.UpdateActionBarLayout
manager.UpdateBottomActionBarPositions=EditModeManagerFrameMixin.UpdateBottomActionBarPositions
manager.UpdateRightActionBarPositions=EditModeManagerFrameMixin.UpdateRightActionBarPositions
function manager:IsInitialized() return true end
function manager:GetDefaultAnchor() return {} end
function manager:GetRightActionBars() return {MultiBarRight,MultiBarLeft} end
function manager:GetRightActionBarTopLimit() return 500 end
function manager:GetRightActionBarBottomLimit() return 0 end
EditModeUtil={}
function EditModeUtil:IsBottomAnchoredActionBar(bar) return bar==PetActionBar end
function EditModeUtil:IsRightAnchoredActionBar() return false end
function EditModeUtil:GetBottomActionBars() return {MainActionBar,MultiBarBottomLeft} end
function EditModeUtil:IsCenterManagedFrame() return false end
ACTION_BARS_RELATIVE_TO_BASE_POSITIONING=false
MAIN_ACTION_BAR_OFFSET_X=0; MAIN_ACTION_BAR_OFFSET_Y=42; BOTTOM_ACTION_BARS_SPACER_Y=4
RIGHT_ACTION_BAR_DEFAULT_OFFSET_X=-5; RIGHT_ACTION_BAR_DEFAULT_OFFSET_Y=0; RIGHT_ACTION_BAR_DEFAULT_PADDING_X=2
function ManageFramePositions()
 nativeLayoutCalls=nativeLayoutCalls+1
 MicroMenuContainer.points={{'BOTTOM',UIParent,'BOTTOM',0,0}}
 BagsBar.points={{'BOTTOM',UIParent,'BOTTOM',0,0}}
end
for _,bar in ipairs({MainActionBar,MultiBarBottomLeft,MultiBarRight,MultiBarLeft}) do
 function bar:IsShown() return self.shown end
 function bar:IsInDefaultPosition() return true end
 function bar:ClearAllPoints()
  assert(inNativeChain,'addon called native clear/snap wrapper'); nativeWrapperCalls=nativeWrapperCalls+1; self.points={}
 end
 function bar:SetPoint(...)
  assert(inNativeChain,'addon called native anchor wrapper'); nativeWrapperCalls=nativeWrapperCalls+1; self.points={{...}}
 end
 function bar:SetScale(value)
  assert(inNativeChain,'addon called native scale wrapper'); nativeWrapperCalls=nativeWrapperCalls+1; self.scale=value
 end
end
local pet=PetActionBar
pet.OnEvent=PetActionBarMixin.OnEvent
pet.Hide=EditModeActionBarMixin.HideOverride
pet.UpdateVisibility=EditModeActionBarMixin.UpdateVisibility
function pet:ShouldBreakSnappedFramesOnHide() return false end
function pet:SetShownBase(value) self.shown=value end
profile.barPositions.Bar4={x=896,y=-28}; profile.barPositions.Bar5={x=-937,y=259}
fire(); flush() -- Installs native manager posthooks through the actual adapter.
local beforeHUD=hudCalls
hasPet=false; pet.shown=true; pet.isShownExternal=true
inNativeChain=true; pet:OnEvent('PLAYER_TARGET_CHANGED'); inNativeChain=false
assert(nativeLayoutCalls>0 and nativeWrapperCalls>0,'native target→pet→visibility→layout chain did not execute')
assert(not pet.shown and not pet.isShownExternal,'native pet dismissal policy changed')
assert(MainActionBar.points[1][4]==profile.barPositions.MainBar.x and MainActionBar.points[1][5]==profile.barPositions.MainBar.y,'target event left temporary main anchor until timer flush')
assert(MultiBarBottomLeft.points[1][4]==24 and MultiBarBottomLeft.points[1][5]==38,'target event left temporary secondary anchor')
assert(MicroMenuContainer.points[1][4]==-12 and BagsBar.points[1][4]==-6,'target event left temporary menu/bag anchors')
assert(hudCalls==beforeHUD,'synchronous native anchor restoration repainted HUD')
assert(#timers>0,'native layout did not retain deferred cosmetics')
flush()
-- The same native target event can run repeatedly without a visible intermediate layout.
for i=1,3 do
 inNativeChain=true; pet:OnEvent('PLAYER_TARGET_CHANGED'); inNativeChain=false
 assert(MainActionBar.points[1][4]==profile.barPositions.MainBar.x,'repeated target event jumped')
end
flush()
-- Native right-side positioning may change scale as well as anchors.
MultiBarRight.shown=true; MultiBarLeft.shown=true
inNativeChain=true; manager:UpdateRightActionBarPositions(); inNativeChain=false
assert(MultiBarRight.scale==1 and MultiBarRight.points[1][4]==896 and MultiBarLeft.points[1][4]==-937,'right-side anchors/scale not restored synchronously')
flush()
-- Native Edit Mode and its exit reset must remain free of synchronous writes.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
local before=mutations
inNativeChain=true; pet:OnEvent('PLAYER_TARGET_CHANGED'); inNativeChain=false
assert(mutations==before,'anchor restoration changed frames inside Edit Mode')
assert(MainActionBar.points[1][4]~=profile.barPositions.MainBar.x,'native Edit Mode layout was overridden')
nativeEditing=false; nativeReset=true
inNativeChain=true; pet:OnEvent('PLAYER_TARGET_CHANGED'); inNativeChain=false
assert(mutations==before,'anchor restoration ran before native exit completed')
nativeReset=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush()
assert(MainActionBar.points[1][4]==profile.barPositions.MainBar.x,'post Edit Mode restoration failed')
combat=true; before=mutations
inNativeChain=true; pet:OnEvent('PLAYER_TARGET_CHANGED'); inNativeChain=false
assert(mutations==before,'synchronous anchor restoration ran in combat')
flush(); combat=false; fire('PLAYER_REGEN_ENABLED'); flush()
assert(MainActionBar.points[1][4]==profile.barPositions.MainBar.x,'combat-deferred restoration failed')
''')
print('PASS native target chain: PetActionBar.OnEvent -> Update -> HideOverride -> UpdateVisibility -> manager layout; imported anchors restored before timers; deferred cosmetics, repeated target events, right-bar scale and combat/Edit Mode gates')
