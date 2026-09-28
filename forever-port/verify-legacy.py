"""Offline preservation tests for the Forever Legacy skin; requires lupa.

Run with the same Python/PYTHONPATH used for verify.py. Mocks deliberately do
not emulate rendering or WoW secure execution; inspect all three pages in game.
"""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "EllesmereUIBlizzardSkin" / "EllesmereUIBlizzardSkin_ForeverLegacy.lua"
lua = LuaRuntime()
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_SharedXML/Mainline/SharedUIPanelTemplates.lua'
native_source = native.read_text(encoding='utf-8')
native_start = native_source.index('function SidePanelTabButtonMixin:SetChecked(checked)')
native_end = native_source.index('function SidePanelTabButtonMixin:GetTooltipTextSetupFunction()', native_start)
lua.execute('SidePanelTabButtonMixin={}; TextureKitConstants={UseAtlasSize=true}')
lua.execute(native_source[native_start:native_end])
lua.execute(r'''
EUI_FOREVER = true
local function region()
    local r = {alpha = 1, shown = true}
    function r:SetColorTexture(...) self.color = {...} end
    function r:SetVertexColor(...) self.vertex = {...} end
    function r:SetAlpha(a) self.alpha = a end
    function r:GetAlpha() return self.alpha end
    function r:SetTexture(t) self.texture = t end
    function r:SetAtlas(a) self.atlas = a end
    function r:SetShown(v) self.shown = v end
    function r:SetAllPoints() end
    return r
end
local function frame()
    local f = {}
    function f:CreateTexture() return region() end
    function f:GetRegions() return region() end
    return f
end
local function bar()
    local f = frame()
    f.fill, f.ProgressBarFrame, f.Text, f.value = region(), region(), region(), 31
    function f:GetStatusBarTexture() return self.fill end
    return f
end
function hooksecurefunc(o, k, fn)
    local original = o[k]
    o[k] = function(self, ...) original(self, ...); fn(self, ...) end
end
local style = "eui"
local W = {Theme = {
    accR=.1, accG=.8, accB=.6, bgR=.08, bgG=.08, bgB=.08, bgA=.92,
    insetR=.04, insetG=.04, insetB=.04, insetA=.85, brdR=.2, brdG=.2, brdB=.2,
}}
function W.GetStyle() return style end
function W.WindowCallback(_, fn)
    return function(...) if style ~= "off" then return fn(...) end end
end
function W.Font(fs) if fs then fs.fontApplied = true end end
function W.AddBorder(f) f.border = true end
function W.ApplyBarFill(f) f.fillColorApplied = true end
function W.Button(f) f.buttonSkinned = true end
function W.StateButtonLabel(f) f.statePreserved = true end
function W.Checkbox(f) f.checkSkinned = true end
function W.Dropdown(f) f.dropdownSkinned = true end
function W.ScrollBar(f)
    if not f then return end
    f.Back.Texture:SetAlpha(0)
    f.Forward.Texture:SetAlpha(0)
end
function W.OnLooksChanged(fn) end
NS = {WSkin = W}
ScrollUtil = {AddInitializedFrameCallback = function(box, fn, owner)
    box.callback = function(row) fn(owner, row) end
end}
local function scroll(row)
    local s = frame()
    function s:ForEachFrame(fn) if row then fn(row) end end
    return s
end
local function scrollBar()
    local b = {Back={Texture=region()}, Forward={Texture=region()}}
    b.Forward.Texture.alpha = .4
    b.Forward.enabled = false
    return b
end
local clicks = 0
local card = frame()
card.RewardCardBG, card.Icon, card.IconBorder = region(), region(), region()
card.Level, card.RewardName, card.EarnedCheckmark = region(), region(), region()
card.info = {level = 3}
function card:GetLevel() return self.info.level end
function card:Refresh(_, display, selected)
    self.EarnedCheckmark.shown = self.info.level <= display
    self.nativeSelected = selected
end
local progress = frame()
function progress:GetElements() return {card} end
local reward = frame()
reward.Background, reward.ProgressBarBackground = region(), region()
reward.LegacyRewardProgressFrame, reward.LegacyRewardProgressBar = progress, bar()
function reward:SetupRewardTrack() end
local cat = frame()
cat.normal, cat.highlight, cat.NotificationIcon = region(), region(), region()
cat.CollapseButton, cat.ButtonText = frame(), region()
function cat:GetNormalTexture() return self.normal end
function cat:GetHighlightTexture() return self.highlight end
function cat:RefreshCardArt() end
function cat:RefreshTitleColorState() end
local row = frame()
row.Background, row.Label, row.Description, row.HiddenDescription = region(), region(), region(), region()
row.Icon, row.Shield, row.completed = {texture=region()}, frame(), false
function row:IsSelected() return self.selected end
function row:RefreshStateArt() end
function row:Saturate() end
function row:Desaturate() end
function row:DisplayObjectives() end
row.OnClick = function() clicks = clicks + 1 end
local treeButton = frame()
treeButton.Background, treeButton.SelectedGlow, treeButton.Icon = region(), region(), region()
treeButton.checked = true
function treeButton:GetChecked() return self.checked end
function treeButton:RefreshSelectionVisuals() self.SelectedGlow.shown = self.checked end
local selection = frame()
selection.treeButtons = {treeButton}
function selection:RefreshTreeButtons() end
local panel = frame()
panel.ApplyButton, panel.ResetButton, panel.UndoButton = frame(), frame(), frame()
panel.ApplyButton.enabled = false
panel.ResetButton.Icon = region()
panel.SearchBox = frame()
panel.SearchBox.searchIcon, panel.SearchBox.clearButton = region(), frame()
local list = frame()
list.ScrollBox, list.ScrollBar, list.SearchBox = scroll(cat), scrollBar(), frame()
list.SearchBox.searchIcon, list.SearchBox.clearButton = region(), frame()
list.FilterDropdown = frame()
list.FilterDropdown.Background, list.FilterDropdown.ResetButton = region(), frame()
local challenges = frame()
challenges.Background, challenges.CategoryList = region(), list
challenges.DetailPane = {ScrollBox=scroll(row), ScrollBar=scrollBar()}
local tab = frame()
tab.Background, tab.Icon, tab.SelectedTexture = region(), region(), region()
tab.Mask, tab.TabGlow, tab.HighlightTexture = region(), region(), region()
tab.Background.atlas, tab.Mask.atlas = 'common-sidetab', 'common-sidetab-mask'
tab.SelectedTexture.atlas, tab.TabGlow.atlas = 'common-sidetab-selected', 'common-sidetab-selected'
tab.HighlightTexture.atlas = 'common-sidetab-hover'
tab.Icon.texture = 'native-legacy-icon'; tab.Icon.mask = tab.Mask
tab.Icon.anchor = {'CENTER', -4, 0}; tab.Icon.width, tab.Icon.height = 50, 50
tab.TabGlow.alpha = .37; tab.HighlightTexture.shown = false
tab.SelectedTexture.shown = false
tab.SetChecked = SidePanelTabButtonMixin.SetChecked
function tab:UpdateIconInterior() self.nativeInteriorRefreshes=(self.nativeInteriorRefreshes or 0)+1 end
local tree = frame()
tree.Background, tree.LegacyTreeSelectionPanel, tree.LegacyTreeTraitPanel = region(), selection, panel
LegacySystemFrame = {
    Tabs={tab}, RewardTrackPage=reward, ChallengesPage=challenges, TreePage=tree,
    SelectPage=function(self, id) self.page=id end,
}
function VerifyLegacy()
    local fill, click = reward.LegacyRewardProgressBar.fill, row.OnClick
    NS.ForeverLegacy(); NS.ForeverLegacy()
    assert(row.OnClick == click and row.Icon.texture.alpha == 1, "challenge native handler/icon changed")
    assert(tab.Icon.alpha == 1 and not tab.SelectedTexture.shown, "side-tab icon/selection changed")
    assert(not tab.border and tab.Background.color==nil and tab.Background.atlas=='common-sidetab', "square side-tab fill/border added")
    assert(tab.Background.alpha==0 and tab.Mask.alpha==1, "raw icon backing/mask treatment changed")
    assert(tab.Mask.atlas=='common-sidetab-mask' and tab.Icon.mask==tab.Mask, "clipped icon mask changed")
    assert(tab.Icon.texture=='native-legacy-icon' and tab.Icon.anchor[2]==-4 and tab.Icon.width==50 and tab.Icon.height==50, "raw icon or native geometry changed")
    assert(tab.TabGlow.alpha==.37 and not tab.HighlightTexture.shown, "native glow/hover state changed")
    assert(tab.SetChecked==SidePanelTabButtonMixin.SetChecked, "selection handler replaced")
    tab:SetChecked(true); NS.ForeverLegacy()
    assert(tab.SelectedTexture.shown and tab.SelectedTexture.atlas=='common-sidetab-selected', "native selected border lost")
    tab:SetChecked(false); NS.ForeverLegacy()
    assert(not tab.SelectedTexture.shown and tab.nativeInteriorRefreshes==2, "native deselection/update changed")
    assert(not panel.ApplyButton.enabled and panel.ResetButton.Icon.alpha == 1, "disabled state/reset glyph changed")
    assert(list.SearchBox.searchIcon.alpha == 1 and panel.SearchBox.searchIcon.alpha == 1, "search glyph removed")
    assert(reward.LegacyRewardProgressBar.fill == fill and reward.LegacyRewardProgressBar.value == 31, "progress identity/value changed")
    assert(list.ScrollBar.Back.Texture.alpha == 1 and list.ScrollBar.Forward.Texture.alpha == .4, "arrow alpha changed")
    assert(not list.ScrollBar.Forward.enabled, "disabled scroll arrow enabled")
    card:Refresh(3, 3, true)
    assert(card.EarnedCheckmark.shown and card.nativeSelected, "reward selection/earned state changed")
    local selectedColor = card.RewardCardBG.color[2]
    card:Refresh(1, 1, false)
    assert(not card.EarnedCheckmark.shown and card.RewardCardBG.color[2] ~= selectedColor, "unearned reward state not reflected")
    treeButton.checked = false; treeButton:RefreshSelectionVisuals()
    assert(not treeButton.SelectedGlow.shown, "tree selection changed")
    -- A frame initialized later must receive the skin via its ScrollBox callback.
    local later = frame()
    later.Label, later.Icon = region(), {texture=region()}
    function later:IsSelected() return false end
    challenges.DetailPane.ScrollBox.callback(later)
    assert(later.border and later.Label.fontApplied and later.Icon.texture.alpha == 1, "pooled row not safely themed")
    list.ScrollBox.callback(cat)
    row.OnClick(); assert(clicks == 1, "native handler not usable")
    LegacySystemFrame:SelectPage(3); assert(LegacySystemFrame.page == 3, "native page dispatch changed")
    style = "off"
    card.RewardCardBG.color = {"sentinel"}; card:Refresh(3, 3, true)
    assert(card.RewardCardBG.color[1] == "sentinel", "disabled skin still paints")
end
''')
lua.execute('assert(loadstring(...))("EllesmereUIBlizzardSkin", NS)', SOURCE.read_text(encoding="utf-8"))
lua.eval("VerifyLegacy")()
print("Legacy: syntax, native clipped side-tab art/mask/selection without square border, pooled refresh, native handlers/icons/disabled states, scroll arrows, progress identity/value, off-style checks passed")
