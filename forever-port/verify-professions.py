"""Test the Forever profession skin against native Camelot card formatting.

Requires lupa and the downloaded Forever UI source. Does not emulate rendering,
secure spell casts or actual crafting/unlearning; those remain native.
"""
import os
import re
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns'))
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
EUI_FOREVER=true; EUI_FOREVER_STATUS={}; disabled=false
NORMAL_FONT_COLOR={r=1,g=.82,b=0}
local methods={}
function New()
 return setmetatable({shown=true,alpha=1,color={1,.82,0},scripts={},regions={}}, {__index=methods})
end
function methods:SetAlpha(a) self.alpha=a end
function methods:SetColorTexture(...) self.fillColor={...}; self.atlas=nil end
function methods:SetVertexColor(...) self.vertex={...} end
function methods:SetDesaturated(value) self.desaturated=value end
function methods:SetTextColor(...) self.color={...} end
function methods:GetTextColor() return unpack(self.color) end
function methods:SetText(t) self.text=t end
function methods:SetTexture(t) self.texture=t end
function methods:SetAtlas(t) self.atlas=t end
function methods:GetAtlas() return self.atlas end
function methods:CreateTexture() local t=New(); self.regions[#self.regions+1]=t; return t end
function methods:SetAllPoints() end
function methods:SetPoint(...) self.anchor={...} end
function methods:SetID(id) self.id=id end
function methods:SetShown(v) self.shown=v end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:IsShown() return self.shown end
function methods:HookScript(key,fn) self.scripts[key]=fn end
function methods:SetScript(key,fn) self.scripts[key]=fn end
function methods:GetRegions() return unpack(self.regions) end
function methods:GetNormalTexture() return self.normal end
function methods:GetHighlightTexture() return self.highlight end
function methods:GetFontString() return self.Text end
function methods:IsEnabled() return self.enabled~=false end
function hooksecurefunc(f,key,hook)
 local old=f[key]
 f[key]=function(...) local r=old(...); hook(...); return r end
end
local W={Theme={insetR=.05,insetG=.05,insetB=.05,accR=.2,accG=.8,accB=.5}}
function W.AddBorder(f) f.bordered=true end
function W.Font(f,r,g,b) if not f then return end; f.themedFont=true; if r then f:SetTextColor(r,g,b) end end
function W.Button(f) f.themedButton=true end
function W.Checkbox(f,opt) assert(opt and opt.stockCheck and opt.boxInset==true,'profession checkbox must draw one inset box'); f.themedCheckbox=true end
-- The shared professions pack marks checkboxes it has already replaced.
local ffd={}
function W.GetFFD(f) ffd[f]=ffd[f] or {}; return ffd[f] end
function W.WindowCallback(_,fn) return function(...) if not disabled then return fn(...) end end end
local pending
function W.Debounce(fn) return function() pending=fn end end
function Drain() local count=0; while pending do local fn=pending; pending=nil; fn(); count=count+1; assert(count<10,'skin refresh did not settle') end end
function W.RegisterWindow(entry) W.entry=entry end
function W.OnLooksChanged(fn) W.looks=fn end
ns={WSkin=W}
ProfessionsBookFrameMixin={}; ProfessionSpellButtonMixin={}; ButtonStateBehaviorMixin={}
function CreateFromMixins(...) local result={}; for i=1,select('#',...) do for k,v in pairs(select(i,...)) do result[k]=v end end; return result end
function UIFrameFlashStop(f) f.flashing=false end
function UIFrameFlash(f) f.flashing=true end
function GetProfessions() return 1,nil,3,4,5 end
function GetProfessionInfo(index) return 'First Aid','icon-'..index,25,75,4,10,129,0 end
C_TradeSkillUI={GetProfessionInfoBySkillLineID=function() return {skillLevel=25,maxSkillLevel=75,skillModifier=0} end}
C_ProfSpecs={ShouldShowPointsReminderForSkillLine=function() return true end}
InputUtil={IsGamepadUIEnabled=function() return false end}
function StaticPopup_Show() error('skin must not unlearn or open confirmation') end
function Caster() error('skin must not cast profession spells') end
''')
lua.execute((SOURCE / 'Blizzard_ProfessionsBook/Camelot/Blizzard_ProfessionsBook.lua').read_text())
side_tab_source = (SOURCE / 'Blizzard_SharedXML/Mainline/SharedUIPanelTemplates.lua').read_text()
lua.execute('SidePanelTabButtonMixin={}; TextureKitConstants={UseAtlasSize=true}')
for method in ('SetChecked', 'UpdateIconInterior'):
    match = re.search(r'function SidePanelTabButtonMixin:' + method + r'\([^\n]*\).*?\nend\n', side_tab_source, re.S)
    assert match, method
    lua.execute(match.group())
lua.execute(r'''
local function Button()
 local b=New(); b.IconTexture=New(); b.OutlineMask=New(); b.Flash=New(); b.cooldown=New(); b.Arrow=New()
 b.spellString=New(); b.subSpellString=New(); b.IconTextureOverlay=New(); b.IconTextureOverlay.atlas='Profession-square-frame'
 b.spellString:SetTextColor(.6,.7,.8)
 function b:UpdateOverlay() self.IconTextureOverlay:SetAtlas('Profession-square-frame'); self.IconTextureOverlay:Show() end
 function b:UpdateButton() self.IconTexture:SetTexture('native-spell'); self:UpdateOverlay() end
 b.scripts.OnClick=Caster
 return b
end
local function Card()
 local c=New(); c.Background=New(); c.ProfessionName=New(); c.specialization=New(); c.missingHeader=New(); c.missingText=New()
 c.UnlearnButton=New(); c.UnlearnButton.Icon=New(); c.UnlearnButton.Overlay=New(); c.GamepadUnlearnButton=New()
 c.StatusBar=New(); local bar=c.StatusBar; bar.Border=New(); bar.Background=New(); bar.Fill=New(); bar.Mask=New(); bar.Flare=New()
 bar.Fill.atlas='animated-native-fill'; bar.Mask.width=87; bar.ratio=.333; bar.interpolator={native=true}
 bar.Rank={Text=New()}; bar.Rank.Text:SetTextColor(1,0,0); bar.ExpansionDropdownButton=New(); bar.ExpansionDropdownButton.Texture=New()
 function bar:Update(info) self.value=info.skillLevel; self.Rank.Text:SetText('25/75'); self.Mask.width=87 end
 c.spellButtons={Button(),Button(),Button(),Button()}
 for i,b in ipairs(c.spellButtons) do c['SpellButton'..i]=b end
 return c
end
local content={}
for _,key in ipairs({'PrimaryProfession1','PrimaryProfession2','SecondaryProfession1','SecondaryProfession2','SecondaryProfession3'}) do content[key]=Card() end
content.PrimaryProfession1.isPrimary=true; content.PrimaryProfession2.isPrimary=true
local function Tab()
 local t=New(); t.Background=New(); t.SelectedTexture=New(); t.Icon=New(); t.TabGlow=New(); t.HighlightTexture=New()
 t.Mask=New(); t.Mask.atlas='common-sidetab-mask'; t.Icon.mask=t.Mask; t.TabGlow.alpha=.35
 t.fillToInterior=true; t.interiorExtent=50; t.activeAtlas='selected-icon'; t.inactiveAtlas='normal-icon'
 function t.Icon:SetTexCoord(...) self.uv={...} end
 function t.Icon:SetSize(w,h) self.width=w; self.height=h end
 function t.Icon:RemoveMaskTexture() error('native side-tab mask removed') end
 t.SetChecked=SidePanelTabButtonMixin.SetChecked; t.UpdateIconInterior=SidePanelTabButtonMixin.UpdateIconInterior
 t:UpdateIconInterior()
 t.disabled=true; t.customMouseUpHandler=Caster
 return t
end
ProfessionsFrame=New(); ProfessionsFrame.BookPage=New(); local book=ProfessionsFrame.BookPage
book.ProfessionsContentFrame=content; book.showProfessionSpellHighlights=true
book.FormatProfession=ProfessionsBookFrameMixin.FormatProfession
book.UpdateRankBar=ProfessionsBookFrameMixin.UpdateRankBar
book.Update=ProfessionsBookFrameMixin.Update
ProfessionsFrame.ProfessionsOverviewTab=Tab(); ProfessionsFrame.rightProfessionTabs={}
for i=1,7 do ProfessionsFrame.rightProfessionTabs[i]=Tab() end
function ProfessionsFrame:RightTabSelected(selected)
 self.ProfessionsOverviewTab:SetChecked(selected==self.ProfessionsOverviewTab)
 for _,tab in ipairs(self.rightProfessionTabs) do tab:SetChecked(selected==tab) end
end
ProfessionsFrame.CraftingPage=New(); decoration=New(); decoration.atlas='Profession-Background-Template2'
reagent=New(); reagent.atlas='meaningful-reagent-icon'; ProfessionsFrame.CraftingPage.regions={decoration,reagent}
local page=ProfessionsFrame.CraftingPage
local function Action()
 local b=New(); b.Left=New(); b.Center=New(); b.Right=New(); b.Text=New(); b.enabled=false; b.Text:SetTextColor(.4,.4,.4); b.scripts.OnClick=Caster
 function b:UpdateButton() self.Center:SetAlpha(1) end
 return b
end
page.CreateButton=Action(); page.CreateAllButton=Action()
page.CreateMultipleInputBox=New(); local spinner=page.CreateMultipleInputBox
spinner.Left=New(); spinner.Middle=New(); spinner.Right=New(); spinner.value=3; spinner.min=1; spinner.max=15; spinner.enabled=false
spinner.IncrementButton=New(); spinner.DecrementButton=New(); spinner.IncrementButton.normal=New(); spinner.DecrementButton.normal=New()
spinner.scripts.OnMouseWheel=Caster
local header=New(); header.ButtonText=New(); header.CollapseButton=New(); header.normal=New(); header.highlight=New(); header.scripts.OnClick=Caster
local recipe=New(); recipe.Label=New(); recipe.Count=New(); recipe.SkillUps={Text=New(),Icon=New()}; recipe.LockedIcon=New(); recipe.SelectedOverlay=New()
recipe.Label:SetTextColor(1,.7,0); recipe.Count:SetTextColor(.5,.5,.5); recipe.SkillUps.Text:SetTextColor(0,1,0)
page.RecipeList={ScrollBox=New()}; local scroll=page.RecipeList.ScrollBox; scroll.rows={header,recipe}
function scroll:ForEachFrame(fn) for _,row in ipairs(self.rows) do fn(row) end end
ScrollUtil={AddInitializedFrameCallback=function(scroll,fn,owner) scroll.initialized=function(row) fn(owner,row) end end}
local form=New(); page.SchematicForm=form; form.OutputText=New(); form.Description=New(); form.RequiredTools=New(); form.RequiredTools:SetTextColor(1,1,0)
form.Reagents={Label=New()}; form.TrackRecipeCheckbox=New(); form.TrackRecipeCheckbox.Text=New(); form.TrackRecipeCheckbox.checked=true; form.TrackRecipeCheckbox.scripts.OnClick=Caster
form.AllocateBestQualityCheckbox=New(); form.AllocateBestQualityCheckbox.Text=New(); ns.WSkin.GetFFD(form.AllocateBestQualityCheckbox).custom=true
local slot=New(); slot.Name=New(); slot.Button=New(); slot.Button.Count=New(); slot.Button.Icon=New(); slot.Button.QualityOverlay=New()
slot.Name:SetTextColor(1,0,0); slot.Button.Count:SetTextColor(1,0,0); slot.Button.Count.text='0 / 3'; slot.Button.Icon.texture='Linen Cloth'
form.reagentSlotPool={slots={slot},EnumerateActive=function(self) local i=0; return function() i=i+1; return self.slots[i] end end}
function form:Refresh() self.Description.themedFont=nil end
function page:ValidateControls() self.CreateButton.enabled=false end
fixture={content=content,book=book}
fixture.page=page; fixture.header=header; fixture.recipe=recipe; fixture.slot=slot
book:Update()
''')
source = (ROOT.parent / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverProfessions.lua').read_text()
chunk = lua.eval('function(source) return assert(loadstring(source)) end')(source)
chunk('EllesmereUIBlizzardSkin', lua.globals().ns)
lua.execute(r'''
local W=ns.WSkin; local x=fixture
assert(W.entry.key=='professions')
local trained=x.content.SecondaryProfession3
local untrained=x.content.PrimaryProfession2
local unlearnHandler=trained.UnlearnButton.scripts.OnClick
W.entry.apply(); Drain()
assert(trained.Background.alpha==0 and trained.bordered,'overview card not themed')
assert(trained.ProfessionName.themedFont and trained.StatusBar.Rank.Text.themedFont,'overview font missed')
assert(trained.StatusBar.Rank.Text.color[1]==1 and trained.StatusBar.Rank.Text.color[2]==0,'warning color lost')
for _,button in ipairs(trained.spellButtons) do
 assert(button.bordered and button.spellString.themedFont,'secondary profession spell slot missed')
 assert(button.IconTexture.alpha==1 and button.OutlineMask.alpha==1 and button.Arrow.alpha==1,'spell icon/mask/flyout art lost')
 assert(button.cooldown.shown and button.scripts.OnClick==Caster,'native spell behavior changed')
 assert(button.spellString.color[1]==.6,'passive spell color changed')
 assert(button.IconTextureOverlay.alpha==0,'decorative spell border not replaced')
end
assert(trained.SpellButton1.Flash.flashing,'native skill-point reminder lost')
assert(trained.StatusBar.Fill.fillColor[1]==W.Theme.accR and trained.StatusBar.Fill.atlas==nil,'rank fill not flattened')
assert(trained.StatusBar.Mask.width==87,'native rank mask changed')
assert(trained.StatusBar.ratio==.333 and trained.StatusBar.interpolator.native,'native progress state changed')
assert(trained.UnlearnButton.scripts.OnClick==unlearnHandler and trained.UnlearnButton.Icon.alpha==1,'unlearn confirmation/glyph changed')
assert(not untrained.StatusBar.shown and untrained.missingHeader.shown and not untrained.SpellButton1.shown,'untrained visibility changed')
assert(decoration.alpha==0 and reagent.alpha==1,'crafting art filter changed content')
local page=x.page; local form=page.SchematicForm
assert(page.CreateButton.themedButton and page.CreateAllButton.themedButton and page.CreateButton.Center.alpha==0,'Camelot crafting button art missed')
assert(not page.CreateButton.enabled and page.CreateButton.Text.color[1]==.4 and page.CreateButton.scripts.OnClick==Caster,'disabled crafting state/handler changed')
assert(page.CreateButton.Text.themedFont and form.Description.themedFont and form.Reagents.Label.themedFont,'crafting content fonts missed')
assert(form.RequiredTools.color[1]==1 and form.RequiredTools.color[2]==1 and form.RequiredTools.color[3]==0,'required-tool warning color changed')
assert(x.slot.Name.themedFont and x.slot.Name.color[1]==1 and x.slot.Name.color[2]==0,'insufficient reagent color changed')
assert(x.slot.Button.Count.text=='0 / 3' and x.slot.Button.Icon.texture=='Linen Cloth' and x.slot.Button.QualityOverlay.alpha==1,'reagent data or quality art changed')
assert(form.TrackRecipeCheckbox.themedCheckbox and form.TrackRecipeCheckbox.checked and form.TrackRecipeCheckbox.scripts.OnClick==Caster,'tracking state or command changed')
assert(not form.AllocateBestQualityCheckbox.themedCheckbox and form.AllocateBestQualityCheckbox.Text.themedFont,'already replaced checkbox was boxed a second time')
local spinner=page.CreateMultipleInputBox
assert(spinner.themedFont and spinner.value==3 and spinner.min==1 and spinner.max==15 and not spinner.enabled,'quantity or disabled state changed')
assert(spinner.IncrementButton.normal.alpha==1 and spinner.DecrementButton.normal.alpha==1 and spinner.scripts.OnMouseWheel==Caster,'quantity arrows/input lost')
assert(x.header.ButtonText.themedFont and x.header.CollapseButton.shown and x.header.scripts.OnClick==Caster,'category collapse control altered')
assert(x.recipe.Label.themedFont and x.recipe.Label.color[2]==.7 and x.recipe.SkillUps.Text.color[2]==1,'recipe difficulty colors changed')
assert(x.recipe.SelectedOverlay.shown and x.recipe.LockedIcon.shown,'recipe selection or lock state changed')
local pooled=New(); pooled.Label=New(); pooled.Label:SetTextColor(.4,.4,.4)
page.RecipeList.ScrollBox.initialized(pooled)
assert(pooled.Label.themedFont and pooled.Label.color[1]==.4,'new pooled recipe or disabled color missed')
form:Refresh(); page.CreateButton:UpdateButton(); Drain()
assert(form.Description.themedFont and page.CreateButton.Center.alpha==0,'recipe refresh/native button repaint reverted style')
assert(not ProfessionsFrame.ProfessionsOverviewTab.bordered and ProfessionsFrame.ProfessionsOverviewTab.Background.alpha==0)
for _,tab in ipairs(ProfessionsFrame.rightProfessionTabs) do
 assert(not tab.bordered and tab.Background.alpha==0 and tab.disabled and tab.customMouseUpHandler==Caster,'side-tab surround or native state/handler changed')
 assert(tab.Icon.mask==tab.Mask and tab.Mask.atlas=='common-sidetab-mask' and tab.Mask.alpha==1 and tab.TabGlow.alpha==.35,'native clipped mask/glow altered')
 assert(tab.Icon.uv[1]==.03125 and tab.Icon.uv[2]==.96875 and tab.Icon.width==50 and #tab.regions==0,'native tab interior cropped or extra square region added')
end
local selected=ProfessionsFrame.rightProfessionTabs[7]
ProfessionsFrame:RightTabSelected(selected); Drain()
assert(selected.SelectedTexture.shown and selected.Icon.atlas=='selected-icon','side tab selection lost')
assert(selected.Icon.uv[1]==.03125 and selected.Icon.width==50 and not selected.bordered and #selected.regions==0,'native selected tab acquired a surround or changed UVs')
assert(not ProfessionsFrame.ProfessionsOverviewTab.SelectedTexture.shown,'overview selection stale')
selected.TabGlow:SetShown(true); W.entry.apply()
assert(selected.TabGlow.shown,'new-content notification lost')
x.book:Update(); Drain()
assert(trained.Background.alpha==0 and trained.SpellButton4.IconTextureOverlay.alpha==0,'native repaint reverted themed card')
disabled=true; decoration.alpha=1; W.entry.apply(); assert(decoration.alpha==1,'disabled style still applied')
''')
print('PASS: profession overview/tabs; crafting buttons/spinner/tracking; pooled recipe rows/details/reagents; native handlers, difficulty/warning/disabled colors, rank animations, quantities, selection and locks; repaint and style gate')

lua.execute((SOURCE / 'Blizzard_ProfessionsTemplates/Blizzard_ProfessionsRankBar.lua').read_text())
lua.execute(r'''
disabled=false
local methods=getmetatable(New()).__index
function methods:GetWidth() return self.width end
function methods:SetWidth(value) self.width=value end
function methods:SetAtlas(value) self.atlas=value; self.fillColor=nil end
function methods:SetFlipBookRows(value) self.rows=value end
function methods:SetFlipBookFrames(value) self.frames=value end
function methods:GetFlipBookColumns() return 2 end
function methods:Restart() self.restarts=(self.restarts or 0)+1; self.playing=true end
function methods:Stop() self.playing=false end
TRADESKILL_NAME_RANK='%s %d/%d'
TRADESKILL_NAME_RANK_WITH_MODIFIER='%s %d +%d/%d'
RED_FONT_COLOR_CODE='|cffff0000'; CAP_REACHED_TRIAL='Trial cap'
trial=false
function GameLimitedMode_IsActive() return trial end
function GetRestrictedAccountData() return 0,0,75 end
Professions={GetAtlasKitSpecifier=function(info) return info.kit end}
C_Texture={GetAtlasInfo=function(atlas) return {height=1020} end}
TextureKitConstants={IgnoreAtlasSize=false}
InterpolatorUtil={InterpolateEaseOut=function(x) return x end, InterpolateLinear=function(a,b,u) return a+(b-a)*u end}
function CreateInterpolator()
 local obj={}
 function obj:Cancel() self.cancelled=true end
 function obj:Interpolate(a,b,duration,step,finish)
  self.a=a; self.b=b; self.duration=duration; self.step=step; self.finish=finish
 end
 return obj
end
local bar=New(); bar.width=300; bar.overrideMaskRightOffset=-5
bar.Fill=New(); bar.Fill.width=290; bar.Fill.anchor={'native-fill-anchor'}
bar.Mask=New(); bar.Mask.anchor={'native-mask-anchor'}; bar.Fill.mask=bar.Mask
bar.Flare=New(); bar.Flare.anchor={'native-flare-anchor'}; bar.Flare.mask=bar.Mask
bar.Background=New(); bar.Border=New(); bar.Rank={Text=New()}
bar.BarAnimation=New(); bar.BarAnimation.Flipbook=New(); bar.FlareFadeOut=New()
bar.GetMaskWidth=ProfessionsRankBarMixin.GetMaskWidth
bar.Update=ProfessionsRankBarMixin.Update
bar.ownerManagesEvents=true
fixture.page.RankBar=bar
local info={professionName='First Aid',profession=1,skillLevel=25,maxSkillLevel=75,skillModifier=0,kit='FirstAid'}
bar:Update(info)
local originalMaskWidth=bar.Mask.width
ns.WSkin.entry.apply(); Drain()
assert(bar.Fill.fillColor[1]==.2 and bar.Fill.fillColor[2]==.8 and bar.Fill.fillColor[3]==.5,'actual native rank fill not themed')
assert(bar.Mask.width==originalMaskWidth and math.abs(bar.ratio-1/3)<.00001,'initial ratio changed')
assert(bar.BarAnimation.playing and bar.BarAnimation.Flipbook.rows==30 and bar.BarAnimation.Flipbook.frames==60,'native flipbook metadata changed')
assert(bar.Fill.mask==bar.Mask and bar.Flare.mask==bar.Mask and bar.Fill.width==290,'native mask association or fill dimensions changed')
assert(bar.Fill.anchor[1]=='native-fill-anchor' and bar.Mask.anchor[1]=='native-mask-anchor' and bar.Flare.anchor[1]=='native-flare-anchor','native rank anchors changed')
assert(bar.Flare.desaturated and bar.Flare.vertex[2]==.8 and bar.Flare.shown and bar.Flare.alpha==1,'native flare visibility/color lost')
assert(bar.Rank.Text.text=='First Aid 25/75' and bar.ownerManagesEvents,'native rank text/event ownership changed')
local restarts=bar.BarAnimation.restarts
bar:Update(info); Drain()
assert(bar.BarAnimation.restarts==restarts and not bar.interpolator,'same-ratio refresh restarted progression')
info.skillLevel=50; bar:Update(info)
local gain=bar.interpolator
assert(gain and gain.duration==.5 and bar.BarAnimation.restarts==restarts+1,'native skill gain animation not started')
gain.step(.5); local midpoint=bar.Mask.width
Drain()
assert(bar.interpolator==gain and not gain.cancelled and bar.Mask.width==midpoint,'styling interrupted native interpolation')
assert(math.abs(midpoint-(300*.5-5))<.00001,'native interpolation midpoint incorrect')
gain.step(1); gain.finish()
assert(bar.Mask.width==195 and bar.interpolator==nil,'native interpolation did not complete')
info.skillLevel=75; trial=true; info.skillModifier=5
bar:Update(info); local full=bar.interpolator; Drain()
assert(bar.FlareFadeOut.playing and bar.FlareFadeOut.restarts==1 and bar.interpolator==full,'full-rank native fade cancelled')
assert(bar.Rank.Text.text=='First Aid 75 +5/75 |cffff0000Trial cap|r','native modifier/trial-cap text changed')
full.step(1); full.finish()
assert(bar.Mask.width==295 and bar.ratio==1,'full-rank native mask changed')
-- Profession changes restore native atlases: the Update posthook must restyle.
info.profession=2; info.professionName='Enchanting'; info.kit='Enchanting'; info.skillLevel=15; info.skillModifier=0
bar:Update(info)
assert(bar.Fill.atlas=='Skillbar_Fill_Flipbook_Enchanting','native profession-change fixture failed')
Drain()
assert(bar.Fill.atlas==nil and bar.Fill.fillColor[2]==.8 and bar.Mask.width==55,'profession swap lost flat fill or changed progress')
assert(not bar.FlareFadeOut.playing and bar.Flare.alpha==1,'profession swap altered flare policy')
-- A native untrained/hidden bar is never exposed by the skin.
bar:Hide(); ns.WSkin.entry.apply(); Drain(); assert(not bar.shown,'skin exposed hidden profession rank')
ns.WSkin.Theme.accR=.7; ns.WSkin.looks(); Drain()
assert(bar.Fill.fillColor[1]==.7 and bar.Flare.vertex[1]==.7,'theme accent update missed rank fill')
''')
print('PASS: actual native rank Update, flat accent fill with original masks/anchors, skill-gain interpolation, flipbook lifecycle, completion flare fade, profession swaps, trial/modifier text, hidden state and theme changes')
