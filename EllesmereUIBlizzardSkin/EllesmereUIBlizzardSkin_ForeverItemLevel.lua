-- Native client averages; never substitute a naive average of bag contents.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local cards, watched = {}, setmetatable({}, { __mode = "k" })
local displayed = { charsheet = "not rendered", inspect = "not rendered" }
local readyGUID, pending, requestHooked
local function Plain(v) return not (issecretvalue and issecretvalue(v)) end
local function Number(v)
    return Plain(v) and type(v) == "number" and v == v and v >= 0 and v < math.huge
end
local function String(v) return Plain(v) and type(v) == "string" and v ~= "" end
local function Read(fn, ...)
    if type(fn) ~= "function" then return false end
    return pcall(fn, ...)
end
local function Visible(frame)
    if not frame then return false end
    local ok, shown = Read(frame.IsVisible or frame.IsShown, frame)
    return ok and Plain(shown) and shown == true
end
local function GUID()
    local unit = InspectFrame and InspectFrame.unit
    if not String(unit) then return end
    local ok, guid = Read(UnitGUID, unit)
    if ok and String(guid) then return guid, unit end
end
local function Value(value, ok)
    if not ok or not Plain(value) then return "Unavailable" end
    if value == nil then return "Loading..." end
    if not Number(value) then return "Unavailable" end
    return string.format("%.2f", value)
end
local function Hide(key)
    local card = cards[key]
    if card then
        card:Hide()
        if GameTooltip and GameTooltip.IsOwned and GameTooltip:IsOwned(card) then GameTooltip:Hide() end
    end
end
local function New(key, parent, controls, inspect)
    if cards[key] then return cards[key] end
    local card = CreateFrame("Frame", nil, parent)
    -- Camelot reserves the band below model controls and above the first
    -- character equipment row. Inspect has only a 76px center gap between
    -- the two 80px inward gear-annotation lanes, so it uses a narrow two-line
    -- summary. Keep its hover rectangle out of those native item/tooltip lanes.
    card:SetPoint("TOP", controls, "BOTTOM", 0, inspect and -4 or -2)
    card:SetSize(inspect and 60 or 280, inspect and 26 or 14)
    card:EnableMouse(true)
    card.label = card:CreateFontString(nil, "OVERLAY")
    if inspect then
        -- Do not put a newline in a non-wrapping FontString: the client can
        -- render only "Equipped" and clip the value. Give each row its own
        -- bounded region, within the existing narrow equipment-label lane.
        card.label:SetPoint("TOP", card, "TOP", 0, 0)
        card.label:SetSize(60, 12)
        card.label:SetJustifyV("MIDDLE")
        card.value = card:CreateFontString(nil, "OVERLAY")
        card.value:SetPoint("TOP", card.label, "BOTTOM", 0, 0)
        card.value:SetSize(60, 14)
        card.value:SetJustifyH("CENTER")
        card.value:SetJustifyV("MIDDLE")
        card.value:SetWordWrap(false)
        card.value:SetFont(STANDARD_TEXT_FONT, 10, "")
    else
        card.label:SetAllPoints(card)
    end
    card.label:SetJustifyH("CENTER")
    card.label:SetWordWrap(false)
    card.label:SetFont(STANDARD_TEXT_FONT, inspect and 10 or 11, "")
    card:SetScript("OnEnter", function(self)
        if not GameTooltip then return end
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:SetText("Average item level")
        GameTooltip:AddLine(inspect and "Equipped: the inspected character's native equipped average. Other players' bag gear is not available."
            or "Equipped: gear currently worn. Overall: the client's native overall average.", 0.85, 0.85, 0.85, true)
        if not inspect and String(STAT_AVERAGE_ITEM_LEVEL_TOOLTIP) then
            GameTooltip:AddLine(STAT_AVERAGE_ITEM_LEVEL_TOOLTIP, 0.85, 0.85, 0.85, true)
        end
        GameTooltip:Show()
    end)
    card:SetScript("OnLeave", function(self)
        if GameTooltip and GameTooltip.IsOwned and GameTooltip:IsOwned(self) then GameTooltip:Hide() end
    end)
    cards[key] = card
    return card
end
local function Paint(key, equipped, overall, inspect)
    local parent = inspect and InspectPaperDollFrame or PaperDollItemsFrame
    local model = inspect and InspectModelFrame or CharacterModelScene
    local controls = model and (model.ControlFrame or model.controlFrame)
    if not (parent and controls) or W.GetStyle(key) == "off" or not Visible(parent) then Hide(key); return end
    local card = New(key, parent, controls, inspect)
    W.Font(card.label, W.Theme.accR, W.Theme.accG, W.Theme.accB)
    local text = inspect and ("Equipped\n" .. equipped) or ("Equipped " .. equipped .. "   |   Overall " .. overall)
    if inspect then
        W.Font(card.value, W.Theme.accR, W.Theme.accG, W.Theme.accB)
        card.label:SetText("Equipped")
        card.value:SetText(equipped)
    else
        card.label:SetText(text)
    end
    displayed[key] = text
    card:Show()
end
local function Refresh()
    if Visible(PaperDollItemsFrame) and W.GetStyle("charsheet") ~= "off" then
        local ok, overall, equipped = Read(GetAverageItemLevel)
        Paint("charsheet", Value(equipped, ok), Value(overall, ok), false)
    else Hide("charsheet") end
    if not Visible(InspectPaperDollFrame) or W.GetStyle("inspect") == "off" then Hide("inspect"); return end
    local guid, unit = GUID()
    local fn = C_PaperDollInfo and C_PaperDollInfo.GetInspectItemLevel
    local text = "Loading..."
    if type(fn) ~= "function" then text = "Unavailable"
    elseif guid and readyGUID == guid then
        local ok, equipped = Read(fn, unit)
        -- The token may change while a client API is reading it. Never publish
        -- an old result under a different inspected character's identity.
        if GUID() == guid then text = Value(equipped, ok) else readyGUID = nil end
    end
    Paint("inspect", text, nil, true)
end
local function Queue()
    if pending then return end
    pending = true
    C_Timer.After(0, function() pending = false; ns.ForeverItemLevel() end)
end
local function Watch(frame, key, invalidate)
    if not frame or watched[frame] then return end
    watched[frame] = true
    frame:HookScript("OnShow", Queue)
    frame:HookScript("OnHide", function()
        if invalidate then readyGUID = nil end
        Hide(key)
    end)
end
function ns.ForeverItemLevel()
    Watch(PaperDollItemsFrame, "charsheet")
    Watch(InspectPaperDollFrame, "inspect")
    Watch(InspectFrame, "inspect", true)
    if not requestHooked and type(NotifyInspect) == "function" then
        -- Observe the native request lifecycle, including same-GUID re-inspects.
        -- Never request/clear inspect data ourselves or write native unit fields.
        hooksecurefunc("NotifyInspect", function() readyGUID = nil; Hide("inspect"); Queue() end)
        requestHooked = true
    end
    Refresh()
end
local driver = CreateFrame("Frame")
for _, event in ipairs({ "ADDON_LOADED", "PLAYER_ENTERING_WORLD", "PLAYER_EQUIPMENT_CHANGED", "UNIT_INVENTORY_CHANGED",
    "BAG_UPDATE_DELAYED", "ITEM_DATA_LOAD_RESULT", "GET_ITEM_INFO_RECEIVED", "PLAYER_AVG_ITEM_LEVEL_UPDATE",
    "INSPECT_READY", "PLAYER_TARGET_CHANGED", "GROUP_ROSTER_UPDATE" }) do
    driver:RegisterEvent(event)
end
driver:SetScript("OnEvent", function(_, event, arg)
    if event == "INSPECT_READY" then
        local guid = GUID()
        readyGUID = String(arg) and guid and arg == guid and guid or nil
    elseif event == "PLAYER_TARGET_CHANGED" or event == "GROUP_ROSTER_UPDATE" then
        if GUID() ~= readyGUID then readyGUID = nil; Hide("inspect") end
    elseif event == "UNIT_INVENTORY_CHANGED" and (not Plain(arg) or arg ~= "player") then return end
    Queue()
end)
W.OnLooksChanged(ns.ForeverItemLevel)
function ns.ForeverItemLevelEvidence(lines)
    -- Cached display strings only: no extra inventory/inspect queries, identities
    -- or protected values are read while building a diagnostic report.
    lines[#lines+1] = "Native item-level APIs: player=" .. tostring(type(GetAverageItemLevel) == "function")
        .. " inspect=" .. tostring(C_PaperDollInfo ~= nil and type(C_PaperDollInfo.GetInspectItemLevel) == "function")
    for _, key in ipairs({ "charsheet", "inspect" }) do
        lines[#lines+1] = "Item-level summary " .. key .. ": visible=" .. tostring(Visible(cards[key]))
            .. " last rendered=" .. displayed[key]:gsub("\n", " / ")
    end
end
Queue()
