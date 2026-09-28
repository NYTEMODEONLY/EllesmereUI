"""Native drag/grid edges and native cooldown numbers, without game access.

Reuse the guarded action-adapter harness, then exercise the actual Blizzard
grid/visibility and countdown preference functions against the loaded adapter.
No simulated addon cooldown timer or secure action implementation is used.
"""
from pathlib import Path
import os
import re
import runpy

context = runpy.run_path(str(Path(__file__).with_name('verify-actions.py')))
lua = context['lua']
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_ActionBar/Shared'
source = (native / 'ActionButton.lua').read_text(encoding='utf-8-sig')
countdown = re.search(r'function ActionButton_UpdateCooldownNumberHidden\(actionButton\).*?\nend', source, re.S).group(0)
lua.execute('local countdownForCooldownsCVarName="countdownForCooldowns";\n' + countdown)
lua.execute(r'''
combat=false; nativeEditing=false; nativeReset=false
local nativeSlots=MainActionBar.actionButtons
local nativeClicks={}
for i,b in ipairs(nativeSlots) do nativeClicks[i]=b.scripts.OnClick end

-- Cosmetic countdown setup must not touch any native timer/state/format text.
local main=MainActionBar; local button=main.actionButtons[1]
local function cooldown()
 local cd=frame('native-cooldown',button)
 cd.shown=true; cd.drawSwipe=true; cd.hideNumbers=true; cd.timerCalls=0
 cd.scripts.OnUpdate='native-engine-timer'
 function cd:GetCountdownFontString() return self.countdownText end
 function cd:SetCooldown(start,duration,rate)
  self.timerCalls=self.timerCalls+1; self.nativeData={start,duration,rate}
 end
 function cd:SetCooldownFromDurationObject(value) self.timerCalls=self.timerCalls+1; self.durationObject=value end
 function cd:SetHideCountdownNumbers(value) self.hideNumbers=value; self.numberCalls=(self.numberCalls or 0)+1 end
 function cd:SetDrawSwipe() error('addon changed native swipe visibility') end
 function cd:SetSwipeColor(...) assert(not combat and not nativeEditing); self.swipeColor={...} end
 function cd:Clear() error('addon cleared native timer') end
 return cd
end
local function label(cd)
 local fs=frame('native-countdown-text',cd)
 function fs:SetFont(path,size,flags)
  assert(not combat and not nativeEditing); self.font={path,size,flags}
 end
 function fs:SetTextColor(...) self.textColor={...} end
 function fs:SetText() error('addon replaced native countdown text/formatter') end
 return fs
end
button.cooldown=cooldown(); button.chargeCooldown=cooldown()
button.chargeCooldown.countdownText=label(button.chargeCooldown)
local cd=button.cooldown
CVarCallbackRegistry={}
EllesmereUIDB={}
countdownEnabled=false; cvarWrites=0
function CVarCallbackRegistry:GetCVarValueBool(key) assert(key=='countdownForCooldowns'); return countdownEnabled end
C_CVar={GetCVarBool=function(key) assert(key=='countdownForCooldowns'); return countdownEnabled end,
 SetCVar=function(key,value)
  assert(not combat and not nativeEditing and key=='countdownForCooldowns')
  cvarWrites=cvarWrites+1; countdownEnabled=value=='1'
  ActionButton_UpdateCooldownNumberHidden(button)
 end}
STANDARD_TEXT_FONT='fallback'
function EllesmereUI.GetFontPath(key) assert(key=='actionBars'); return 'Pickme-font' end
profile.bars.MainBar.cooldownFontSize=12
profile.bars.MainBar.cooldownTextXOffset=2; profile.bars.MainBar.cooldownTextYOffset=-1
profile.bars.MainBar.cooldownTextColor={r=.2,g=.8,b=.4}
_EAB_Apply(); flush()
assert(cvarWrites==1 and countdownEnabled and EllesmereUIDB.foreverActionCountdownMigrated)
assert(profile.foreverCountdownMigrated==nil,'client preference migration leaked into bar profile')
assert(not cd.hideNumbers and button.chargeCooldown.hideNumbers,'native charge visibility changed')
assert(cd.timerCalls==0 and cd.shown and cd.drawSwipe and cd.scripts.OnUpdate=='native-engine-timer')
assert(cd.swipeColor[1]==0 and cd.swipeColor[4]==.85,'cooldown shading missing before lazy text')
-- Classic can create this FontString only after its first actual cooldown.
cd:SetCooldown(100,120,1); cd.countdownText=label(cd); flush()
assert(cd.timerCalls==1 and cd.nativeData[1]==100 and cd.nativeData[2]==120)
assert(cd.countdownText.font[1]=='Pickme-font' and cd.countdownText.font[2]==16)
assert(cd.countdownText.textColor[1]==.2 and cd.countdownText.points[1][4]==2 and cd.countdownText.points[1][5]==-1)
cd:SetCooldown(222,60,1); flush(); assert(cd.timerCalls==2 and cd.nativeData[2]==60)
local SECRET={}; function issecretvalue(v) return rawequal(v,SECRET) end
cd:SetCooldown(SECRET,SECRET,SECRET); flush(); assert(cd.nativeData[1]==SECRET)
cd:SetCooldownFromDurationObject(SECRET); flush(); assert(cd.durationObject==SECRET)
-- Formatting/visibility remain native after the one-time migration.
C_CVar.SetCVar('countdownForCooldowns','0'); flush(); _EAB_Apply(); flush()
assert(cvarWrites==2 and not countdownEnabled and cd.hideNumbers,'import overrode later native preference')
local previousProfile=profile
profile={bars=previousProfile.bars,barPositions=previousProfile.barPositions}; addon.db.profile=profile
_EAB_Apply(); flush()
assert(cvarWrites==2 and not countdownEnabled and cd.hideNumbers,'profile switch repeated global preference import')
local report=EUI_FOREVER_STATUS.ActionBarReport()
assert(report:find('Native cooldown countdown: false; preference imported: true',1,true))
local getter=C_CVar.GetCVarBool; local writesBeforeReport=cvarWrites
C_CVar.GetCVarBool=function() return SECRET end; EllesmereUIDB.foreverActionCountdownMigrated=SECRET
report=EUI_FOREVER_STATUS.ActionBarReport()
assert(report:find('Native cooldown countdown: unavailable; preference imported: unavailable',1,true))
assert(cvarWrites==writesBeforeReport,'diagnostic report changed preference')
C_CVar.GetCVarBool=getter; EllesmereUIDB.foreverActionCountdownMigrated=true
C_CVar.SetCVar('countdownForCooldowns','1'); flush()
profile.bars.MainBar.cooldownFontSize=30; profile.bars.MainBar.cooldownFontFit=true
_EAB_Apply(); flush(); assert(cd.countdownText.font[2]==12,'fit did not use shorter 24px button axis')
profile.bars.MainBar.foreverCooldownFontSize=18; profile.bars.MainBar.cooldownFontFit=false
profile.foreverCooldownSwipeAlpha=90
_EAB_Apply(); flush(); assert(cd.countdownText.font[2]==18 and cd.swipeColor[4]==.9)
local fontBefore=cd.countdownText.font
combat=true; cd:SetCooldown(400,120,1); flush(); assert(cd.countdownText.font==fontBefore)
combat=false; fire('PLAYER_REGEN_ENABLED'); flush(); assert(cd.countdownText.font~=fontBefore)
for i,b in ipairs(nativeSlots) do assert(b.scripts.OnClick==nativeClicks[i]) end

-- Fresh bar uses the actual native grid/visibility methods before the adapter
-- installs hooks. Native show/hide and action state remain owned by these methods.
main=system('MainActionBar'); MainActionBar=main
main.actionButtons={}; main.shownButtonContainers={}; main.numButtonsShowable=4
main.numRows=1; main.minButtonPadding=2; main.buttonPadding=2
main.isHorizontal=true; main.addButtonsToRight=true; main.addButtonsToTop=false; main.nativeEnabled=true
main.UpdateShownButtons=ActionBarMixin.UpdateShownButtons
main.UpdateGridLayout=ActionBarMixin.UpdateGridLayout
main.ShouldUpdateGrid=ActionBarMixin.ShouldUpdateGrid
main.CacheGridSettings=ActionBarMixin.CacheGridSettings
main.GetShowAllButtons=ActionBarMixin.GetShowAllButtons
main.SetShowGrid=ActionBarMixin.SetShowGrid
function main:UpdateFrameStrata() self.strataUpdates=(self.strataUpdates or 0)+1 end
function main:UpdateSpellFlyoutDirection() self.flyoutUpdates=(self.flyoutUpdates or 0)+1 end
function main:Layout() self:SetSize(144,36) end
function main:UpdateVisibility()
 local show=self.nativeEnabled or self:GetShowAllButtons()
 local changed=self.shown~=show; self.shown=show
 if changed and show and self.scripts.OnShow then self.scripts.OnShow(self) end
end
for i=1,4 do
 local container=frame('native-container'..i,main)
 function container:SetShown(show) self.shown=show end
 local b=frame('native-button'..i,container); b.container=container; b.index=i; b.actionButton=true
 b.scripts.OnClick='native-click'; b.scripts.OnDragStart='native-pickup'; b.scripts.OnReceiveDrag='native-place'
 b.hasAction=i~=3; b.grid=false; b.statehidden=i==2
 function b:GetAttribute(key) if key=='statehidden' then return self.statehidden end; return self.attributes[key] end
 function b:GetShowGrid() return self.grid end
 function b:SetShowGrid(value) self.grid=value end
 function b:HasAction() return self.hasAction end
 function b:SetShown(show) self.shown=show end
 main.actionButtons[i]=b
end
function table.wipe(t) for k in pairs(t) do t[k]=nil end end
function KeybindFrames_InQuickKeybindMode() return false end
InputUtil.IsGamepadUIEnabled=function() return false end
ACTION_BUTTON_SHOW_GRID_REASON_EVENT=1; ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION=2
bit={bor=function(a,b) return a+b end,band=function(a,b) return b==-2 and 0 or a end,bnot=function() return -2 end}
AnchorUtil={CreateAnchor=function(...) return {...} end}
GridLayoutUtil={CreateStandardGridLayout=function(...) return {...} end}
function GridLayoutUtil.ApplyGridLayout(containers,anchor,layout)
 for i,container in ipairs(containers) do
  container:ClearAllPoints(); container:SetPoint('BOTTOMLEFT',main,'BOTTOMLEFT',(i-1)*38,0)
  container:SetSize(36,36)
 end
end
profile.bars.MainBar={buttonWidth=30,buttonHeight=24,buttonPadding=3,numIcons=4,numRows=2}
_EAB_Apply(); flush()
local first=main.actionButtons[1]; local fourth=main.actionButtons[4]
local function desiredGrid()
 assert(main.w==63 and main.h==51)
 assert(first.container.points[1][1]=='TOPLEFT' and first.container.points[1][4]==0)
 assert(fourth.container.points[1][4]==33 and fourth.container.points[1][5]==-27)
 assert(first.container.w==30 and first.container.h==24)
end
desiredGrid()
-- The actual native grid writes default geometry; posthook must repair it
-- before any queued work runs, including action assignment/removal storms.
main:UpdateShownButtons(); main.oldGridSettings=nil; main:UpdateGridLayout(); desiredGrid()
assert(not main.actionButtons[2].shown and not main.actionButtons[3].shown,'native hidden/empty buttons forced shown')
for i=1,5 do
 first.hasAction=not first.hasAction
 main:UpdateShownButtons(); main.oldGridSettings=nil; main:UpdateGridLayout(); desiredGrid()
end
flush(); desiredGrid()
assert(first.scripts.OnDragStart=='native-pickup' and first.scripts.OnReceiveDrag=='native-place')
assert(first.attributes.action==7 and first.attributes.type=='action')
-- Protected/throwing geometry reads are skipped rather than compared, restored,
-- or reported as addon errors. Other native state updates still complete.
local getWidth,getPoint,getButtonPoint=main.GetWidth,first.container.GetPoint,first.GetPoint
main.GetWidth=function() return SECRET end
first.container.GetPoint=function() return SECRET,SECRET,SECRET,SECRET,SECRET end
first.GetPoint=function() error('geometry temporarily unavailable') end
local beforeProtected=mutations; main:UpdateShownButtons(); assert(mutations==beforeProtected)
main.GetWidth=getWidth; first.container.GetPoint=getPoint; first.GetPoint=getButtonPoint
flush(); desiredGrid()
-- Disabled EUI bars remain disabled when native drag/spell collection grids open.
profile.bars.MainBar.enabled=false; main.nativeEnabled=false; _EAB_Apply(); flush(); assert(not main.shown)
main:SetShowGrid(true,ACTION_BUTTON_SHOW_GRID_REASON_EVENT)
assert(not main.shown and main.actionButtons[3].shown and not main.actionButtons[2].shown)
flush(); assert(not main.shown,'drag enabled a disabled bar'); desiredGrid()
main:SetShowGrid(false,ACTION_BUTTON_SHOW_GRID_REASON_EVENT); flush(); assert(not main.shown)
assert(not main.actionButtons[3].shown and not main.actionButtons[2].shown)
-- The Talent window uses SPELLCOLLECTION, not the drag reason. Repeated open/
-- close edges must settle synchronously, with no full cosmetic/HUD repaint.
for _,setting in ipairs({'enabled','alwaysHidden','barVisibility'}) do
 profile.bars.MainBar.enabled=true; profile.bars.MainBar.alwaysHidden=nil; profile.bars.MainBar.barVisibility=nil
 if setting=='enabled' then profile.bars.MainBar.enabled=false
 elseif setting=='alwaysHidden' then profile.bars.MainBar.alwaysHidden=true
 else profile.bars.MainBar.barVisibility='never' end
 _EAB_Apply(); flush()
 local beforeHUD=hudCalls
 for i=1,3 do
  main:SetShowGrid(true,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION)
  assert(not main.shown,'Talent open revealed disabled bar before timer flush')
  main:SetShowGrid(false,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION)
  assert(not main.shown,'Talent close revealed disabled bar')
 end
 assert(#timers==0 and hudCalls==beforeHUD,'grid edge queued full HUD repaint')
end
profile.bars.MainBar.enabled=true; profile.bars.MainBar.alwaysHidden=nil; profile.bars.MainBar.barVisibility=nil
profile.bars.MainBar.numIcons=3; _EAB_Apply(); flush()
local beforeHUD=hudCalls
for i=1,3 do
 main:SetShowGrid(true,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION)
 assert(main.shown and not fourth.container.shown,'Talent open exposed excess slot')
 main:SetShowGrid(false,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION)
 assert(main.shown and not fourth.container.shown,'Talent close hid enabled bar or exposed excess slot')
end
assert(#timers==0 and hudCalls==beforeHUD,'enabled grid edge queued full repaint')
profile.bars.MainBar.numIcons=4; _EAB_Apply(); flush()
-- No synchronous geometry restoration inside combat or native Edit Mode.
combat=true; local before=mutations; main:UpdateShownButtons(); flush(); assert(mutations==before)
combat=false; nativeEditing=true; before=mutations; main:UpdateShownButtons(); flush(); assert(mutations==before)
nativeEditing=false; profile.bars.MainBar.enabled=true; _EAB_Apply(); flush()
desiredGrid()
''')
print('PASS action edits: actual native grids restored before timers, drag-grid availability/statehidden preserved, action/drag handlers untouched, native countdown migration once, 60/120-second/secret cooldown data preserved, lazy font styling and combat/Edit Mode gates.')
