-- Local Forever port bootstrap; loaded before libraries and migrations.
if not EUI_FOREVER then return end

EUI_FOREVER_VERSION = "0.4.0"
EUI_FOREVER_STATUS = { errors = {}, aliases = {}, errorIndex = {}, errorCounts = {}, errorSites = {} }
local status = EUI_FOREVER_STATUS

-- Forever's Blizzard_DeprecatedSpecialization TOC excludes Camelot. Restore
-- only exact native aliases used by this suite, only when the old name is absent.
-- No fake spec IDs, secret-value bypasses, or fabricated API return values.
for _, name in ipairs({ "GetSpecialization", "GetSpecializationInfo",
    "GetActiveSpecGroup", "GetNumSpecializationsForClassID" }) do
    if not _G[name] and C_SpecializationInfo and C_SpecializationInfo[name] then
        _G[name] = C_SpecializationInfo[name]
        status.aliases[#status.aliases + 1] = name
    end
end

-- Exact C_Item aliases: Forever does not load the Retail deprecated wrappers.
for _, name in ipairs({ "GetItemInfo", "GetItemInfoInstant",
    "GetItemQualityColor", "IsEquippableItem" }) do
    if not _G[name] and C_Item and C_Item[name] then
        _G[name] = C_Item[name]
        status.aliases[#status.aliases + 1] = name
    end
end

-- Preserve the normal error handler, while keeping the first suite failures
-- available as copyable text even if initialization stops partway through.
if geterrorhandler and seterrorhandler then
    local previous = geterrorhandler()
    local function PublicErrorText(value)
        -- Stack traces and error messages can both be secret in tainted calls.
        -- Test before indexing, concatenating, converting or using as a key.
        if issecretvalue and issecretvalue(value) then return "<protected>" end
        if type(value) == "string" then return value end
        return "<non-string diagnostic>"
    end
    local function CaptureError(err)
        local message = PublicErrorText(err)
        local stack = ""
        if debugstack then stack = PublicErrorText(debugstack(3, 12, 0)) end
        if (message:find("Ellesmere", 1, true) or stack:find("Ellesmere", 1, true))
            then
            local index = status.errorIndex[message]
            if index then
                status.errorCounts[index] = status.errorCounts[index] + 1
            elseif #status.errors < 50 then
                index = #status.errors + 1
                status.errorIndex[message] = index
                status.errorCounts[index] = 1
                status.errors[index] = message .. "\n" .. stack
                status.errorSites[index] = {}
            end
            local site = stack:match("(%[Interface/AddOns/Ellesmere[^\n]+)")
            if index and site then status.errorSites[index][site] = true end
        end
    end
    seterrorhandler(function(err)
        -- Diagnostic collection must never mask the original error, even if
        -- a beta getter throws. Forward the untouched value to the native UI.
        pcall(CaptureError, err)
        if previous then return previous(err) end
    end)
end

local function Present(value)
    return value and "available" or "MISSING"
end

-- Read-only UI evidence helps distinguish a loaded patch from files merely
-- installed on disk. Never load windows, change filters or inspect secret data.
local function DiagnosticValue(value)
    if issecretvalue and issecretvalue(value) then return "<protected>" end
    return tostring(value)
end
local function SocialEvidence(lines)
    local function Geometry(label, frame, isTab)
        if not frame then return end
        local details = { label, "shown=" .. DiagnosticValue(frame:IsShown()) }
        if frame.IsVisible then details[#details+1] = "visible=" .. DiagnosticValue(frame:IsVisible()) end
        local tabID = isTab and (frame.GetTabID or frame.GetID)
        if tabID then details[#details+1] = "id=" .. DiagnosticValue(tabID(frame)) end
        if frame.GetAlpha then details[#details+1] = "alpha=" .. DiagnosticValue(frame:GetAlpha()) end
        if frame.GetFrameLevel then details[#details+1] = "level=" .. DiagnosticValue(frame:GetFrameLevel()) end
        if frame.GetRect then
            local x,y,w,h = frame:GetRect()
            details[#details+1] = "rect=" .. DiagnosticValue(x) .. "," .. DiagnosticValue(y)
                .. "," .. DiagnosticValue(w) .. "," .. DiagnosticValue(h)
        end
        lines[#lines+1] = table.concat(details, " ")
    end
    if not FriendsFrame then return end
    Geometry("Social window", FriendsFrame)
    if BNConnected then lines[#lines+1] = "Social Battle.net connected=" .. DiagnosticValue(BNConnected()) end
    if C_SocialRestrictions and C_SocialRestrictions.IsFriendsDisabled then
        lines[#lines+1] = "Social friends restricted=" .. DiagnosticValue(C_SocialRestrictions.IsFriendsDisabled())
    end
    if C_FriendList and C_FriendList.IsLegacyFriendSystemEnabled then
        lines[#lines+1] = "Social legacy friend system=" .. DiagnosticValue(C_FriendList.IsLegacyFriendSystemEnabled())
    end
    lines[#lines+1] = "Social selected bottom tab=" .. DiagnosticValue(FriendsFrame.selectedTab)
    for _, key in ipairs({ "FriendsFrameTab1", "FriendsFrameTab2", "FriendsFrameTab3", "FriendsFrameTab4",
        "FriendsListFrame", "RecentAlliesFrame", "RecruitAFriendFrame", "RaidFrame", "QuickJoinFrame" }) do
        Geometry(key, _G[key], key:match("^FriendsFrameTab%d+$") ~= nil)
    end
    local list = FriendsListFrame
    local scroll = list and list.ScrollBox
    Geometry("Social scroll", scroll)
    Geometry("Social unavailable notice", list and list.FriendsDisabledText)
    local bnet = FriendsFrameBattlenetFrame
    Geometry("Social Battle.net unavailable label", bnet and bnet.UnavailableLabel)
    Geometry("Social Battle.net unavailable help", bnet and bnet.UnavailableInfoFrame)
    local provider = scroll and scroll.GetDataProvider and scroll:GetDataProvider()
    if provider and provider.GetSize then
        -- Only row count, never friend names, IDs, notes, status text or messages.
        lines[#lines+1] = "Social native provider rows=" .. DiagnosticValue(provider:GetSize())
    end
    if scroll and scroll.EnumerateFrames then
        for _, row in scroll:EnumerateFrames() do Geometry("Social first rendered row", row); break end
    end
    local header = FriendsTabHeader
    local system = header and header.TabSystem
    if system and system.GetTabButton then
        for _, key in ipairs({ "friendsTabID", "recentAlliesTabID", "recruitAFriendTabID" }) do
            if header[key] then Geometry("Social header " .. key, system:GetTabButton(header[key]), true) end
        end
    end
end
local function WindowEvidence(lines)
    local modules = EllesmereUI and EllesmereUI._ModuleNS
    local skin = modules and modules.EllesmereUIBlizzardSkin
    local state = skin and skin.WSkin and skin.WSkin.FFD
    for _, name in ipairs({ "CharacterFrame", "InspectFrame" }) do
        local frame = _G[name]
        local portrait = frame and frame.PortraitContainer
        if portrait then
            local data = state and state[frame]
            local border = data and data.atlasBorderFrame
            lines[#lines+1] = name .. " portrait levels: window=" .. DiagnosticValue(frame:GetFrameLevel())
                .. " portrait=" .. DiagnosticValue(portrait:GetFrameLevel())
                .. " border=" .. DiagnosticValue(border and border:GetFrameLevel())
            for _, entry in ipairs({ {"container", portrait}, {"image", portrait.portrait}, {"mask", portrait.CircleMask} }) do
                local region = entry[2]
                if region and region.GetRect then
                    local x, y, width, height = region:GetRect()
                    lines[#lines+1] = name .. " portrait " .. entry[1] .. " rect="
                        .. DiagnosticValue(x) .. "," .. DiagnosticValue(y) .. ","
                        .. DiagnosticValue(width) .. "," .. DiagnosticValue(height)
                end
            end
        end
    end
    local tracker = _G.ObjectiveTrackerFrame
    if tracker then
        local point, relative, relPoint, x, y = tracker:GetPoint(1)
        lines[#lines+1] = "Tracker: " .. DiagnosticValue(point) .. " relative "
            .. DiagnosticValue(relative and relative:GetName()) .. " " .. DiagnosticValue(relPoint)
            .. " " .. DiagnosticValue(x) .. "," .. DiagnosticValue(y)
    end
    local menu = _G.MicroMenu
    if menu then
        local buttons = {}
        for _, button in ipairs({menu:GetChildren()}) do
            if button.layoutIndex and button.GetNormalTexture then
                buttons[#buttons+1] = DiagnosticValue(button:GetName())
                    .. " shown=" .. DiagnosticValue(button:IsShown())
                    .. " enabled=" .. DiagnosticValue(button:IsEnabled())
            end
        end
        lines[#lines+1] = "Native menu: " .. table.concat(buttons, "; ")
    end
    local journal = _G.CollectionsJournal
    if journal and journal.TabContainer then
        local tabs = {}
        for _, tab in ipairs(journal.TabContainer.Tabs or {}) do
            tabs[#tabs+1] = DiagnosticValue(tab:GetID()) .. " shown=" .. DiagnosticValue(tab:IsShown())
        end
        lines[#lines+1] = "Collections tabs: " .. table.concat(tabs, "; ")
        if GetCVarBool then
            lines[#lines+1] = "Collections collected-only: " .. DiagnosticValue(GetCVarBool("onlyShowCollectedItemsInJournal"))
        end
    end
end

local function Report()
    local version, build, _, iface = GetBuildInfo()
    local lines = {
        "EllesmereUI Forever " .. EUI_FOREVER_VERSION,
        "Upstream: 9.3 (verified official release); local customization layer 0.4.0",
        "Client: " .. tostring(version) .. " build " .. tostring(build) .. " interface " .. tostring(iface),
        "Project ID: " .. tostring(WOW_PROJECT_ID),
        "Profile: " .. tostring(EllesmereUIDB and EllesmereUIDB.activeProfile),
        "Action bars: " .. tostring(status.actionBars or "upstream custom buttons"),
        "Group frames: " .. tostring(status.groupFrames or "upstream custom headers"),
        "Group finder: " .. tostring(status.groupFinder or "not opened / disabled"),
        "Character: " .. tostring(status.character or "not skinned / disabled"),
        "Inspect: " .. tostring(status.inspect or "not opened / disabled"),
        "Legacy: " .. tostring(status.legacy or "not opened / disabled"),
        "Spellbook: " .. tostring(status.spellbook or "not opened / disabled"),
        "Professions: " .. tostring(status.professions or "not opened / disabled"),
        "Bank: " .. tostring(status.bank or "not skinned / disabled"),
        "Import: " .. tostring(status.import or "not staged"),
        "Specialization API: " .. Present(C_SpecializationInfo and C_SpecializationInfo.GetSpecialization),
        "Aura API: " .. Present(C_UnitAuras),
        "Aura container utilities: " .. Present(C_AuraContainerUtil),
        "Cooldown viewer: " .. Present(C_CooldownViewer),
        "Damage meter: " .. Present(C_DamageMeter),
        "Secret values: " .. Present(issecretvalue),
        "Compatibility aliases: " .. table.concat(status.aliases, ", "),
        "Excluded Retail features: Mythic+ Tools/portals, keystone sharing, Skyriding HUD, Great Vault, crest upgrader",
    }
    if GetSpecialization and GetSpecializationInfo then
        local ok, spec = pcall(GetSpecialization)
        if ok and spec and spec > 0 then
            local infoOK, id, name = pcall(GetSpecializationInfo, spec)
            if infoOK then lines[#lines + 1] = "Spec: " .. tostring(id) .. " / " .. tostring(name) end
        end
    end
    if C_AddOns and C_AddOns.GetNumAddOns then
        for i = 1, C_AddOns.GetNumAddOns() do
            local name = C_AddOns.GetAddOnInfo(i)
            if name and name:find("^Ellesmere") then
                lines[#lines + 1] = name .. ": " .. (C_AddOns.IsAddOnLoaded(name) and "loaded" or "not loaded")
            end
        end
    end
    lines[#lines + 1] = "Captured suite errors: " .. #status.errors
    for i, err in ipairs(status.errors) do
        lines[#lines + 1] = "\nError " .. i .. " (" .. status.errorCounts[i] .. " occurrences):\n" .. err
        for site in pairs(status.errorSites[i]) do lines[#lines + 1] = "Caller: " .. site end
    end
    if status.ActionBarReport then lines[#lines + 1] = status.ActionBarReport() end
    local evidenceOK, evidenceError = pcall(WindowEvidence, lines)
    if not evidenceOK then lines[#lines+1] = "UI diagnostic unavailable: " .. tostring(evidenceError) end
    local socialOK, socialError = pcall(SocialEvidence, lines)
    if not socialOK then lines[#lines+1] = "Social evidence unavailable: " .. tostring(socialError) end
    local skinNS = EllesmereUI and EllesmereUI._ModuleNS and EllesmereUI._ModuleNS.EllesmereUIBlizzardSkin
    if skinNS and skinNS.ForeverEquipmentEvidence then
        local gearOK, gearError = pcall(skinNS.ForeverEquipmentEvidence, lines)
        if not gearOK then lines[#lines+1] = "Equipment evidence unavailable: " .. tostring(gearError) end
    end
    if skinNS and skinNS.ForeverItemLevelEvidence then
        local averageOK, averageError = pcall(skinNS.ForeverItemLevelEvidence, lines)
        if not averageOK then lines[#lines+1] = "Item-level evidence unavailable: " .. tostring(averageError) end
    end
    local namesNS = EllesmereUI and EllesmereUI._ModuleNS and EllesmereUI._ModuleNS.EllesmereUINameplates
    if namesNS and namesNS.ForeverFriendlyEvidence then
        local namesOK, namesError = pcall(namesNS.ForeverFriendlyEvidence, lines)
        if not namesOK then lines[#lines+1] = "Friendly-name evidence unavailable: " .. tostring(namesError) end
    end
    local unitNS = EllesmereUI and EllesmereUI._ModuleNS and EllesmereUI._ModuleNS.EllesmereUIUnitFrames
    if unitNS and unitNS.ForeverPredictionEvidence then
        local predictionOK, predictionError = pcall(unitNS.ForeverPredictionEvidence, lines)
        if not predictionOK then lines[#lines+1] = "Incoming-heal evidence unavailable: " .. tostring(predictionError) end
    end
    if status.LayoutTraceReport then lines[#lines+1] = status.LayoutTraceReport() end
    return table.concat(lines, "\n")
end

local function ShowReport()
    if not status.window then
        local f = CreateFrame("Frame", "EUIForeverReport", UIParent, "BackdropTemplate")
        f:SetSize(700, 480)
        f:SetPoint("CENTER")
        f:SetFrameStrata("DIALOG")
        f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8X8", edgeFile = "Interface\\Buttons\\WHITE8X8", edgeSize = 1 })
        f:SetBackdropColor(0.04, 0.05, 0.06, 0.98)
        f:SetBackdropBorderColor(0.05, 0.82, 0.62, 1)
        f:EnableMouse(true)
        local title = f:CreateFontString(nil, "OVERLAY", "GameFontNormal")
        title:SetPoint("TOPLEFT", 16, -14)
        title:SetText("EllesmereUI Forever report - Ctrl+C to copy, Escape to close")
        local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
        close:SetPoint("TOPRIGHT")
        local scroll = CreateFrame("ScrollFrame", nil, f, "UIPanelScrollFrameTemplate")
        scroll:SetPoint("TOPLEFT", 16, -42)
        scroll:SetPoint("BOTTOMRIGHT", -34, 16)
        local edit = CreateFrame("EditBox", nil, scroll)
        edit:SetMultiLine(true)
        edit:SetFontObject(ChatFontNormal)
        edit:SetWidth(640)
        edit:SetAutoFocus(false)
        edit:SetMaxLetters(0)
        edit:SetScript("OnEscapePressed", function() f:Hide() end)
        scroll:SetScrollChild(edit)
        f.edit = edit
        status.window = f
        table.insert(UISpecialFrames, "EUIForeverReport")
    end
    status.window:Show()
    status.window.edit:SetText(Report())
    status.window.edit:SetFocus()
    status.window.edit:HighlightText()
end

-- Keep five bounded error-bearing checkpoints across clean reloads. The game
-- alone writes SavedVariables; agents read these literal strings as data.
local function SaveReport()
    if not EllesmereUIDB then return end
    local report = Report()
    EllesmereUIDB._foreverLastReport = report
    if #status.errors == 0 then return end
    local history = EllesmereUIDB._foreverErrorReports
    if type(history) ~= "table" then history = {}; EllesmereUIDB._foreverErrorReports = history end
    local snapshot = report:sub(1, 32768)
    if history[#history] ~= snapshot then history[#history + 1] = snapshot end
    while #history > 5 do table.remove(history, 1) end
end
status.SaveReport = SaveReport

SLASH_EUIFOREVER1 = "/euiforever"
SlashCmdList.EUIFOREVER = function(message)
    local traceCommand = message and message:match("^trace%s*(.*)$")
    if traceCommand and status.LayoutTraceCommand then
        status.LayoutTraceCommand(traceCommand)
        return
    end
    if message and message:match("^save%s*$") then
        if EllesmereUIDB then
            SaveReport()
            print("EllesmereUI Forever: report staged in saved settings; /reload writes it to disk.")
        end
        return
    end
    ShowReport()
end
status.Report = Report

-- Save at the normal game checkpoint, never overwrite WTF files externally.
-- Deduplication keeps repeated secure-handler failures from obscuring other bugs.
local persist = CreateFrame("Frame")
persist:RegisterEvent("PLAYER_LOGOUT")
persist:SetScript("OnEvent", function()
    SaveReport()
end)

local login = CreateFrame("Frame")
login:RegisterEvent("PLAYER_LOGIN")
login:SetScript("OnEvent", function(self)
    self:UnregisterAllEvents()
    print("|cff0cd29fEllesmereUI Forever " .. EUI_FOREVER_VERSION .. "|r: experimental port loaded. /euiforever opens a copyable diagnostic report.")
end)
