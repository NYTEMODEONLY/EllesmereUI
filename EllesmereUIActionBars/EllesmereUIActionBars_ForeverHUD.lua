-- Keep Camelot's progression calculations, tooltips, menu dispatch and bag
-- actions. Replace their presentation using the imported Ellesmere settings.
if not EUI_FOREVER_NATIVE_ACTIONS then return end
local styled, hooked = {}, {}
local xpStyles = setmetatable({}, {__mode="k"})
local xpEditing = false
if EventRegistry then
    EventRegistry:RegisterCallback("EditMode.Enter", function() xpEditing=true end, xpStyles)
    EventRegistry:RegisterCallback("EditMode.Exit", function() xpEditing=false end, xpStyles)
end
local WHITE = "Interface\\Buttons\\WHITE8X8"
local textureLookup
local function Texture(settings)
    local key = settings.barTexture
    if key and key ~= "none" and EllesmereUI.ResolveTexturePath then
        if not textureLookup and EllesmereUI.BuildBarTextureTables then
            textureLookup = EllesmereUI.BuildBarTextureTables()
        end
        return EllesmereUI.ResolveTexturePath(textureLookup, key, WHITE)
    end
    return WHITE
end
local function BarKey(bar)
    if not bar then return nil end
    if bar.isExpBar then return "XPBar" end
    local enum = StatusTrackingBarInfo and StatusTrackingBarInfo.BarsEnum
    if enum then
        for kind, key in pairs({ Reputation="RepBar", Honor="HonorBar", HouseFavor="FavorBar", Artifact="ArtifactBar", Azerite="AzeriteBar" }) do
            if enum[kind] and bar.barIndex == enum[kind] then return key end
        end
    end
    -- Unknown/pet progression keeps its native identity and receives a separate
    -- fallback slot; it must not share reputation's saved screen location.
    return nil
end
local function CopyPosition(p)
    return { point=p.point or "CENTER", relPoint=p.relPoint or "CENTER", relativeTo=p.relativeTo, x=p.x or 0, y=p.y or 0 }
end
local function Layouts(manager, profile)
    local layouts, occupied, claimed = {}, {}, {}
    local positions = profile.barPositions or {}
    for index, container in ipairs(manager.barContainers) do
        local bar = container:GetShownBar()
        local key = BarKey(bar)
        local settings = key and profile.bars[key] or profile.bars.RepBar or {}
        settings = settings or {}
        local entry = {container=container, key=key, index=index, settings=settings, width=settings.width or 400, height=settings.height or 20}
        local saved = key and positions[key] or (profile.foreverProgressionPositions or {})[index]
        if saved and not claimed[key or index] then
            entry.position = CopyPosition(saved)
            claimed[key or index] = true
            occupied[#occupied+1] = entry
        end
        layouts[index] = entry
    end
    local base = positions.RepBar or positions.XPBar or {x=-760, y=-249}
    for _, entry in ipairs(layouts) do
        if not entry.position then
            local p = CopyPosition(base)
            -- Reserve all explicit positions first, then stack remaining bars.
            -- Matching reference anchors lets this remain resolution-independent.
            local collided = true
            while collided do
                collided = false
                for _, other in ipairs(occupied) do
                    local q = other.position
                    if p.point == q.point and p.relPoint == q.relPoint
                        and math.abs(p.x-q.x) < (entry.width+other.width)/2
                        and math.abs(p.y-q.y) < (entry.height+other.height)/2+4 then
                        p.y = q.y + (entry.height+other.height)/2 + 4
                        collided = true
                        break
                    end
                end
            end
            entry.position = p
            occupied[#occupied+1] = entry
        end
    end
    return layouts
end
local function Anchor(frame, position)
    local clear = frame.ClearAllPointsBase or frame.ClearAllPoints
    local set = frame.SetPointBase or frame.SetPoint
    clear(frame)
    set(frame, position.point or "CENTER", _G[position.relativeTo or "UIParent"] or UIParent, position.relPoint or "CENTER", position.x or 0, position.y or 0)
end
local function Border(frame)
    if not styled[frame] then
        styled[frame] = EllesmereUI.MakeBorder(frame, 0, 0, 0, 1)
    end
end
local function Track(frame, queue, methods)
    if hooked[frame] then return end
    hooked[frame] = true
    for _, method in ipairs(methods) do
        if frame[method] then hooksecurefunc(frame, method, queue) end
    end
end

local function XPText(native, text, settings)
    -- Use the native bar's level-data policy, including future client changes.
    -- Capped/trial bars retain their banked-XP wording and tooltip semantics.
    if native.IsCapped and native:IsCapped() then return end
    if not native.GetLevelData then return end
    local current, maximum, level = native:GetLevelData()
    if not (current and maximum and level) then return end
    maximum = math.max(maximum, 1)
    local rested = GetXPExhaustion() or 0
    local prefix = settings.showLevel and string.format("%s %d - ", LEVEL, level) or ""
    local value, suffix
    if settings.showRawValues then
        value = string.format("%s / %s", AbbreviateLargeNumbers(current), AbbreviateLargeNumbers(maximum))
        suffix = rested > 0 and string.format(EllesmereUI.L(" (Rested: %s)"), AbbreviateLargeNumbers(rested)) or ""
    else
        value = string.format("%.1f%%", current / maximum * 100)
        suffix = rested > 0 and string.format(EllesmereUI.L(" (Rested: %.1f%%)"), rested / maximum * 100) or ""
    end
    text:SetText(prefix .. value .. suffix)
    text:Show()
end

local function XPFill(native, state, resetTexture)
    local settings, fill = state.settings, native.StatusBar
    local path = Texture(settings)
    if resetTexture or state.texture ~= path then
        fill:SetStatusBarTexture(path)
        state.texture = path
    end
    local rested = (GetXPExhaustion() or 0) > 0
    local r,g,b = rested and 0 or 0.60, rested and 0.44 or 0.40, rested and 0.87 or 0.85
    if settings.colorMode == "accent" then
        local c = EllesmereUI.ELLESMERE_GREEN; r,g,b = c.r,c.g,c.b
    elseif settings.colorMode == "custom" and settings.customColor then
        local c = settings.customColor; r,g,b = c.r,c.g,c.b
    end
    fill:SetStatusBarColor(r,g,b)
end
local function XPDataHooks(native, settings, textSettings)
    local state = xpStyles[native]
    if not state then
        state = {}; xpStyles[native] = state
        local function Refresh(textureChanged, textOnly)
            if InCombatLockdown() or xpEditing
                or (EditModeManagerFrame and EditModeManagerFrame:IsEditModeActive()) then return end
            -- Finish cosmetics in the native event, before a frame can display
            -- Blizzard's atlas/text. Do not queue a full HUD layout, call UpdateTick,
            -- or touch XP values, animation state, dimensions or anchors here.
            if not textOnly then XPFill(native, state, textureChanged) end
            local text = native.OverlayFrame and native.OverlayFrame.Text
            if text then XPText(native, text, state.textSettings) end
        end
        if native.UpdateStatusBarTextures then
            hooksecurefunc(native, "UpdateStatusBarTextures", function() Refresh(true) end)
        end
        if native.Update then hooksecurefunc(native, "Update", function() Refresh(false) end) end
        for _, method in ipairs({"UpdateCurrentText", "UpdateTextVisibility"}) do
            if native[method] then hooksecurefunc(native, method, function() Refresh(false, true) end) end
        end
    end
    state.settings, state.textSettings = settings, textSettings
    return state
end

local function Progression(profile, queue)
    local manager = StatusTrackingBarManager
    if not (manager and manager.barContainers) then return end
    Track(manager, queue, {"UpdateBarVisuals", "CheckForLayoutChange", "UpdateBarsShown"})
    local font = EllesmereUI.GetFontPath("actionBars")
    for _, entry in ipairs(Layouts(manager, profile)) do
        local container = entry.container
        -- Native visibility/priority chooses XP, pet XP, reputation and any new
        -- progression bars. Never unregister or hide the manager or its bars.
        local settings, position, w, h = entry.settings, entry.position, entry.width, entry.height
        Track(container, queue, {"SetPoint", "SetPointBase", "ResizeContainerBars", "ApplySystemAnchor", "UpdateDividers", "ApplyPendingBarToShow"})
        local setScale = container.SetScaleBase or container.SetScale
        setScale(container, 1)
        container:SetSize(w, h)
        Anchor(container, position)
        if EUI_FOREVER_CombatLayout then
            local key,index=entry.key,entry.index
            EUI_FOREVER_CombatLayout.Register(container, position, 1, function(p)
                if key then profile.barPositions[key]=p
                else
                    profile.foreverProgressionPositions=profile.foreverProgressionPositions or {}
                    profile.foreverProgressionPositions[index]=p
                end
            end)
        end
        if container.BarFrameTexture then container.BarFrameTexture:SetAlpha(0) end
        if container.HorizontalDividersPool then
            for divider in container.HorizontalDividersPool:EnumerateActive() do
                if divider.BarDividerTexture then divider.BarDividerTexture:SetAlpha(0) end
            end
        end
        Border(container)
        for _, native in pairs(container.bars or {}) do
            local xpState = native.isExpBar and XPDataHooks(native, settings, profile.bars.XPBar or {})
            native:ClearAllPoints()
            native:SetPoint("TOPLEFT", container, "TOPLEFT", 1, -1)
            native:SetSize(w-2, h-2)
            -- UpdateTick also restores Blizzard's XP atlas and animation atlases.
            -- Run it before our cosmetic fill, after sizing the native frame, so
            -- the rested endpoint is correct and cannot overwrite our final skin.
            if native.UpdateTick then native:UpdateTick() end
            local fill = native.StatusBar
            fill:ClearAllPoints()
            fill:SetAllPoints(native)
            if fill.Background then fill.Background:SetColorTexture(0.06, 0.06, 0.08, 0.85) end
            if native.isExpBar then
                XPFill(native, xpState, false)
                if native.ExhaustionLevelFillBar then
                    native.ExhaustionLevelFillBar:SetColorTexture(0.15, 0.30, 0.60, 0.5)
                    native.ExhaustionLevelFillBar:SetHeight(h-2)
                end
            end
            -- Non-XP atlases encode native reputation/honor/favor colors. Keep
            -- those until an adapter can preserve their deferred level-up colors;
            -- turning every atlas into white would erase that state information.
            local text = native.OverlayFrame and native.OverlayFrame.Text
            if text then
                text:SetFont(font, settings.textSize or 9, "OUTLINE")
                text:SetTextColor(1,1,1)
                text:ClearAllPoints()
                text:SetPoint("CENTER", native, "CENTER", settings.textOffsetX or 0, settings.textOffsetY or 0)
                if native.isExpBar then XPText(native, text, profile.bars.XPBar or {}) end
            end
            if not native.isExpBar then
                Track(native, queue, {"UpdateStatusBarTextures", "Update", "UpdateCurrentText", "UpdateTextVisibility"})
            end
        end
    end
end

local function BagState(texture, button, r, g, b, alpha)
    if not texture then return end
    -- These native regions carry pressed, hover and open-bag visibility.
    -- Replace only their artwork; do not Show/Hide them or change button state.
    texture:SetColorTexture(r, g, b, alpha)
    texture:SetVertexColor(1, 1, 1)
    texture:SetAlpha(1)
    texture:SetBlendMode("BLEND")
    texture:SetRotation(0)
    texture:SetTexCoord(0, 1, 0, 1)
    texture:ClearAllPoints()
    texture:SetPoint("TOPLEFT", button, "TOPLEFT", 2, -2)
    texture:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -2, 2)
end

local bagMasks = setmetatable({}, { __mode = "k" })
local function HasAtlas(atlas)
    return C_Texture and C_Texture.GetAtlasInfo and C_Texture.GetAtlasInfo(atlas) ~= nil
end
local function BagAtlas(texture, button, atlas, highlight)
    if not texture or not HasAtlas(atlas) then return false end
    texture:SetAtlas(atlas)
    texture:SetVertexColor(1, 1, 1)
    texture:SetAlpha(highlight and 0.4 or 1)
    texture:SetBlendMode(highlight and "ADD" or "BLEND")
    texture:SetRotation(0)
    texture:ClearAllPoints()
    texture:SetAllPoints(button)
    return true
end
local function CircularBag(button, icon)
    local data = bagMasks[button]
    if not data then
        local mask = button.CircleMask or button:CreateMaskTexture(nil, "BORDER")
        mask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
        mask:ClearAllPoints()
        local inset = button == MainMenuBarBackpackButton and 4 or 2
        mask:SetPoint("TOPLEFT", button, "TOPLEFT", inset, -inset)
        mask:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -(inset+2), inset+2)
        data = {mask=mask, regions={}}
        bagMasks[button] = data
    end
    for _, region in pairs({ icon=icon, search=button.searchOverlay, context=button.ItemContextOverlay }) do
        if region and region.AddMaskTexture and not data.regions[region] then
            if button.SquareMask and region.RemoveMaskTexture then region:RemoveMaskTexture(button.SquareMask) end
            region:AddMaskTexture(data.mask)
            data.regions[region] = true
        end
    end
end

local function BagButton(button, queue)
    if not button then return end
    Track(button, queue, {"UpdateTextures"})
    local backpack = button == MainMenuBarBackpackButton
    button:SetSize(backpack and 48 or 30, backpack and 48 or 30)
    local icon = button.icon or button.Icon
    -- Camelot's keyring also has a separate icon. Unknown future buttons
    -- without one retain their normal/pressed glyphs.
    if icon then
        CircularBag(button, icon)
        icon:ClearAllPoints()
        icon:SetAllPoints(button)
        -- Keyring uses a named atlas rather than an item texture. Preserve its
        -- native atlas coordinates (including the unrevealed-keyring state).
        if not button.bagAtlas then icon:SetTexCoord(0, 1, 0, 1) end
        local count = button.GetBagID and ContainerFrame_GetContainerNumSlots(button:GetBagID()) or 0
        local empty = not count or count == 0
        local prefix = button == CharacterReagentBag0Slot and "bag-reagent-border" or "bag-border"
        local atlas = backpack and "bag-main" or (prefix .. (empty and "-empty" or ""))
        local highlight = backpack and "bag-main-highlight" or "bag-border-highlight"
        local normal = button:GetNormalTexture()
        local hasNormal = BagAtlas(normal, button, atlas)
        if not hasNormal and normal then normal:SetAlpha(0) end
        -- Retail's bag-main atlas contains the backpack itself. The Camelot
        -- item icon remains available as a fallback if that atlas is missing.
        icon:SetAlpha(backpack and hasNormal and 0 or 1)
        if not BagAtlas(button:GetPushedTexture(), button, atlas) then
            BagState(button:GetPushedTexture(), button, 1, 1, 1, 0.20)
        end
        if not BagAtlas(button:GetHighlightTexture(), button, highlight, true) then
            BagState(button:GetHighlightTexture(), button, 1, 1, 1, 0.10)
        end
        if not BagAtlas(button.SlotHighlightTexture, button, highlight) then
            local accent = EllesmereUI.ELLESMERE_GREEN
            BagState(button.SlotHighlightTexture, button, accent.r, accent.g, accent.b, 0.25)
        end
    end
    -- The reference uses native count typography and backpack CENTER(0,-10).
    -- Keep that text, color, visibility and placement entirely native.
end

local function Bags(queue)
    if BagsBar then
        if BagsBar.BorderArt then BagsBar.BorderArt:SetAlpha(0) end
        Track(BagsBar, queue, {"Layout", "UpdateDividers", "SetPoint", "SetPointBase", "ApplySystemAnchor"})
        for _, key in ipairs({"HorizontalDividersPool", "VerticalDividersPool"}) do
            local pool = BagsBar[key]
            if pool then
                for divider in pool:EnumerateActive() do
                    -- Bag dividers are decorative NineSliceCodeTemplate frames,
                    -- unlike progression's BarDividerTexture regions.
                    divider:SetAlpha(0)
                end
            end
        end
    end
    local buttons = {}
    local function Include(button) if button then buttons[#buttons+1] = button end end
    if MainMenuBarBagManager and MainMenuBarBagManager.EnumerateBagButtons then
        -- Read the native registration list so new bag types are included.
        -- Never alter its ordering, expansion rules or native layout fields.
        Track(MainMenuBarBagManager, queue, {"RegisterBagButton"})
        for _, button in MainMenuBarBagManager:EnumerateBagButtons() do Include(button) end
    else
        Include(MainMenuBarBackpackButton)
        for index=0,(NUM_BAG_SLOTS or 0)-1 do Include(_G["CharacterBag"..index.."Slot"]) end
        Include(CharacterReagentBag0Slot)
        Include(KeyRingButton)
    end
    for _, button in ipairs(buttons) do BagButton(button, queue) end
    if BagsBar then
        -- Match the supplied Retail reference: large backpack on the right,
        -- small circular slots to its left. Native visibility still determines
        -- available slots, including keyring and future registered controls.
        local width = 0
        local function Place(button, size)
            button:ClearAllPoints()
            button:SetPoint("RIGHT", BagsBar, "RIGHT", -width, 0)
            width = width + size
        end
        if MainMenuBarBackpackButton and MainMenuBarBackpackButton:IsShown() then Place(MainMenuBarBackpackButton, 48) end
        for _, button in ipairs(buttons) do
            if button ~= MainMenuBarBackpackButton and button:IsShown() then Place(button, 30) end
        end
        BagsBar:SetSize(math.max(width, 1), 48)
    end
end

function EUI_FOREVER_StyleHUD(profile, queue)
    if InCombatLockdown() then return end
    Progression(profile, queue)
    Bags(queue)
    if MicroMenuContainer then Track(MicroMenuContainer, queue, {"SetPoint", "SetPointBase", "ApplySystemAnchor"}) end
end
