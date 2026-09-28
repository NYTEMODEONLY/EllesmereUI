-- Forever's native HUD editor: decoration only. Never refresh preview units,
-- initialize settings, select layouts, or write native values from this skin.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local T, KEY = W.Theme, "settings" -- existing reskinSettings option
local state = setmetatable({}, { __mode = "k" })
local function Data(frame)
    if not state[frame] then state[frame] = {} end
    return state[frame]
end
local function Flat(texture, r, g, b, a)
    if texture and texture.SetColorTexture then texture:SetColorTexture(r, g, b, a or 1) end
end
local function Font(label) W.Font(label) end -- disabled/validation colors stay native
local function Heading(label) W.Font(label, .9, .9, .9) end
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
local function OnShow(frame, painter)
    if not frame or Data(frame).showHook then return end
    frame:HookScript("OnShow", W.WindowCallback(KEY, painter))
    Data(frame).showHook = true
end
local function TextButton(button)
    if not button then return end
    W.Button(button)
    W.StateButtonLabel(button)
    Font(button.Text or (button.GetFontString and button:GetFontString()))
end
local function Check(frame)
    if not frame then return end
    if frame.Button then W.Checkbox(frame.Button, { stockCheck = true }) end
    Font(frame.Label)
    -- Do not call UpdateDisplay: it sets checked/enabled state and reads CVars.
end
local function Dropdown(frame)
    if not frame then return end
    local label = frame.Text
    local r, g, b, a
    if label and label.GetTextColor then r, g, b, a = label:GetTextColor() end
    W.Dropdown(frame)
    Font(label)
    if r then label:SetTextColor(r, g, b, a) end
end
local function Slider(frame)
    if not frame then return end
    -- MinimalSliderWithSteppersTemplate: only the track/handle artwork changes.
    -- Keep both arrow glyphs, alpha, enabled state, bounds and thumb position.
    local slider = frame.Slider
    if slider then
        for _, key in ipairs({ "Left", "Middle", "Right" }) do
            Flat(slider[key], T.insetR, T.insetG, T.insetB, 1)
        end
        Flat(slider.Thumb, T.accR, T.accG, T.accB, 1)
    end
    for _, key in ipairs({ "LeftText", "RightText", "TopText", "MinText", "MaxText" }) do Font(frame[key]) end
end
local function ScrollBar(bar)
    if not bar then return end
    local arrows = {}
    for _, key in ipairs({ "Back", "Forward" }) do
        local button = bar[key]
        if button and button.Texture then arrows[#arrows + 1] = { button.Texture, button.Texture:GetAlpha() } end
    end
    W.ScrollBar(bar)
    for _, arrow in ipairs(arrows) do arrow[1]:SetAlpha(arrow[2]) end
end
local function Input(box)
    if not box then return end
    Fill(box)
    for _, key in ipairs({ "Left", "Middle", "Right" }) do
        if box[key] then box[key]:SetAlpha(0) end
    end
    Font(box)
    Font(box.Instructions)
end
local function Shell(frame)
    W.Shell(KEY, frame, { noTopBar = true })
    -- Border is a dedicated DialogBorder* NineSlice panel, containing no controls.
    if frame.Border then W.Inset(frame.Border) end
    Heading(frame.Title)
    W.CloseButton(frame.CloseButton)
end
local function Setting(frame)
    Font(frame.Label)
    Dropdown(frame.Dropdown)
    Slider(frame.Slider)
    Check(frame)
end
local function SystemSettings(frame)
    if not frame then return end
    Shell(frame)
    if frame.Buttons then
        TextButton(frame.Buttons.RevertChangesButton)
        Flat(frame.Buttons.Divider, T.brdR, T.brdG, T.brdB, .65)
    end
    if frame.pools and frame.pools.EnumerateActiveByTemplate then
        for _, template in ipairs({ "EditModeSettingDropdownTemplate", "EditModeSettingSliderTemplate", "EditModeSettingCheckboxTemplate" }) do
            for row in frame.pools:EnumerateActiveByTemplate(template) do Setting(row) end
        end
        for button in frame.pools:EnumerateActiveByTemplate("EditModeSystemSettingsDialogExtraButtonTemplate") do
            TextButton(button) -- child NewOptionsFrame badge remains intact
        end
    end
    OnShow(frame, SystemSettings)
    local d = Data(frame)
    if not d.dialogHook and type(frame.UpdateDialog) == "function" then
        -- Runs after the native dialog has acquired and configured all rows.
        -- Never hooks the manager, selected HUD system, or secure unit frames.
        hooksecurefunc(frame, "UpdateDialog", W.WindowCallback(KEY, SystemSettings))
        d.dialogHook = true
    end
end
local function Dialog(frame)
    if not frame then return end
    Shell(frame)
    Heading(frame.EditBoxLabel)
    Heading(frame.NameEditBoxLabel)
    Input(frame.LayoutNameEditBox)
    Check(frame.CharacterSpecificLayoutCheckButton)
    for _, key in ipairs({ "AcceptButton", "CancelButton", "SaveAndProceedButton", "ProceedButton" }) do TextButton(frame[key]) end
    local box = frame.ImportBox
    if box then
        Fill(box)
        for _, key in ipairs({ "TopLeftTex", "TopRightTex", "TopTex", "BottomLeftTex", "BottomRightTex", "BottomTex", "LeftTex", "RightTex", "MiddleTex" }) do
            if box[key] then box[key]:SetAlpha(0) end
        end
        Font(box.EditBox)
        Font(box.EditBox and box.EditBox.Instructions)
        Font(box.CharCount)
        ScrollBar(box.ScrollBar)
    end
    OnShow(frame, Dialog)
end
local function Manager(frame)
    Shell(frame)
    Heading(frame.LayoutLabel)
    Dropdown(frame.LayoutDropdown)
    for _, key in ipairs({ "ShowGridCheckButton", "EnableSnapCheckButton", "EnableAdvancedOptionsCheckButton" }) do Check(frame[key]) end
    Slider(frame.GridSpacingSlider and frame.GridSpacingSlider.Slider)
    TextButton(frame.SaveChangesButton)
    TextButton(frame.RevertAllChangesButton)
    local account = frame.AccountSettings
    if account then
        -- Native collection includes Camelot SwingTimer and TotemActionBar;
        -- no assumptions about availability, shown previews, or future entries.
        for _, checkbox in pairs(account.settingsCheckButtons or {}) do Check(checkbox) end
        local container = account.SettingsContainer
        if container then
            if container.BorderArt then W.Inset(container.BorderArt) end
            ScrollBar(container.ScrollBar)
            local advanced = container.ScrollChild and container.ScrollChild.AdvancedOptionsContainer
            if advanced then
                for _, key in ipairs({ "FramesTitle", "CombatTitle", "MiscTitle" }) do Heading(advanced[key] and advanced[key].Title) end
            end
        end
        if account.Expander then
            Font(account.Expander.Label)
            Flat(account.Expander.Divider, T.brdR, T.brdG, T.brdB, .65)
        end
    end
    OnShow(frame, Manager)
end
local function Apply()
    if not EditModeManagerFrame then return end
    W.ResolveTheme()
    Manager(EditModeManagerFrame)
    SystemSettings(EditModeSystemSettingsDialog)
    for _, name in ipairs({ "EditModeLayoutDialog", "EditModeImportLayoutDialog", "EditModeImportLayoutLinkDialog", "EditModeUnsavedChangesDialog" }) do Dialog(_G[name]) end
end
local ApplyWindow = W.WindowCallback(KEY, Apply)
W.RegisterWindow({ key = KEY, addons = { Blizzard_EditMode = true }, apply = ApplyWindow })
W.OnLooksChanged(ApplyWindow)
ns.ForeverEditMode = ApplyWindow
