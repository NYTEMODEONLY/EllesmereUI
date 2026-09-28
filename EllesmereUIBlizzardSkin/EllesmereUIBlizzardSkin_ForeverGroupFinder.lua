-- Forever loads Blizzard_GroupFinder_VanillaStyle, not Retail's PVEFrame.
-- All actions, list data, role availability and protected comment text remain
-- native. Named decoration only; never sweep icons or inspect search-result data.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T = W.Theme
local KEY = "lfg" -- existing reskinLFGMenu option / imported window style
local state = setmetatable({}, { __mode = "k" })
local globalHooks = {}
local function Data(frame)
    if not state[frame] then state[frame] = {} end
    return state[frame]
end
local function HookGlobal(name, fn)
    if globalHooks[name] or type(_G[name]) ~= "function" then return end
    hooksecurefunc(name, W.WindowCallback(KEY, fn))
    globalHooks[name] = true
end
local function Hook(frame, method, fn)
    if not frame or type(frame[method]) ~= "function" then return end
    local d = Data(frame)
    if d[method] then return end
    hooksecurefunc(frame, method, W.WindowCallback(KEY, fn))
    d[method] = true
end
local function Flat(texture, r, g, b, a)
    if texture and texture.SetColorTexture then texture:SetColorTexture(r, g, b, a or 1) end
end
local function Font(fs) W.Font(fs) end -- class, delisted, unavailable colors stay native
local function Label(fs) W.Font(fs, 0.9, 0.9, 0.9) end
local function Fill(frame)
    if not frame then return end
    local d = Data(frame)
    if not d.fill then
        d.fill = frame:CreateTexture(nil, "BACKGROUND", nil, -7)
        d.fill:SetAllPoints(frame)
    end
    Flat(d.fill, T.insetR, T.insetG, T.insetB, T.insetA)
    W.AddBorder(frame)
end
local function TextButton(button)
    if not button then return end
    W.Button(button)
    W.StateButtonLabel(button)
    Font(button.Text or (button.GetFontString and button:GetFontString()))
end
local function Checkbox(button)
    if not button then return end
    W.Checkbox(button, { stockCheck = true })
end
local function Input(box)
    if not box then return end
    Fill(box)
    for _, key in ipairs({ "Left", "Middle", "Right", "Mid", "Backdrop" }) do
        local texture = box[key]
        if texture and texture.SetAlpha then texture:SetAlpha(0) end
    end
    Font(box)
    Font(box.Instructions)
    -- No SetText, focus, security, paste or script changes, including Comments.
end
local function ScrollBar(bar)
    if not bar then return end
    if bar.ThumbTexture then
        -- Comment uses legacy UIPanelScrollBarTemplate, with texture thumb
        -- and ScrollUp/DownButton glyphs rather than MinimalScrollBar frames.
        Flat(bar.ThumbTexture, 0.7, 0.7, 0.7, 0.65)
        return
    end
    local arrows = {}
    for _, key in ipairs({ "Back", "Forward" }) do
        local button = bar[key]
        if button and button.Texture then arrows[#arrows + 1] = { button.Texture, button.Texture:GetAlpha() } end
    end
    W.ScrollBar(bar)
    for _, arrow in ipairs(arrows) do arrow[1]:SetAlpha(arrow[2]) end
end
local function SideTab(tab)
    if not tab then return end
    -- Keep native clipped-corner icons and selection; omit the outer square.
    if tab.Background then tab.Background:SetAlpha(0) end
    for _, key in ipairs({ "SelectedTexture", "TabGlow", "HighlightTexture" }) do
        if tab[key] then tab[key]:SetVertexColor(T.accR, T.accG, T.accB) end
    end
end
local function Page(frame)
    if not frame then return end
    W.Shell(KEY, frame, { noTopBar = true })
    if frame.Inset then W.Inset(frame.Inset) end
    Label(frame.TitleContainer and frame.TitleContainer.TitleText)
end
local function Pool(pool, fn)
    if pool and pool.EnumerateActive then
        for frame in pool:EnumerateActive() do fn(frame) end
    end
end
local function WatchRows(box, painter)
    if not box then return end
    local d = Data(box)
    if not d.rows and ScrollUtil and ScrollUtil.AddInitializedFrameCallback then
        ScrollUtil.AddInitializedFrameCallback(box, W.WindowCallback(KEY, function(_, row) painter(row) end), box, false)
        d.rows = true
    end
    if box.ForEachFrame then box:ForEachFrame(painter) end
end
local function Category(button)
    -- Category artwork is an activity identity; preserve Icon and selection.
    Fill(button)
    if button.Cover then button.Cover:SetAlpha(0) end
    Label(button.Label)
    if button.SelectedTexture then button.SelectedTexture:SetVertexColor(T.accR, T.accG, T.accB) end
end
local function Categories(view)
    if not view then return end
    for _, button in ipairs(view.CategoryButtons or {}) do Category(button) end
end
local function Activity(row)
    Font(row.Level)
    Font(row.NameButton and row.NameButton.Name)
    Checkbox(row.CheckButton)
    -- Native normal/pushed expand glyphs, InstanceLockWarningIcon and its
    -- tooltip stay intact. The row's selection checkbox remains authoritative.
    Fill(row.ExpandOrCollapseButton)
end
local function Locked(view)
    if not view then return end
    Font(view.ErrorText)
    Label(view.ActivityText)
    Pool(view.framePool, function(row) Font(row.Text) end)
end
local function Listing(frame)
    if not frame then return end
    Page(frame)
    -- RolesSection's only region is its blue decorative backdrop in native XML.
    if frame.RolesSection then W.Panel(frame.RolesSection, { inset = true }) end
    TextButton(frame.BackButton)
    TextButton(frame.PostButton)
    Fill(frame.OptionsButton) -- cog is an action glyph, not generic dropdown art
    local solo = frame.SoloRoleButtons
    for _, role in ipairs(solo and solo.RoleButtons or {}) do
        Flat(role.Background, 0.035, 0.035, 0.035, 0.8)
        Checkbox(role.CheckButton)
        -- role's normal texture is the role icon; cover encodes disabled state.
    end
    local group = frame.GroupRoleButtons
    if group then
        TextButton(group.RolePollButton)
        W.Dropdown(group.RoleDropdown)
        Font(group.RoleDropdown and group.RoleDropdown.Text)
        Font(group.Label)
    end
    if frame.NewPlayerFriendlyButton then Checkbox(frame.NewPlayerFriendlyButton.CheckButton) end
    Categories(frame.CategoryView)
    local activity = frame.ActivityView
    if activity then
        ScrollBar(activity.ScrollBar)
        WatchRows(activity.ScrollBox, Activity)
        Flat(activity.BarMiddle, T.brdR, T.brdG, T.brdB, 0.7)
        if activity.Comment then
            Fill(activity.Comment)
            for _, key in ipairs({ "TopLeftTex", "TopRightTex", "TopTex", "BottomLeftTex", "BottomRightTex", "BottomTex", "LeftTex", "RightTex", "MiddleTex" }) do
                if activity.Comment[key] then activity.Comment[key]:SetAlpha(0) end
            end
            Input(activity.Comment.EditBox)
            Font(activity.Comment.Instructions)
            ScrollBar(activity.Comment.ScrollBar)
        end
    end
    Locked(frame.LockedView)
end
local function BrowseRow(row)
    Flat(row.ResultBG, T.insetR, T.insetG, T.insetB, 0.9)
    Flat(row.Selected, T.accR, T.accG, T.accB, 0.18)
    Flat(row.Highlight, 1, 1, 1, 0.08)
    Font(row.Name)
    Font(row.Level)
    Font(row.ActivityName)
    Label(row.CategoryLabel)
    local display = row.DataDisplay
    if display then
        Font(display.Comment)
        Label(display.Solo and display.Solo.RolesText)
        Font(display.PlayerCount and display.PlayerCount.Count)
        if display.RoleCount then
            for _, key in ipairs({ "TankCount", "HealerCount", "DamagerCount" }) do Font(display.RoleCount[key]) end
        end
        -- Delist is an icon button; preserve the X and all native role arrays.
        Fill(display.DelistButton)
    end
    -- Keep ClassIcon, PartyIcon, NewPlayerFriendlyIcon, collapse/expand icons,
    -- role counts, desaturation and selected visibility. Do not read resultID.
end
local function Browse(frame)
    if not frame then return end
    Page(frame)
    W.Dropdown(frame.CategoryDropdown)
    W.Dropdown(frame.ActivityDropdown)
    -- WowStyle1DropdownTemplate stores its selection label in Text. Font-only
    -- writes leave native selection/disabled colors and selected text intact.
    Font(frame.CategoryDropdown and frame.CategoryDropdown.Text)
    Font(frame.ActivityDropdown and frame.ActivityDropdown.Text)
    Fill(frame.RefreshButton)
    Fill(frame.OptionsButton)
    TextButton(frame.SendMessageButton)
    TextButton(frame.GroupInviteButton)
    Font(frame.NoResultsFound)
    Label(frame.SearchingSpinner and frame.SearchingSpinner.Label)
    ScrollBar(frame.ScrollBar)
    WatchRows(frame.ScrollBox, BrowseRow)
end
local function WhoRow(row)
    Flat(row.Background, T.insetR, T.insetG, T.insetB, 0.9)
    Flat(row.Selected, T.accR, T.accG, T.accB, 0.18)
    for _, key in ipairs({ "Name", "Level", "Race", "Class", "Variable", "GuildName" }) do Font(row[key]) end
    Hook(row, "InitButton", WhoRow)
end
local function Who(frame)
    if not frame then return end
    Page(frame)
    Flat(frame.headerBackground, T.insetR, T.insetG, T.insetB, 0.9)
    if frame.insideFrame then frame.insideFrame:SetAlpha(0) end
    Input(frame.EditBox)
    Fill(frame.WhoSearch) -- preserve refresh/search glyph and user command
    Font(frame.WhoFrameTotals)
    ScrollBar(frame.ScrollBar)
    WatchRows(frame.ScrollBox, WhoRow)
end
local function TooltipMember(frame)
    Font(frame.Name)
    Font(frame.Level)
end
local function Tooltip(frame)
    if not frame then return end
    -- This is a custom tooltip, not GameTooltip. Its colored warnings, class
    -- names and native member/role/icon structure are deliberately preserved.
    if frame.SetBackdropColor then frame:SetBackdropColor(T.bgR, T.bgG, T.bgB, 0.98) end
    if frame.SetBackdropBorderColor then frame:SetBackdropBorderColor(T.brdR, T.brdG, T.brdB, 1) end
    for _, key in ipairs({ "Delisted", "NewPlayerFriendlyText", "Comment", "MemberCount", "CompletedEncounterHeader" }) do Font(frame[key]) end
    if frame.Leader then TooltipMember(frame.Leader) end
    Pool(frame.memberPool, TooltipMember)
    Pool(frame.activityPool, Font)
    Pool(frame.completedEncounterPool, Font)
end
local function Apply()
    local frame = LFGParentFrame
    if not frame then return end
    W.ResolveTheme()
    W.Shell(KEY, frame, { noTopBar = true })
    W.CloseButton(frame.CloseButton or LFGParentFrameCloseButton)
    for _, key in ipairs({ "ListingTab", "BrowsingTab", "WhoListingTab" }) do SideTab(frame[key]) end
    Listing(LFGListingFrame)
    Browse(LFGBrowseFrame)
    Who(LFGWhoListFrame)
    Tooltip(LFGBrowseSearchEntryTooltip)
    for _, page in ipairs({ frame, LFGListingFrame, LFGBrowseFrame, LFGWhoListFrame }) do
        local d = Data(page)
        if not d.shownHook then
            page:HookScript("OnShow", W.WindowCallback(KEY, Apply))
            d.shownHook = true
        end
    end
    Hook(frame, "UpdateTabs", function()
        for _, key in ipairs({ "ListingTab", "BrowsingTab", "WhoListingTab" }) do SideTab(frame[key]) end
    end)
    HookGlobal("LFGListingCategorySelection_UpdateCategoryButtons", Categories)
    HookGlobal("LFGListingActivityView_InitActivityGroupButton", Activity)
    HookGlobal("LFGListingActivityView_InitActivityButton", Activity)
    HookGlobal("LFGListingLockedView_RefreshContent", Locked)
    HookGlobal("LFGBrowseSearchEntry_Update", BrowseRow)
    HookGlobal("LFGBrowseSearchEntryTooltip_UpdateAndShow", Tooltip)
    if EUI_FOREVER_STATUS then EUI_FOREVER_STATUS.groupFinder = "Forever Listing, Browse and Who; native roles, activities and actions" end
end

local ApplyWindow = W.WindowCallback(KEY, Apply)
W.RegisterWindow({ key = KEY, addons = { Blizzard_GroupFinder_VanillaStyle = true }, apply = ApplyWindow })
W.OnLooksChanged(ApplyWindow)
ns.ForeverGroupFinder = ApplyWindow
