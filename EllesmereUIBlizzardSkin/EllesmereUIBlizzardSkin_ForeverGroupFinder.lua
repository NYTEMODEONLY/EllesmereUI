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
    -- Native boxes are 24 and 30 wide on 22-high rows: one inset box, or the
    -- frame-sized borders overlap down the activity list.
    W.Checkbox(button, { stockCheck = true, boxInset = true })
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
    -- Single-line inputs only: the box is the EditBox itself. No SetText,
    -- focus, security, paste or script changes.
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
local COMMENT_ART = { "TopLeftTex", "TopRightTex", "TopTex", "BottomLeftTex", "BottomRightTex", "BottomTex", "LeftTex", "RightTex", "MiddleTex" }
local function CommentBox(scroll)
    if not scroll then return end
    -- UIPanelInputScrollFrameTemplate: the ScrollFrame is the visible box and
    -- its EditBox is a single text line inside it, so a box on each drew two
    -- outlines. One box only, on our own frame at the extent of the native
    -- border art (5 outside the ScrollFrame), which keeps the text's padding.
    local d = Data(scroll)
    if not d.box then
        local box = CreateFrame("Frame", nil, scroll)
        box:SetPoint("TOPLEFT", scroll, "TOPLEFT", -5, 5)
        box:SetPoint("BOTTOMRIGHT", scroll, "BOTTOMRIGHT", 5, -5)
        box:SetFrameLevel(scroll:GetFrameLevel())
        d.box = box
    end
    Fill(d.box)
    for _, key in ipairs(COMMENT_ART) do
        if scroll[key] then scroll[key]:SetAlpha(0) end
    end
    local edit = scroll.EditBox
    Font(edit)
    Font(edit and edit.Instructions)
    Font(scroll.Instructions)
    ScrollBar(scroll.ScrollBar)
    -- No SetText, focus, security, paste or script changes on the EditBox.
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
        CommentBox(activity.Comment)
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

-- Last-equipped inspection for the hovered Forever LFG listing.
-- Kept separate from decoration: native listing actions and Inspect UI own
-- their state. No distance/visibility checks, saved player data or gear arithmetic.
do
    local cache, rows = {}, {}
    local tip, baseWidth, pending, timer, hooked, ownRequest
    local nextRequest = 0
    local Pump, Paint
    local function Plain(v) return not (issecretvalue and issecretvalue(v)) end
    local function Text(v) return Plain(v) and type(v) == "string" and v ~= "" end
    local function Number(v) return Plain(v) and type(v) == "number" and v == v and v >= 0 and v < math.huge end
    local function Read(fn, ...)
        if type(fn) == "function" then return pcall(fn, ...) end
        return false
    end
    local function Shown(frame)
        if not frame then return false end
        local ok, value = Read(frame.IsShown, frame)
        return ok and Plain(value) and value == true
    end
    local function ManualInspect()
        if InspectFrame and (InspectFrame.unit or Shown(InspectFrame)) then return true end
        local ok, inspecting = Read(PlayerSpellsFrame and PlayerSpellsFrame.IsInspecting, PlayerSpellsFrame)
        return ok and (not Plain(inspecting) or inspecting == true)
    end
    local function CancelTimer()
        if timer then timer:Cancel(); timer = nil end
    end
    local function Schedule(delay)
        if timer or not Shown(tip) then return end
        timer = C_Timer.NewTimer(delay, function() timer = nil; Pump() end)
    end
    local function Remember(name, text, lifetime)
        local now, count = GetTime(), 0
        for key, entry in pairs(cache) do
            if entry.expires <= now then cache[key] = nil else count = count + 1 end
        end
        if count >= 100 then wipe(cache) end
        cache[name] = { text = text, expires = now + lifetime }
    end
    local function Cached(name)
        local entry = cache[name]
        return entry and entry.expires > GetTime() and entry.text or nil
    end
    Paint = function()
        if not Shown(tip) then return end
        local width = baseWidth
        for _, row in ipairs(rows) do
            local value = Cached(row.name) or "Loading..."
            row.label:SetText("Equipped: " .. value)
            W.Font(row.label, W.Theme.accR, W.Theme.accG, W.Theme.accB)
            row.label:Show()
            -- All native role icons retain their anchors and colors. The extra
            -- column starts after the widest name/level/role lane, including
            -- hidden role slots, so loading/value transitions never overlap it.
            width = math.max(width, row.offset + row.label:GetStringWidth() + 40)
        end
        tip:SetWidth(width)
    end
    local function Finish(text, lifetime)
        if not pending then return end
        Remember(pending.name, text, lifetime)
        pending = nil
        Paint()
        Schedule(math.max(.05, nextRequest - GetTime()))
    end
    Pump = function()
        if not Shown(tip) then return end
        if pending then
            if GetTime() >= pending.deadline then Finish("Unavailable", 10) else Schedule(.25) end
            return
        end
        if InCombatLockdown() or ManualInspect() then Schedule(.5); return end
        if GetTime() < nextRequest then Schedule(nextRequest - GetTime()); return end
        for _, row in ipairs(rows) do
            if not Cached(row.name) then
                local ok, allowed = Read(CanInspect, row.name)
                if not ok or not Plain(allowed) or allowed ~= true
                    or type(NotifyInspect) ~= "function"
                    or not C_PaperDollInfo or type(C_PaperDollInfo.GetInspectItemLevel) ~= "function" then
                    Remember(row.name, "Unavailable", 10)
                else
                    local guidOK, guid = Read(UnitGUID, row.name)
                    pending = { name = row.name, guid = guidOK and Text(guid) and guid or nil,
                        deadline = GetTime() + 5 }
                    nextRequest = GetTime() + 1.5
                    ownRequest = true
                    local sent = Read(NotifyInspect, row.name)
                    ownRequest = false
                    if not sent then Finish("Unavailable", 10) end
                    Paint()
                    Schedule(.25)
                    return
                end
            end
        end
        Paint()
    end
    local function Matches(guid)
        if not pending or not Text(guid) then return false end
        if pending.guid then return guid == pending.guid end
        -- Some remote identities become resolvable only after the reply. Never
        -- assign the next INSPECT_READY blindly to the current hover.
        local ok, resolved = Read(UnitGUID, pending.name)
        if ok and Text(resolved) then return resolved == guid end
        if not Plain(resolved) then return false end
        -- A remote reply can carry an identity before a world unit exists.
        -- Accept only an exact native name/realm match, never a shortened name.
        local playerOK, _, _, _, _, _, name, realm = Read(GetPlayerInfoByGUID, guid)
        if not playerOK or not Text(name) or not Plain(realm) or type(realm) ~= "string" then return false end
        if realm ~= "" and pending.name == name .. "-" .. realm then return true end
        local realmOK, localRealm = Read(GetNormalizedRealmName)
        return pending.name == name and (realm == "" or (realmOK and Text(localRealm) and realm == localRealm))
    end
    local labels = setmetatable({}, { __mode = "k" })
    local function OnTooltip(frame, resultID)
        CancelTimer()
        for _, label in pairs(labels) do label:Hide() end
        rows = {}
        tip, baseWidth = frame, frame:GetWidth()
        if not Plain(resultID) or not Number(resultID) or not C_LFGList then return end
        local ok, info = Read(C_LFGList.GetSearchResultInfo, resultID)
        if not ok or not Plain(info) or type(info) ~= "table"
            or not Plain(info.isDelisted) or info.isDelisted then return end
        local count = info.numMembers
        if not Number(count) or count < 1 then return end
        local names = {}
        local function Add(info)
            if Plain(info) and type(info) == "table" and Text(info.name) then names[info.name] = true end
        end
        local leaderOK, leader = Read(C_LFGList.GetSearchResultLeaderInfo, resultID)
        if leaderOK then Add(leader) end
        if count <= 10 then
            for i = 1, count do
                local memberOK, member = Read(C_LFGList.GetSearchResultPlayerInfo, resultID, i)
                if memberOK then Add(member) end
            end
        end
        local frames = { frame.Leader }
        if frame.memberPool then
            for member in frame.memberPool:EnumerateActive() do frames[#frames + 1] = member end
        end
        local offset = 0
        for _, member in ipairs(frames) do
            if Shown(member) and member.Name and member.Level then
                local name = member.Name:GetText()
                if Text(name) and names[name] then
                    local lane = member.Name:GetWidth() + member.Level:GetStringWidth() + 82
                    offset = math.max(offset, lane)
                    local label = labels[member]
                    if not label then
                        label = member:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
                        label:SetJustifyH("LEFT")
                        label:SetWordWrap(false)
                        labels[member] = label
                    end
                    rows[#rows + 1] = { name = name, label = label, frame = member }
                end
            end
        end
        for _, row in ipairs(rows) do
            row.offset = offset
            row.label:ClearAllPoints()
            row.label:SetPoint("TOPLEFT", row.frame.Name, "TOPLEFT", offset, 0)
        end
        Paint()
        Schedule(.2) -- Skip brief cursor passes; inspect only the hovered listing.
    end
    local function Install()
        if hooked or type(LFGBrowseSearchEntryTooltip_UpdateAndShow) ~= "function"
            or not LFGBrowseSearchEntryTooltip or not C_Timer or not C_Timer.NewTimer then return end
        hooked = true
        hooksecurefunc("LFGBrowseSearchEntryTooltip_UpdateAndShow", OnTooltip)
        LFGBrowseSearchEntryTooltip:HookScript("OnHide", function()
            CancelTimer()
            rows = {}
            tip = nil
        end)
    end
    local driver = CreateFrame("Frame")
    driver:RegisterEvent("ADDON_LOADED")
    driver:RegisterEvent("INSPECT_READY")
    driver:RegisterEvent("PLAYER_REGEN_ENABLED")
    driver:SetScript("OnEvent", function(_, event, guid)
        if event == "ADDON_LOADED" then Install()
        elseif event == "PLAYER_REGEN_ENABLED" then Schedule(.2)
        elseif Matches(guid) then
            local ok, value = Read(C_PaperDollInfo and C_PaperDollInfo.GetInspectItemLevel, pending.name)
            if ok and Number(value) then Finish(string.format("%.2f", value), 60)
            else Finish("Unavailable", 10) end
        end
    end)
    -- A manual inspection or another addon's request always takes precedence.
    -- Never call ClearInspectPlayer or alter InspectFrame.unit/INSPECTED_UNIT.
    if type(NotifyInspect) == "function" then
        hooksecurefunc("NotifyInspect", function()
            if ownRequest then return end
            pending = nil
            nextRequest = GetTime() + 5
            Schedule(5)
        end)
    end
    if type(ClearInspectPlayer) == "function" then
        hooksecurefunc("ClearInspectPlayer", function() pending = nil; Schedule(.2) end)
    end
    W.OnLooksChanged(function() Paint() end)
    Install()
end
