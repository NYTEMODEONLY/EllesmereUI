"""Targeted Forever HUD regression checks with Lua 5.1 and native XP methods.

Requires lupa and the downloaded Forever UI source in the research temp folder.
This checks data/geometry and callback behavior, not actual client rendering.
"""
import os
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_StatusTrackingBar'
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute((SOURCE / 'Shared/ExpBar.lua').read_text())
lua.execute((SOURCE / 'Mainline/ExpBarOverrides.lua').read_text())
lua.execute(r'''
EUI_FOREVER_NATIVE_ACTIONS=true
geometryWrites=0; nativeEditing=false; callbacks={}
EventRegistry={RegisterCallback=function(_,event,fn) callbacks[event]=fn end}
EditModeManagerFrame={IsEditModeActive=function() return nativeEditing end}
local methods={}
function NewFrame()
 return setmetatable({width=1192,height=17,alpha=1}, {__index=methods})
end
function methods:ClearAllPoints() geometryWrites=geometryWrites+1; self.anchor=nil end
function methods:SetPoint(point, relative, relPoint, x, y) geometryWrites=geometryWrites+1; self.anchor={point,relative,relPoint,x,y} end
function methods:SetAllPoints(parent) geometryWrites=geometryWrites+1; self.allPoints=parent end
function methods:SetSize(w,h) geometryWrites=geometryWrites+1; self.width=w; self.height=h end
function methods:GetWidth() return self.width end
function methods:SetHeight(h) self.height=h end
function methods:SetWidth(w) self.width=w end
function methods:SetScale(s) self.scale=s end
function methods:SetAlpha(a) self.alpha=a end
function methods:SetShown(v) self.shown=v end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:GetParent() return self.parent end
function methods:SetColorTexture(...) self.color={...} end
function methods:SetTextColor(...) self.textColor={...} end
function methods:SetTexCoord(...) self.uv={...} end
function methods:SetFont(...) self.font={...} end
function methods:SetText(value) self.text=value end
function methods:SetStatusBarColor(...) self.barColor={...} end
function methods:SetStatusBarTexture(path) self.texture=path; self.textureWrites=(self.textureWrites or 0)+1 end
function methods:SetBarTexture(path) self:SetStatusBarTexture(path) end
function methods:SetAnimationTextures(gain, level) self.gainAtlas=gain; self.levelAtlas=level end
function methods:SetValue(v) self.value=v end
function methods:GetShownBar() return self.bars[self.shownBarIndex] end
function methods:ApplyPendingBarToShow() self.shownBarIndex=self.pendingBarToShowIndex end
function methods:ResizeContainerBars() end
function methods:UpdateDividers() end
function methods:Update() self.updates=(self.updates or 0)+1 end
function hooksecurefunc(object, method, hook)
 local original=object[method]
 object[method]=function(...) local result=original(...); hook(...); return result end
end
UIParent=NewFrame()
StatusTrackingBarInfo={BarsEnum={Experience=4, Reputation=1, Honor=2, HouseFavor=6}}
EllesmereUI={ELLESMERE_GREEN={r=.2,g=.8,b=.4}}
function EllesmereUI.MakeBorder() return true end
function EllesmereUI.GetFontPath() return 'font.ttf' end
function EllesmereUI.BuildBarTextureTables() return {smooth='smooth.tga'} end
function EllesmereUI.ResolveTexturePath(lookup,key,fallback) return lookup[key] or fallback end
function EllesmereUI.L(value) return value end
LEVEL='Level'
function AbbreviateLargeNumbers(value) return tostring(value) end
NUM_BAG_SLOTS=0
max=math.max; min=math.min
function Clamp(v,lo,hi) return math.max(lo,math.min(v,hi)) end
combat=false
function InCombatLockdown() return combat end
function UnitXP() return 25 end
function UnitXPMax() return 100 end
restedXP=50
function GetXPExhaustion() return restedXP end
function GetRestState() return 1 end
function IsXPUserDisabled() return false end
function ShouldRestedXpBarDisplayWhenOverflowing() return true end
GameRulesUtil={IsPlayerAtEffectiveMaxLevel=function() return false end}
local function Bar(id, xp)
 local bar=NewFrame(); bar.barIndex=id; bar.isExpBar=xp
 bar.StatusBar=NewFrame(); bar.StatusBar.value=25; bar.StatusBar.pendingValue=50
 bar.StatusBar.texture='native-'..id
 bar.StatusBar.Background=NewFrame()
 bar.OverlayFrame={Text=NewFrame()}
 if xp then
  bar.ExhaustionLevelFillBar=NewFrame()
  bar.ExhaustionTick=NewFrame(); bar.ExhaustionTick.parent=bar
  bar.ExhaustionTick.UpdateTickPosition=ExhaustionTickMixin.UpdateTickPosition
  bar.ExhaustionTick.UpdateExhaustionColor=ExhaustionTickMixin.UpdateExhaustionColor
  bar.UpdateTick=ExpBarMixin.UpdateTick
  bar.UpdateStatusBarTextures=ExpBarMixin.UpdateStatusBarTextures
  bar.Update=ExpBarMixin.Update
  bar.OnEvent=ExpBarMixin.OnEvent
  function bar:SetBarValues(...) self.nativeValues={...} end
  function bar:GetMaxLevel() return 100 end
  function bar:GetLevelData() return 25,100,14 end
  function bar:IsCapped() return self.capped end
  function bar:UpdateCurrentText() self.OverlayFrame.Text:SetText(self.capped and 'Banked XP: 700' or '25 / 100') end
  function bar:UpdateTextVisibility() self.OverlayFrame.Text:Hide() end
 end
 return bar
end
function Container(id, xp)
 local container=NewFrame(); container.shownBarIndex=id
 container.bars={[id]=Bar(id,xp)}
 return container
end
xpContainer=Container(4,true); repContainer=Container(1); honorContainer=Container(2)
unknownContainer=Container(77); petContainer=Container(88)
StatusTrackingBarManager={barContainers={xpContainer,repContainer,honorContainer,unknownContainer,petContainer}}
profile={bars={XPBar={width=400,height=20,barTexture='smooth'},RepBar={width=300,height=16}},
 barPositions={XPBar={x=-760,y=-249},RepBar={x=-760,y=-220}}}
applying=false; pending=false; queueCount=0; applyCount=0
function Queue()
 if applying or pending then return end
 pending=true; queueCount=queueCount+1
end
function Apply()
 if combat then return end
 applying=true; applyCount=applyCount+1
 EUI_FOREVER_StyleHUD(profile,Queue)
 applying=false
end
function Flush()
 if pending then pending=false; if not combat then Apply() end end
end
''')
lua.execute((ROOT.parent / 'EllesmereUIActionBars/EllesmereUIActionBars_ForeverHUD.lua').read_text())
lua.execute(r'''
Apply()
local bar=xpContainer:GetShownBar()
assert(bar.StatusBar.texture=='smooth.tga','native UpdateTick overwrote imported texture')
assert(bar.StatusBar.gainAtlas=='UI-HUD-ExperienceBar-Flare-Rested-2x-Flipbook','native gain animation altered')
assert(bar.StatusBar.value==25 and bar.StatusBar.pendingValue==50,'native progression/animation values altered')
assert(bar.OverlayFrame.Text.text=='25.0% (Rested: 50.0%)' and bar.OverlayFrame.Text.shown,'default EUI XP label missing')
assert(bar.ExhaustionLevelFillBar.width==398*.75,'rested endpoint did not follow resized native width')
assert(bar.ExhaustionLevelFillBar.height==18,'rested height did not follow imported height')
assert(xpContainer.anchor[4]==-760 and xpContainer.anchor[5]==-249,'XP imported anchor changed')
assert(repContainer.anchor[5]==-220,'reputation imported anchor changed')
assert(repContainer:GetShownBar().StatusBar.texture=='native-1','reputation semantic atlas lost')
assert(honorContainer:GetShownBar().StatusBar.texture=='native-2','honor semantic atlas lost')
assert(unknownContainer:GetShownBar().StatusBar.texture=='native-77','unknown semantic atlas lost')
local containers=StatusTrackingBarManager.barContainers
for i=1,#containers do
 for j=i+1,#containers do
  assert(math.abs(containers[i].anchor[5]-containers[j].anchor[5]) >= (containers[i].height+containers[j].height)/2,
   'visible progression bars overlap')
 end
end
assert(not pending,'layout recursively queued itself')
-- Native XP/text changes must be restored before the current event returns:
-- a timer that converges next frame still allows a visible native-skin flash.
local paints,queues=applyCount,queueCount
bar:UpdateStatusBarTextures(true)
assert(bar.StatusBar.texture=='smooth.tga','XP native texture leaked until next frame')
bar:UpdateCurrentText(); bar:UpdateTextVisibility()
assert(bar.OverlayFrame.Text.text=='25.0% (Rested: 50.0%)' and bar.OverlayFrame.Text.shown,
 'XP native text/visibility leaked until next frame')
assert(not pending and applyCount==paints and queueCount==queues,'XP data event repainted the entire HUD')
local geometry,textures=geometryWrites,bar.StatusBar.textureWrites
for i=1,20 do
 bar:OnEvent('PLAYER_XP_UPDATE')
 bar:UpdateCurrentText(); bar:UpdateTextVisibility()
end
assert(geometryWrites==geometry and bar.StatusBar.textureWrites==textures,
 'XP value/text updates unnecessarily rebuilt geometry or reset the fill texture')
assert(applyCount==paints and queueCount==queues and not pending)
assert(bar.nativeValues[1]==25 and bar.nativeValues[3]==100 and bar.nativeValues[4]==14,
 'native XP event no longer updates native progression values')
assert(bar.StatusBar.value==25 and bar.StatusBar.pendingValue==50,'cosmetics changed gain animation state')
nativeEditing=true; callbacks['EditMode.Enter']()
bar:UpdateStatusBarTextures(true); bar:UpdateCurrentText()
assert(bar.StatusBar.texture=='UI-HUD-ExperienceBar-Fill-Rested' and bar.OverlayFrame.Text.text=='25 / 100')
nativeEditing=false; bar:UpdateStatusBarTextures(true)
assert(bar.StatusBar.texture=='UI-HUD-ExperienceBar-Fill-Rested','cosmetics resumed before Edit Mode exit reset')
callbacks['EditMode.Exit'](); Apply()
assert(bar.StatusBar.texture=='smooth.tga' and not pending)
bar:UpdateCurrentText(); bar:UpdateTextVisibility()
Flush()
assert(bar.OverlayFrame.Text.text=='25.0% (Rested: 50.0%)' and bar.OverlayFrame.Text.shown,'native hover/text visibility overwrote EUI label')
profile.bars.XPBar.showLevel=true; profile.bars.XPBar.showRawValues=true
Apply()
assert(bar.OverlayFrame.Text.text=='Level 14 - 25 / 100 (Rested: 50)','imported raw/level label options ignored')
profile.bars.XPBar.showLevel=nil; profile.bars.XPBar.showRawValues=nil
restedXP=0; Apply()
assert(bar.OverlayFrame.Text.text=='25.0%','unrested XP should omit rested suffix')
restedXP=50
bar.capped=true; bar:UpdateCurrentText(); bar:UpdateTextVisibility(); Flush()
assert(bar.OverlayFrame.Text.text=='Banked XP: 700' and not bar.OverlayFrame.Text.shown,'capped/banked native text policy changed')
bar.capped=false; Apply()
bar:UpdateStatusBarTextures(true)
assert(not pending and bar.StatusBar.texture=='smooth.tga','native repaint did not restore synchronously')
Flush()
assert(bar.StatusBar.texture=='smooth.tga' and not pending,'native repaint failed to settle')
local count=applyCount
combat=true
bar:UpdateStatusBarTextures(true)
Flush()
assert(applyCount==count and bar.StatusBar.texture=='UI-HUD-ExperienceBar-Fill-Rested','combat updates touched layout')
combat=false
-- Parent adapter queues this on PLAYER_REGEN_ENABLED.
Queue(); Flush()
assert(applyCount==count+1 and bar.StatusBar.texture=='smooth.tga','combat deferral did not recover')
profile.bars.XPBar.barTexture='missing'
Apply()
assert(bar.StatusBar.texture=='Interface\\Buttons\\WHITE8X8','missing texture fallback failed')
assert(profile.barPositions.RepBar.y==-220,'fallback stacking mutated saved position')
-- Deferred native swaps must request layout after the container selects its bar.
honorContainer.bars[6]=honorContainer.bars[2]
honorContainer.pendingBarToShowIndex=6
honorContainer:ApplyPendingBarToShow()
assert(pending,'animation-delayed visible-bar swap was not hooked')
''')
print('PASS: immediate XP texture/text restoration before timer flush; 20 native XP events without geometry/full-HUD repaint or redundant texture reset; native values/animations, Edit Mode latch, combat deferral, capped text and delayed swaps preserved')

# Use Camelot's real atlas-update methods to exercise bag events after styling.
lua.execute('BaseBagSlotButtonMixin={}; CharacterReagentBagMixin={}')
lua.execute((SOURCE.parent / 'Blizzard_MainMenuBarBagButtons/Camelot/MainMenuBarBagButtons.lua').read_text())
lua.execute((SOURCE.parent / 'Blizzard_MainMenuBarBagButtons/Shared/BagsBar.lua').read_text())
lua.execute(r'''
local methods=getmetatable(NewFrame()).__index
function methods:GetFont() return 'native.ttf',12,'OUTLINE' end
function methods:SetVertexColor(...) self.vertexColor={...} end
function methods:SetBlendMode(value) self.blend=value end
function methods:SetRotation(value) self.rotation=value end
function methods:IsShown() return self.shown~=false end
function methods:GetHeight() return self.height end
function methods:CreateMaskTexture() self.masksCreated=(self.masksCreated or 0)+1; return NewFrame() end
function methods:AddMaskTexture(mask) self.addedMask=mask end
function methods:SetAtlas(value) self.atlas=value; self.color=nil; self.uv={'native-atlas'} end
function methods:SetTexture(value) self.texture=value end
function methods:RemoveMaskTexture(mask) self.removedMask=mask end
function methods:GetNormalTexture() return self.normal end
function methods:GetPushedTexture() return self.pushed end
function methods:GetHighlightTexture() return self.highlight end
function methods:GetBagID() return self.bagID end
function ContainerFrame_GetContainerNumSlots(id) return id==3 and 0 or 16 end
missingAtlas=nil
C_Texture={GetAtlasInfo=function(atlas) if atlas~=missingAtlas then return {width=32,height=32} end end}
function Bag(id)
 local bag=NewFrame(); bag.width=45; bag.height=45; bag.bagID=id
 bag.icon=NewFrame(); bag.icon.texture='item-'..id
 bag.normal=NewFrame(); bag.pushed=NewFrame(); bag.highlight=NewFrame()
 bag.pushed.shown=false; bag.highlight.shown=false
 bag.SquareMask=NewFrame(); bag.SlotHighlightTexture=NewFrame(); bag.SlotHighlightTexture.shown=false
 bag.Count=NewFrame(); bag.Count.text='7'; bag.Count.textColor={1,0,0}; bag.Count.shown=false
 bag.ItemContextOverlay=NewFrame(); bag.ItemContextOverlay.shown=true
 bag.searchOverlay=NewFrame(); bag.searchOverlay.shown=false
 bag.AnimIcon=NewFrame(); bag.AnimIcon.texture='new-item'; bag.AnimIcon.shown=true
 bag.FlyIn={playing=true}; bag.locked=true; bag.enabled=false
 bag.GetSlotAtlases=BaseBagSlotButtonMixin.GetSlotAtlases
 bag.UpdateTextures=BaseBagSlotButtonMixin.UpdateTextures
 return bag
end
local ordinary=Bag(1)
KeyRingButton=Bag(2); KeyRingButton.width=33; KeyRingButton.bagAtlas='UI-HUD-ActionBar-Keyring-Small'
KeyRingButton.GetSlotAtlases=KeyRingMixin.GetSlotAtlases
KeyRingButton.initialWidth=33; KeyRingButton.initialHeight=45; KeyRingButton.UpdateOrientation=KeyRingMixin.UpdateOrientation
local unfamiliar=Bag(3)
MainMenuBarBackpackButton=Bag(0); MainMenuBarBackpackButton.bagIcon='native-backpack'
CharacterReagentBag0Slot=Bag(4)
local hidden=Bag(5); hidden.shown=false
MainMenuBarBagManager={allBagButtons={MainMenuBarBackpackButton,ordinary,CharacterReagentBag0Slot,KeyRingButton,unfamiliar,hidden}}
function MainMenuBarBagManager:EnumerateBagButtons() return ipairs(self.allBagButtons) end
function MainMenuBarBagManager:RegisterBagButton(button) table.insert(self.allBagButtons,button) end
local horizontal,vertical=NewFrame(),NewFrame()
horizontal.shown=true; vertical.shown=false
local function Pool(divider)
 return {EnumerateActive=function() local done=false; return function() if not done then done=true; return divider end end end}
end
BagsBar=NewFrame(); BagsBar.width=325; BagsBar.height=45
BagsBar.BorderArt=NewFrame(); BagsBar.HorizontalDividersPool=Pool(horizontal); BagsBar.VerticalDividersPool=Pool(vertical)
BagsBar.useDividers=true; BagsBar.initialHeight=45; BagsBar.bagPadding=2; BagsBar.hideExpandToggle=true
Enum={BagsDirection={Left=1,Up=2}}
BagsBar.isHorizontal=true; BagsBar.direction=Enum.BagsDirection.Left
for _,key in ipairs({'Layout','IsHorizontal','IsDirectionLeft','IsDirectionUp','GetBagBarLength','GetBagButtonAnchorPoints','ShouldShowExpandToggle'}) do BagsBar[key]=BagsBarMixin[key] end
function BagsBar:UpdateDividers() horizontal.alpha=1; vertical.alpha=1 end
ordinary:UpdateTextures(); KeyRingButton:UpdateTextures(); unfamiliar:UpdateTextures()
Apply()
for _,bag in MainMenuBarBagManager:EnumerateBagButtons() do
 assert(bag.normal.alpha==1 and bag.pushed.atlas and bag.highlight.atlas,'Retail bag states missing')
 assert(bag.highlight.alpha==.4 and bag.SlotHighlightTexture.atlas,'native hover/open-bag state artwork missing')
 assert(not bag.pushed.shown and not bag.highlight.shown and not bag.SlotHighlightTexture.shown,'native bag visibility changed')
 assert(not bag.Count.font and bag.Count.text=='7' and not bag.Count.shown and bag.Count.textColor[2]==0,'native count typography/semantics changed')
 assert(bag.ItemContextOverlay.shown and bag.AnimIcon.shown and bag.FlyIn.playing and bag.locked and not bag.enabled,'bag state/animation changed')
 assert(bag.icon.addedMask==bag.ItemContextOverlay.addedMask and bag.icon.addedMask==bag.searchOverlay.addedMask,'circular search/context masks missing')
 assert(bag.masksCreated==1 and not bag.searchOverlay.shown,'mask duplicated or search visibility changed')
end
assert(ordinary.normal.atlas=='bag-border' and unfamiliar.normal.atlas=='bag-border-empty','equipped/empty Retail atlases incorrect')
assert(CharacterReagentBag0Slot.normal.atlas=='bag-reagent-border','reagent-specific Retail border missing')
assert(MainMenuBarBackpackButton.normal.atlas=='bag-main' and MainMenuBarBackpackButton.highlight.atlas=='bag-main-highlight' and MainMenuBarBackpackButton.icon.alpha==0,'large Retail backpack art incorrect')
assert(KeyRingButton.icon.atlas=='UI-HUD-ActionBar-Keyring-Small' and KeyRingButton.icon.uv[1]=='native-atlas','keyring atlas/crop changed')
assert(ordinary.icon.texture=='item-1' and ordinary.icon.removedMask==ordinary.SquareMask,'item art/mask incorrect')
assert(KeyRingButton.width==30 and KeyRingButton.height==30 and MainMenuBarBackpackButton.width==48 and MainMenuBarBackpackButton.height==48,'Retail small/backpack dimensions wrong')
assert(BagsBar.width==168 and BagsBar.height==48 and MainMenuBarBackpackButton.anchor[4]==0 and ordinary.anchor[4]==-48 and unfamiliar.anchor[4]==-138,'Retail right-aligned row geometry wrong')
assert(not hidden.shown and not hidden.anchor,'hidden native bag slot exposed or positioned')
assert(BagsBar.useDividers and BagsBar.initialHeight==45 and BagsBar.bagPadding==2 and BagsBar.hideExpandToggle,'native layout policy changed')
assert(horizontal.alpha==0 and vertical.alpha==0 and horizontal.shown and not vertical.shown,'decorative dividers not flattened safely')
assert(#MainMenuBarBagManager.allBagButtons==6 and MainMenuBarBagManager.allBagButtons[5]==unfamiliar,'native registration list changed')
pending=false
ordinary.SlotHighlightTexture:Show(); ordinary:UpdateTextures()
assert(pending and ordinary.pushed.atlas=='ui-hud-actionbar-iconframe-bags','native texture event not hooked')
Flush()
assert(ordinary.pushed.atlas=='bag-border' and ordinary.SlotHighlightTexture.shown and not pending,'bag re-skin lost open state or recursed')
BagsBar:UpdateDividers(); Flush()
assert(horizontal.alpha==0 and vertical.alpha==0,'native divider recycling lost flat skin')
local added=Bag(4)
MainMenuBarBagManager:RegisterBagButton(added); Flush()
assert(added.pushed.atlas=='bag-border' and added.width==30 and BagsBar.width==198,'new registered bag was omitted')
BagsBar:Layout()
assert(pending and KeyRingButton.width==33 and KeyRingButton.height==45 and BagsBar.height==45,'actual native layout/orientation fixture did not run')
Flush()
assert(KeyRingButton.width==30 and KeyRingButton.height==30 and BagsBar.width==198 and BagsBar.height==48 and not pending,'native bag layout overwrote Retail sizing permanently')
-- Art lookup failures keep native controls and a visible item/backpack fallback.
missingAtlas='bag-main'; MainMenuBarBackpackButton:UpdateTextures(); Flush()
assert(MainMenuBarBackpackButton.icon.alpha==1 and MainMenuBarBackpackButton.icon.texture=='native-backpack' and MainMenuBarBackpackButton.width==48,'missing backpack atlas lost reachable visible fallback')
missingAtlas=nil; Queue(); Flush()
assert(MainMenuBarBackpackButton.icon.alpha==0 and ordinary.masksCreated==1,'atlas recovery failed or duplicated masks')
combat=true; ordinary:UpdateTextures(); Flush()
assert(ordinary.pushed.atlas=='ui-hud-actionbar-iconframe-bags','bag artwork changed during combat')
combat=false; Queue(); Flush()
assert(ordinary.pushed.atlas=='bag-border' and not pending,'bag combat repaint did not recover')
''')
print('PASS: Retail circular bag/backpack geometry and atlases, native Camelot updates, keyring/new/hidden slots, search/context masks, missing-atlas fallback, count/animation/disabled preservation, unchanged native policy, divider recycling and combat deferral')
