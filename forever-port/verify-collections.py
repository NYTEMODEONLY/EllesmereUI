"""Forever Collections regression checks in Lua 5.1 (requires lupa).

Fixtures mirror Camelot side tabs/counts, Classic companion journal and shared
collection controls. These verify preservation, not rendering or secure-client
behavior. No collection API, summon, use, dress-up or favorite action is called.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "EllesmereUIBlizzardSkin" / "EllesmereUIBlizzardSkin_ForeverCollections.lua"
PACK = SOURCE.with_name("EllesmereUIBlizzardSkin_WindowPacks.lua")
assert "local function Skin_Collections()\n    if EUI_FOREVER then return end" in PACK.read_text(encoding="utf-8")
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true
local style="off"
local function forbidden() error("skin invoked a native action/API/setter") end
local function texture()
    local t={alpha=.7,shown=false,color={.5,.2,.2,1},atlas="native",text="native",width=88}
    function t:SetAlpha(a) self.alpha=a end
    function t:GetAlpha() return self.alpha end
    function t:SetColorTexture(...) self.fill={...} end
    function t:SetTexture(file) self.texture=file end
    function t:SetVertexColor(...) self.vertex={...} end
    function t:SetAllPoints() end
    function t:GetTextColor() return unpack(self.color) end
    function t:SetTextColor(...) self.color={...} end
    t.SetText=forbidden; t.Show=forbidden; t.Hide=forbidden
    return t
end
local function frame()
    local f={shown=false,enabled=false,checked=true,width=703,value=9,id=17,hooks={},created={}}
    function f:CreateTexture() local t=texture(); self.created[#self.created+1]=t; return t end
    function f:HookScript(event,fn) self.hooks[event]=fn end
    function f:GetFontString() return self.Text end
    for _,key in ipairs({"SetScript","SetPoint","ClearAllPoints","SetSize","SetHeight","Show","Hide","SetShown","SetValue","SetChecked","SetEnabled","SetAttribute","SetText","SetDisplayInfo","SetUnit","TryOn","SetViewInsets","SetCameraPosition"}) do f[key]=forbidden end
    f.nativeAction=function() return "native action" end; f.OnClick=f.nativeAction
    f.Text=texture(); return f
end
local function bar() return {Back={Texture=texture()},Forward={Texture=texture()}} end
local function row()
    local f=frame()
    for _,k in ipairs({"name","subName","background","icon","factionIcon","petTypeIcon","selectedTexture","favorite","isDead","newGlow","Name","Label","Background","SelectedTexture","ProgressBar"}) do f[k]=texture() end
    f.IconFrame={Icon=texture(),Cover=texture(),Favorite=texture()}; return f
end
local function scroll()
    local f=frame(); f.rows={row()}
    function f:ForEachFrame(fn) for _,r in ipairs(self.rows) do fn(r) end end
    return f
end
local function paging() return {PageText=texture(),PrevPageButton=frame(),NextPageButton=frame()} end
local function count() local f=frame(); f.Count,f.Label=texture(),texture(); return f end
local function progress()
    local f=frame(); f.fill,f.text,f.border=texture(),texture(),texture()
    function f:GetStatusBarTexture() return self.fill end
    return f
end
local function journal()
    local f=frame(); f.LeftInset,f.RightInset,f.searchBox,f.FilterDropdown=frame(),frame(),frame(),frame()
    f.ScrollBar,f.ScrollBox,f.PagingFrame=bar(),scroll(),paging(); return f
end
local function spell()
    local f=frame()
    for _,k in ipairs({"name","new","level","special","iconTexture","iconTextureUncollected","slotFrameCollected","slotFrameUncollected","pendingUpgradeGlow","glow","slotFrameUncollectedInnerGlow"}) do f[k]=texture() end
    f.cooldown=frame(); f.cooldownWrapper={slotFavorite=texture()}; f.itemID=12345; return f
end
local W={Theme={bgR=.07,bgG=.07,bgB=.07,bgA=.9,insetR=.03,insetG=.03,insetB=.03,insetA=.9,accR=.1,accG=.8,accB=.6}}
function W.WindowCallback(key,fn) assert(key=="collections"); return function(...) if style~="off" then fn(...) end end end
function W.ResolveTheme() end
local ffd={}
function W.GetFFD(f) if not ffd[f] then ffd[f]={} end; return ffd[f] end
function W.Font(f,r,g,b) if f then f.font=true; if r then f.color={r,g,b} end end end
function W.AddBorder(f) f.skinBorder=true end
function W.Button(f) f.buttonSkin=true end
function W.StateButtonLabel() end
function W.Checkbox(f,opt) assert(opt.stockCheck); f.checkSkin=true end
function W.Dropdown(f) f.dropdownSkin=true; f.Text.color={1,1,1,1}; if f.PrecedingVariantIcon then f.PrecedingVariantIcon:SetAlpha(0) end end
function W.Shell(key,f) assert(key=="collections"); f.shell=true end
function W.Inset(f) f.insetSkin=true; for _,t in ipairs(f.created or {}) do t.alpha=0 end end
function W.CloseButton() end
function W.ScrollBar(f) f.Back.Texture.alpha=0; f.Forward.Texture.alpha=0 end
function W.RegisterWindow(entry) W.entry=entry end
function W.OnLooksChanged(fn) W.look=fn end
function hooksecurefunc(object,key,fn)
    if type(object)=="string" then fn=key; key=object; object=_G end
    local original=object[key]; object[key]=function(...) original(...); fn(...) end
end
ScrollUtil={AddInitializedFrameCallback=function(box,fn,owner) box.initialize=function(r) fn(owner,r) end end}
NS={WSkin=W}
for _,name in ipairs({"C_MountJournal","C_PetJournal","C_ToyBox","C_Heirloom","C_TransmogCollection","C_TransmogSets"}) do _G[name]=setmetatable({}, {__index=forbidden}) end
CollectionsJournal=frame(); local root=CollectionsJournal
root.TitleContainer={TitleText=texture()}; root.TabContainer={Tabs={},selectedTab=3}
for i=1,5 do
 local t=frame(); t.Icon,t.Background,t.SelectedTexture,t.Mask,t.TabGlow,t.HighlightTexture=texture(),texture(),texture(),texture(),texture(),texture()
 t.Icon.mask=t.Mask; root.TabContainer.Tabs[i]=t
 t.Icon.RemoveMaskTexture=forbidden; t.Icon.SetTexCoord=forbidden
end
MountJournal=journal(); local mount=MountJournal
mount.MountCount=count(); mount.MountButton=frame()
mount.BottomLeftInset=frame(); mount.BottomLeftInset.SlotButton=spell()
mount.MountDisplay={YesMountsTex=texture(),NoMountsTex=texture(),NoMounts=texture(),InfoButton={Name=texture(),Source=texture(),Lore=texture()},ModelScene=frame()}
mount.MountDisplay.ModelScene.TogglePlayer=frame(); mount.MountDisplay.ModelScene.TogglePlayer.TogglePlayerText=texture()
mount.MountDisplay.ModelScene.ControlFrame=frame(); mount.ToggleDynamicFlightFlyoutButton=spell()
PetJournal=journal(); local pet=PetJournal
pet.PetCount=count(); pet.SummonButton=frame(); pet.PetCard={PetBackground=texture(),PetInfo=row(),modelScene=frame()}
pet.PetCard.modelScene.RotateLeftButton=frame(); pet.PetCard.modelScene.RotateRightButton=frame()
ToyBox=journal(); local toys=ToyBox
toys.ProgressTracker=count(); toys.iconsFrame=frame()
for i=1,18 do toys.iconsFrame['spellButton'..i]=spell() end
HeirloomsJournal=journal(); local heir=HeirloomsJournal
heir.progressBar=progress(); heir.iconsFrame=frame(); heir.heirloomEntryFrames={spell()}; heir.heirloomHeaderFrames={{text=texture()}}
function heir:LayoutCurrentPage() self.nativeLayouts=(self.nativeLayouts or 0)+1 end
function heir:UpdateButton() self.nativeUpdates=(self.nativeUpdates or 0)+1 end
WardrobeCollectionFrame=journal(); local ward=WardrobeCollectionFrame
ward.ItemsTab,ward.SetsTab=frame(),frame(); ward.progressBar=progress()
ward.ItemsCollectionFrame=frame(); ward.ItemsCollectionFrame.PagingFrame=paging(); ward.ItemsCollectionFrame.WeaponDropdown=frame()
local model=frame(); model.NewString,model.Border,model.SlotInvalidTexture=texture(),texture(),texture()
ward.ItemsCollectionFrame.Models={model}; ward.ItemsCollectionFrame.SlotsFrame={Buttons={spell(),spell()}}
ward.SetsCollectionFrame={LeftInset=frame(),RightInset=frame(),ListContainer={ScrollBox=scroll(),ScrollBar=bar()},Model=frame(),DetailsFrame={Name=texture(),LongName=texture(),Label=texture(),LimitedSet={Text=texture(),Icon=texture()},VariantSetsDropdown=frame()}}
local variant=ward.SetsCollectionFrame.DetailsFrame.VariantSetsDropdown
variant.PrecedingVariantIcon=texture(); variant.PrecedingVariantIcon.OnEnter=frame().nativeAction
function MountJournal_InitMountButton() end
function PetJournal_InitPetButton() end
function ToySpellButton_UpdateButton() end
function HeirloomsJournal_UpdateButton() end
function verify()
    assert(W.entry.addons.Blizzard_Collections)
    W.entry.apply(); assert(not root.shell)
    style="modern"; W.look(); assert(root.shell and root.TitleContainer.TitleText.font)
    assert(root.TabContainer.selectedTab==3 and #root.TabContainer.Tabs==5)
    for _,tab in ipairs(root.TabContainer.Tabs) do
        assert(not tab.skinBorder and tab.Background.alpha==0 and tab.Icon.atlas=="native" and tab.Icon.alpha==.7 and tab.checked and tab.OnClick==tab.nativeAction and tab.width==703 and not tab.shown)
        assert(tab.Icon.mask==tab.Mask and tab.Mask.atlas=='native' and tab.Mask.alpha==.7 and tab.SelectedTexture.atlas=='native' and not tab.SelectedTexture.shown and tab.TabGlow.alpha==.7,'native clipped corner/selection/glow changed')
        assert(#tab.created==0,'extra collection tab square texture created')
    end
    for _,j in ipairs({mount,pet,toys,heir,ward}) do
        assert(j.searchBox.font and j.FilterDropdown.Text.font and j.FilterDropdown.Text.color[1]==.5)
        assert(j.ScrollBar.Back.Texture.alpha==.7 and j.ScrollBar.Forward.Texture.alpha==.7)
        local r=j.ScrollBox.rows[1]; assert(r.name.font and r.name.color[1]==.5 and r.name.color[2]==.2)
        assert(r.icon.atlas=="native" and not r.selectedTexture.shown and r.OnClick==r.nativeAction)
        assert(j.PagingFrame.PrevPageButton.OnClick==j.PagingFrame.PrevPageButton.nativeAction and not j.PagingFrame.PrevPageButton.enabled)
    end
    assert(toys.ProgressTracker.Count.font and toys.ProgressTracker.value==9 and not toys.ProgressTracker.shown)
    assert(not ward.progressBar.shown and ward.progressBar.width==703 and ward.progressBar.value==9)
    assert(ward.progressBar.fill.texture=='Interface\\Buttons\\WHITE8X8')
    assert(mount.MountDisplay.NoMountsTex.atlas=="native" and mount.MountDisplay.NoMountsTex.alpha==.7)
    assert(mount.MountDisplay.ModelScene.TogglePlayer.checked and not mount.MountDisplay.ModelScene.TogglePlayer.enabled)
    assert(not mount.MountDisplay.ModelScene.ControlFrame.buttonSkin)
    assert(pet.PetCard.modelScene.RotateLeftButton.OnClick==pet.PetCard.modelScene.RotateLeftButton.nativeAction)
    assert(not pet.PetCard.modelScene.RotateLeftButton.buttonSkin)
    assert(model.NewString.font and model.Border.atlas=="native" and model.SlotInvalidTexture.alpha==.7)
    assert(variant.dropdownSkin and variant.PrecedingVariantIcon.alpha==.7 and variant.PrecedingVariantIcon.OnEnter)
    for _,s in ipairs({toys.iconsFrame.spellButton1,heir.heirloomEntryFrames[1],mount.BottomLeftInset.SlotButton}) do
        assert(s.itemID==12345 and s.OnClick==s.nativeAction and s.checked)
        assert(s.iconTexture.atlas=="native" and s.slotFrameUncollected.alpha==.7 and not s.pendingUpgradeGlow.shown)
        assert(s.cooldown.value==9 and not s.cooldownWrapper.slotFavorite.shown)
    end
    local late=row(); mount.ScrollBox.initialize(late); assert(late.name.font and late.name.color[2]==.2)
    local latePet=row(); PetJournal_InitPetButton(latePet); assert(latePet.name.font)
    local lateHeir=spell(); heir.heirloomEntryFrames[2]=lateHeir; heir:LayoutCurrentPage()
    assert(heir.nativeLayouts==1 and lateHeir.name.font and lateHeir.itemID==12345)
    style="off"; local inactive=row(); mount.ScrollBox.initialize(inactive); assert(not inactive.name.font)
    local unstyled=spell(); ToySpellButton_UpdateButton(unstyled); assert(not unstyled.name.font)
    style="modern"; ToySpellButton_UpdateButton(unstyled); assert(unstyled.name.font and unstyled.iconTexture.atlas=="native")
    W.look()
    assert(W.GetFFD(toys.iconsFrame).fill.alpha==1,"repainting inset hid its EUI backing")
    assert(W.GetFFD(mount.BottomLeftInset).fill.alpha==1,"repainting equipment panel hid its EUI backing")
end
''')
lua.execute("local fn=assert(loadstring(...)); fn('EllesmereUIBlizzardSkin',NS)", SOURCE.read_text(encoding="utf-8"))
lua.eval("verify")()
print("PASS: Collections side tabs, models, secure spell controls, semantic icons/colors, native paging/counts, dynamic pools and style gates preserved")
