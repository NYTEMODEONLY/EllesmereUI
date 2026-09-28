-- Camelot Legacy is not AchievementFrame. Theme the documented native controls
-- individually: no child/region sweeps, replacement handlers or trait mutations.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T = W.Theme
local seen = setmetatable({}, { __mode = "k" })

local function Data(frame)
    if not seen[frame] then seen[frame] = {} end
    return seen[frame]
end

local function Hook(frame, method, callback)
    if not frame or type(frame[method]) ~= "function" then return end
    local d = Data(frame)
    if d[method] then return end
    hooksecurefunc(frame, method, W.WindowCallback("achievements", callback))
    d[method] = true
end

local function Flat(texture, r, g, b, a)
    if texture and texture.SetColorTexture then
        texture:SetColorTexture(r, g, b, a or 1)
        texture:SetVertexColor(1, 1, 1)
    end
end

local function Text(fs, readable)
    if readable then W.Font(fs, 0.92, 0.92, 0.92) else W.Font(fs) end
end

local function Accent(texture, alpha)
    Flat(texture, T.accR, T.accG, T.accB, alpha)
end

local function Progress(bar, backdrop)
    if not bar then return end
    -- Keep the existing status texture object: RewardTrack masks retain it.
    local fill = bar.GetStatusBarTexture and bar:GetStatusBarTexture()
    if fill then fill:SetTexture("Interface\\Buttons\\WHITE8X8") end
    W.ApplyBarFill(bar)
    Flat(backdrop, 0.02, 0.02, 0.02, 1)
    if bar.ProgressBarFrame then bar.ProgressBarFrame:SetAlpha(0) end
    W.AddBorder(bar)
    Text(bar.Text, true)
end

local function Panel(frame)
    if not frame then return end
    local d = Data(frame)
    if not d.fill then
        d.fill = frame:CreateTexture(nil, "BACKGROUND", nil, -7)
        d.fill:SetAllPoints(frame)
    end
    Flat(d.fill, T.insetR, T.insetG, T.insetB, T.insetA)
    W.AddBorder(frame)
end

local function Divider(frame)
    if not frame then return end
    -- These dedicated separator frames contain precisely one background region.
    local texture = frame.VerticalDivider or select(1, frame:GetRegions())
    Flat(texture, T.brdR, T.brdG, T.brdB, 0.7)
end

local function SideTab(tab)
    -- Keep the raw icon and native clipped mask, without the decorative backing.
    -- Retain the atlas so no texture identity or native geometry is replaced.
    if tab.Background then tab.Background:SetAlpha(0) end
    -- Only tint the existing selection/hover/glow; native state stays authoritative.
    if tab.SelectedTexture then tab.SelectedTexture:SetVertexColor(T.accR, T.accG, T.accB) end
    if tab.TabGlow then tab.TabGlow:SetVertexColor(T.accR, T.accG, T.accB) end
    if tab.HighlightTexture then tab.HighlightTexture:SetVertexColor(T.accR, T.accG, T.accB) end
end

local function ScrollBar(bar)
    if not bar then return end
    local glyphs = {}
    for _, key in ipairs({ "Back", "Forward" }) do
        local button = bar[key]
        if button and button.Texture then
            glyphs[#glyphs + 1] = { texture = button.Texture, alpha = button.Texture:GetAlpha() }
        end
    end
    W.ScrollBar(bar)
    -- The shared Retail primitive removes the arrow glyphs. Preserve the
    -- native glyph alpha and enabled/disabled atlas alongside its EUI thumb.
    for _, glyph in ipairs(glyphs) do glyph.texture:SetAlpha(glyph.alpha) end
end

local function RewardCard(card, actualLevel, displayLevel, selected)
    local d = Data(card)
    if displayLevel ~= nil then d.displayLevel, d.selected = displayLevel, selected end
    local level = card.GetLevel and card:GetLevel()
    local earned = level and d.displayLevel and level <= d.displayLevel
    local active = d.selected or (level and level == d.displayLevel)
    if active then
        Flat(card.RewardCardBG, T.accR * 0.18 + 0.03, T.accG * 0.18 + 0.03, T.accB * 0.18 + 0.03, 0.96)
    else
        Flat(card.RewardCardBG, 0.06, 0.06, 0.06, 0.96)
    end
    -- Native icons, desaturation, check marks, level plate and availability text
    -- retain their earned state. Only the ornamental border changes palette.
    if card.IconBorder then
        if active then card.IconBorder:SetVertexColor(T.accR, T.accG, T.accB)
        elseif earned then card.IconBorder:SetVertexColor(0.8, 0.8, 0.8)
        else card.IconBorder:SetVertexColor(0.45, 0.45, 0.45) end
    end
    Text(card.Level)
    Text(card.RewardName)
    Hook(card, "Refresh", RewardCard)
end

local function RewardTrack(page)
    if not page then return end
    Flat(page.Background, T.bgR, T.bgG, T.bgB, T.bgA)
    Text(page.Points, true)
    Text(page.PointsLabel, true)
    Progress(page.LegacyRewardProgressBar, page.ProgressBarBackground)
    local progress = page.LegacyRewardProgressFrame
    if progress and progress.GetElements then
        for _, card in ipairs(progress:GetElements()) do RewardCard(card) end
        -- Preserve native arrow glyphs and their disabled/hidden state.
        for _, key in ipairs({ "LeftButton", "RightButton", "JumpLeftButton", "JumpRightButton" }) do
            local button = progress[key]
            if button then Panel(button) end
        end
    end
    Hook(page, "SetupRewardTrack", RewardTrack)
end

local function Category(row)
    local selected = row.selected
    local normal = row.GetNormalTexture and row:GetNormalTexture()
    if selected then
        Flat(normal, T.accR * 0.25, T.accG * 0.25, T.accB * 0.25, 1)
    else
        Flat(normal, 0.08, 0.08, 0.08, 0.95)
    end
    local highlight = row.GetHighlightTexture and row:GetHighlightTexture()
    Flat(highlight, 1, 1, 1, 0.12)
    Text(row.ButtonText, true)
    -- The separate CollapseButton and NotificationIcon remain visible and native.
    W.AddBorder(row)
    Hook(row, "RefreshCardArt", Category)
    Hook(row, "RefreshTitleColorState", Category)
end

local function Criteria(row)
    Flat(row.Background, 0.04, 0.04, 0.04, 0.8)
    Text(row.Name)
    Progress(row.ProgressBar, row.ProgressBarBackground)
    Hook(row, "Init", Criteria)
end

local function Objectives(frame)
    if not frame then return end
    if frame.criteriaPool then
        for row in frame.criteriaPool:EnumerateActive() do Criteria(row) end
    end
    Hook(frame, "Display", Objectives)
end

local function Challenge(row)
    local selected = row.IsSelected and row:IsSelected()
    local completed = row.completed
    for _, key in ipairs({ "Background", "BackgroundTop", "BackgroundMiddle", "BackgroundBottom" }) do
        Flat(row[key], completed and 0.085 or 0.045, completed and 0.085 or 0.045, completed and 0.085 or 0.045, 0.98)
    end
    Flat(row.TitleBar, 0.025, 0.025, 0.025, 0.8)
    Accent(row.SelectedOverlay, 0.12)
    local bright = completed or selected
    for _, key in ipairs({ "Label", "Description", "HiddenDescription" }) do
        local fs = row[key]
        local value = bright and 0.94 or 0.66
        W.Font(fs, value, value, value)
    end
    if row.Icon then
        if row.Icon.frame then row.Icon.frame:SetVertexColor(0.65, 0.65, 0.65) end
    end
    if row.Shield then Text(row.Shield.Points); Text(row.Shield.DateCompleted) end
    if row.Tracked then W.Checkbox(row.Tracked, { stockCheck = true }); Text(row.Tracked.Text, true) end
    W.AddBorder(row)
    Hook(row, "RefreshStateArt", Challenge)
    Hook(row, "Saturate", Challenge)
    Hook(row, "Desaturate", Challenge)
    Hook(row, "DisplayObjectives", function() Objectives(LegacyChallengeObjectives) end)
end

local function WatchRows(scrollBox, painter)
    if not scrollBox then return end
    local d = Data(scrollBox)
    if not d.rows and ScrollUtil and ScrollUtil.AddInitializedFrameCallback then
        -- Use explicit existing iteration: ScrollUtil passes different arguments
        -- to its convenience existing-frame path and its registered callback.
        ScrollUtil.AddInitializedFrameCallback(scrollBox, W.WindowCallback("achievements", function(_, row) painter(row) end), scrollBox, false)
        d.rows = true
    end
    if scrollBox.ForEachFrame then scrollBox:ForEachFrame(painter) end
end

local function Challenges(page)
    if not page then return end
    Flat(page.Background, T.bgR, T.bgG, T.bgB, T.bgA)
    Divider(page.VerticalDivider)
    local list, detail = page.CategoryList, page.DetailPane
    if list then
        Panel(list)
        -- SearchBox's SearchIcon and clear button convey actions; preserve them
        -- instead of the generic EditBox primitive's blanket texture fading.
        Panel(list.SearchBox)
        if list.SearchBox then
            for _, key in ipairs({ "Left", "Middle", "Right" }) do
                if list.SearchBox[key] then list.SearchBox[key]:SetAlpha(0) end
            end
        end
        -- This template has only a background and text on the dropdown itself;
        -- the reset control is a child. The primitive supplies a visible arrow.
        W.Dropdown(list.FilterDropdown)
        W.StateButtonLabel(list.FilterDropdown)
        Text(list.FilterDropdown and list.FilterDropdown.Text, true)
        Text(list.NoResultsText, true)
        ScrollBar(list.ScrollBar)
        WatchRows(list.ScrollBox, Category)
    end
    if detail then ScrollBar(detail.ScrollBar); WatchRows(detail.ScrollBox, Challenge) end
    local summary = page.LegacyChallengePointSummary
    if summary then
        Progress(summary.PointsBar, summary.ProgressBarBackground)
        Text(summary.Shield and summary.Shield.Points, true)
    end
    Objectives(LegacyChallengeObjectives)
end

local function TreeButton(button)
    local selected = button.GetChecked and button:GetChecked()
    Flat(button.Background, selected and T.accR * 0.18 or 0.06, selected and T.accG * 0.18 or 0.06, selected and T.accB * 0.18 or 0.06, 0.95)
    if button.SelectedGlow then button.SelectedGlow:SetVertexColor(T.accR, T.accG, T.accB) end
    Hook(button, "RefreshSelectionVisuals", TreeButton)
end

local function TreeSelections(panel)
    if not panel then return end
    for _, button in ipairs(panel.treeButtons or {}) do TreeButton(button) end
    Hook(panel, "RefreshTreeButtons", TreeSelections)
end

local function Tree(page)
    if not page then return end
    Flat(page.Background, T.bgR, T.bgG, T.bgB, T.bgA)
    Divider(page.VerticalDivider)
    TreeSelections(page.LegacyTreeSelectionPanel)
    local summary = page.LegacyTreePointSummary
    if summary then
        Flat(summary.Border, 0.04, 0.04, 0.04, 0.95)
        Text(summary.AvailablePointsLabel, true)
        Text(summary.Shield and summary.Shield.Points, true)
    end
    local panel = page.LegacyTreeTraitPanel
    if not panel then return end
    Text(panel.SelectedTreeIcon and panel.SelectedTreeIcon.SelectedTreeLabel, true)
    Text(panel.SpentPointsFrame and panel.SpentPointsFrame.Text, true)
    if panel.ApplyButton then W.Button(panel.ApplyButton); W.StateButtonLabel(panel.ApplyButton) end
    -- IconButton's glyph, disabled overlay and native tooltip stay intact.
    Panel(panel.ResetButton)
    Panel(panel.UndoButton)
    Panel(panel.SearchBox)
    if panel.SearchBox then
        for _, key in ipairs({ "Left", "Middle", "Right" }) do
            if panel.SearchBox[key] then panel.SearchBox[key]:SetAlpha(0) end
        end
    end
    -- Talent buttons and edges encode rank, availability, prerequisite links and
    -- pending changes. Their semantic art remains; never use ButtonsIn here.
end

function ns.ForeverLegacy()
    if W.GetStyle("achievements") == "off" then return end
    local frame = LegacySystemFrame
    if not frame then return end
    for _, tab in ipairs(frame.Tabs or {}) do SideTab(tab) end
    RewardTrack(frame.RewardTrackPage)
    Challenges(frame.ChallengesPage)
    Tree(frame.TreePage)
    Hook(frame, "SelectPage", ns.ForeverLegacy)
end

W.OnLooksChanged(function()
    if LegacySystemFrame then ns.ForeverLegacy() end
end)
