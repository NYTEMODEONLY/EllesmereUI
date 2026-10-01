-- Camelot banks equip bags, paginate their slots, and expose native purchase
-- controls. Midnight's fixed-tab replacement cannot represent that structure.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local boot = CreateFrame("Frame")
local installed = false
local function Install()
    local ns = EllesmereUI and EllesmereUI._ModuleNS
    local skin = ns and ns.EllesmereUIBlizzardSkin
    local W = skin and skin.WSkin
    local bank = BankFrame
    if installed or not (W and bank) then return end
    W.ResolveTheme()
    local T = W.Theme
    local state = setmetatable({}, { __mode = "k" })
    local function Data(frame)
        if not state[frame] then state[frame] = {} end
        return state[frame]
    end
    local function Hook(frame, method, fn)
        if not frame or type(frame[method]) ~= "function" then return end
        local d = Data(frame)
        if d[method] then return end
        hooksecurefunc(frame, method, W.WindowCallback("foreverbank", fn))
        d[method] = true
    end
    local function Flat(tex, r, g, b, a)
        if tex and tex.SetColorTexture then tex:SetColorTexture(r, g, b, a or 1) end
    end
    local function Font(fs) W.Font(fs) end -- retain price/quality/disabled colors
    local function Fill(frame)
        if not frame then return end
        local d = Data(frame)
        if not d.bg then
            d.bg = frame:CreateTexture(nil, "BACKGROUND", nil, -7)
            d.bg:SetAllPoints(frame)
        end
        Flat(d.bg, T.insetR, T.insetG, T.insetB, T.insetA)
        W.AddBorder(frame)
    end
    local function FadeKeys(frame, keys)
        if not frame then return end
        for _, key in ipairs(keys) do
            local tex = frame[key]
            if tex and tex.SetAlpha then tex:SetAlpha(0) end
        end
    end
    local nineSliceKeys = { "TopLeftCorner", "TopRightCorner", "BottomLeftCorner", "BottomRightCorner", "TopEdge", "BottomEdge", "LeftEdge", "RightEdge", "Center" }
    local function Chrome(frame)
        if not frame then return end
        FadeKeys(frame.NineSlice or frame, nineSliceKeys)
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
        W.Checkbox(button, { stockCheck = true, boxInset = true })
        Font(button.Text or button.Label)
    end
    local function Input(box)
        if not box then return end
        Fill(box)
        FadeKeys(box, { "Left", "Middle", "Right", "Mid", "IconSelectorPopupNameLeft", "IconSelectorPopupNameMiddle", "IconSelectorPopupNameRight" })
        Font(box)
        Font(box.Instructions)
        -- Search magnifier, clear button and input bindings remain native.
    end
    local function ScrollBar(bar)
        if not bar then return end
        local keep = {}
        for _, key in ipairs({ "Back", "Forward" }) do
            local button = bar[key]
            if button and button.Texture then keep[#keep + 1] = { button.Texture, button.Texture:GetAlpha() } end
        end
        W.ScrollBar(bar)
        for _, saved in ipairs(keep) do saved[1]:SetAlpha(saved[2]) end
    end
    local function Money(frame)
        if not frame then return end
        -- Coin glyphs, totals, red unaffordable costs and native money tooltip
        -- buttons remain native. Change only the font face, never the value.
        for _, key in ipairs({ "GoldButton", "SilverButton", "CopperButton" }) do
            local button = frame[key]
            if button then Font(button.Text or (button.GetFontString and button:GetFontString())) end
        end
    end
    local function Item(button)
        if not button then return end
        Fill(button)
        Flat(button.Background, 0.035, 0.035, 0.035, 0.95)
        local normal = button.GetNormalTexture and button:GetNormalTexture()
        if normal then normal:SetAlpha(0) end -- Camelot slot frame, not its icon
        Font(button.Count)
        Font(button.ItemLevelText)
        -- Keep quality, quest, new-item, search, bag-hover and lock overlays;
        -- they communicate facts that a generic Button skin would remove.
        Hook(button, "Refresh", Item)
        Hook(button, "SetItemLocation", Item)
        Hook(button, "UpdateBackgroundForBankType", Item)
    end
    local function PageTab(tab)
        if not tab then return end
        -- Keep the native clipped-corner art and mask. A rectangular fill or
        -- additional border creates a second box around the actual page tab.
        if tab.Background then tab.Background:SetAlpha(0) end
        if tab.SelectedTexture then tab.SelectedTexture:SetVertexColor(T.accR, T.accG, T.accB) end
        if tab.TabGlow then tab.TabGlow:SetVertexColor(T.accR, T.accG, T.accB) end
        if tab.Border then tab.Border:SetVertexColor(0.4, 0.4, 0.4) end
        -- SetChecked/native selection, page number, icon, bank type and tooltip
        -- are untouched; both character and account page pools use this path.
        Hook(tab, "SetPageInfo", PageTab)
    end
    local function Pool(pool, painter)
        if pool and pool.EnumerateActive then
            for frame in pool:EnumerateActive() do painter(frame) end
        end
    end
    local function Items(panel) Pool(panel.itemButtonPool, Item) end
    local function BagSlots() Pool(bank.itemButtonBagPool, Item) end
    local function Pages() Pool(bank.bankPageTabPool, PageTab) end
    local function TabButtons(panel)
        Pool(panel.bankTabPool, PageTab)
        PageTab(panel.PurchaseTab)
    end
    local function Prompt(frame)
        if not frame then return end
        Fill(frame)
        FadeKeys(frame, { "BottomLeftInner", "BottomRightInner", "TopRightInner", "TopLeftInner", "LeftInner", "RightInner", "TopInner", "BottomInner" })
        Flat(frame.Background, T.insetR, T.insetG, T.insetB, 0.98)
        Font(frame.PromptText)
        Font(frame.Title)
        local cost = frame.TabCostFrame
        if cost then
            W.Font(cost.TabCost, 0.7, 0.7, 0.7) -- static "Cost:" label only
            Money(cost.MoneyDisplay)
            TextButton(cost.PurchaseButton)
        end
    end
    local function Settings(menu)
        if not menu then return end
        Fill(menu)
        Flat(menu.BG, T.bgR, T.bgG, T.bgB, 0.98)
        local border = menu.BorderBox
        if border then
            Chrome(border)
            Font(border.EditBoxHeaderText)
            Font(border.IconSelectionText)
            Input(border.IconSelectorEditBox)
            W.Dropdown(border.IconTypeDropdown)
            TextButton(border.OkayButton)
            TextButton(border.CancelButton)
            local selected = border.SelectedIconArea
            if selected then
                Fill(selected.SelectedIconButton)
                local text = selected.SelectedIconText
                if text then Font(text.SelectedIconHeader); Font(text.SelectedIconDescription) end
            end
        end
        local icons = menu.IconSelector
        if icons then ScrollBar(icons.ScrollBar) end
        local settings = menu.DepositSettingsMenu
        if settings then
            Font(settings.AssignExpansionHeader)
            Font(settings.AssignSettingsHeader)
            Font(settings.CleanUpSettingsHeader)
            for _, key in ipairs({ "AssignEquipmentCheckbox", "AssignConsumablesCheckbox", "AssignProfessionGoodsCheckbox", "AssignReagentsCheckbox", "AssignJunkCheckbox", "IgnoreCleanUpCheckbox" }) do Checkbox(settings[key]) end
            W.Dropdown(settings.ExpansionFilterDropdown)
        end
    end
    local function CleanUpPopup()
        local popup = BankCleanUpConfirmationPopup
        if not popup then return end
        Fill(popup)
        Chrome(popup.Border)
        Font(popup.Text)
        TextButton(popup.AcceptButton)
        TextButton(popup.CancelButton)
        if popup.HidePopupCheckbox then
            Checkbox(popup.HidePopupCheckbox.Checkbox)
            Font(popup.HidePopupCheckbox.Label)
        end
    end
    local Apply = W.WindowCallback("foreverbank", function()
        W.Shell("foreverbank", bank, { noTopBar = true })
        if bank.CloseButton then W.CloseButton(bank.CloseButton) end
        -- The inherited portrait title is TitleContainer.TitleText; Camelot
        -- also declares BankFrameTitleText. Neither is a money value.
        W.Font(bank.TitleContainer and bank.TitleContainer.TitleText, 1, 1, 1)
        W.Font(BankFrameTitleText, 1, 1, 1)
        W.Font(bank.BagText, 0.82, 0.82, 0.82)
        W.Font(bank.BagCost, 0.7, 0.7, 0.7)
        Input(bank.BankItemSearchBox)
        -- Flatten the identified decorative divider, not all root textures.
        if bank.GetRegions then
            for _, region in ipairs({ bank:GetRegions() }) do
                if region.GetAtlas and region:GetAtlas() == "bank-divider" then
                    Flat(region, T.brdR, T.brdG, T.brdB, 0.8)
                end
            end
        end
        local panel = bank.BankPanel
        if panel then
            Chrome(panel.NineSlice)
            FadeKeys(panel.EdgeShadows, { "LeftTopCorner-Shadow", "LeftBottomCorner-Shadow", "RightTopCorner-Shadow", "RightBottomCorner-Shadow", "Right-Shadow", "Left-Shadow", "Bottom-Shadow", "Top-Shadow" })
            Fill(panel.AutoSortButton) -- retain its native sort glyph and tooltip
            Font(panel.Header and panel.Header.Text)
            Money(panel.MoneyDisplay)
            TextButton(panel.PurchaseButton)
            local money = panel.MoneyFrame
            if money then
                -- ThinGoldEdgeTemplate is a dedicated three-texture chrome
                -- frame. Its sibling MoneyDisplay owns all coins and values.
                if money.Border then W.Panel(money.Border, { inset = true }) end
                Money(money.MoneyDisplay)
                TextButton(money.WithdrawButton)
                TextButton(money.DepositButton)
            end
            local deposit = panel.AutoDepositFrame
            if deposit then TextButton(deposit.DepositButton); Checkbox(deposit.IncludeReagentsCheckbox) end
            Prompt(panel.LockPrompt)
            Prompt(panel.PurchasePrompt)
            Settings(panel.TabSettingsMenu)
            Items(panel)
            TabButtons(panel)
            Hook(panel, "GenerateItemSlotsForSelectedTab", Items)
            Hook(panel, "RefreshBankTabs", TabButtons)
        end
        BagSlots()
        Pages()
        CleanUpPopup()
        -- No calls to SetTab, purchase, sort, transfer, deposit or withdraw:
        -- native code owns all availability, item identity and interactions.
        if EUI_FOREVER_STATUS then
            EUI_FOREVER_STATUS.bank = "Ellesmere bank items, pages, bags, prompts, search and money controls; native actions"
        end
    end)
    Apply()
    bank:HookScript("OnShow", Apply)
    Hook(bank, "RefreshBagButtons", BagSlots)
    Hook(bank, "RefreshPageTabs", Pages)
    W.OnLooksChanged(Apply)
    installed = true
end
boot:RegisterEvent("PLAYER_LOGIN")
boot:RegisterEvent("ADDON_LOADED")
boot:SetScript("OnEvent", function(_, event, addon)
    if event == "PLAYER_LOGIN" or addon == "Blizzard_UIPanels_Game" or addon == "EllesmereUIBlizzardSkin" then
        Install()
    end
end)
