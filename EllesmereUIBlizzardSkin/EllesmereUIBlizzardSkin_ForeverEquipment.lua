-- Forever equipment annotations. Native slots, item data, flyouts, tooltips,
-- durability, cooldowns and equipment actions remain owned by Blizzard.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local W = ns.WSkin
if not W then return end
local states = setmetatable({}, { __mode = "k" })
local requested, watched = {}, setmetatable({}, { __mode = "k" })
local pending, driver
local contexts = {
    { key = "charsheet", prefix = "Character", frameName = "PaperDollFrame", levelKey = "showItemLevel", enchantKey = "showEnchants" },
    { key = "inspect", prefix = "Inspect", frameName = "InspectPaperDollFrame", levelKey = "inspectShowItemLevel", enchantKey = "inspectShowEnchants" },
}
local function ResetEvidence(context)
    context.evidence = { slots = 0, equipped = 0, levels = 0, enchants = 0, gems = 0, pending = 0 }
end
for _, context in ipairs(contexts) do ResetEvidence(context) end
local slots = {
    {"Head", "left"}, {"Neck", "left"}, {"Shoulder", "left"}, {"Back", "left"},
    {"Chest", "left"}, {"Shirt", "left"}, {"Tabard", "left"}, {"Wrist", "left"}, {"Hands", "right"}, {"Waist", "right"},
    {"Legs", "right"}, {"Feet", "right"}, {"Finger0", "right"}, {"Finger1", "right"},
    {"Trinket0", "right"}, {"Trinket1", "right"}, {"MainHand", "bottom"},
    {"SecondaryHand", "bottom"}, {"Ranged", "bottom"}, {"Ammo", "bottom"},
}
local function Plain(value) return not (issecretvalue and issecretvalue(value)) end
local function Number(value) return Plain(value) and type(value) == "number" and value == value and value > -math.huge and value < math.huge end
local function String(value) return Plain(value) and type(value) == "string" and value ~= "" end
local function Read(fn, ...)
    if type(fn) ~= "function" then return end
    local ok, a, b, c, d, e = pcall(fn, ...)
    if ok then return a, b, c, d, e end
end
local function Visible(frame)
    local shown = frame and Read(frame.IsVisible or frame.IsShown, frame)
    return Plain(shown) and shown == true
end
local function Identity(context)
    if context.key == "charsheet" then return "player", "player" end
    local unit = InspectFrame and InspectFrame.unit
    if not String(unit) then return end
    local guid = Read(UnitGUID, unit)
    if String(guid) then return unit, guid end
end
local function Current(context, unit, guid)
    local currentUnit, currentGUID = Identity(context)
    return unit ~= nil and currentUnit == unit and currentGUID == guid
        and (context.key ~= "inspect" or context.readyGUID == guid)
        and Visible(_G[context.frameName])
        and (context.key ~= "inspect" or Visible(InspectFrame))
end
local function Link(unit, slotID)
    local link = Read(GetInventoryItemLink, unit, slotID)
    if String(link) then return link end
end
local function Request(id)
    if not Number(id) or id <= 0 or requested[id] then return end
    if C_Item and type(C_Item.RequestLoadItemDataByID) == "function" then
        requested[id] = true
        Read(C_Item.RequestLoadItemDataByID, id)
    end
end
local function Queue()
    if pending then return end
    pending = true
    C_Timer.After(0, function() pending = false; ns.ForeverEquipment() end)
end
local function Hide(data)
    data.host:Hide()
    data.link, data.enchantText = nil, nil
    if GameTooltip and GameTooltip.IsOwned and GameTooltip:IsOwned(data.hit) then GameTooltip:Hide() end
end
local function HideAll(context)
    for _, data in pairs(states) do if data.context == context then Hide(data) end end
    ResetEvidence(context)
end
local function EnchantPattern()
    if not String(ENCHANTED_TOOLTIP_LINE) then return end
    local head, tail = ENCHANTED_TOOLTIP_LINE:match("^(.-)%%s(.*)$")
    if not head then return end
    local function Escape(s) return (s:gsub("([%(%)%.%[%]%^%$%*%+%-%?%%])", "%%%1")) end
    return "^" .. Escape(head) .. "(.+)" .. Escape(tail) .. "$"
end
local function EnchantText(text, full)
    local raw = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
    local pattern = EnchantPattern()
    raw = (pattern and raw:match(pattern)) or raw
    if full then return raw end
    -- Only abbreviate a recognized, already-present stat and numeric bonus.
    -- Other locales and effects keep their actual text, clipped by the label.
    local locale = Read(GetLocale)
    if Plain(locale) and (not locale or locale == "enUS" or locale == "enGB") then
        local short = { Stamina = "Stam", Strength = "Str", Agility = "Agi", Intellect = "Int", Spirit = "Spirit" }
        local stat, value = raw:match("^([%a ]+) ([%+%-]%d+)$")
        if not stat then value, stat = raw:match("^([%+%-]%d+) ([%a ]+)$") end
        if stat and short[stat] then return value .. " " .. short[stat] end
    end
    return raw
end
local function EnchantName(unit, slotID)
    local data = Read(C_TooltipInfo and C_TooltipInfo.GetInventoryItem, unit, slotID)
    if not Plain(data) or type(data) ~= "table" then return end
    local lines = data.lines
    if not Plain(lines) or type(lines) ~= "table" then return end
    local types = Enum and Enum.TooltipDataLineType
    local permanent = types and types.ItemEnchantmentPermanent
    local pattern = EnchantPattern()
    for _, line in ipairs(lines) do
        if Plain(line) and type(line) == "table" then
            local text, kind = line.leftText, line.type
            if String(text) and Plain(kind) then
                -- Preserve localized wording. Socket bonuses / temporary
                -- weapon imbues are not permanent item enchantments.
                local raw = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
                local socketBonus = types and types.GemSocketEnchantment
                local temporary = types and types.ItemEnchantmentTemporary
                if (permanent and kind == permanent)
                    or (not (socketBonus and kind == socketBonus) and not (temporary and kind == temporary) and pattern and raw:match(pattern)) then return text end
            end
        end
    end
end
local function Font(label, key, defaultSize, db, maximum)
    local size = db["charSheet" .. key .. "Size"]
    if not Number(size) then size = defaultSize end
    size = math.max(6, math.min(maximum or 24, 24, size))
    local path = EllesmereUI and EllesmereUI.GetFontPath and EllesmereUI.GetFontPath("blizzardSkin") or STANDARD_TEXT_FONT
    label:SetFont(path, size, db["charSheet" .. key .. "Outline"] and "OUTLINE" or "")
    label:SetShadowColor(0, 0, 0, db["charSheet" .. key .. "Shadow"] and 1 or 0)
    label:SetShadowOffset(1, -1)
    return size
end
local function New(context, slot, kind)
    local host = CreateFrame("Frame", nil, context.key == "charsheet" and (PaperDollItemsFrame or PaperDollFrame) or _G[context.frameName])
    host:SetAllPoints(slot)
    host:EnableMouse(false)
    local data = { host = host, slot = slot, kind = kind, context = context, gems = {} }
    states[slot] = data
    data.level = host:CreateFontString(nil, "OVERLAY")
    data.name = host:CreateFontString(nil, "OVERLAY")
    data.name:SetWordWrap(false)
    data.name:SetMaxLines(1)
    data.hit = CreateFrame("Frame", nil, host)
    data.hit:EnableMouse(true)
    data.indicator = data.hit:CreateTexture(nil, "OVERLAY")
    data.indicator:SetTexture("Interface\\RaidFrame\\ReadyCheck-Ready")
    data.indicator:SetSize(14, 14)
    data.indicator:SetPoint("CENTER")
    data.hit:SetScript("OnEnter", function(self)
        -- Revalidate at hover time as well as paint time: delayed item events
        -- must never leave the previous item's enchant tooltip on a new item.
        if not data.link or not Current(context, data.unit, data.guid) or Link(data.unit, data.slotID) ~= data.link or W.GetStyle(context.key) == "off" then return end
        if not GameTooltip then return end
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        if String(data.enchantText) then GameTooltip:SetText(data.enchantText)
        else GameTooltip:SetInventoryItem(data.unit, data.slotID) end
        GameTooltip:Show()
    end)
    data.hit:SetScript("OnLeave", function(self)
        if GameTooltip and GameTooltip.IsOwned and GameTooltip:IsOwned(self) then GameTooltip:Hide() end
    end)
    return data
end
local function Layout(data, db)
    local slot, host = data.slot, data.host
    local frameLevel = Read(slot.GetFrameLevel, slot)
    if Number(frameLevel) then host:SetFrameLevel(frameLevel + 1) end
    local alpha = Read(slot.GetAlpha, slot)
    host:SetAlpha(Number(alpha) and alpha or 1)
    local levelSize = Font(data.level, "ItemLevel", 11, db)
    local enchantSize = Font(data.name, "Enchant", 9, db)
    local hitHeight = 14
    local width = 80
    if data.kind == "bottom" then
        local nativeWidth = Read(slot.GetWidth, slot)
        width = Number(nativeWidth) and math.max(14, nativeWidth) or 27
        -- Offhand/ranged gap is only 6px; never put Retail's rightward hover
        -- frame over the next slot. All weapon/ammo annotations stay bounded.
        levelSize = Font(data.level, "ItemLevel", 11, db, 14)
        enchantSize = Font(data.name, "Enchant", 9, db, 11)
        data.level:SetPoint("BOTTOM", slot, "TOP", 0, 2)
        data.name:SetPoint("BOTTOM", slot, "TOP", 0, 4 + levelSize)
        data.hit:SetPoint("BOTTOM", slot, "TOP", 0, 4 + levelSize)
        data.gemY = 6 + levelSize + hitHeight
        data.level:SetJustifyH("CENTER"); data.name:SetJustifyH("CENTER")
    else
        -- Fit both text rows and the 9px gem row inside the native slot pitch.
        -- Large font preferences are bounded for this narrow surface, without
        -- changing the saved sizes or changing native equipment geometry.
        local height = Read(slot.GetHeight, slot)
        local rowHeight = math.max(34, math.min(48, (Number(height) and height or 37) + 2))
        local available = rowHeight - (db.showGems ~= false and 9 or 0) - 4
        local nameHeight = math.max(14, math.min(enchantSize, available / 2))
        levelSize = Font(data.level, "ItemLevel", 11, db, available - nameHeight)
        enchantSize = Font(data.name, "Enchant", 9, db, available - levelSize)
        hitHeight = math.max(14, enchantSize)
        local levelY = rowHeight / 2 - levelSize / 2
        local enchantY = rowHeight / 2 - levelSize - 2 - hitHeight / 2
        data.gemY = rowHeight / 2 - levelSize - 2 - hitHeight - 2 - 4.5
        local leftSlot, rightSlot = _G[data.context.prefix .. "HeadSlot"], _G[data.context.prefix .. "HandsSlot"]
        local left = leftSlot and Read(leftSlot.GetRight, leftSlot)
        local right = rightSlot and Read(rightSlot.GetLeft, rightSlot)
        if Number(left) and Number(right) then width = math.max(14, math.min(80, (right - left - 10) / 2)) end
        -- Inspect's wrist/trinket rows share vertical space with the weapon
        -- annotations. Keep side lanes outside the native weapon columns:
        -- 338px frame -> left 50..94, right 242..286; ranged ends at 237.
        if data.context.key == "inspect" then width = math.min(width, 44) end
        local side, anchor, offset = "LEFT", "RIGHT", 5
        if data.kind == "right" then side, anchor, offset = "RIGHT", "LEFT", -5 end
        data.level:SetPoint(side, slot, anchor, offset, levelY)
        data.name:SetPoint(side, slot, anchor, offset, enchantY)
        data.hit:SetPoint(side, slot, anchor, offset, enchantY)
        data.level:SetJustifyH(side); data.name:SetJustifyH(side)
    end
    data.width = width
    data.level:SetWidth(width); data.name:SetWidth(width)
    if data.context.key == "charsheet" and ns.ForeverOfficialCharacterStats then
        data.level:ClearAllPoints()
        data.level:SetPoint("TOPRIGHT", slot, "TOPRIGHT", -1, -1)
        data.level:SetJustifyH("RIGHT")
        data.level:SetWidth(0)
        Font(data.level, "ItemLevel", 11, db, 11)
    end
    data.hit:SetSize(width, hitHeight)
    local enabled = Read(slot.IsEnabled, slot)
    data.hit:EnableMouse(Plain(enabled) and enabled ~= false)
    if Plain(enabled) and enabled == false then host:SetAlpha((Number(alpha) and alpha or 1) * .5) end
end
local function Paint(context, unit, guid, slot, kind, db)
    local evidence = context.evidence
    local data = states[slot]
    if not Visible(slot) then if data then Hide(data) end; return end
    local id = Read(slot.GetID, slot)
    if not Number(id) or id < 0 then if data then Hide(data) end; return end
    local link = Link(unit, id)
    if not link then if data then Hide(data) end; return end
    data = data or New(context, slot, kind)
    if data.link ~= link or data.unit ~= unit or data.guid ~= guid then Hide(data) end
    local previousName = data.enchantText
    local ownedTooltip = GameTooltip and GameTooltip.IsOwned and GameTooltip:IsOwned(data.hit)
    data.slotID, data.link, data.unit, data.guid = id, link, unit, guid
    data.enchantText = nil
    Layout(data, db)
    data.level:Hide(); data.name:Hide(); data.indicator:Hide()
    for _, icon in pairs(data.gems) do icon:Hide() end
    evidence.equipped = evidence.equipped + 1
    local itemID, enchantID = link:match("item:(%d+):(%d*)")
    itemID, enchantID = tonumber(itemID), tonumber(enchantID)
    -- Shirt (4) and tabard (19) never participate in item-level displays,
    -- regardless of rarity. This applies to both Character and Inspect.
    local tracksItemLevel = id ~= 4 and id ~= 19
    local level = tracksItemLevel and Read(C_Item and C_Item.GetDetailedItemLevelInfo, link)
    local quality = Read(GetInventoryItemQuality, unit, id)
    local color = Number(quality) and ITEM_QUALITY_COLORS and ITEM_QUALITY_COLORS[quality]
    if db.charSheetColorItemLevel == false then color = nil end
    if db.charSheetItemLevelUseColor and type(db.charSheetItemLevelColor) == "table" then color = db.charSheetItemLevelColor end
    local r, g, b = 1, 1, 1
    if color and Number(color.r) and Number(color.g) and Number(color.b) then r, g, b = color.r, color.g, color.b end
    data.level:SetTextColor(r, g, b)
    -- Enchant effects carry their own status color, independent of item rarity.
    data.name:SetTextColor(0.1, 1, 0.1)
    if tracksItemLevel and db[context.levelKey] ~= false and Number(level) and level > 0 then
        data.level:SetText(tostring(math.floor(level))); data.level:Show(); evidence.levels = evidence.levels + 1
    elseif tracksItemLevel and not Number(level) then Request(itemID); evidence.pending = evidence.pending + 1 end
    -- A positive permanent-enchant field is evidence; absence is NOT evidence
    -- that the slot is eligible or missing an enchant in this new ruleset.
    local hasEnchant = db[context.enchantKey] ~= false and enchantID and enchantID > 0
    if hasEnchant then
        data.enchantText = EnchantName(unit, id)
        if data.enchantText then
            data.name:SetText(EnchantText(data.enchantText, db.charSheetEnchantNames)); data.name:Show()
        else data.indicator:Show() end
        evidence.enchants = evidence.enchants + 1
        if not data.enchantText then evidence.pending = evidence.pending + 1 end
    end
    data.hit:SetShown(hasEnchant and true or false)
    if ownedTooltip then
        if not hasEnchant then GameTooltip:Hide()
        elseif data.enchantText and data.enchantText ~= previousName then
            GameTooltip:SetText(data.enchantText); GameTooltip:Show()
        end
    end
    -- Native sockets already display real gems in timerunning. Avoid duplicate
    -- icons when that native display is active; do not change its visibility.
    if db.showGems ~= false and not Visible(slot.SocketDisplay) and C_Item then
        local count = Read(C_Item.GetItemNumSockets, link)
        if Number(count) and count >= 0 and count <= 8 then
            for index = 1, math.floor(count) do
                local gemID = Read(C_Item.GetItemGemID, link, index)
                if Number(gemID) and gemID > 0 then
                    local texture = Read(C_Item.GetItemIconByID, gemID)
                    if (Number(texture) and texture > 0) or String(texture) then
                        local icon = data.gems[index]
                        if not icon then icon = data.host:CreateTexture(nil, "OVERLAY"); data.gems[index] = icon end
                        local size, spacing = 9, 2
                        local width = data.width
                        if Number(width) then
                            spacing = math.min(2, math.max(0, (width-count) / math.max(1, count-1)))
                            size = math.max(1, math.min(9, (width - (count-1)*spacing) / count))
                        end
                        icon:SetTexture(texture); icon:SetSize(size, size)
                        local x = (index - (count+1)/2) * (size+spacing)
                        if kind == "bottom" then icon:SetPoint("BOTTOM", slot, "TOP", x, data.gemY)
                        elseif kind == "left" then icon:SetPoint("LEFT", slot, "RIGHT", 5+(index-1)*(size+spacing), data.gemY)
                        else icon:SetPoint("RIGHT", slot, "LEFT", -5-(index-1)*(size+spacing), data.gemY) end
                        icon:Show(); evidence.gems = evidence.gems + 1
                    else Request(gemID); evidence.pending = evidence.pending + 1 end
                end
            end
        end
    end
    -- All reads were synchronous, but keep the final identity guard explicit.
    if not Current(context, unit, guid) or Link(unit, id) ~= link then Hide(data); Queue(); return end
    data.host:Show()
end
local function PaintAll(context)
    ResetEvidence(context)
    local unit, guid = Identity(context)
    if not Current(context, unit, guid) then HideAll(context); return end
    local db = EllesmereUIDB or {}
    for _, entry in ipairs(slots) do
        local slot = _G[context.prefix .. entry[1] .. "Slot"]
        if slot then
            context.evidence.slots = context.evidence.slots + 1
            if not watched[slot] then
                watched[slot] = true
                slot:HookScript("OnShow", Queue)
                slot:HookScript("OnHide", function() if states[slot] then Hide(states[slot]) end; Queue() end)
            end
            Paint(context, unit, guid, slot, entry[2], db)
        end
    end
end
for _, context in ipairs(contexts) do
    context.paint = W.WindowCallback(context.key, function() PaintAll(context) end)
end
local function InvalidateInspect()
    contexts[2].readyGUID = nil
    HideAll(contexts[2])
end
local function WatchFrames(context)
    local frame = _G[context.frameName]
    if frame and not watched[frame] then
        watched[frame] = true
        frame:HookScript("OnShow", Queue)
        frame:HookScript("OnHide", function() HideAll(context) end)
    end
    if context.key ~= "inspect" or not InspectFrame then return end
    if not watched[InspectFrame] then
        watched[InspectFrame] = true
        -- A module enabled while inspection is already visible may adopt that
        -- native completed inspection. Future targets require INSPECT_READY.
        if Visible(InspectFrame) then local _, guid = Identity(context); context.readyGUID = guid end
        InspectFrame:HookScript("OnShow", Queue)
        InspectFrame:HookScript("OnHide", InvalidateInspect)
    end
    if not context.requestHook and type(InspectFrame_Show) == "function" then
        context.requestHook = true
        hooksecurefunc("InspectFrame_Show", function() InvalidateInspect(); Queue() end)
    end
    if not context.changeHook and type(InspectFrame.UnitChanged) == "function" then
        context.changeHook = true
        hooksecurefunc(InspectFrame, "UnitChanged", function() InvalidateInspect(); Queue() end)
    end
end
function ns.ForeverEquipment()
    if not driver then
        driver = CreateFrame("Frame")
        for _, event in ipairs({ "PLAYER_EQUIPMENT_CHANGED", "UNIT_INVENTORY_CHANGED", "GET_ITEM_INFO_RECEIVED", "ITEM_DATA_LOAD_RESULT", "SOCKET_INFO_UPDATE", "TOOLTIP_DATA_UPDATE", "PLAYER_REGEN_ENABLED", "INSPECT_READY", "PLAYER_TARGET_CHANGED", "GROUP_ROSTER_UPDATE", "ADDON_LOADED" }) do driver:RegisterEvent(event) end
        driver:SetScript("OnEvent", function(_, event, unit)
            local inspect = contexts[2]
            local currentUnit, guid = Identity(inspect)
            if inspect.readyGUID and inspect.readyGUID ~= guid then InvalidateInspect() end
            if event == "INSPECT_READY" then
                if not String(unit) or unit ~= guid then return end
                inspect.readyGUID = guid
            elseif (event == "PLAYER_TARGET_CHANGED" and currentUnit == "target")
                or (event == "GROUP_ROSTER_UPDATE" and currentUnit and currentUnit ~= "target") then
                InvalidateInspect()
            elseif event == "UNIT_INVENTORY_CHANGED" then
                if not String(unit) or (unit ~= "player" and unit ~= currentUnit) then return end
            elseif event == "ADDON_LOADED" then
                if unit ~= "Blizzard_InspectUI" then return end
                WatchFrames(inspect)
            end
            -- Hide immediately on identity changes, before a queued repaint or
            -- an old item-data completion can expose the previous character.
            if Visible(PaperDollFrame) or Visible(InspectFrame) then Queue() end
        end)
    end
    for _, context in ipairs(contexts) do
        WatchFrames(context)
        local unit, guid = Identity(context)
        if W.GetStyle(context.key) == "off" or not Current(context, unit, guid)
            or (InCombatLockdown and InCombatLockdown()) then HideAll(context)
        else context.paint() end
    end
end
W.OnLooksChanged(ns.ForeverEquipment)
-- The shared Fonts page uses these bridges even when the Retail character
-- implementation is gated off. Chain any existing owner; never replace it.
if EllesmereUI then
    for _, key in ipairs({ "_refreshCharSheetSlotLabels", "_applyCharSheetTextSizes", "_refreshItemLevelVisibility", "_refreshEnchantsVisibility", "_refreshGemsVisibility", "_refreshInspectSlotLabels", "_refreshInspectItemLevelVisibility", "_refreshInspectEnchantsVisibility" }) do
        if type(EllesmereUI[key]) == "function" then hooksecurefunc(EllesmereUI, key, Queue)
        else EllesmereUI[key] = Queue end
    end
end
function ns.ForeverEquipmentEvidence(lines)
    for _, context in ipairs(contexts) do
        local evidence = context.evidence
        lines[#lines+1] = string.format("Forever equipment %s: slots=%d equipped=%d levels=%d enchants=%d gems=%d pending=%d", context.key, evidence.slots, evidence.equipped, evidence.levels, evidence.enchants, evidence.gems, evidence.pending)
    end
end
