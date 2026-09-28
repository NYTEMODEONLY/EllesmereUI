if EUI_CLIENT_BLOCKED then return end
local _, ns = ...
local EUI = EllesmereUI
if not EUI or not ns.ResetAllMeterData then return end

-- One decision per instance visit. Reloads preserve data without asking again.
-- No data is reset by zone events; only the Yes callback performs a reset.
local visit, pending, active, hookedDimmer
local TryShow

local function InstanceKey()
    local inside, kind = IsInInstance()
    if issecretvalue(inside) or issecretvalue(kind) then return nil end
    if not inside or type(kind) ~= "string" or kind == "none" then return nil end
    local _, _, difficulty, _, _, _, _, id = GetInstanceInfo()
    if issecretvalue(id) or issecretvalue(difficulty) then return nil end
    if type(id) ~= "number" or id <= 0 or type(difficulty) ~= "number" then return nil end
    return kind .. ":" .. id .. ":" .. difficulty
end

local function Dismiss()
    local old = active
    active = nil
    local popup = _G.EUIConfirmPopup
    -- The confirmation frame is shared: never dismiss another feature's dialog.
    if old and popup and popup._onCancel == old.cancel then
        popup._dimmer:Hide()
    end
end

TryShow = function()
    if not pending or active or InCombatLockdown() then return end
    if InstanceKey() ~= pending then pending = nil; return end
    local dimmer = _G.EUIConfirmDimmer
    if dimmer and dimmer:IsShown() then
        if hookedDimmer ~= dimmer then
            hookedDimmer = dimmer
            dimmer:HookScript("OnHide", function()
                -- Let the existing popup's click callback finish before reuse.
                if pending then C_Timer.After(0, TryShow) end
            end)
        end
        return
    end

    local token = {}
    pending = nil
    active = token
    token.cancel = function()
        if active == token then active = nil end
    end
    EUI:ShowConfirmPopup({
        modal = true,
        allowWorldInput = true,
        compact = true,
        title = EUI.L("Reset damage meters?"),
        message = EUI.L("You just entered an instance."),
        confirmText = EUI.L("Yes"),
        cancelText = EUI.L("No"),
        onCancel = token.cancel,
        onConfirm = function()
            if active ~= token then return end
            active = nil
            -- Protect the click even if the combat event has not arrived yet.
            if InCombatLockdown() then return end
            ns.ResetAllMeterData()
        end,
    })
end

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_ENTERING_WORLD")
events:RegisterEvent("ZONE_CHANGED_NEW_AREA")
events:RegisterEvent("PLAYER_REGEN_DISABLED")
events:RegisterEvent("PLAYER_REGEN_ENABLED")
events:RegisterEvent("CHALLENGE_MODE_START")
events:RegisterEvent("DAMAGE_METER_RESET")
events:SetScript("OnEvent", function(_, event, _, reloadingUI)
    if event == "PLAYER_ENTERING_WORLD" or event == "ZONE_CHANGED_NEW_AREA" then
        local key = InstanceKey()
        if event == "PLAYER_ENTERING_WORLD" and reloadingUI then
            pending = nil; Dismiss(); visit = key
            return
        end
        if key ~= visit then
            visit = key
            -- Keep an unanswered dialog through zone changes. Its Yes button
            -- always resets all meters; don't stack another prompt behind it.
            pending = not active and key or nil
        end
        TryShow()
    elseif event == "PLAYER_REGEN_DISABLED" then
        pending = nil
        Dismiss()
    elseif event == "PLAYER_REGEN_ENABLED" then
        TryShow()
    else
        -- Already-reset data needs no queued prompt. A visible question still
        -- belongs to the user until Yes, No, or combat dismisses it.
        pending = nil
    end
end)
