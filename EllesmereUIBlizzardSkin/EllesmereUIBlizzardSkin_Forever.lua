-- Forever (Camelot) uses native side tabs and independently collapsible panes.
-- Keep native scripts, anchors, models, item slots and progression controls.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
-- Each dedicated surface adapter tints native clipped-corner tab selection.
-- Do not add a second square border, rectangular fill, or selection strip here.

local function Shell(key, frame)
    if not frame then return end
    W.Shell(key, frame, { noTopBar = true })
    W.Font(frame.TitleContainer and frame.TitleContainer.TitleText, 1, 1, 1)
    if frame.CloseButton then W.CloseButton(frame.CloseButton) end
end

local function Character()
    local f = CharacterFrame
    if not (f and f.ModeTabs and f.RightPaneHost) then return end
    Shell("charsheet", f)
    -- These hosts contain background art only; their child content stays native.
    if f.LeftPaneHost then W.Shell("charsheet", f.LeftPaneHost, { noTopBar = true, noBorder = true }) end
    W.Shell("charsheet", f.RightPaneHost, { noTopBar = true, noBorder = true })
    if ns.ForeverCharacter then ns.ForeverCharacter() end
    if ns.ForeverEquipment then ns.ForeverEquipment() end
    if ns.ForeverItemLevel then ns.ForeverItemLevel() end
    if ns.ForeverRefreshOfficialCharacterStats then ns.ForeverRefreshOfficialCharacterStats() end
    -- Never move CharacterFrameInsetRight, alter tab selection, or replace
    -- RefreshDisplay: each mode supplies its own detail pane and native width.
    if EUI_FOREVER_STATUS then EUI_FOREVER_STATUS.character = "Forever six-mode skin; native detail panes" end
end

local function Inspect()
    Shell("inspect", InspectFrame)
    if ns.ForeverInspect then ns.ForeverInspect() end
    if ns.ForeverEquipment then ns.ForeverEquipment() end
    if ns.ForeverItemLevel then ns.ForeverItemLevel() end
    -- Camelot's ranged slot, talent inspection and model controls stay intact.
    if InspectFrame and EUI_FOREVER_STATUS then EUI_FOREVER_STATUS.inspect = "Forever equipment, model, guild and talent controls; native inspection" end
end

local function Legacy()
    local f = LegacySystemFrame
    if not f then return end
    -- The imported achievement-window style becomes the Legacy style in Forever.
    Shell("achievements", f)
    if ns.ForeverLegacy then ns.ForeverLegacy() end
    -- Reward track, challenges, tree nodes, claim/reset buttons and point
    -- calculations belong to the beta. Do not apply AchievementFrame row hacks.
    if EUI_FOREVER_STATUS then EUI_FOREVER_STATUS.legacy = "Legacy rewards, challenges and tree; native controls" end
end

W.RegisterWindow({ key = "charsheet", apply = W.WindowCallback("charsheet", Character) })
W.RegisterWindow({ key = "inspect", addons = { Blizzard_InspectUI = true }, apply = W.WindowCallback("inspect", Inspect) })
W.RegisterWindow({ key = "achievements", addons = { Blizzard_LegacySystem = true }, apply = W.WindowCallback("achievements", Legacy) })
EllesmereUI.ApplyThemedCharacterSheet = W.WindowCallback("charsheet", Character)
EllesmereUI.ApplyThemedInspectSheet = W.WindowCallback("inspect", Inspect)
