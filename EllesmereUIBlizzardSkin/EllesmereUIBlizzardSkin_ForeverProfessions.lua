-- Camelot embeds the profession overview inside ProfessionsFrame.BookPage.
-- Paint native cards and side tabs without replacing profession spell actions,
-- skill-rank animation, unlearn confirmation, or trained/untrained visibility.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T = W.Theme
local state = setmetatable({}, { __mode = "k" })
local function Data(frame)
    if not state[frame] then state[frame] = {} end
    return state[frame]
end
local function Fill(frame)
    local d = Data(frame)
    if not d.fill then
        d.fill = frame:CreateTexture(nil, "BACKGROUND", nil, -6)
        d.fill:SetAllPoints(frame)
        W.AddBorder(frame)
    end
    d.fill:SetColorTexture(T.insetR, T.insetG, T.insetB, 0.7)
end
local function Font(fs, heading)
    if not fs then return end
    if heading then
        W.Font(fs, T.accR, T.accG, T.accB)
    else
        W.Font(fs)
        -- Keep passive spell, unavailable, modifier and warning colors.
        -- Only the generic UI gold is changed to the Ellesmere neutral label.
        if fs.GetTextColor and NORMAL_FONT_COLOR then
            local r, g, b = fs:GetTextColor()
            if not (issecretvalue and (issecretvalue(r) or issecretvalue(g) or issecretvalue(b)))
                and r and math.abs(r-NORMAL_FONT_COLOR.r) < 0.001
                and math.abs(g-NORMAL_FONT_COLOR.g) < 0.001
                and math.abs(b-NORMAL_FONT_COLOR.b) < 0.001 then
                fs:SetTextColor(0.9, 0.9, 0.9)
            end
        end
    end
end
local function SideTab(tab)
    if not tab then return end
    -- Preserve the native clipped-corner icon and selected outline, without
    -- an extra rectangular plate or Ellesmere border around the whole tab.
    if tab.Background then tab.Background:SetAlpha(0) end
    -- Native SetChecked chooses active/inactive glyphs and controls selection.
    -- Recoloring state carriers preserves checked, hover and notification pulses.
    if tab.SelectedTexture then tab.SelectedTexture:SetVertexColor(T.accR, T.accG, T.accB) end
    if tab.TabGlow then tab.TabGlow:SetVertexColor(T.accR, T.accG, T.accB) end
    if tab.HighlightTexture then tab.HighlightTexture:SetVertexColor(0.65, 0.65, 0.65) end
end
local function RankBar(bar)
    if not bar then return end
    if bar.Border then bar.Border:SetAlpha(0) end
    if bar.Background then bar.Background:SetColorTexture(0.025, 0.025, 0.025, 0.95) end
    W.AddBorder(bar)
    Font(bar.Rank and bar.Rank.Text)
    -- Native progress animates Mask's width, independently of the patterned
    -- Fill flipbook. Solid pixels stay flat through every flipbook UV frame;
    -- retain the original mask association, texture geometry and animations.
    if bar.Fill then bar.Fill:SetColorTexture(T.accR, T.accG, T.accB, 1) end
    if bar.Flare then
        -- Keep the native gain marker and full-rank fade, with Ellesmere color.
        bar.Flare:SetDesaturated(true)
        bar.Flare:SetVertexColor(T.accR, T.accG, T.accB)
    end
    local dropdown = bar.ExpansionDropdownButton
    if dropdown then
        Fill(dropdown)
        -- Its Texture is the native glyph and includes pressed/disabled states.
    end
end
local function SpellButton(button)
    if not button then return end
    Font(button.spellString)
    Font(button.subSpellString)
    -- Camelot's square overlay is decorative. Keep OutlineMask, IconTexture,
    -- cooldown, Flash reminder, flyout arrow, drag handlers and secure scripts.
    local overlay = button.IconTextureOverlay
    if overlay and overlay.GetAtlas and overlay:GetAtlas() == "Profession-square-frame" then overlay:SetAlpha(0) end
    W.AddBorder(button)
end
local Apply
local refresh = W.Debounce(W.WindowCallback("professions", function()
    local f = ProfessionsFrame
    if f and f:IsShown() then Apply() end
end))
local function Hook(frame, methods)
    if not frame then return end
    local d = Data(frame)
    for _, method in ipairs(methods) do
        if not d[method] and type(frame[method]) == "function" then
            d[method] = true
            hooksecurefunc(frame, method, refresh)
        end
    end
    if not d.onShow then
        d.onShow = true
        frame:HookScript("OnShow", refresh)
    end
end
local function RecipeRow(row)
    if not row then return end
    if row.ButtonText and row.CollapseButton then
        -- Native ListHeaderVisualTemplate: keep its collapse glyph and scripts.
        Font(row.ButtonText)
        local normal = row.GetNormalTexture and row:GetNormalTexture()
        if normal then normal:SetColorTexture(T.insetR, T.insetG, T.insetB, 0.8) end
        local highlight = row.GetHighlightTexture and row:GetHighlightTexture()
        if highlight then highlight:SetColorTexture(1, 1, 1, 0.08) end
    end
    -- These colors describe difficulty, learned/locked state, or availability.
    -- Change only the typeface, never normalize gold/yellow on recipe content.
    W.Font(row.Label)
    W.Font(row.Count)
    if row.SkillUps then W.Font(row.SkillUps.Text) end
    if row.RankBar then W.Font(row.RankBar.Rank) end
    -- SelectedOverlay, HighlightOverlay, LockedIcon and SkillUps.Icon stay native.
end
local function ActionButton(button)
    if not button then return end
    W.Button(button)
    -- Camelot uses SharedButtonSmallTemplate's Center (not Retail Middle).
    for _, key in ipairs({ "Left", "Center", "Right" }) do
        if button[key] then button[key]:SetAlpha(0) end
    end
    local label = button.Text or (button.GetFontString and button:GetFontString())
    if button.IsEnabled and not button:IsEnabled() then W.Font(label) else Font(label) end
    Hook(button, { "UpdateButton" })
end
local function Spinner(spinner)
    if not spinner then return end
    for _, key in ipairs({ "Left", "Middle", "Right" }) do
        if spinner[key] then spinner[key]:SetAlpha(0) end
    end
    Fill(spinner)
    W.Font(spinner)
    for _, key in ipairs({ "IncrementButton", "DecrementButton" }) do
        local arrow = spinner[key]
        if arrow then
            Fill(arrow)
            -- Normal, pushed and disabled arrow textures and all input methods
            -- remain native, including repeat, shift-wheel and quantity limits.
        end
    end
end
local function Reagent(slot)
    if not slot then return end
    W.Font(slot.Name)
    if slot.Button then W.Font(slot.Button.Count); W.AddBorder(slot.Button) end
    -- Preserve insufficient counts, quality borders, optional/locked overlays.
end
local function Crafting(page)
    if not page then return end
    RankBar(page.RankBar)
    Hook(page.RankBar, { "Update" })
    ActionButton(page.CreateButton)
    ActionButton(page.CreateAllButton)
    ActionButton(page.ViewGuildCraftersButton)
    Spinner(page.CreateMultipleInputBox)
    local list = page.RecipeList
    if list then
        Font(list.NoResultsText)
        W.Font(list.SearchBox)
        local scroll = list.ScrollBox
        if scroll and scroll.ForEachFrame then
            scroll:ForEachFrame(RecipeRow)
            if not Data(scroll).rowsHooked and ScrollUtil and ScrollUtil.AddInitializedFrameCallback then
                Data(scroll).rowsHooked = true
                ScrollUtil.AddInitializedFrameCallback(scroll, W.WindowCallback("professions", function(_, row)
                    RecipeRow(row)
                end), Data(scroll), false)
            end
        end
    end
    local form = page.SchematicForm
    if form then
        for _, key in ipairs({ "OutputText", "OutputSubText", "Description", "RequiredTools", "Cooldown", "MinimizedCooldown",
            "RecraftingOutputText", "RecraftingDescription", "RecraftingRequiredTools" }) do
            W.Font(form[key])
        end
        for _, key in ipairs({ "Reagents", "OptionalReagents", "FinishingReagents", "Concentrate" }) do
            local container = form[key]
            if container then W.Font(container.Label) end
        end
        for _, key in ipairs({ "TrackRecipeCheckbox", "AllocateBestQualityCheckbox" }) do
            local checkbox = form[key]
            if checkbox then
                -- The shared professions pack runs first and already replaces
                -- these with its own 14px box; a second box drew a double outline.
                local replaced = W.GetFFD and W.GetFFD(checkbox).custom
                if not replaced then W.Checkbox(checkbox, { stockCheck=true, boxInset=true }) end
                W.Font(checkbox.Text)
            end
        end
        if form.RecipeSourceButton then W.Font(form.RecipeSourceButton.Text) end
        if form.FirstCraftBonus then W.Font(form.FirstCraftBonus.Text) end
        if form.OutputIcon then W.Font(form.OutputIcon.Count) end
        if form.reagentSlotPool then
            for slot in form.reagentSlotPool:EnumerateActive() do Reagent(slot) end
        end
        Hook(form, { "Init", "Refresh", "Update", "UpdateRecipeDescription", "UpdateAllSlots" })
    end
    Hook(page, { "CreateControls", "Init", "Refresh", "ValidateControls", "OnRecipeSelected", "SetupMultipleInputBox" })
end
local function Card(frame)
    if not frame then return end
    if frame.Background then frame.Background:SetAlpha(0) end
    Fill(frame)
    Font(frame.ProfessionName, true)
    Font(frame.specialization)
    Font(frame.missingHeader, true)
    Font(frame.missingText)
    RankBar(frame.StatusBar)
    Hook(frame.StatusBar, { "Update" })
    -- Secondary professions have four native spell slots. Iterate the supplied
    -- collection so later beta additions are included without Retail's 2 limit.
    for _, button in ipairs(frame.spellButtons or {}) do
        SpellButton(button)
        Hook(button, { "UpdateButton", "UpdateOverlay" })
    end
    local unlearn = frame.UnlearnButton
    if unlearn then
        Fill(unlearn)
        -- The red cross, pushed Overlay and confirmation handler stay native.
    end
end
Apply = function()
    local f = ProfessionsFrame
    if not (f and f.BookPage) then return end
    SideTab(f.ProfessionsOverviewTab)
    for _, tab in ipairs(f.rightProfessionTabs or {}) do SideTab(tab) end
    local book = f.BookPage
    local content = book.ProfessionsContentFrame
    if content then
        for _, key in ipairs({ "PrimaryProfession1", "PrimaryProfession2", "SecondaryProfession1", "SecondaryProfession2", "SecondaryProfession3" }) do
            Card(content[key])
        end
    end
    local crafting = f.CraftingPage
    Crafting(crafting)
    if crafting and crafting.GetRegions then
        -- Only this exact, page-wide Camelot decoration covers the root shell.
        -- Do not strip output/reagent icons, rank animations or recipe content.
        for i=1,select("#", crafting:GetRegions()) do
            local texture = select(i, crafting:GetRegions())
            if texture.GetAtlas and texture:GetAtlas() == "Profession-Background-Template2" then texture:SetAlpha(0) end
        end
    end
    Hook(f, { "RefreshRightTabs", "RightTabSelected", "OverrideArt", "SelectBookPage" })
    Hook(book, { "Update", "FormatProfession" })
    Hook(crafting, {})
    if EUI_FOREVER_STATUS then EUI_FOREVER_STATUS.professions = "Forever overview, eight side tabs, pooled recipe rows and crafting controls themed; native skill/reagent states" end
end
W.RegisterWindow({ key="professions", addons={ Blizzard_Professions=true }, apply=W.WindowCallback("professions", Apply) })
W.OnLooksChanged(W.WindowCallback("professions", function()
    if ProfessionsFrame then Apply() end
end))
