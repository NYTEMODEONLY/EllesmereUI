-- Camelot's spellbook uses icon categories and ranked spells; its talent page
-- contains three Classic trees. Keep the native objects and their state logic.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T = W.Theme
local state = setmetatable({}, { __mode = "k" })
local function Data(f)
    if not state[f] then state[f] = {} end
    return state[f]
end
local function FadeNamed(f, keys)
    if not f then return end
    for _, key in ipairs(keys) do
        local texture = f[key]
        if texture and texture.SetAlpha then texture:SetAlpha(0) end
    end
end
local function Text(fs, r, g, b)
    if fs and fs.SetTextColor then W.Font(fs, r or 1, g or 1, b or 1) end
end
local function Plate(f)
    if not f then return end
    local d = Data(f)
    if not d.fill then
        d.fill = f:CreateTexture(nil, "BACKGROUND", nil, -2)
        d.fill:SetAllPoints(f)
        W.AddBorder(f)
    end
    d.fill:SetColorTexture(T.bgR, T.bgG, T.bgB, T.bgA)
end
local TAB_ART = { "Left", "Middle", "Right", "LeftActive", "MiddleActive", "RightActive",
    "LeftHighlight", "MiddleHighlight", "RightHighlight", "SquareBackground", "SquareBackgroundActive", "SquareBackgroundActiveGlow" }
local function PaintTab(tab)
    if tab.squareMode then
        -- Camelot icon categories already have native masks and a selected
        -- outline/glow. Keep those shapes; remove only the inactive surround.
        if tab.SquareBackground then tab.SquareBackground:SetAlpha(0) end
        for _, key in ipairs({ "SquareBackgroundActive", "SquareBackgroundActiveGlow" }) do
            if tab[key] then tab[key]:SetVertexColor(T.accR, T.accG, T.accB) end
        end
        return
    end
    FadeNamed(tab, TAB_ART)
    Plate(tab)
    local d = Data(tab)
    if not d.selected then
        d.selected = tab:CreateTexture(nil, "OVERLAY")
        d.selected:SetPoint("BOTTOMLEFT", 2, 0)
        d.selected:SetPoint("BOTTOMRIGHT", -2, 0)
        d.selected:SetHeight(2)
    end
    d.selected:SetColorTexture(T.accR, T.accG, T.accB, 1)
    d.selected:SetShown(tab.isSelected or false)
    -- Native selected tabs are disabled too. Only force-disabled tabs are locked.
    local locked = tab.IsForceDisabled and tab:IsForceDisabled()
    local c = locked and 0.5 or 1
    Text(tab.Text, c, c, c)
end
local function Tabs(system)
    for _, tab in ipairs(system and system.tabs or {}) do
        if not Data(tab).tabHook then
            Data(tab).tabHook = true
            if tab.SetTabSelected then hooksecurefunc(tab, "SetTabSelected", PaintTab) end
            if tab.SetTabEnabled then hooksecurefunc(tab, "SetTabEnabled", PaintTab) end
        end
        PaintTab(tab)
    end
end
local function Search(box)
    if not box then return end
    -- Keep the native magnifier, clear button, instructions and search preview.
    FadeNamed(box, { "Left", "Middle", "Right", "Mid", "Background" })
    Plate(box)
    Text(box)
end
local function IconControl(button)
    if not button then return end
    Plate(button)
    -- These are native arrows / settings glyphs, including disabled textures.
    -- Their state and visibility remain entirely native.
    for _, getter in ipairs({ "GetNormalTexture", "GetPushedTexture", "GetDisabledTexture" }) do
        local texture = button[getter] and button[getter](button)
        if texture and texture.SetDesaturated then texture:SetDesaturated(true) end
    end
end
local function PaintSpell(item)
    if not (item and item.Button and item.Button.Icon and item.TextContainer) then return end
    Text(item.Name)
    Text(item.SubName, 0.78, 0.8, 0.84)
    Text(item.RequiredLevel, 0.9, 0.78, 0.52)
    -- Preserve unlearned alpha, rank text, passive mask, trainer glow, action-bar
    -- marker, cooldown, locks, flyout arrow, autocast and click-binding overlays.
    FadeNamed(item, { "Backplate" })
    FadeNamed(item.Button, { "BorderShadow" })
    W.AddBorder(item.Button)
    local d = Data(item)
    if not d.itemHook then
        d.itemHook = true
        if item.UpdateVisuals then hooksecurefunc(item, "UpdateVisuals", PaintSpell) end
        if item.OnIconEnter then hooksecurefunc(item, "OnIconEnter", PaintSpell) end
        if item.OnIconLeave then hooksecurefunc(item, "OnIconLeave", PaintSpell) end
    end
end
local function PaintHeader(header)
    Text(header.Text)
    FadeNamed(header, { "Backplate" })
    if header.Border then
        header.Border:SetDesaturated(true)
        header.Border:SetVertexColor(T.accR, T.accG, T.accB, 0.7)
    end
end
local function BookContents(book)
    local paged = book and book.PagedSpellsFrame
    if not (paged and paged.EnumerateFrames) then return end
    -- Enumerate native materialized content, including newly pooled headers.
    for _, frame in paged:EnumerateFrames() do
        if frame.Button and frame.TextContainer then PaintSpell(frame)
        elseif frame.Text and frame.Backplate and frame.Border then PaintHeader(frame) end
    end
    Tabs(book.CategoryTabSystem)
    local paging = paged.PagingControls
    if paging then
        Text(paging.PageText)
        IconControl(paging.PrevPageButton)
        IconControl(paging.NextPageButton)
    end
end
local function TalentChrome(talents)
    if not talents then return end
    -- The node icons, connections, point counters, locks and animations are
    -- semantic content. Only the fixed panel trim gets replaced.
    FadeNamed(talents, { "BackgroundBorder", "DividerHorizontalLeft", "DividerHorizontalRight" })
    if talents.Background then talents.Background:SetAlpha(0.18) end
    if talents.ClassBackground then talents.ClassBackground:SetAlpha(0.18) end
    for _, key in ipairs({ "DividerVerticalLeft", "DividerVerticalRight" }) do
        local divider = talents[key]
        if divider then divider:SetDesaturated(true); divider:SetVertexColor(T.accR, T.accG, T.accB, 0.45) end
    end
    Search(talents.SearchBox)
    Tabs(talents.TabSystem)
    IconControl(talents.SearchOptionsDropdown)
    IconControl(talents.ResetButton)
    IconControl(talents.UndoButton)
    if talents.LoadSystem and talents.LoadSystem.Dropdown then W.Dropdown(talents.LoadSystem.Dropdown) end
    for _, key in ipairs({ "ApplyButton", "InspectCopyButton" }) do
        local button = talents[key]
        if button then W.Button(button); W.StateButtonLabel(button) end
    end
    if talents.ActiveSpec then
        Text(talents.ActiveSpec.ActiveLabel)
        local button = talents.ActiveSpec.ActivateButton
        if button then W.Button(button); W.StateButtonLabel(button) end
    end
    local currency = talents.ClassCurrencyDisplay
    if currency then
        FadeNamed(currency, { "Border" })
        Text(currency.UnspentLabel)
        W.Font(currency.CurrentAmountContainer and currency.CurrentAmountContainer.CurrencyAmount)
        Plate(currency)
    end
    for _, header in ipairs(talents.treeHeaders or {}) do
        Text(header.Name)
        -- Preserve pending-spending colors and native counter values.
        W.Font(header.Text)
        if header.MainRing then header.MainRing:SetDesaturated(true) end
        if header.Divider then header.Divider:SetDesaturated(true); header.Divider:SetVertexColor(T.accR, T.accG, T.accB, 0.65) end
    end
end
local Apply
local function InstallHooks(f)
    local d = Data(f)
    if d.hooked then return end
    d.hooked = true
    local refresh = W.Debounce(W.WindowCallback("playerspells", function()
        if f:IsShown() then Apply() end
    end))
    f:HookScript("OnShow", refresh)
    local book = f.SpellBookFrame
    if book then
        book:HookScript("OnShow", refresh)
        for _, method in ipairs({ "SetTab", "CreateCategoryMixins", "SetMinimized" }) do
            if book[method] then hooksecurefunc(book, method, refresh) end
        end
        local paged = book.PagedSpellsFrame
        if paged and paged.RegisterCallback and PagedContentFrameBaseMixin then
            paged:RegisterCallback(PagedContentFrameBaseMixin.Event.OnUpdate, refresh, d)
        end
    end
    local talents = f.TalentsFrame
    if talents then
        talents:HookScript("OnShow", refresh)
        for _, method in ipairs({ "RefreshTreeHeaders", "InitializeTabSystem" }) do
            if talents[method] then hooksecurefunc(talents, method, refresh) end
        end
    end
end
Apply = function()
    local f = PlayerSpellsFrame
    if not f then return end
    W.Shell("playerspells", f)
    -- Root PortraitFrame chrome only; none of the content children are swept.
    W.RemovePortrait(f)
    if f.CloseButton then W.CloseButton(f.CloseButton) end
    Text(f.TitleText)
    Text(f.TitleContainer and f.TitleContainer.TitleText)
    local mm = f.MaximizeMinimizeButton
    if mm then IconControl(mm.MinimizeButton); IconControl(mm.MaximizeButton) end
    local book = f.SpellBookFrame
    if book then
        FadeNamed(book, { "TopBar", "BookBGLeft", "BookBGRight", "BookBGHalved", "BookCornerFlipbook", "Bookmark" })
        Search(book.SearchBox)
        IconControl(book.SettingsDropdown)
        BookContents(book)
    end
    TalentChrome(f.TalentsFrame)
    InstallHooks(f)
    if EUI_FOREVER_STATUS then EUI_FOREVER_STATUS.spellbook = "Ellesmere Forever spellbook and Classic talent chrome; native icons, ranks and controls" end
end
W.RegisterWindow({ key = "playerspells", addons = { Blizzard_PlayerSpells = true }, apply = W.WindowCallback("playerspells", Apply) })
W.OnLooksChanged(W.WindowCallback("playerspells", function()
    if PlayerSpellsFrame then Apply() end
end))
