-- Camelot uses five side tabs, the Classic companion journal and a toy count.
-- Style exact decoration; never enumerate/sweep model or secure spell children.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T, KEY = W.Theme, "collections"
local state = setmetatable({}, { __mode = "k" })
local globals = {}
local function Data(frame)
    if not state[frame] then state[frame] = {} end
    return state[frame]
end
local function Font(label) W.Font(label) end -- unavailable/quality/warning colors remain native
local function Label(label) W.Font(label, .9, .9, .9) end
local function Flat(texture, r, g, b, a)
    if texture and texture.SetColorTexture then texture:SetColorTexture(r, g, b, a or 1) end
end
local function Fill(frame)
    if not frame then return end
    local d = Data(frame)
    if not d.fill then
        d.fill = frame:CreateTexture(nil, "BACKGROUND", nil, -7)
        d.fill:SetAllPoints(frame)
        W.GetFFD(frame).fill = d.fill -- preserve our fill in the shared restrip pass
    end
    d.fill:SetAlpha(1)
    Flat(d.fill, T.insetR, T.insetG, T.insetB, T.insetA)
    W.AddBorder(frame)
end
local function Fade(frame, keys)
    if not frame then return end
    for _, key in ipairs(keys) do
        if frame[key] and frame[key].SetAlpha then frame[key]:SetAlpha(0) end
    end
end
local function Hook(frame, method, painter)
    if not frame or type(frame[method]) ~= "function" or Data(frame)[method] then return end
    hooksecurefunc(frame, method, W.WindowCallback(KEY, painter))
    Data(frame)[method] = true
end
local function HookGlobal(name, painter)
    if globals[name] or type(_G[name]) ~= "function" then return end
    hooksecurefunc(name, W.WindowCallback(KEY, painter))
    globals[name] = true
end
local function OnShow(frame, painter)
    if not frame or Data(frame).shown then return end
    frame:HookScript("OnShow", W.WindowCallback(KEY, painter))
    Data(frame).shown = true
end
local function TextButton(frame)
    if not frame then return end
    W.Button(frame)
    W.StateButtonLabel(frame)
    Font(frame.Text or (frame.GetFontString and frame:GetFontString()))
end
local function Dropdown(frame)
    if not frame then return end
    -- VariantSetsDropdown contains an interactive PrecedingVariantIcon. Keep
    -- its atlas/alpha and tooltip despite the shared dropdown's region fade.
    local icon = frame.PrecedingVariantIcon
    local alpha = icon and icon:GetAlpha()
    local text = frame.Text
    local r, g, b, a
    if text and text.GetTextColor then r, g, b, a = text:GetTextColor() end
    W.Dropdown(frame)
    Font(text)
    if r then text:SetTextColor(r, g, b, a) end
    if icon then icon:SetAlpha(alpha) end
end
local function Search(frame)
    if not frame then return end
    Fill(frame)
    Fade(frame, { "Left", "Middle", "Right" })
    Font(frame)
    Font(frame.Instructions)
    -- Clear button/search glyph, text, focus and native search callbacks stay.
end
local function ScrollBar(frame)
    if not frame then return end
    local arrows = {}
    for _, key in ipairs({ "Back", "Forward" }) do
        local button = frame[key]
        if button and button.Texture then arrows[#arrows + 1] = { button.Texture, button.Texture:GetAlpha() } end
    end
    W.ScrollBar(frame)
    for _, arrow in ipairs(arrows) do arrow[1]:SetAlpha(arrow[2]) end
end
local function Paging(frame)
    if not frame then return end
    Font(frame.PageText)
    Fill(frame.PrevPageButton)
    Fill(frame.NextPageButton)
    -- Arrow normal/pushed/disabled textures, page bounds and handlers stay.
end
local function Background(frame)
    if not frame then return end
    -- CollectionsBackgroundTemplate/InsetFrameTemplate direct chrome only.
    W.Inset(frame)
    Fill(frame)
end
local function Count(frame)
    if not frame then return end
    W.Inset(frame)
    Fill(frame)
    Font(frame.Count)
    Label(frame.Label)
end
local function Progress(frame)
    if not frame then return end
    -- Camelot ToyProgressTracker is a count, even though the XML element is
    -- StatusBar. Do not turn it into Retail's percentage/progress presentation.
    if frame.Count then Count(frame); return end
    Fade(frame, { "border", "barBorderLeft", "barBorderRight", "barBorderCenter" })
    local fill = frame.GetStatusBarTexture and frame:GetStatusBarTexture()
    if fill then
        fill:SetTexture("Interface\\Buttons\\WHITE8X8")
        fill:SetVertexColor(T.accR, T.accG, T.accB)
    end
    Font(frame.text)
    Fill(frame)
    -- No visibility, height, range or value writes (Wardrobe hides this).
end
local function SideTab(frame)
    -- Native icon alpha/masks and the selected outline supply the tab shape.
    if frame.Background then frame.Background:SetAlpha(0) end
    for _, key in ipairs({ "SelectedTexture", "TabGlow", "HighlightTexture" }) do
        if frame[key] then frame[key]:SetVertexColor(T.accR, T.accG, T.accB) end
    end
end
local function InnerTab(frame)
    if not frame then return end
    -- Preserve PanelTopTab native selection textures and all tab geometry.
    for _, key in ipairs({ "Left", "Middle", "Right", "LeftActive", "MiddleActive", "RightActive", "LeftDisabled", "MiddleDisabled", "RightDisabled" }) do
        if frame[key] and frame[key].SetVertexColor then frame[key]:SetVertexColor(.55, .55, .55) end
    end
    Font(frame.Text or (frame.GetFontString and frame:GetFontString()))
end
local function Row(frame)
    if not frame then return end
    Flat(frame.background or frame.Background, T.insetR, T.insetG, T.insetB, T.insetA)
    for _, key in ipairs({ "name", "subName", "new", "SteadyFlightLabel", "Name", "Label" }) do Font(frame[key]) end
    -- Icon, faction/pet type, dead, favorite/new, selected and unusable tint
    -- all remain native. In particular, never force a recycled name white.
end
local function Rows(box)
    if not box then return end
    if not Data(box).rows and ScrollUtil and ScrollUtil.AddInitializedFrameCallback then
        ScrollUtil.AddInitializedFrameCallback(box, W.WindowCallback(KEY, function(_, row) Row(row) end), box, false)
        Data(box).rows = true
    end
    if box.ForEachFrame then box:ForEachFrame(Row) end
end
local function Spell(frame)
    if not frame then return end
    Font(frame.name)
    Font(frame.new)
    Font(frame.special)
    Font(frame.level)
    -- Secure CollectionsSpellButton: do not write attributes/scripts or touch
    -- collected/uncollected borders, cooldown, favorite, upgrade glows or IDs.
end
local function Common(frame)
    for _, key in ipairs({ "LeftInset", "RightInset", "Inset" }) do Background(frame[key]) end
    Search(frame.SearchBox or frame.searchBox)
    Dropdown(frame.FilterDropdown or frame.FilterButton)
    Dropdown(frame.ClassDropdown)
    ScrollBar(frame.ScrollBar)
    Rows(frame.ScrollBox)
    Paging(frame.PagingFrame)
end
local function Mounts(frame)
    if not frame then return end
    Common(frame)
    Count(frame.MountCount)
    TextButton(frame.MountButton)
    local bottom = frame.BottomLeftInset
    if bottom then
        -- The equipment slot is a child; native drag/locked states stay intact.
        W.Inset(bottom)
        Fill(bottom)
        Font(bottom.SlotLabel)
        Font(bottom.SlotRequirementLabel)
    end
    local display = frame.MountDisplay
    if display then
        Flat(display.YesMountsTex, T.insetR, T.insetG, T.insetB, T.insetA)
        Font(display.NoMounts)
        if display.InfoButton then
            for _, key in ipairs({ "Name", "Source", "Lore", "New" }) do Font(display.InfoButton[key]) end
        end
        local toggle = display.ModelScene and display.ModelScene.TogglePlayer
        if toggle then W.Checkbox(toggle, { stockCheck = true, boxInset = true }); Font(toggle.TogglePlayerText) end
        -- NoMountsTex, camera controls, models, random/flying spell glyphs stay.
    end
    OnShow(frame, Mounts)
end
local function Pets(frame)
    if not frame then return end
    Common(frame)
    Count(frame.PetCount)
    TextButton(frame.SummonButton)
    local card = frame.PetCard
    if card then
        Flat(card.PetBackground, T.insetR, T.insetG, T.insetB, T.insetA)
        Row(card.PetInfo)
        -- Camelot companion model and both rotation buttons stay native.
    end
    OnShow(frame, Pets)
end
local function Toys(frame)
    if not frame then return end
    Common(frame)
    Progress(frame.ProgressTracker)
    Background(frame.iconsFrame)
    if frame.iconsFrame then
        for index = 1, 18 do Spell(frame.iconsFrame["spellButton" .. index]) end
    end
    OnShow(frame, Toys)
end
local function Heirlooms(frame)
    if not frame then return end
    Common(frame)
    Progress(frame.progressBar)
    Background(frame.iconsFrame)
    for _, row in ipairs(frame.heirloomEntryFrames or {}) do Spell(row) end
    for _, header in ipairs(frame.heirloomHeaderFrames or {}) do Label(header.text) end
    Hook(frame, "LayoutCurrentPage", Heirlooms)
    Hook(frame, "UpdateButton", function(_, button) Spell(button) end)
    OnShow(frame, Heirlooms)
end
local function Wardrobe(frame)
    if not frame then return end
    Common(frame)
    InnerTab(frame.ItemsTab)
    InnerTab(frame.SetsTab)
    Progress(frame.progressBar)
    local searchProgress = frame.SearchBox and frame.SearchBox.ProgressFrame
    if searchProgress then
        Flat(searchProgress.background, T.insetR, T.insetG, T.insetB, T.insetA)
        Font(searchProgress.LoadingFrame and searchProgress.LoadingFrame.Text)
        Progress(searchProgress.ProgressBar)
    end
    local items = frame.ItemsCollectionFrame
    if items then
        Background(items)
        Paging(items.PagingFrame)
        Dropdown(items.WeaponDropdown)
        for _, model in ipairs(items.Models or {}) do Font(model.NewString) end
        -- Camelot has ranged/secondaryhand slots. Native SlotsFrame.Buttons,
        -- every model, favorite/invalid/hidden marker and selection stay intact.
    end
    local sets = frame.SetsCollectionFrame
    if sets then
        Background(sets.LeftInset)
        Background(sets.RightInset)
        local list = sets.ListContainer
        if list then ScrollBar(list.ScrollBar); Rows(list.ScrollBox) end
        local details = sets.DetailsFrame
        if details then
            Font(details.Name); Font(details.LongName); Font(details.Label)
            Font(details.LimitedSet and details.LimitedSet.Text)
            Dropdown(details.VariantSetsDropdown)
            -- Model fade, itemFramesPool quality borders, limited-time icon and
            -- variant relationship tooltip are content, never decoration.
        end
    end
    OnShow(frame, Wardrobe)
end
local function Apply()
    local frame = CollectionsJournal
    if not frame then return end
    W.ResolveTheme()
    W.Shell(KEY, frame, { noTopBar = true })
    if frame.NineSlice then W.Inset(frame.NineSlice) end
    W.CloseButton(frame.CloseButton)
    Label(frame.TitleContainer and frame.TitleContainer.TitleText)
    for _, tab in ipairs(frame.TabContainer and frame.TabContainer.Tabs or {}) do SideTab(tab) end
    Mounts(MountJournal)
    Pets(PetJournal)
    Toys(ToyBox)
    Heirlooms(HeirloomsJournal)
    Wardrobe(WardrobeCollectionFrame)
    HookGlobal("MountJournal_InitMountButton", Row)
    HookGlobal("PetJournal_InitPetButton", Row)
    HookGlobal("ToySpellButton_UpdateButton", Spell)
    HookGlobal("HeirloomsJournal_UpdateButton", Spell)
    OnShow(frame, Apply)
end
local ApplyWindow = W.WindowCallback(KEY, Apply)
W.RegisterWindow({ key = KEY, addons = { Blizzard_Collections = true }, apply = ApplyWindow })
W.OnLooksChanged(ApplyWindow)
ns.ForeverCollections = ApplyWindow
