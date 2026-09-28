-- Forever incoming heals: native calculator values, rendered by the client.
-- Shields/heal absorbs keep their existing independent painters and settings.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local _, ns = ...
local frames = setmetatable({}, { __mode = "k" })
local function Plain(value) return not (issecretvalue and issecretvalue(value)) end
local function Number(value) return Plain(value) and type(value) == "number" and value == value and value > -math.huge and value < math.huge end

function ns.ForeverLayoutPredictionShields(frame, settings)
    local state = frames[frame]
    local absorb = frame.HealthPrediction and frame.HealthPrediction.damageAbsorb
    if not state or state.official or not absorb or not absorb._forward then return end
    settings = settings or state.settings(frame._euiUnit or state.baseUnit) or {}
    if (settings.absorbEdgeMode or "overlay") ~= "overlay" then return end
    local prediction, carrier = state.bar:GetStatusBarTexture(), state.carrier:GetStatusBarTexture()
    local fromLeft = settings.overshieldMode == "fromleft"
    local forward = absorb._forward
    forward:ClearAllPoints(); absorb:ClearAllPoints()
    -- Shield starts AFTER the predicted heal. Backfill stays clipped to actual
    -- health; the invisible reverse carrier shifts its far anchor by the heal
    -- width so it still represents only shield overflow. No secret arithmetic.
    if state.vertical then
        if state.reverse then
            forward:SetPoint("TOPLEFT", prediction, "BOTTOMLEFT"); forward:SetPoint("TOPRIGHT", prediction, "BOTTOMRIGHT")
            absorb:SetPoint("BOTTOMLEFT", fromLeft and prediction or carrier, fromLeft and "BOTTOMLEFT" or "TOPLEFT")
            absorb:SetPoint("BOTTOMRIGHT", fromLeft and prediction or carrier, fromLeft and "BOTTOMRIGHT" or "TOPRIGHT")
        else
            forward:SetPoint("BOTTOMLEFT", prediction, "TOPLEFT"); forward:SetPoint("BOTTOMRIGHT", prediction, "TOPRIGHT")
            absorb:SetPoint("TOPLEFT", fromLeft and prediction or carrier, fromLeft and "TOPLEFT" or "BOTTOMLEFT")
            absorb:SetPoint("TOPRIGHT", fromLeft and prediction or carrier, fromLeft and "TOPRIGHT" or "BOTTOMRIGHT")
        end
    elseif state.reverse then
        forward:SetPoint("TOPRIGHT", prediction, "TOPLEFT"); forward:SetPoint("BOTTOMRIGHT", prediction, "BOTTOMLEFT")
        absorb:SetPoint("TOPLEFT", fromLeft and prediction or carrier, fromLeft and "TOPLEFT" or "TOPRIGHT")
        absorb:SetPoint("BOTTOMLEFT", fromLeft and prediction or carrier, fromLeft and "BOTTOMLEFT" or "BOTTOMRIGHT")
    else
        forward:SetPoint("TOPLEFT", prediction, "TOPRIGHT"); forward:SetPoint("BOTTOMLEFT", prediction, "BOTTOMRIGHT")
        absorb:SetPoint("TOPRIGHT", fromLeft and prediction or carrier, fromLeft and "TOPRIGHT" or "TOPLEFT")
        absorb:SetPoint("BOTTOMRIGHT", fromLeft and prediction or carrier, fromLeft and "BOTTOMRIGHT" or "BOTTOMLEFT")
    end
end

local function Layout(frame, state)
    local hp, bar = frame.Health, state.bar
    local settings = state.settings(frame._euiUnit or state.baseUnit) or {}
    local vertical, reverse = settings.healthVerticalFill == true, settings.healthReverseFill == true
    local width, height = hp:GetWidth(), hp:GetHeight()
    if not Number(width) or not Number(height) then return end
    if state.width == width and state.height == height and state.vertical == vertical and state.reverse == reverse then return end
    state.width, state.height, state.vertical, state.reverse = width, height, vertical, reverse
    local fill = hp:GetStatusBarTexture()
    bar:ClearAllPoints()
    bar:SetOrientation(vertical and "VERTICAL" or "HORIZONTAL")
    bar:SetReverseFill(reverse)
    state.carrier:SetOrientation(vertical and "VERTICAL" or "HORIZONTAL")
    state.carrier:SetReverseFill(not reverse)
    bar:SetSize(width, height)
    if vertical then
        if reverse then bar:SetPoint("TOPLEFT", fill, "BOTTOMLEFT"); bar:SetPoint("TOPRIGHT", fill, "BOTTOMRIGHT")
        else bar:SetPoint("BOTTOMLEFT", fill, "TOPLEFT"); bar:SetPoint("BOTTOMRIGHT", fill, "TOPRIGHT") end
    elseif reverse then
        bar:SetPoint("TOPRIGHT", fill, "TOPLEFT"); bar:SetPoint("BOTTOMRIGHT", fill, "BOTTOMLEFT")
    else
        bar:SetPoint("TOPLEFT", fill, "TOPRIGHT"); bar:SetPoint("BOTTOMLEFT", fill, "BOTTOMRIGHT")
    end
    ns.ForeverLayoutPredictionShields(frame, settings)
end

function ns.ForeverCreateHealPrediction(frame, unit, settings)
    if frames[frame] then return end
    -- Official EUI now owns these units, including the OFF setting. Do not
    -- allocate a second calculator, carrier, overlay or event channel for them.
    -- Migrate once per settings table; later user choices remain authoritative.
    if ns.UF_HEAL_PRED_UNITS and ns.UF_HEAL_PRED_UNITS[unit] then
        local appearance = settings(unit)
        if appearance and not appearance.foreverOfficialHealMigrated then
            appearance.healPrediction = true
            appearance.foreverOfficialHealMigrated = true
        end
        return
    end
    local hp = frame.Health
    -- The imported profile disabled shield overlays. Enable them once for the
    -- requested healing display; subsequent choices in Absorbs stay respected.
    local appearance = settings(unit)
    if appearance and not appearance.foreverHealingDisplayMigrated then
        if not appearance.showPlayerAbsorb or appearance.showPlayerAbsorb == "none" then
            appearance.showPlayerAbsorb = "clean"
        end
        appearance.foreverHealingDisplayMigrated = true
    end
    local state = { baseUnit = unit, settings = settings, events = 0, healEvents = 0,
        positiveUpdates = 0, protectedUpdates = 0, result = "not updated" }
    frames[frame] = state
    local clip = CreateFrame("Frame", nil, hp)
    clip:SetAllPoints(hp); clip:SetClipsChildren(true)
    local bar = CreateFrame("StatusBar", nil, clip)
    state.bar = bar
    bar:SetFrameLevel(hp:GetFrameLevel() + 1)
    bar:SetStatusBarTexture("Interface\\Buttons\\WHITE8X8")
    bar:SetStatusBarColor(0.35, 1, 0.55, 0.7)
    bar:SetMinMaxValues(0, 1); bar:SetValue(0)
    local carrier = CreateFrame("StatusBar", nil, hp)
    carrier:SetAllPoints(hp); carrier:SetStatusBarTexture("Interface\\Buttons\\WHITE8X8")
    carrier:SetAlpha(0); carrier:SetMinMaxValues(0, 1); carrier:SetValue(0)
    state.carrier = carrier
    local mask = hp:CreateMaskTexture()
    mask:SetAllPoints(hp); mask:SetTexture("Interface\\Buttons\\WHITE8X8")
    bar:GetStatusBarTexture():AddMaskTexture(mask)
    -- This child is independent of damageAbsorb, whose OnHide hides shield
    -- siblings. Turning off shield styling must never disable incoming heals.
    frame.ForeverIncomingHeal = bar
    if CreateUnitHealPredictionCalculator and UnitGetDetailedHealPrediction and Enum
        and Enum.UnitMaximumHealthMode and Enum.UnitIncomingHealClampMode and Enum.UnitHealAbsorbMode then
        local calculator = CreateUnitHealPredictionCalculator()
        calculator:SetMaximumHealthMode(Enum.UnitMaximumHealthMode.Default)
        calculator:SetIncomingHealClampMode(Enum.UnitIncomingHealClampMode.MissingHealth)
        calculator:SetIncomingHealOverflowPercent(1)
        calculator:SetHealAbsorbMode(Enum.UnitHealAbsorbMode.ReducedByIncomingHeals)
        state.calculator = calculator
    end
    Layout(frame, state)
    hp:HookScript("OnSizeChanged", function() Layout(frame, state) end)
end

function ns.ForeverSetPredictionOwner(frame, official)
    local state = frames[frame]
    if not state then return end
    if state.official ~= official then state.width = nil end
    state.official = official
    if official then
        state.bar:SetValue(0); state.carrier:SetValue(0)
        state.result = "official prediction selected"
    end
end

local function Paint(frame, unit, event)
    local state = frames[frame]
    if not state then return end
    state.events, state.event = state.events + 1, event
    if event == "UNIT_HEAL_PREDICTION" then state.healEvents = state.healEvents + 1 end
    Layout(frame, state)
    local bar, calculator, carrier = state.bar, state.calculator, state.carrier
    if state.official then bar:SetValue(0); carrier:SetValue(0); return end
    if not unit or not calculator then
        bar:SetValue(0); carrier:SetValue(0); state.result = calculator and "no unit" or "calculator unavailable"; return
    end
    -- C++ applies heal-absorb reductions and missing-health clamping. Returned
    -- amounts may be secret: feed only the native StatusBar sinks, never Lua
    -- arithmetic, width calculations, health comparisons or Show/Hide branches.
    local ok = pcall(UnitGetDetailedHealPrediction, unit, "player", calculator)
    if not ok then bar:SetValue(0); carrier:SetValue(0); state.result = "prediction unavailable"; return end
    local maximum = calculator:GetMaximumHealth()
    bar:SetMinMaxValues(0, maximum); carrier:SetMinMaxValues(0, maximum)
    local incoming = calculator:GetIncomingHeals()
    bar:SetValue(incoming); carrier:SetValue(incoming)
    if not Plain(incoming) then
        state.protectedUpdates = state.protectedUpdates + 1
        state.result = "protected value rendered"
    elseif incoming == 0 then state.result = "zero"
    else state.positiveUpdates = state.positiveUpdates + 1; state.result = "incoming heal rendered" end
end
ns.Engine.SetPainter("incomingHeal", Paint)
ns.ForeverRefreshHealPrediction = Paint

function ns.ForeverPredictionEvidence(lines)
    -- Cached categories only: no extra unit reads or identity/health disclosure.
    for _, state in pairs(frames) do
        lines[#lines+1] = "Incoming-heal preview " .. state.baseUnit .. ": " .. state.result
            .. "; updates=" .. state.events .. "; healEvents=" .. state.healEvents
            .. "; positive=" .. state.positiveUpdates .. "; protected=" .. state.protectedUpdates
            .. "; last=" .. tostring(state.event)
    end
end
