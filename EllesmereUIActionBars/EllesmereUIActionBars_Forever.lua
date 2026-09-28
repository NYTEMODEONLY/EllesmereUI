-- Build 69913 loads Blizzard's restricted addon environment after its secure
-- compiler has been removed. Use Blizzard's existing action buttons on this
-- build; keep native bindings, paging, spell execution and combat ownership.
-- This adapter changes layout/art only, outside combat. No secure snippets.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
if tostring(select(2, GetBuildInfo())) ~= "69913" then return end
EUI_FOREVER_NATIVE_ACTIONS = true

local name = ...
local addon = EllesmereUI.Lite.NewAddon(name)
local definitions = {
    { "MainBar", "MainActionBar" },
    { "Bar2", "MultiBarBottomLeft" },
    { "Bar3", "MultiBarBottomRight" },
    { "Bar4", "MultiBarRight" },
    { "Bar5", "MultiBarLeft" },
    { "Bar6", "MultiBar5" },
    { "Bar7", "MultiBar6" },
    { "Bar8", "MultiBar7" },
    { "StanceBar", "StanceBar", true },
    { "PetBar", "PetActionBar", true },
}
local applying, queued = false, false
local hooked = {}
local buttonBorders = setmetatable({}, { __mode = "k" })
local grids = setmetatable({}, { __mode = "k" })
local barKeys = setmetatable({}, { __mode = "k" })
local cooldowns = setmetatable({}, { __mode = "k" })
local Apply
local editing = false
local function HUDPosition(profile,kind)
    local key=kind=="menu" and "foreverMenuPosition" or "foreverBagsPosition"
    if not profile[key] then profile[key]={point="BOTTOMRIGHT",relPoint="BOTTOMRIGHT",
        x=kind=="menu" and -12 or -6,y=kind=="menu" and 6 or 54} end
    return profile[key]
end
local function Relative(position) return _G[position.relativeTo or "UIParent"] or UIParent end
local function IsEditing()
    return editing or (EditModeManagerFrame and EditModeManagerFrame:IsEditModeActive())
end
local function Queue()
    if applying or queued or IsEditing() then return end
    queued = true
    C_Timer.After(0, function()
        queued = false
        if not InCombatLockdown() then Apply() end
    end)
end

local function Plain(value) return not (issecretvalue and issecretvalue(value)) end
local function Number(value) return Plain(value) and type(value) == "number" and value == value and value > -math.huge and value < math.huge end
local function Read(fn, ...)
    if type(fn) ~= "function" then return end
    local ok, value = pcall(fn, ...)
    if ok and Plain(value) then return value end
end
local function BarHidden(settings)
    return settings.enabled == false or settings.alwaysHidden or settings.barVisibility == "never"
end
local function RestoreVisibility(bar)
    if applying or InCombatLockdown() or IsEditing() or not addon.db then return end
    local key = barKeys[bar]
    if not key then return end -- Pet/stance availability stays native.
    local hidden = BarHidden(addon.db.profile.bars[key] or {})
    local shown = Read(bar.IsShownBase or bar.IsShown, bar)
    if type(shown) ~= "boolean" or shown == (not hidden) then return end
    applying = true
    -- Spell collection and dragging both expose native grids. Neither enables
    -- an EUI-disabled bar. Repair before rendering, including the hide edge on
    -- close, without writing native visibility flags or invoking their wrappers.
    local method = hidden and (bar.HideBase or bar.Hide) or (bar.ShowBase or bar.Show)
    local ok, err = pcall(method, bar)
    applying = false
    if not ok then geterrorhandler()("EllesmereUI Forever native visibility restoration: " .. tostring(err)) end
end
local function MigrateCountdownPreference()
    -- Countdown preference is client/account-wide, so a profile switch must
    -- not repeat the import and override a later choice in native Settings.
    local settings = EllesmereUIDB
    if type(settings) ~= "table" or settings.foreverActionCountdownMigrated then return end
    local get = C_CVar and C_CVar.GetCVarBool or GetCVarBool
    local set = C_CVar and C_CVar.SetCVar or SetCVar
    if Read(get, "countdownForCooldowns") ~= true then
        if type(set) ~= "function" then return end
        Read(set, "countdownForCooldowns", "1")
    end
    -- This is a one-time import of Pickme's enabled native preference. Future
    -- changes through the game's own checkbox remain owned by that checkbox.
    if Read(get, "countdownForCooldowns") == true then settings.foreverActionCountdownMigrated = true end
end
local function CooldownFontSize(settings)
    if Number(settings.foreverCooldownFontSize) then return settings.foreverCooldownFontSize end
    return math.max(16, Number(settings.cooldownFontSize) and settings.cooldownFontSize or 12)
end
local function StyleCooldown(frame, state)
    if InCombatLockdown() or IsEditing() then return end
    -- Style the native sweep before its countdown text is lazily created.
    -- The engine still owns sweep visibility, progress and expiration.
    local profile = addon.db and addon.db.profile or {}
    local opacity = Number(profile.foreverCooldownSwipeAlpha) and profile.foreverCooldownSwipeAlpha or 85
    if frame.SetSwipeColor then frame:SetSwipeColor(0, 0, 0, math.max(0, math.min(100, opacity)) / 100) end
    local label = Read(frame.GetCountdownFontString, frame)
    if not label and frame.GetRegions then
        local regions = { pcall(frame.GetRegions, frame) }
        if regions[1] then
            for index = 2, #regions do
                local region = regions[index]
                if Plain(region) and (type(region) == "table" or type(region) == "userdata") and Read(region.GetObjectType, region) == "FontString" then label = region; break end
            end
        end
    end
    if not label or (type(label) ~= "table" and type(label) ~= "userdata") or type(label.SetFont) ~= "function" then return end
    local settings = state.settings
    local size = CooldownFontSize(settings)
    if settings.cooldownFontFit then size = math.min(size, math.max(5, math.floor(math.min(state.width, state.height) * .5))) end
    size = math.max(5, math.min(72, size))
    local path = EllesmereUI.GetFontPath and EllesmereUI.GetFontPath("actionBars") or STANDARD_TEXT_FONT
    if EllesmereUI.ApplyIconTextFont then EllesmereUI.ApplyIconTextFont(label, path, size, "actionBars")
    else label:SetFont(path, size, "OUTLINE") end
    local color = settings.cooldownTextColor or {}
    label:SetTextColor(Number(color.r) and color.r or 1, Number(color.g) and color.g or 1, Number(color.b) and color.b or 1)
    label:ClearAllPoints()
    label:SetPoint("CENTER", frame, "CENTER", Number(settings.cooldownTextXOffset) and settings.cooldownTextXOffset or 0, Number(settings.cooldownTextYOffset) and settings.cooldownTextYOffset or 0)
end
local function StyleButtonCooldowns(button, settings, width, height)
    for _, key in ipairs({ "cooldown", "Cooldown", "chargeCooldown" }) do
        local frame = button[key]
        if frame then
            local state = cooldowns[frame]
            if not state then
                state = {}; cooldowns[frame] = state
                local function Changed()
                    if state.pending then return end
                    state.pending = true
                    -- One refresh after a native data/visibility edge handles
                    -- lazily created text. No timer values are read or changed.
                    C_Timer.After(0, function() state.pending = false; StyleCooldown(frame, state) end)
                end
                for _, method in ipairs({ "SetCooldown", "SetCooldownDuration", "SetCooldownFromDurationObject", "SetCooldownFromExpirationTime", "SetCooldownUNIX", "SetHideCountdownNumbers" }) do
                    if type(frame[method]) == "function" then hooksecurefunc(frame, method, Changed) end
                end
                if frame.HookScript then frame:HookScript("OnShow", Changed) end
            end
            state.settings, state.width, state.height = settings, width, height
            StyleCooldown(frame, state)
        end
    end
end

local function RestoreGrid(bar)
    if applying or InCombatLockdown() or IsEditing() then return end
    local grid = grids[bar]
    if not grid then return end
    applying = true
    local ok, err = pcall(function()
        local function Size(frame, width, height)
            local currentWidth, currentHeight = Read(frame.GetWidth, frame), Read(frame.GetHeight, frame)
            if Number(currentWidth) and Number(currentHeight) and (currentWidth ~= width or currentHeight ~= height) then frame:SetSize(width, height) end
        end
        local function Point(frame, point, relative, relativePoint, x, y)
            if type(frame.GetPoint) ~= "function" then return end
            local success, p, rel, rp, px, py = pcall(frame.GetPoint, frame)
            if not success or not Plain(p) or not Plain(rel) or not Plain(rp) or not Plain(px) or not Plain(py) then return end
            if (px ~= nil and not Number(px)) or (py ~= nil and not Number(py)) then return end
            if p ~= point or rel ~= relative or rp ~= relativePoint or (px or 0) ~= x or (py or 0) ~= y then
                frame:ClearAllPoints(); frame:SetPoint(point, relative, relativePoint, x, y)
            end
        end
        -- A native drag/slot change can lay out 12 default-size containers.
        -- Restore cached physical geometry before that native call returns,
        -- preserving every native shown/hidden/checked/action/cooldown state.
        Size(bar, grid.width, grid.height)
        for _, entry in ipairs(grid.buttons) do
            local container, button = entry.container, entry.button
            Point(container, "TOPLEFT", bar, "TOPLEFT", entry.x, entry.y)
            Size(container, grid.buttonWidth, grid.buttonHeight)
            Size(button, grid.buttonWidth, grid.buttonHeight)
            Point(button, "CENTER", container, "CENTER", 0, 0)
        end
        -- Native grid updates also reveal containers beyond EUI's icon count.
        -- Restore the selected slots now, not on a full repaint next frame.
        for index, button in ipairs(bar.actionButtons) do
            local container = button.container or button:GetParent()
            local shown = Read(container.IsShown, container)
            local wanted = index <= #grid.buttons
            if type(shown) == "boolean" and shown ~= wanted then
                if wanted then container:Show() else container:Hide() end
            end
        end
    end)
    applying = false
    if not ok then geterrorhandler()("EllesmereUI Forever native grid restoration: " .. tostring(err)) end
end

local function RestoreAnchors()
    if applying or InCombatLockdown() or IsEditing() or not addon.db then return end
    -- Native target/pet events can reposition the entire action-bar stack.
    -- Restore base frame anchors before that native layout call returns so
    -- its temporary coordinates never reach a rendered frame. This path must
    -- not dispatch native layout/visibility wrappers or repaint button state.
    applying = true
    local ok, err = pcall(function()
        local positions = addon.db.profile.barPositions
        for _, definition in ipairs(definitions) do
            local bar, position = _G[definition[2]], positions[definition[1]]
            if bar and position then
                local scale = bar.SetScaleBase or bar.SetScale
                local clear = bar.ClearAllPointsBase or bar.ClearAllPoints
                local point = bar.SetPointBase or bar.SetPoint
                scale(bar, 1)
                clear(bar)
                point(bar, position.point or "CENTER", Relative(position),
                    position.relPoint or "CENTER", position.x or 0, position.y or 0)
            end
        end
        local menu = MicroMenuContainer
        if menu then
            local clear = menu.ClearAllPointsBase or menu.ClearAllPoints
            local point = menu.SetPointBase or menu.SetPoint
            clear(menu)
            local p=HUDPosition(addon.db.profile,"menu")
            point(menu, p.point, Relative(p), p.relPoint, p.x, p.y)
            if MicroMenu and MicroMenu:GetParent() == menu then
                MicroMenu:ClearAllPoints()
                MicroMenu:SetPoint("BOTTOMRIGHT", menu, "BOTTOMRIGHT")
            end
        end
        if BagsBar then
            local clear = BagsBar.ClearAllPointsBase or BagsBar.ClearAllPoints
            local point = BagsBar.SetPointBase or BagsBar.SetPoint
            clear(BagsBar)
            local p=HUDPosition(addon.db.profile,"bags")
            point(BagsBar, p.point, Relative(p), p.relPoint, p.x, p.y)
        end
    end)
    applying = false
    if not ok then geterrorhandler()("EllesmereUI Forever native anchor restoration: " .. tostring(err)) end
end
local nativeLayoutHooks = {}
local function HookNativeLayout()
    local manager = EditModeManagerFrame
    if not manager then return end
    for _, method in ipairs({ "UpdateBottomActionBarPositions", "UpdateRightActionBarPositions" }) do
        if not nativeLayoutHooks[method] and type(manager[method]) == "function" then
            nativeLayoutHooks[method] = true
            hooksecurefunc(manager, method, function()
                RestoreAnchors()
            end)
        end
    end
end

local function LayoutBar(bar, settings, position, nativeVisibility)
    -- Keep native buttons under their original bars, with secure attributes intact.
    local buttons = bar.actionButtons
    if not buttons or #buttons == 0 then return end
    if not hooked[bar] then
        hooked[bar] = true
        if bar.UpdateGridLayout then
            hooksecurefunc(bar, "UpdateGridLayout", function()
                if nativeVisibility then Queue() else RestoreGrid(bar) end
            end)
        end
        if not nativeVisibility then
            if bar.UpdateShownButtons then hooksecurefunc(bar, "UpdateShownButtons", function() RestoreGrid(bar) end) end
            if bar.UpdateVisibility then hooksecurefunc(bar, "UpdateVisibility", function() RestoreVisibility(bar) end) end
        end
        if bar.ApplySystemAnchor then hooksecurefunc(bar, "ApplySystemAnchor", Queue) end
        hooksecurefunc(bar, "SetPoint", Queue)
        if bar.SetPointBase then hooksecurefunc(bar, "SetPointBase", Queue) end
        if nativeVisibility then
            for _, method in ipairs({ "Update", "UpdateState", "UpdateShownButtons", "UpdateVisibility" }) do
                if bar[method] then hooksecurefunc(bar, method, Queue) end
            end
        end
        bar:HookScript("OnShow", function()
            if nativeVisibility then Queue() else RestoreVisibility(bar); RestoreGrid(bar) end
        end)
    end
    if nativeVisibility then
        -- Stances omit unavailable form containers; pet bars deliberately keep
        -- empty native slots as spacers. Read that policy without changing it.
        local available = {}
        for index, button in ipairs(buttons) do
            local container = button.container or button:GetParent()
            if index <= (bar.numButtonsShowable or #buttons) and container:IsShown() then
                available[#available+1] = button
            end
        end
        buttons = available
        if #buttons == 0 then return end
    end
    local hidden = BarHidden(settings)
    local isShown = bar.IsShownBase or bar.IsShown
    if hidden and not nativeVisibility then
        if isShown(bar) then
            local hide = bar.HideBase or bar.Hide
            hide(bar)
        end
        return
    end

    local width = settings.buttonWidth or 0
    local height = settings.buttonHeight or 0
    if width <= 0 then width = 36 end
    if height <= 0 then height = width end
    local count = nativeVisibility and #buttons or math.max(1, math.min(#buttons, settings.overrideNumIcons or settings.numIcons or #buttons))
    local rows = math.max(1, math.min(count, settings.overrideNumRows or settings.numRows or 1))
    local stride = math.ceil(count / rows)
    rows = math.ceil(count / stride)
    local vertical = settings.orientation == "vertical"
    local columns, actualRows = vertical and rows or stride, vertical and stride or rows
    local padding = settings.buttonPadding or 2
    local grid = { width = columns * width + (columns-1) * padding, height = actualRows * height + (actualRows-1) * padding,
        buttonWidth = width, buttonHeight = height, buttons = {} }
    -- Stance/pet availability changes may replace their live container set;
    -- they retain the native availability path and queued layout handling.
    if not nativeVisibility then grids[bar] = grid end
    -- Use the native frame methods for placement. The Edit Mode wrappers also
    -- trigger managed-layout/snap updates, which can reset this saved anchor.
    local setScale = bar.SetScaleBase or bar.SetScale
    setScale(bar, 1)
    bar:SetSize(columns * width + (columns - 1) * padding, actualRows * height + (actualRows - 1) * padding)
    if position and position.x and position.y then
        -- Do not call BreakFromFrameManager or write native manager flags:
        -- its shared managed-frame table is consumed again by secure Edit Mode.
        -- Native anchoring may run later; our posthook queues a separate repaint.
        if not nativeVisibility and bar:GetParent() ~= UIParent then bar:SetParent(UIParent) end
        local clearPoints = bar.ClearAllPointsBase or bar.ClearAllPoints
        local setPoint = bar.SetPointBase or bar.SetPoint
        clearPoints(bar)
        setPoint(bar, position.point or "CENTER", Relative(position), position.relPoint or "CENTER", position.x, position.y)
    end
    local reversed = settings.iconOrder == "reversed" or (not settings.iconOrder and settings.reverseIconOrder)
    for i, button in ipairs(buttons) do
        local container = button.container or button:GetParent()
        if i <= count then
            local slot = reversed and (count - i) or (i - 1)
            local col = vertical and math.floor(slot / stride) or (slot % stride)
            local row = vertical and (slot % stride) or math.floor(slot / stride)
            grid.buttons[#grid.buttons+1] = { container = container, button = button, x = col * (width+padding), y = -row * (height+padding) }
            container:ClearAllPoints()
            container:SetPoint("TOPLEFT", bar, "TOPLEFT", col * (width + padding), -row * (height + padding))
            container:SetSize(width, height)
            button:SetSize(width, height)
            button:ClearAllPoints()
            button:SetPoint("CENTER", container, "CENTER")
            if not nativeVisibility and not container:IsShown() then container:Show() end
            local icon = button.icon or button.Icon
            if icon then
                if button.IconMask and icon.RemoveMaskTexture then icon:RemoveMaskTexture(button.IconMask) end
                local zoom = settings.iconZoom and settings.iconZoom / 100 or 0.05
                zoom = math.max(0, math.min(0.45, zoom))
                icon:SetTexCoord(zoom, 1 - zoom, zoom, 1 - zoom)
                icon:ClearAllPoints()
                icon:SetPoint("TOPLEFT", button, "TOPLEFT", 1, -1)
                icon:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -1, 1)
            end
            if button.SlotArt then button.SlotArt:SetAlpha(0) end
            if button.SlotBackground then
                button.SlotBackground:SetColorTexture(0.06, 0.06, 0.08, 0.85)
                button.SlotBackground:SetDrawLayer("BACKGROUND", -8)
            end
            if not buttonBorders[button] then buttonBorders[button] = EllesmereUI.MakeBorder(button, 0, 0, 0, 1) end
            local normal = button:GetNormalTexture()
            if normal then normal:SetAlpha(0) end
            if nativeVisibility then
                -- SmallActionButton fixes these regions at roughly 31 pixels.
                -- Fit the native state carriers to the imported icon dimensions,
                -- retaining checked/disabled/cooldown/autocast state and scripts.
                local accent = EllesmereUI.ELLESMERE_GREEN
                for _, key in ipairs({ "PushedTexture", "HighlightTexture", "CheckedTexture" }) do
                    local texture = button[key]
                    if texture then
                        if key == "CheckedTexture" then
                            texture:SetColorTexture(accent.r, accent.g, accent.b, 0.25)
                        else
                            texture:SetColorTexture(1, 1, 1, key == "PushedTexture" and 0.20 or 0.10)
                        end
                        texture:ClearAllPoints()
                        texture:SetPoint("TOPLEFT", button, "TOPLEFT", 1, -1)
                        texture:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -1, 1)
                    end
                end
                for _, key in ipairs({ "AutoCastOverlay", "QuickKeybindHighlightTexture", "NewActionTexture", "SpellHighlightTexture", "Border", "Flash" }) do
                    if button[key] then button[key]:SetSize(width, height) end
                end
            end
            if button.HotKey then button.HotKey:SetAlpha(settings.hideKeybind and 0 or 1) end
            if button.Name then button.Name:SetAlpha(settings.hideMacroText and 0 or 1) end
            StyleButtonCooldowns(button, settings, width, height)
        else
            if container:IsShown() then container:Hide() end
        end
    end
    if bar.BorderArt then bar.BorderArt:SetAlpha(0) end
    if bar.EndCaps then bar.EndCaps:SetAlpha(0) end
    -- Show is also an Edit Mode override: it writes isShownExternal and runs
    -- shared native layout. Change only the frame's OOC visibility here.
    if not nativeVisibility and not isShown(bar) then (bar.ShowBase or bar.Show)(bar) end
end

local function ApplyLayout()
    local profile = addon.db.profile
    MigrateCountdownPreference()
    for _, definition in ipairs(definitions) do
        local key, frameName = definition[1], definition[2]
        local bar = _G[frameName]
        if bar then
            if not definition[3] then barKeys[bar] = key end
            local ok, err = pcall(LayoutBar, bar, profile.bars[key] or {}, profile.barPositions[key], definition[3])
            if not ok then geterrorhandler()("EllesmereUI Forever native action bars: " .. tostring(err)) end
        end
    end
    -- Visibility and resizing can synchronously reposition other native bars.
    -- Restore every anchor after those changes have finished for the whole set.
    for _, definition in ipairs(definitions) do
        local bar, position = _G[definition[2]], profile.barPositions[definition[1]]
        if bar and position then
            local clearPoints = bar.ClearAllPointsBase or bar.ClearAllPoints
            local setPoint = bar.SetPointBase or bar.SetPoint
            clearPoints(bar)
            setPoint(bar, position.point or "CENTER", Relative(position), position.relPoint or "CENTER", position.x or 0, position.y or 0)
        end
    end
    -- The native micro menu occupies the imported primary bar's location.
    -- Match the Retail reference: circular bags above the bottom micro menu.
    local menu = _G.MicroMenuContainer
    if menu then
        local clearPoints = menu.ClearAllPointsBase or menu.ClearAllPoints
        local setPoint = menu.SetPointBase or menu.SetPoint
        if menu:GetParent() ~= UIParent then menu:SetParent(UIParent) end
        clearPoints(menu)
        local p=HUDPosition(profile,"menu")
        setPoint(menu, p.point, Relative(p), p.relPoint, p.x, p.y)
        if MicroMenu and MicroMenu:GetParent() == menu then
            MicroMenu:ClearAllPoints()
            MicroMenu:SetPoint("BOTTOMRIGHT", menu, "BOTTOMRIGHT")
        end
    end
    local bags = _G.BagsBar
    if bags then
        local clearPoints = bags.ClearAllPointsBase or bags.ClearAllPoints
        local setPoint = bags.SetPointBase or bags.SetPoint
        clearPoints(bags)
        local p=HUDPosition(profile,"bags")
        setPoint(bags, p.point, Relative(p), p.relPoint, p.x, p.y)
    end
    if EUI_FOREVER_StyleHUD then EUI_FOREVER_StyleHUD(profile, Queue) end
    if EUI_FOREVER_CombatLayout then
        for _, definition in ipairs(definitions) do
            EUI_FOREVER_CombatLayout.Register(_G[definition[2]], profile.barPositions[definition[1]])
        end
        EUI_FOREVER_CombatLayout.Register(menu, HUDPosition(profile,"menu"))
        EUI_FOREVER_CombatLayout.Register(bags, HUDPosition(profile,"bags"))
    end
end

Apply = function()
    if InCombatLockdown() or IsEditing() or applying or not addon.db then return end
    HookNativeLayout()
    applying = true
    local ok, err = pcall(ApplyLayout)
    applying = false
    if not ok then geterrorhandler()("EllesmereUI Forever native layout: " .. tostring(err)) end
end

function addon:OnInitialize()
    self.db = EllesmereUI.Lite.NewDB("EllesmereUIActionBarsDB", { profile = { bars = {}, barPositions = {} } })
end

function addon:OnEnable()
    -- Hold the latch through the native exit reset: Blizzard clears its own
    -- active flag before resetting unit frames. These callbacks only queue work.
    if EventRegistry then
        EventRegistry:RegisterCallback("EditMode.Enter", function() editing = true end, addon)
        EventRegistry:RegisterCallback("EditMode.Exit", function() editing = false; Queue() end, addon)
    end
    HookNativeLayout()
    self:RegisterEvent("PLAYER_ENTERING_WORLD", Queue)
    self:RegisterEvent("PLAYER_REGEN_ENABLED", Queue)
    self:RegisterEvent("UI_SCALE_CHANGED", Queue)
    self:RegisterEvent("DISPLAY_SIZE_CHANGED", Queue)
    Queue()
    C_Timer.After(2, Queue)
    EllesmereUI:RegisterModule(name, {
        title = "Action Bars - Forever",
        description = "Pickme layout on native buttons. Changes apply out of combat. Stance and pet availability, keybindings and paging remain native.",
        pages = { "MainBar", "Bar2", "Bar3", "Bar4", "Bar5", "Bar6", "Bar7", "Bar8", "StanceBar", "PetBar" },
        buildPage = function(key, parent, y)
            local start, W = y, EllesmereUI.Widgets
            EllesmereUI:ClearContentHeader()
            local profile = addon.db.profile
            profile.bars[key] = profile.bars[key] or {}
            profile.barPositions[key] = profile.barPositions[key] or {point="CENTER", relPoint="CENTER", x=0, y=0}
            local settings, position = profile.bars[key], profile.barPositions[key]
            local nativeVisibility = key == "StanceBar" or key == "PetBar"
            local function Slider(text, target, field, default, min, max)
                return {type="slider", text=text, min=min, max=max, step=1,
                    getValue=function() return target[field] or default end,
                    setValue=function(value) target[field]=value; Queue() end}
            end
            local _, h = W:SectionHeader(parent, "NATIVE BAR LAYOUT", y); y=y-h
            if nativeVisibility then
                _, h = W:SectionHeader(parent, "AVAILABILITY AND BUTTON COUNT FOLLOW THE GAME", y); y=y-h
                _, h = W:DualRow(parent, y,
                    {type="toggle", text="Vertical", getValue=function() return settings.orientation=="vertical" end,
                        setValue=function(value) settings.orientation=value and "vertical" or "horizontal"; Queue() end},
                    Slider("Rows",settings,"overrideNumRows",1,1,10)); y=y-h
            else
                _, h = W:DualRow(parent, y,
                {type="toggle", text="Show Bar", getValue=function() return settings.enabled ~= false and not settings.alwaysHidden and settings.barVisibility ~= "never" end,
                    setValue=function(value) settings.enabled=value; settings.alwaysHidden=not value; settings.barVisibility=value and "always" or "never"; Queue() end},
                {type="toggle", text="Vertical", getValue=function() return settings.orientation=="vertical" end,
                    setValue=function(value) settings.orientation=value and "vertical" or "horizontal"; Queue() end}); y=y-h
            end
            _, h = W:DualRow(parent,y,Slider("Horizontal Offset",position,"x",0,-1920,1920),Slider("Vertical Offset",position,"y",0,-1080,1080)); y=y-h
            _, h = W:DualRow(parent,y,Slider("Button Width",settings,"buttonWidth",36,16,72),Slider("Button Height",settings,"buttonHeight",36,16,72)); y=y-h
            if not nativeVisibility then
                _, h = W:DualRow(parent,y,Slider("Buttons",settings,"overrideNumIcons",12,1,12),Slider("Rows",settings,"overrideNumRows",1,1,12)); y=y-h
            end
            _, h = W:DualRow(parent,y,Slider("Spacing",settings,"buttonPadding",2,0,20),Slider("Icon Crop (%)",settings,"iconZoom",5,0,20)); y=y-h
            _, h = W:DualRow(parent,y,Slider("Cooldown Text Size",settings,"foreverCooldownFontSize",CooldownFontSize(settings),8,32),Slider("Cooldown Darkness (%)",profile,"foreverCooldownSwipeAlpha",85,0,100)); y=y-h
            return start-y
        end,
    })
end

_G._EAB_Apply = Queue
EUI_FOREVER_STATUS.actionBars = "Native Blizzard buttons with Pickme layout (beta secure-handler limitation)"
EUI_FOREVER_STATUS.ActionBarReport = function()
    local lines = { "Native layout: UIParent " .. UIParent:GetWidth() .. " x " .. UIParent:GetHeight() .. " scale " .. UIParent:GetEffectiveScale() }
    lines[#lines+1] = "Combat layout: " .. tostring(EUI_FOREVER_STATUS.combatLayout or "not loaded")
    local countdown = Read(C_CVar and C_CVar.GetCVarBool or GetCVarBool, "countdownForCooldowns")
    local migrated = EllesmereUIDB and EllesmereUIDB.foreverActionCountdownMigrated
    lines[#lines+1] = "Native cooldown countdown: " .. (type(countdown) == "boolean" and tostring(countdown) or "unavailable")
        .. "; preference imported: " .. (Plain(migrated) and type(migrated) == "boolean" and tostring(migrated) or "unavailable")
    for _, definition in ipairs(definitions) do
        local bar = _G[definition[2]]
        if bar then
            local point, relative, relativePoint, x, y = bar:GetPoint()
            lines[#lines + 1] = definition[1] .. " " .. tostring(point) .. " " .. tostring(relativePoint) .. " " .. tostring(x) .. "," .. tostring(y) .. " size " .. bar:GetWidth() .. "," .. bar:GetHeight()
            local desired = addon.db and addon.db.profile.barPositions[definition[1]]
            lines[#lines + 1] = "  saved " .. tostring(desired and desired.x) .. "," .. tostring(desired and desired.y)
        end
    end
    for _, frameName in ipairs({"MicroMenuContainer", "MicroMenu", "BagsBar", "StatusTrackingBarManager"}) do
        local frame = _G[frameName]
        if frame then
            local point, relative, relativePoint, x, y = frame:GetPoint()
            lines[#lines+1] = frameName .. " " .. tostring((frame.IsShownBase or frame.IsShown)(frame)) .. " " .. tostring(point) .. " relative " .. tostring(relative and relative:GetName()) .. " " .. tostring(relativePoint) .. " " .. tostring(x) .. "," .. tostring(y) .. " size " .. frame:GetWidth() .. "," .. frame:GetHeight()
        end
    end
    for index, container in ipairs(StatusTrackingBarManager and StatusTrackingBarManager.barContainers or {}) do
        local bar = container:GetShownBar()
        local point, _, relativePoint, x, y = container:GetPoint()
        lines[#lines+1] = "Progression " .. index .. " type " .. tostring(bar and bar.barIndex)
            .. " " .. tostring(point) .. " " .. tostring(relativePoint) .. " " .. tostring(x) .. "," .. tostring(y)
            .. " size " .. container:GetWidth() .. "," .. container:GetHeight()
    end
    return table.concat(lines, "\n")
end
