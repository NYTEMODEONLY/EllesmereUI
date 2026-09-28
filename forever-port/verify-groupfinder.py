"""Offline Forever Group Finder preservation checks; requires lupa (Lua 5.1).

Mocks verify adapter behavior, not rendering, secure execution or server search.
Never sends messages, creates listings, selects roles, or invites players.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "EllesmereUIBlizzardSkin" / "EllesmereUIBlizzardSkin_ForeverGroupFinder.lua"
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true
EUI_FOREVER_STATUS={}
local style="off"
local function texture()
    local t={alpha=1,shown=true,color={.3,.3,.3},text="native",value=7}
    function t:SetAlpha(a) self.alpha=a end
    function t:GetAlpha() return self.alpha end
    function t:SetColorTexture(...) self.fill={...} end
    function t:SetVertexColor(...) self.vertex={...} end
    function t:SetAllPoints() end
    function t:SetText() error("adapter attempted a native text write") end
    return t
end
local function frame()
    local f={shown=false,enabled=false,checked=true,width=458,parent="native",hooks={}}
    function f:CreateTexture() return texture() end
    function f:HookScript(event,fn) self.hooks[event]=fn end
    function f:GetFontString() return self.Text end
    function f:GetRegions() return end
    function f:SetText() error("adapter attempted a native text write") end
    function f:SetScript() error("adapter replaced native scripts") end
    function f:SetPoint() error("adapter changed native anchors") end
    function f:Show() error("adapter changed native visibility") end
    function f:Hide() error("adapter changed native visibility") end
    f.OnClick=function() return "native action" end
    return f
end
local function pool(...)
    local p={active={...}}
    function p:EnumerateActive() local i=0; return function() i=i+1; return self.active[i] end end
    return p
end
local function scroll(row)
    local f=frame(); f.rows={row}
    function f:ForEachFrame(fn) for _,v in ipairs(self.rows) do fn(v) end end
    return f
end
local function scrollBar()
    return {Back={Texture=texture()},Forward={Texture=texture()}}
end
local function page() local p=frame(); p.TitleContainer={TitleText=texture()}; return p end
local function sideTab()
    local f=frame(); f.Background,f.Icon,f.SelectedTexture,f.Mask,f.TabGlow=texture(),texture(),texture(),texture(),texture()
    f.Icon.mask=f.Mask; f.Mask.atlas='native-clipped'; f.SelectedTexture.atlas='native-selected'
    function f.Icon:RemoveMaskTexture() error('native LFG tab mask removed') end
    function f.Icon:SetTexCoord() error('native LFG tab icon UVs cropped') end
    function f:CreateTexture() error('extra LFG tab square texture created') end
    f.SelectedTexture.shown=false; return f
end
local W={Theme={accR=.1,accG=.8,accB=.6,bgR=.08,bgG=.08,bgB=.08,bgA=.92,insetR=.04,insetG=.04,insetB=.04,insetA=.85,brdR=.2,brdG=.2,brdB=.2}}
function W.GetStyle() return style end
function W.ResolveTheme() end
function W.WindowCallback(key,fn)
    assert(key=="lfg","wrong imported style key")
    return function(...) if style~="off" then fn(...) end end
end
function W.Font(f,r,g,b) if f then f.font=true; if r then f.color={r,g,b} end end end
function W.AddBorder(f) f.border=true end
function W.Button(f) f.buttonSkin=true end
function W.StateButtonLabel() end
function W.Checkbox(f) f.checkSkin=true end
function W.Dropdown(f) if f then f.dropdownSkin=true end end
function W.Panel(f) f.panelSkin=true end
function W.Shell(key,f) assert(key=="lfg"); f.shell=true end
function W.Inset() end
function W.CloseButton() end
function W.ScrollBar(f) f.Back.Texture.alpha=0; f.Forward.Texture.alpha=0 end
function W.RegisterWindow(entry) W.entry=entry end
function W.OnLooksChanged(fn) W.look=fn end
function hooksecurefunc(object,key,fn)
    if type(object)=="string" then fn=key; key=object; object=_G end
    local original=object[key]
    object[key]=function(...) original(...); fn(...) end
end
ScrollUtil={AddInitializedFrameCallback=function(box,fn,owner)
    box.initialize=function(row) fn(owner,row) end
end}
NS={WSkin=W}
C_LFGList=setmetatable({}, {__index=function() error("skin queried listing/player API") end})
local category=frame(); category.Icon,category.Cover,category.Label=texture(),texture(),texture()
local activity=frame()
activity.Level=texture(); activity.NameButton={Name=texture()}
activity.CheckButton=frame(); activity.ExpandOrCollapseButton=frame()
activity.InstanceLockWarningIcon={Icon=texture(),shown=true}
local result=frame(); result.ResultBG,result.Selected,result.Name=texture(),texture(),texture()
result.Level,result.ActivityName=texture(),texture()
result.ClassIcon,result.PartyIcon,result.NewPlayerFriendlyIcon=texture(),texture(),texture()
result.Selected.shown=false
result.DataDisplay={Comment=texture(),Solo={Roles={texture()},RolesText=texture()},RoleCount={TankCount=texture(),TankIcon=texture()},DelistButton=frame()}
result.DataDisplay.DelistButton.Icon=texture()
local who=frame(); who.Class,who.Name,who.Selected,who.Background=texture(),texture(),texture(),texture()
function who:InitButton() end
local role=frame(); role.Background,role.cover,role.Icon=texture(),texture(),texture(); role.CheckButton=frame()
local lockedLine={Text=texture()}
LFGParentFrame=page(); LFGParentFrame.ListingTab=sideTab(); LFGParentFrame.BrowsingTab=sideTab(); LFGParentFrame.WhoListingTab=sideTab()
function LFGParentFrame:UpdateTabs() end
LFGListingFrame=page()
LFGListingFrame.PostButton=frame(); LFGListingFrame.BackButton=frame()
LFGListingFrame.SoloRoleButtons={RoleButtons={role}}
LFGListingFrame.GroupRoleButtons={RoleDropdown={Text=texture()}}
LFGListingFrame.NewPlayerFriendlyButton={CheckButton=frame(),Icon=texture()}
LFGListingFrame.CategoryView={CategoryButtons={category}}
local comment=frame(); comment.EditBox=frame(); comment.EditBox.Instructions=texture()
comment.EditBox.securityDisableSetText=true; comment.EditBox.securityDisablePaste=true
comment.ScrollBar={ThumbTexture=texture(),ScrollUpButton={Icon=texture()},ScrollDownButton={Icon=texture()}}
LFGListingFrame.ActivityView={ScrollBox=scroll(activity),ScrollBar=scrollBar(),Comment=comment}
LFGListingFrame.LockedView={ErrorText=texture(),ActivityText=texture(),framePool=pool(lockedLine),shown=true}
LFGBrowseFrame=page(); LFGBrowseFrame.ScrollBox=scroll(result); LFGBrowseFrame.ScrollBar=scrollBar()
LFGBrowseFrame.ScrollBar.Forward.Texture.alpha=.35
LFGBrowseFrame.CategoryDropdown={Text=texture()}
LFGBrowseFrame.ActivityDropdown={Text=texture(),ResetButton={Icon=texture(),shown=true}}
LFGBrowseFrame.SendMessageButton=frame(); LFGBrowseFrame.GroupInviteButton=frame()
LFGBrowseFrame.RefreshButton=frame(); LFGBrowseFrame.RefreshButton.Icon=texture()
LFGBrowseFrame.SearchingSpinner={shown=true,Label=texture()}
LFGWhoListFrame=page(); LFGWhoListFrame.ScrollBox=scroll(who); LFGWhoListFrame.EditBox=frame()
LFGWhoListFrame.EditBox.searchIcon=texture(); LFGWhoListFrame.WhoSearch=frame(); LFGWhoListFrame.WhoSearch.Icon=texture()
local member={Name=texture(),Level=texture(),Role=texture()}
LFGBrowseSearchEntryTooltip={memberPool=pool(member),activityPool=pool(texture()),completedEncounterPool=pool(texture()),Leader=member,Delisted=texture(),NewPlayerFriendlyIcon=texture()}
function LFGBrowseSearchEntry_Update(row) row.refreshes=(row.refreshes or 0)+1 end
function LFGBrowseSearchEntryTooltip_UpdateAndShow() end
function LFGListingCategorySelection_UpdateCategoryButtons() end
function LFGListingActivityView_InitActivityButton() end
function LFGListingActivityView_InitActivityGroupButton() end
function LFGListingLockedView_RefreshContent() end
function VerifyGroupFinder()
    assert(W.entry.addons.Blizzard_GroupFinder_VanillaStyle, "wrong LoD addon")
    W.entry.apply(); assert(not LFGParentFrame.shell, "off style paints")
    local originalAction=LFGBrowseFrame.SendMessageButton.OnClick
    style="eui"; W.look()
    assert(LFGParentFrame.shell and LFGListingFrame.shell and LFGBrowseFrame.shell and LFGWhoListFrame.shell,"three-page skin missing")
    assert(not LFGParentFrame.ListingTab.SelectedTexture.shown and LFGParentFrame.ListingTab.Icon.alpha==1,"side tab state/icon changed")
    for _,tab in ipairs({LFGParentFrame.ListingTab,LFGParentFrame.BrowsingTab,LFGParentFrame.WhoListingTab}) do
        assert(not tab.border and tab.Background.alpha==0,'extra group-finder tab surround remains')
        assert(tab.Icon.mask==tab.Mask and tab.Mask.alpha==1 and tab.Mask.atlas=='native-clipped' and tab.SelectedTexture.atlas=='native-selected' and tab.TabGlow.alpha==1,'native tab mask/selection/glow changed')
    end
    assert(not LFGBrowseFrame.SendMessageButton.enabled and originalAction==LFGBrowseFrame.SendMessageButton.OnClick,"native action or disabled state replaced")
    assert(role.Icon.alpha==1 and role.cover.alpha==1 and role.CheckButton.checked,"role icons/availability/selection changed")
    assert(activity.InstanceLockWarningIcon.Icon.alpha==1 and activity.CheckButton.checked,"activity lock/selection changed")
    assert(category.Icon.alpha==1 and category.Label.font,"category identity lost")
    assert(comment.EditBox.securityDisableSetText and comment.EditBox.securityDisablePaste,"comment security changed")
    assert(comment.ScrollBar.ScrollUpButton.Icon.alpha==1 and comment.ScrollBar.ScrollDownButton.Icon.alpha==1,"legacy comment arrows removed")
    assert(result.ClassIcon.alpha==1 and result.NewPlayerFriendlyIcon.alpha==1 and not result.Selected.shown,"result icons/state lost")
    assert(result.Name.color[1]==.3 and result.ActivityName.color[1]==.3 and who.Class.color[1]==.3,"semantic text colors changed")
    assert(result.DataDisplay.RoleCount.TankCount.value==7 and result.DataDisplay.RoleCount.TankIcon.alpha==1,"role count or glyph changed")
    assert(LFGBrowseFrame.RefreshButton.Icon.alpha==1 and LFGBrowseFrame.ActivityDropdown.ResetButton.Icon.alpha==1 and LFGBrowseFrame.SearchingSpinner.shown,"filter/search affordance lost")
    for _,dropdown in ipairs({LFGBrowseFrame.CategoryDropdown,LFGBrowseFrame.ActivityDropdown,LFGListingFrame.GroupRoleButtons.RoleDropdown}) do
        assert(dropdown.Text.font and dropdown.Text.color[1]==.3 and dropdown.Text.text=="native","dropdown label font/color/text regression")
    end
    assert(LFGBrowseFrame.SearchingSpinner.Label.font and LFGBrowseFrame.SearchingSpinner.Label.color[1]==.9,"search progress label not themed")
    assert(LFGBrowseFrame.ScrollBar.Forward.Texture.alpha==.35,"disabled arrow alpha changed")
    assert(LFGWhoListFrame.EditBox.searchIcon.alpha==1 and LFGWhoListFrame.WhoSearch.Icon.alpha==1,"Who action glyph removed")
    assert(LFGParentFrame.width==458 and LFGWhoListFrame.parent=="native" and not LFGWhoListFrame.shown,"layout or visibility changed")
    assert(member.Role.alpha==1 and member.Name.color[1]==.3 and member.Name.font,"tooltip member state changed")
    local later=frame(); later.Name=texture(); later.ResultBG=texture()
    LFGBrowseFrame.ScrollBox.initialize(later)
    assert(later.Name.font and later.ResultBG.fill,"later result not themed")
    local laterWho=frame(); laterWho.Class=texture()
    LFGWhoListFrame.ScrollBox.initialize(laterWho); assert(laterWho.Class.font,"later Who row not themed")
    local laterActivity=frame(); laterActivity.CheckButton=frame()
    LFGListingFrame.ActivityView.ScrollBox.initialize(laterActivity); assert(laterActivity.CheckButton.checkSkin,"later activity not themed")
    local lateMember={Name=texture(),Level=texture(),Role=texture()}
    LFGBrowseSearchEntryTooltip.memberPool.active={lateMember}
    LFGBrowseSearchEntryTooltip_UpdateAndShow(LFGBrowseSearchEntryTooltip)
    assert(lateMember.Name.font and lateMember.Role.alpha==1,"pooled tooltip member not themed")
    LFGParentFrame.hooks.OnShow(); LFGParentFrame:UpdateTabs()
    style="off"; result.ResultBG.fill={"sentinel"}; LFGBrowseSearchEntry_Update(result)
    assert(result.refreshes==1 and result.ResultBG.fill[1]=="sentinel","off-style native refresh altered")
end
''')
source = SOURCE.read_text(encoding="utf-8")
lua.execute('assert(loadstring(...))("EllesmereUIBlizzardSkin", NS)', source)
lua.eval("VerifyGroupFinder")()
retail = LuaRuntime()
retail.execute('EUI_FOREVER=false; assert(loadstring(...))()', source)
print("Group Finder: Lua 5.1, LoD/style gates, three native pages, handlers/layout/visibility, comment security, icons/colors/roles, dynamic rows/tooltips and scroll arrows passed")
