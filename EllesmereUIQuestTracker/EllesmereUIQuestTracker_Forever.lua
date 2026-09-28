-- Forever keeps native objective modules, sizes and quest actions. Only the
-- tracker anchor is restored here; no native settings or manager tables change.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
if tostring(select(2, GetBuildInfo())) ~= "69913" then return end
local _, ns = ...
local EQT = ns.EQT
local pending, applying, initialized, editing, positionChanged = false, false, false, false, false
local points = {TOPLEFT=true,TOP=true,TOPRIGHT=true,LEFT=true,CENTER=true,RIGHT=true,BOTTOMLEFT=true,BOTTOM=true,BOTTOMRIGHT=true}
local function IsEditing()
    return editing or (EditModeManagerFrame and EditModeManagerFrame.IsEditModeActive and EditModeManagerFrame:IsEditModeActive())
end
local function Position()
    local cfg = EQT.DB()
    if cfg.foreverPosition == nil then
        local active = EllesmereUIDB and EllesmereUIDB.activeProfile
        if active == "Pickme" or active == "Pickme - Forever" then
            -- Retail WTF/Account/PRIVATE/edit-mode-cache-account.txt,
            -- named Pickme layout: system 12, anchor 5/5, UIParent, -109/-16.
            -- ObjectiveTracker=12 in EditModeManagerConstantsDocumentation.lua;
            -- anchor 5 is RIGHT (also used by the native right action-bar preset).
            -- EUI's Pickme QuestTracker profile is empty: this position belonged
            -- to Blizzard Edit Mode and was not part of the copied EUI settings.
            cfg.foreverPosition = {point="RIGHT",relativeTo="UIParent",relPoint="RIGHT",x=-109,y=-16}
        end
    end
    local p = cfg.foreverPosition
    if type(p) ~= "table" or not points[p.point] or not points[p.relPoint]
        or type(p.x) ~= "number" or type(p.y) ~= "number" then return end
    return p
end
local function Apply(anchorOnly)
    if applying or InCombatLockdown() or IsEditing() then return end
    local tracker = ObjectiveTrackerFrame
    if not tracker then return end
    local p = Position()
    if anchorOnly and not p then return end
    local relative = p and _G[p.relativeTo or "UIParent"]
    -- Preserve a deliberately saved native snap to another frame. If that frame
    -- is not loaded yet, wait for ADDON_LOADED instead of inventing a new anchor.
    if p and not relative then return end
    applying = true
    local ok,err = pcall(function()
        if p then
            local clear = tracker.ClearAllPointsBase or tracker.ClearAllPoints
            local set = tracker.SetPointBase or tracker.SetPoint
            clear(tracker)
            set(tracker,p.point,relative,p.relPoint,p.x,p.y)
            if EUI_FOREVER_CombatLayout then EUI_FOREVER_CombatLayout.Register(tracker,p,tracker:GetScale()) end
        end
        if not anchorOnly then tracker:SetClampedToScreen(EQT.Cfg("forceOnScreen") == true) end
    end)
    applying = false
    if not ok then error(err,0) end
end
local function Queue()
    if pending or applying or InCombatLockdown() or IsEditing() then return end
    pending = true
    C_Timer.After(0,function() pending=false; Apply() end)
end
EQT.QueueForeverPosition = Queue

local function RestoreAnchor()
    -- Target/pet changes can run ManageFramePositions and reset the managed
    -- tracker before the queued repair renders. Restore only its base anchor
    -- when that entire native call has finished (including UpdateHeight).
    -- Never invoke native layout/height/settings methods from this posthook.
    Apply(true)
end

function EQT.InitForeverPosition()
    if initialized or not ObjectiveTrackerFrame then return end
    initialized = true
    local tracker = ObjectiveTrackerFrame
    for _,key in ipairs({"SetPoint","SetPointBase"}) do
        if type(tracker[key]) == "function" then hooksecurefunc(tracker,key,Queue) end
    end
    if type(tracker.ApplySystemAnchor) == "function" then
        hooksecurefunc(tracker,"ApplySystemAnchor",RestoreAnchor)
    end
    if type(ManageFramePositions) == "function" then
        hooksecurefunc("ManageFramePositions",RestoreAnchor)
    end
    tracker:HookScript("OnShow",Queue)
    -- These hooks only observe native user actions. A saved drag/reset updates
    -- our own profile; closing/canceling Edit Mode never replaces its anchor.
    for _,key in ipairs({"OnSystemPositionChange","ResetToDefaultPosition"}) do
        if type(tracker[key]) == "function" then
            hooksecurefunc(tracker,key,function() if IsEditing() then positionChanged=true end end)
        end
    end
    if EventRegistry and EventRegistry.RegisterCallback then
        editing = IsEditing() and true or false
        EventRegistry:RegisterCallback("EditMode.Enter",function() editing=true; positionChanged=false end,EQT)
        EventRegistry:RegisterCallback("EditMode.SavedLayouts",function()
            if not IsEditing() or not positionChanged or not Position() then return end
            local point,relative,relPoint,x,y = tracker:GetPoint(1)
            local relativeName = relative and relative.GetName and relative:GetName()
            if points[point] and points[relPoint] and relativeName
                and type(x)=="number" and type(y)=="number" then
                EQT.DB().foreverPosition = {point=point,relativeTo=relativeName,relPoint=relPoint,x=x,y=y}
                positionChanged=false
            end
        end,EQT)
        -- ExitEditMode clears its native flag before resetting managed frames.
        -- Hold our latch until the final event; resume on the next timer tick.
        EventRegistry:RegisterCallback("EditMode.Exit",function()
            editing=false; positionChanged=false; Queue()
        end,EQT)
    end
    local events = CreateFrame("Frame")
    for _,event in ipairs({"PLAYER_ENTERING_WORLD","PLAYER_REGEN_ENABLED","UI_SCALE_CHANGED","DISPLAY_SIZE_CHANGED","ADDON_LOADED"}) do
        events:RegisterEvent(event)
    end
    events:SetScript("OnEvent",Queue)
    Queue()
end
