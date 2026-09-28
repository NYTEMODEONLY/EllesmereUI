"""Offline bank-skin preservation regression tests. Requires lupa (Lua 5.1).

Does not emulate WoW rendering, bank access, protected actions or combat.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "EllesmereUIBags" / "EllesmereUIBags_ForeverBank.lua"
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER = true
EUI_FOREVER_STATUS = {}
local frames = {}
local function region()
    local r = {alpha=1, shown=true, color={1, 0, 0}, texture="native"}
    function r:SetAlpha(a) self.alpha=a end
    function r:GetAlpha() return self.alpha end
    function r:SetColorTexture(...) self.fill={...} end
    function r:SetVertexColor(...) self.vertex={...} end
    function r:SetAllPoints() end
    function r:GetAtlas() return "native-icon" end
    return r
end
function CreateFrame()
    local f = {shown=true, enabled=false, parent="native-parent", width=480, hooks={}, scripts={}}
    function f:CreateTexture() return region() end
    function f:RegisterEvent() end
    function f:SetScript(event, callback) self.scripts[event]=callback end
    function f:HookScript(event, callback) self.hooks[event]=callback end
    function f:GetRegions() return end
    function f:GetFontString() return self.Text end
    frames[#frames+1]=f
    return f
end
function hooksecurefunc(f, method, callback)
    local original=f[method]
    f[method]=function(self, ...) original(self, ...); callback(self, ...) end
end
local function pool(...)
    local p={active={...}}
    function p:EnumerateActive() local i=0; return function() i=i+1; return self.active[i] end end
    return p
end
local W={Theme={accR=.1,accG=.8,accB=.6,insetR=.04,insetG=.04,insetB=.04,insetA=.85,bgR=.08,bgG=.08,bgB=.08,bgA=.92,brdR=.2,brdG=.2,brdB=.2}}
local style="off"
function W.GetStyle() return style end
function W.ResolveTheme() end
function W.WindowCallback(_, callback) return function(...) if style~="off" then callback(...) end end end
function W.Font(f,r,g,b)
    if f then f.font=true; if r then f.color={r,g,b} end end
end
function W.AddBorder(f) f.border=true end
function W.Shell(_, f) f.shell=true end
function W.Panel(f) f.panel=true end
function W.CloseButton(f) end
function W.Button(f) f.skinned=true end
function W.StateButtonLabel(f) end
function W.Checkbox(f) f.skinned=true end
function W.Dropdown(f) end
function W.ScrollBar(f) f.Back.Texture.alpha=0; f.Forward.Texture.alpha=0 end
function W.OnLooksChanged(callback) W.lookChanged=callback end
EllesmereUI={_ModuleNS={EllesmereUIBlizzardSkin={WSkin=W}}}
local function item(bag, slot)
    local f=CreateFrame()
    f.bankTabID, f.containerSlotID, f.itemInfo = bag,slot,{quality=4,isFiltered=true,isLocked=true}
    f.icon, f.Background, f.normal, f.Count = region(),region(),region(),region()
    f.IconQuestTexture, f.BagIndicator, f.DisabledOverlay = region(),region(),region()
    f.IconBorder, f.Cooldown, f.SearchOverlay = region(),region(),region()
    f.Click=function() return "native-item-action" end
    function f:GetNormalTexture() return self.normal end
    function f:Refresh() self.normal.alpha=1 end
    function f:SetItemLocation() self.locationUpdated=true end
    function f:UpdateBackgroundForBankType() end
    return f
end
local slot=item(8,3)
local bag=item(8,2)
local page=CreateFrame()
page.Background,page.SelectedTexture,page.Icon=region(),region(),region()
page.Mask,page.TabGlow=region(),region()
page.Background.texture="common-sidetab"
page.SelectedTexture.texture="common-sidetab-selected"
page.Mask.texture="common-sidetab-mask"
page.pageNumber,page.bankType,page.checked=2,"account",false
page.OnMouseUp=function() return "native-page-action" end
function page:SetPageInfo(bankType, number, selected)
    self.bankType,self.pageNumber,self.checked=bankType,number,selected
end
BankFrame=CreateFrame()
BankFrame.TitleContainer={TitleText=region()}
BankFrameTitleText=region()
BankFrame.BagText,BankFrame.BagCost=region(),region()
BankFrame.itemButtonBagPool=pool(bag)
BankFrame.bankPageTabPool=pool(page)
BankFrame.BankItemSearchBox=CreateFrame()
BankFrame.BankItemSearchBox.searchIcon=region()
BankFrame.BankItemSearchBox.clearButton=CreateFrame()
function BankFrame:RefreshBagButtons() end
function BankFrame:RefreshPageTabs() end
local panel=CreateFrame()
BankFrame.BankPanel=panel
panel.itemButtonPool=pool(slot)
panel.currentPage=2
panel.PurchaseButton=CreateFrame()
panel.PurchaseButton.Click=function() return "native-purchase-confirmation" end
panel.AutoSortButton=CreateFrame(); panel.AutoSortButton.glyph=region()
panel.LockPrompt=CreateFrame(); panel.LockPrompt.PromptText=region()
panel.PurchasePrompt=CreateFrame(); panel.PurchasePrompt.shown=false
panel.MoneyDisplay={GoldButton={Text=region()}}
panel.MoneyDisplay.SilverButton={Text=region(),NormalTexture=region()}
panel.MoneyDisplay.SilverButton.Text.value=10
panel.MoneyFrame={WithdrawButton=CreateFrame(),DepositButton=CreateFrame()}
function panel:GenerateItemSlotsForSelectedTab() end
function panel:RefreshBankTabs() end
local menu=CreateFrame(); panel.TabSettingsMenu=menu
menu.IconSelector={ScrollBar={Back={Texture=region()},Forward={Texture=region()}}}
menu.IconSelector.ScrollBar.Forward.Texture.alpha=.35
local purchase=panel.PurchaseButton.Click
function VerifyBank()
    local boot=frames[#frames]
    boot.scripts.OnEvent(boot,"PLAYER_LOGIN")
    assert(not BankFrame.shell, "off style painted at startup")
    style="eui"; W.lookChanged()
    assert(BankFrame.shell and slot.border and slot.normal.alpha==0, "skin not installed")
    assert(slot.bankTabID==8 and slot.containerSlotID==3 and panel.currentPage==2, "item/page identities changed")
    assert(slot.Click()=="native-item-action" and page.OnMouseUp()=="native-page-action", "native actions changed")
    assert(panel.PurchaseButton.Click==purchase and not panel.PurchaseButton.enabled, "purchase availability changed")
    assert(panel.LockPrompt.shown and not panel.PurchasePrompt.shown, "native lock/purchase prompt visibility changed")
    assert(bag.DisabledOverlay.shown and bag.DisabledOverlay.alpha==1, "unbought bag lock removed")
    for _,key in ipairs({"icon","IconQuestTexture","IconBorder","Cooldown","SearchOverlay","BagIndicator"}) do assert(slot[key].alpha==1,key.." removed") end
    assert(panel.MoneyDisplay.GoldButton.Text.color[1]==1 and panel.MoneyDisplay.GoldButton.Text.color[2]==0, "unaffordable red price overwritten")
    assert(panel.MoneyDisplay.SilverButton.Text.value==10 and panel.MoneyDisplay.SilverButton.Text.color[2]==0, "red ten-silver cost changed")
    assert(panel.MoneyDisplay.SilverButton.NormalTexture.alpha==1, "silver coin glyph hidden")
    assert(BankFrame.TitleContainer.TitleText.color[2]==1 and BankFrameTitleText.color[2]==1, "native bank titles not white")
    assert(BankFrame.BagText.color[1]==.82 and BankFrame.BagText.color[2]==.82, "bag label not neutral")
    assert(BankFrame.BagCost.color[1]==.7 and BankFrame.BagCost.color[2]==.7, "static cost label not neutral")
    assert(BankFrame.BankItemSearchBox.searchIcon.alpha==1 and panel.AutoSortButton.glyph.alpha==1, "search/sort glyph removed")
    assert(menu.IconSelector.ScrollBar.Forward.Texture.alpha==.35, "scroll arrow dimming changed")
    assert(slot.width==480 and slot.parent=="native-parent", "native layout changed")
    assert(not page.border and not page.Background.fill, "extra square tab decoration added")
    assert(page.Background.alpha==0, "raw page icon still has a backplate")
    assert(page.Background.texture=="common-sidetab" and page.Mask.texture=="common-sidetab-mask", "tab silhouette changed")
    assert(page.Icon.texture=="native" and page.SelectedTexture.texture=="common-sidetab-selected", "native tab/selection art replaced")
    page:SetPageInfo("character",3,true)
    assert(page.pageNumber==3 and page.checked and page.bankType=="character", "page selection overwritten")
    assert(not page.border and not page.Background.fill, "pooled tab refresh added square decoration")
    local later=item(9,1); panel.itemButtonPool.active={later}
    panel:GenerateItemSlotsForSelectedTab()
    assert(later.border and later.normal.alpha==0 and later.containerSlotID==1, "new pooled item not safely themed")
    later:Refresh(); assert(later.normal.alpha==0, "recycled native slot art not re-themed")
    style="off"; later:Refresh(); assert(later.normal.alpha==1, "off-style refresh still paints")
end
''')
lua.execute('assert(loadstring(...))()', SOURCE.read_text(encoding="utf-8"))
lua.eval("VerifyBank")()
print("Bank: syntax, pooled slots, native actions/IDs/layout, lock/purchase/disabled states, overlays, prices, search/sort/arrows, style toggle passed")
