-- Camelot character content cosmetics. All native layout and interactions stay
-- owned by Blizzard; this file only paints the documented controls and art.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T = W.Theme
local state = setmetatable({}, { __mode = "k" })
local function State(frame)
    if not state[frame] then state[frame] = {} end
    return state[frame]
end

local function Fade(texture)
    if texture and texture.SetAlpha then texture:SetAlpha(0) end
end

-- Exact decorative atlases from Camelot's XML. In particular, never sweep
-- every texture: the same templates contain resistance, currency, reward,
-- faction and equipment icons, focus indicators and selection state.
local decoration = {
    ["UI-Character-Info-GearSlot"] = true,
    ["UI-Character-Info-ScrollLine"] = true,
    ["UI-Character-Info-ScrollLine-Long"] = true,
    ["UI-Character-Info-Title"] = true,
    ["UI-Character-Info-Line-Bounce"] = true,
    ["UI-Character-Info-Line-Bounce2"] = true,
    ["UI-Character-Info-ItemLevel-Bounce"] = true,
    ["common-insideframe"] = true,
    ["common-framedivider"] = true,
}
local function DecorativeRegions(frame)
    if not frame or not frame.GetRegions then return end
    for i = 1, select("#", frame:GetRegions()) do
        local texture = select(i, frame:GetRegions())
        local atlas = texture.GetAtlas and texture:GetAtlas()
        if atlas and decoration[atlas] then Fade(texture) end
    end
end

local function Fill(frame, alpha)
    if not frame then return end
    local d = State(frame)
    if not d.fill then
        d.fill = frame:CreateTexture(nil, "BACKGROUND", nil, -7)
        d.fill:SetAllPoints(frame)
    end
    d.fill:SetColorTexture(T.insetR, T.insetG, T.insetB, alpha or 0.65)
end

local function Font(fs, heading)
    if not fs then return end
    -- Preserve native green/red/quality colors on values and descriptive text.
    if heading then
        W.Font(fs, T.accR, T.accG, T.accB)
    else
        W.Font(fs)
        -- Default UI gold is presentation, unlike explicit warning, quality,
        -- standing or stat colors. Neutralize only that exact normal color.
        if fs.GetTextColor and NORMAL_FONT_COLOR then
            local r, g, b = fs:GetTextColor()
            if not (issecretvalue and (issecretvalue(r) or issecretvalue(g) or issecretvalue(b)))
                and r and math.abs(r - NORMAL_FONT_COLOR.r) < 0.001
                and math.abs(g - NORMAL_FONT_COLOR.g) < 0.001
                and math.abs(b - NORMAL_FONT_COLOR.b) < 0.001 then
                fs:SetTextColor(0.88, 0.88, 0.88)
            end
        end
    end
end

local function ScrollBar(bar)
    if not bar then return end
    W.ScrollBar(bar)
    -- The shared Retail skin strips these visible arrow controls. Restore the
    -- native glyph regions; their mixins still select enabled/disabled atlases.
    for _, key in ipairs({ "Back", "Forward" }) do
        local button = bar[key]
        if button and button.Texture then button.Texture:SetAlpha(1) end
    end
end

local function IconControl(button)
    if not button then return end
    Fill(button, 0.8)
    W.AddBorder(button)
    -- Arrow, rotation and zoom glyphs remain native, including pushed state.
end

local function TextButton(button)
    if not button then return end
    W.Button(button)
    W.StateButtonLabel(button)
end

local function SideTabs(list)
    for _, tab in ipairs(list or {}) do
        -- The native Icon already has Camelot's trimmed-corner Mask. Keep it
        -- and its selected outline without painting a larger square behind it.
        Fade(tab.Background)
        -- SelectedTexture and TabGlow are kept as native state carriers and
        -- recolored, so checked, hover and new-content pulses all survive.
        if tab.SelectedTexture then tab.SelectedTexture:SetVertexColor(T.accR, T.accG, T.accB) end
        if tab.TabGlow then tab.TabGlow:SetVertexColor(T.accR, T.accG, T.accB) end
        if tab.HighlightTexture then tab.HighlightTexture:SetVertexColor(0.65, 0.65, 0.65) end
    end
end

local function HeaderPortrait(frame, winKey)
    local portrait = frame and frame.PortraitContainer
    local skin = W.FFD and W.FFD[frame]
    local border = skin and skin.atlasBorderFrame
    if not (portrait and border and portrait.GetFrameLevel and portrait.SetFrameLevel) then return end
    -- AtlasBorder lives on a child at window level +6. Its corner art must not
    -- draw over the native circular emblem. Preserve the portrait and CircleMask
    -- geometry/UVs; only raise a container that would otherwise be occluded.
    local minimum = border:GetFrameLevel() + 1
    if portrait:GetFrameLevel() < minimum then portrait:SetFrameLevel(minimum) end
    local d = State(portrait)
    if not d.levelHooked and frame.SetFrameLevelsFromBaseLevel then
        hooksecurefunc(frame, "SetFrameLevelsFromBaseLevel", W.WindowCallback(winKey, function()
            HeaderPortrait(frame, winKey)
        end))
        d.levelHooked = true
    end
end

local function Progress(bar)
    if not bar then return end
    -- Camelot ColoredProgressBar is a Frame with a masked Fill, not necessarily
    -- a StatusBar. Retain its fill, native values, standing colors and tooltip.
    for i = 1, select("#", bar:GetRegions()) do
        local texture = select(i, bar:GetRegions())
        if texture.GetAtlas and texture:GetAtlas() == "common-stat-bar-BG" then
            texture:SetColorTexture(0.025, 0.025, 0.025, 0.95)
        end
    end
    Font(bar.Text)
end

local function Row(row, stats)
    if not row then return end
    DecorativeRegions(row)
    Font(row.Label)
    Font(row.Value)
    Font(row.Name, row.StateIcon ~= nil)
    Font(row.Title, true)
    Font(row.Text)
    if not stats and (row.Title or (row.Background and row.Label and not row.Value and not row.Icon)) then
        Fill(row, 0.7)
        Font(row.Label, true)
    end
    local c = row.Content
    if c then
        Font(c.Name)
        Font(c.Count)
        Font(c.Value)
        Progress(c.ReputationBar)
        Progress(c.SkillsBar)
        -- Flatten only the three known highlight panels. Their native parent
        -- controls hover/selected opacity, so neither state is lost.
        local h = c.BackgroundHighlight
        if h then
            for _, key in ipairs({ "Left", "Middle", "Right" }) do
                if h[key] then h[key]:SetColorTexture(T.accR, T.accG, T.accB, 0.2) end
            end
        end
    end
    -- Category list plates are decorative; the separate +/- StateIcon stays.
    for i = 1, select("#", row:GetRegions()) do
        local texture = select(i, row:GetRegions())
        if texture.GetAtlas and texture:GetAtlas() == "common-button-list-collapseExpand" then
            local layer = texture:GetDrawLayer()
            texture:SetColorTexture(0.12, 0.12, 0.12, layer == "HIGHLIGHT" and 0.3 or 0.95)
        end
    end
end

-- Retail EUI's category palette, applied to Camelot's own categories/rows.
-- Never rebuild the provider: Classic weapon skills, Spirit, resistance icons,
-- pet stats, native conditional rows and tooltip payloads all remain native.
local statColors = {
    General = { r = 0.15, g = 0.85, b = 1 },
    Attributes = { r = 0.047, g = 0.824, b = 0.616 },
    Attack = { r = 1, g = 0.353, b = 0.122 },
    ["Secondary Stats"] = { r = 0.471, g = 0.255, b = 0.784 },
    Defense = { r = 0.247, g = 0.655, b = 1 },
    ["Tertiary Stats"] = { r = 0.859, g = 0.325, b = 0.855 },
}
local function StatColor(name)
    local key
    if name == STAT_CATEGORY_GENERAL then key = "General"
    elseif name == STAT_CATEGORY_PRIMARY_ATTRIBUTES then key = "Attributes"
    elseif name == STAT_CATEGORY_WEAPONS then key = "Attack"
    elseif name == STAT_CATEGORY_MODIFIERS then key = "Secondary Stats"
    elseif name == STAT_CATEGORY_DEFENSE then key = "Defense"
    elseif name == STAT_CATEGORY_RESISTANCE then key = "Tertiary Stats" end
    local useCustom = key and EllesmereUIDB and EllesmereUIDB.statCategoryUseColor and EllesmereUIDB.statCategoryUseColor[key]
    local custom = useCustom and EllesmereUIDB.statCategoryColors and EllesmereUIDB.statCategoryColors[key]
    return custom or (key and statColors[key]) or { r = T.accR, g = T.accG, b = T.accB }
end
local function SameColor(r, g, b, color)
    return color and math.abs(r - color.r) < 0.001 and math.abs(g - color.g) < 0.001 and math.abs(b - color.b) < 0.001
end
local function StatValue(fs, color)
    if not (fs and fs.GetTextColor) then return end
    local r, g, b, a = fs:GetTextColor()
    if issecretvalue and (issecretvalue(r) or issecretvalue(g) or issecretvalue(b)) then return end
    local d = State(fs)
    -- Only plain native values and our previous tint are presentation colors.
    -- Explicit green/red/quality colors and embedded |c strings stay intact.
    if r and g and b and (SameColor(r, g, b, { r = 1, g = 1, b = 1 })
        or SameColor(r, g, b, NORMAL_FONT_COLOR) or SameColor(r, g, b, { r = 0.88, g = 0.88, b = 0.88 })
        or SameColor(r, g, b, d.statColor)) then
        fs:SetTextColor(color.r, color.g, color.b, a)
        d.statColor = { r = color.r, g = color.g, b = color.b }
    end
end
local function StatsRow(row, data)
    if not row then return end
    data = data or (row.GetElementData and row:GetElementData())
    if not data then return end
    local d = State(row)
    if not d.statInitHooked and row.Init then
        hooksecurefunc(row, "Init", W.WindowCallback("charsheet", function(self, elementData)
            Row(self, true)
            StatsRow(self, elementData)
        end))
        d.statInitHooked = true
    end
    if data.isHeader and row.Title then
        local color = StatColor(data.name)
        W.Font(row.Title, color.r, color.g, color.b)
        if not d.statLines then
            local left = row:CreateTexture(nil, "ARTWORK")
            local right = row:CreateTexture(nil, "ARTWORK")
            left:SetPoint("LEFT", row, "LEFT", 4, 1)
            left:SetPoint("RIGHT", row.Title, "LEFT", -6, 0)
            right:SetPoint("LEFT", row.Title, "RIGHT", 6, 0)
            right:SetPoint("RIGHT", row, "RIGHT", -4, 1)
            d.statLines = { left, right }
        end
        local scale = row.GetEffectiveScale and row:GetEffectiveScale() or 1
        local perfect = EllesmereUI and EllesmereUI.PP and EllesmereUI.PP.perfect or 1
        for _, line in ipairs(d.statLines) do
            line:SetHeight(scale > 0 and perfect / scale or 1)
            line:SetColorTexture(color.r, color.g, color.b, 0.8)
            if line.SetSnapToPixelGrid then line:SetSnapToPixelGrid(false); line:SetTexelSnappingBias(0) end
        end
    elseif row.Value then
        local category
        for _, entry in ipairs(PAPERDOLL_STATCATEGORIES or {}) do
            if not entry.unit or entry.unit == data.unit then
                for _, stat in ipairs(entry.stats or {}) do
                    if data.name and stat.stat == data.name then category = entry.categoryName; break end
                end
            end
            if category then break end
        end
        -- Resistance rows have atlas/label/value fields rather than a stat key.
        if not category and data.atlas and data.labelText then category = STAT_CATEGORY_RESISTANCE end
        StatValue(row.Value, StatColor(category))
    end
end

local function List(frame, stats)
    if not frame then return end
    DecorativeRegions(frame)
    ScrollBar(frame.ScrollBar)
    if frame.ClassBackground then frame.ClassBackground:SetAlpha(0.12) end
    local box = frame.ScrollBox
    if not box then return end
    local d = State(box)
    if not d.rowsHooked and ScrollUtil and ScrollUtil.AddInitializedFrameCallback then
        -- Callback API passes owner first; existing rows are handled separately.
        ScrollUtil.AddInitializedFrameCallback(box, W.WindowCallback("charsheet", function(_, row, data)
            Row(row, stats)
            if stats then StatsRow(row, data) end
        end), d)
        d.rowsHooked = true
    end
    if box.ForEachFrame then box:ForEachFrame(function(row)
        Row(row, stats)
        if stats then StatsRow(row) end
    end) end
    -- ScrollBox's two decorative line hosts are its direct XML children.
    for _, child in ipairs({ box:GetChildren() }) do DecorativeRegions(child) end
end

local function DetailRows(pane)
    if pane.rowPools and pane.rowPools.EnumerateActive then
        for row in pane.rowPools:EnumerateActive() do Row(row) end
    elseif pane.Content then
        for _, row in ipairs({ pane.Content:GetChildren() }) do Row(row) end
    end
end

local function Detail(pane)
    if not pane then return end
    DecorativeRegions(pane)
    Font(pane.Title)
    Font(pane.Subtitle)
    Font(pane.EmptyText)
    ScrollBar(pane.DescriptionScrollBar)
    Progress(pane.StandingBar)
    Progress(pane.RankBar)
    for _, key in ipairs({ "AtWarCheckbox", "MakeInactiveCheckbox", "WatchFactionCheckbox", "InactiveCheckbox", "BackpackCheckbox" }) do
        local cb = pane[key]
        if cb then W.Checkbox(cb, { stockCheck = true, boxInset = true }); Font(cb.Label) end
    end
    TextButton(pane.ViewRenownButton)
    -- CurrencyTransferToggleButton is an icon control, not a text button.
    IconControl(pane.CurrencyTransferToggleButton)
    local d = State(pane)
    if not d.rowsHooked and pane.LayoutRows then
        hooksecurefunc(pane, "LayoutRows", W.WindowCallback("charsheet", DetailRows))
        d.rowsHooked = true
    end
    DetailRows(pane)
end

local slots = { "Head", "Neck", "Shoulder", "Back", "Chest", "Shirt", "Tabard", "Wrist", "Hands", "Waist", "Legs", "Feet", "Finger0", "Finger1", "Trinket0", "Trinket1", "MainHand", "SecondaryHand", "Ranged", "Ammo" }
local function Equipment(prefix)
    for _, slot in ipairs(slots) do
        local button = _G[prefix .. slot .. "Slot"]
        if button then
            DecorativeRegions(button.BorderFrame)
            local normal = button.GetNormalTexture and button:GetNormalTexture()
            if normal then normal:SetAlpha(0) end
            local icon = button.icon or button.Icon or _G[prefix .. slot .. "SlotIconTexture"]
            if icon then W.SquareIcon(icon, button, true) end
            -- Item quality, durability overlays, socketed gems, flyout arrows,
            -- cooldowns and ammunition count all remain visible and native.
            W.AddBorder(button)
        end
    end
end

local function Model(model)
    if not model then return end
    for _, key in ipairs({ "BackgroundTopLeft", "BackgroundTopRight", "BackgroundBotLeft", "BackgroundBotRight", "BackgroundOverlay" }) do
        if model[key] then model[key]:SetAlpha(0.28) end
    end
    local controls = model.ControlFrame
    if controls then
        for _, key in ipairs({ "RotateLeftButton", "RotateRightButton", "ZoomInButton", "ZoomOutButton", "ResetButton" }) do IconControl(controls[key]) end
    end
end

function ns.ForeverCharacter()
    local f = CharacterFrame
    if not (f and f.ModeTabs) then return end
    HeaderPortrait(f, "charsheet")
    if f.RightPaneHost then
        for _, child in ipairs({ f.RightPaneHost:GetChildren() }) do DecorativeRegions(child) end
    end
    SideTabs(f.ModeTabs.Tabs)
    IconControl(f.RightPaneToggleButton)
    Font(f.TitleContainer and f.TitleContainer.TitleText)
    Fade(CharacterLevelTextBackground)
    Font(CharacterLevelText)
    Equipment("Character")
    Model(CharacterModelScene)
    List(CharacterStatsPaneScrollBox, true)
    List(CharacterStatsPanePetScrollBox, true)
    if CharacterStatsPane then
        for _, child in ipairs({ CharacterStatsPane:GetChildren() }) do Row(child) end
    end
    for _, pane in ipairs(f.SidePanes or {}) do Detail(pane) end
    for _, name in ipairs({ "ReputationFrame", "SkillsFrame", "TokenFrame", "StatisticsFrame" }) do List(_G[name]) end
    if ReputationFrame then W.Dropdown(ReputationFrame.filterDropdown) end
    if PaperDollFrame then
        List(PaperDollFrame.TitleManagerPane)
        local equipment = PaperDollFrame.EquipmentManagerPane
        List(equipment)
        if equipment then TextButton(equipment.EquipSet); TextButton(equipment.SaveSet); TextButton(equipment.NewSet) end
    end
    if PVPRankFrame then
        Font(PVPRankFrame.SeasonTimerField)
        local info = PVPRankFrame.MainInfoFrame
        if info then
            Font(info.CurrentSeasonField, true)
            Font(info.CurrentRankField)
            Font(info.CurrentRankProgressField)
            -- RankProgressBarDisplay, faction badge and next-reward item are
            -- meaningful progression displays; retain them in full.
        end
    end
    local d = State(f)
    if not d.refreshHooked then
        local refresh = W.WindowCallback("charsheet", ns.ForeverCharacter)
        if f.RefreshDisplay then hooksecurefunc(f, "RefreshDisplay", refresh) end
        f:HookScript("OnShow", refresh)
        d.refreshHooked = true
    end
end

function ns.ForeverInspect()
    local f = InspectFrame
    if not f then return end
    HeaderPortrait(f, "inspect")
    SideTabs(f.ModeTabs and f.ModeTabs.Tabs)
    Equipment("Inspect")
    Model(InspectModelFrame)
    Font(InspectLevelText)
    Font(InspectTitleText)
    Font(InspectGuildText)
    local guild = InspectGuildFrame
    if guild then
        -- The guild tabard and banner describe the inspected guild. Only the
        -- separate parchment backdrop and label fonts are presentation.
        if InspectGuildFrameBG then
            InspectGuildFrameBG:SetColorTexture(T.insetR, T.insetG, T.insetB, 0.85)
        end
        Font(guild.guildName, true)
        -- These are identity/count labels, not standing or warning colors.
        W.Font(guild.guildRealmName, 0.88, 0.88, 0.88)
        W.Font(guild.guildLevel, 0.88, 0.88, 0.88)
        W.Font(guild.guildNumMembers, 0.88, 0.88, 0.88)
        local gd = State(guild)
        if not gd.refreshHooked then
            guild:HookScript("OnShow", W.WindowCallback("inspect", ns.ForeverInspect))
            gd.refreshHooked = true
        end
    end
    if InspectPaperDollFrame then
        TextButton(InspectPaperDollFrame.InspectTalents)
        TextButton(InspectPaperDollFrame.ViewButton)
    end
    for _, suffix in ipairs({ "TopLeft", "TopRight", "BottomLeft", "BottomRight", "Left", "Right", "Top", "Bottom", "Bottom2" }) do
        Fade(_G["InspectModelFrameBorder" .. suffix])
    end
    local d = State(f)
    if not d.refreshHooked then
        local refresh = W.WindowCallback("inspect", ns.ForeverInspect)
        f:HookScript("OnShow", refresh)
        for _, method in ipairs({ "SetupModeTabs", "UpdateTabs" }) do
            if type(f[method]) == "function" then hooksecurefunc(f, method, refresh) end
        end
        d.refreshHooked = true
    end
end

-- Late-loaded currency/statistics content receives the same treatment when it
-- appears. This is visual dispatch only; it never loads or exposes hidden modes.
local loader = CreateFrame("Frame")
loader:RegisterEvent("ADDON_LOADED")
loader:SetScript("OnEvent", function(_, _, name)
    if name == "Blizzard_TokenUI" or name == "Blizzard_Statistics" then
        W.WindowCallback("charsheet", ns.ForeverCharacter)()
    end
end)
W.OnLooksChanged(function()
    W.WindowCallback("charsheet", ns.ForeverCharacter)()
    W.WindowCallback("inspect", ns.ForeverInspect)()
end)
