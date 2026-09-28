-- Bounded, read-only layout tracing for transient beta UI movement.
-- No game input, CVars, native layout state, or visual frame properties change.
if not EUI_FOREVER or not EUI_FOREVER_STATUS then return end
local status = EUI_FOREVER_STATUS
local names = {
    "UIParent", "ObjectiveTrackerFrame", "EllesmereUIQTBackground",
    "WorldMapFrame", "QuestMapFrame", "QuestLogFrame", "LegacySystemFrame",
    "MainActionBar", "MultiBarBottomLeft", "MultiBarBottomRight",
    "MultiBarRight", "MultiBarLeft", "MultiBar5", "MultiBar6", "MultiBar7",
    "StanceBar", "PetActionBar",
    "MicroMenuContainer", "BagsBar", "StatusTrackingBarManager",
    "PartyFrame", "CompactPartyFrame", "CompactRaidFrameContainer",
    "CompactPartyFrameMember1", "CompactPartyFrameMember2", "CompactPartyFrameMember3",
    "CompactPartyFrameMember4", "CompactPartyFrameMember5",
}
-- Native progression bars are anonymous frames; the manager's own geometry
-- does not reveal changes to the XP bar beneath it. Resolve by native slot,
-- never by unit/XP values, and retain stable diagnostic labels across swaps.
local resolvers = {}
for index=1,4 do
    for _, kind in ipairs({"Container", "XP", "XPFill"}) do
        local slot, part = index, kind
        local label = "Progression" .. slot .. "." .. part
        names[#names+1] = label
        resolvers[label] = function()
            local containers = StatusTrackingBarManager and StatusTrackingBarManager.barContainers
            local container = containers and containers[slot]
            if part == "Container" then return container end
            local enum = StatusTrackingBarInfo and StatusTrackingBarInfo.BarsEnum
            local xp = container and container.bars and enum and container.bars[enum.Experience]
            if part == "XP" then return xp end
            return xp and xp.StatusBar
        end
    end
end
local function Resolve(name) if resolvers[name] then return resolvers[name]() end; return _G[name] end
local trace = { enabled=false, rows={}, next=1, total=0, dropped=0, last={} }
local limit, duration = 240, 180
local hooked = setmetatable({}, {__mode="k"})
local globals, managers = {}, setmetatable({}, {__mode="k"})
local reading, pending, generation = false, false, 0
local function Now() return GetTime and GetTime() or 0 end
local function Value(value)
    if issecretvalue and issecretvalue(value) then return "<protected>" end
    if type(value) == "number" then return string.format("%.3f", value) end
    if type(value) == "string" or type(value) == "boolean" or value == nil then return tostring(value) end
    return "<object>"
end
local function FrameName(frame)
    if issecretvalue and issecretvalue(frame) then return "<protected>" end
    if type(frame) == "string" then return frame end
    return frame and frame.GetName and Value(frame:GetName()) or "nil"
end
local function Active()
    if not trace.enabled then return false end
    if Now() > trace.untilTime then trace.enabled=false; return false end
    return true
end
local function Add(reason, detail, stack)
    if not Active() then return end
    local line = string.format("+%.3f %s | %s", Now()-trace.started, reason, detail)
    if stack then line=line .. "\n  caller: " .. stack:gsub("\n", " | ") end
    trace.rows[trace.next] = line
    trace.next = trace.next % limit + 1
    trace.total = trace.total + 1
    if trace.total > limit then trace.dropped = trace.dropped + 1 end
end
local function Geometry(frame)
    local point, relative, relPoint, x, y = frame:GetPoint(1)
    local parent = frame.GetParent and frame:GetParent()
    return table.concat({
        "parent=" .. FrameName(parent), "shown=" .. Value(frame:IsShown()),
        "anchor=" .. Value(point) .. "/" .. FrameName(relative) .. "/" .. Value(relPoint),
        "offset=" .. Value(x) .. "," .. Value(y),
        "size=" .. Value(frame:GetWidth()) .. "x" .. Value(frame:GetHeight()),
        "scale=" .. Value(frame:GetScale()),
        "alpha=" .. Value(frame.GetAlpha and frame:GetAlpha()),
    }, " ")
end
local function CaptureFrame(name, reason, includeStack)
    if reading or not Active() then return end
    local frame = Resolve(name)
    if not frame or not frame.GetPoint then return end
    reading = true
    local ok, detail = pcall(Geometry, frame)
    if not ok then detail = "geometry unavailable" end
    if trace.last[name] ~= detail then
        trace.last[name] = detail
        local stack
        -- Capture only a few call sites per session, never locals, chat or unit data.
        if includeStack and debugstack and trace.stackCount < 20 then
            trace.stackCount = trace.stackCount + 1
            local stackOK, rawStack = pcall(debugstack, 3, 5, 0)
            stack = stackOK and Value(rawStack) or "<stack unavailable>"
        end
        Add(reason, name .. " " .. detail, stack)
    end
    reading = false
end
local function Capture(reason)
    for _, name in ipairs(names) do CaptureFrame(name, reason) end
end
local function Later(reason)
    if pending or not Active() then return end
    pending = true
    local token = generation
    C_Timer.After(0, function()
        if token ~= generation then return end
        pending = false
        if not Active() then return end
        Capture(reason .. ":next-frame")
        C_Timer.After(0.1, function()
            if token == generation then Capture(reason .. ":settled") end
        end)
    end)
end
local function Install()
    for _, name in ipairs(names) do
        local frame = Resolve(name)
        if frame and not hooked[frame] then
            hooked[frame] = true
            for _, method in ipairs({"SetPoint","SetPointBase","SetScale","SetScaleBase","SetSize","SetWidth","SetHeight","SetAlpha"}) do
                if type(frame[method]) == "function" then
                    local frameName, methodName = name, method
                    hooksecurefunc(frame, method, function()
                        if not Active() or reading then return end
                        CaptureFrame(frameName, methodName, true)
                        Later("layout")
                    end)
                end
            end
            for _, script in ipairs({"OnShow","OnHide"}) do
                local frameName, scriptName = name, script
                frame:HookScript(script, function()
                    if Active() then CaptureFrame(frameName, scriptName); Later("visibility") end
                end)
            end
        end
    end
    for _, method in ipairs({"ManageFramePositions","HideUIPanel","CloseAllWindows"}) do
        if not globals[method] and type(_G[method]) == "function" then
            globals[method] = true
            local reason = method
            hooksecurefunc(method, function()
                if Active() then Add(reason, "completed"); Capture(reason); Later(reason) end
            end)
        end
    end
    -- Compact party frames can be created after login by a mode/roster change.
    -- Observe generation without asking the native code to refresh any units.
    if not globals.CompactPartyFrame_Generate and type(CompactPartyFrame_Generate)=="function" then
        globals.CompactPartyFrame_Generate=true
        hooksecurefunc("CompactPartyFrame_Generate",function()
            if Active() then Install(); Capture("party-created"); Later("party-created") end
        end)
    end
    local manager = _G.EditModeManagerFrame
    if manager and not managers[manager] then
        managers[manager] = true
        for _, method in ipairs({"UpdateBottomActionBarPositions","UpdateRightActionBarPositions"}) do
            if type(manager[method]) == "function" then
                local reason = method
                hooksecurefunc(manager, method, function()
                    if Active() then Add(reason, "completed"); Capture(reason); Later(reason) end
                end)
            end
        end
    end
end
local function Start()
    generation = generation + 1
    pending = false
    if EllesmereUIDB then EllesmereUIDB._foreverTraceDisabled = nil end
    trace.rows, trace.last = {}, {}
    trace.next, trace.total, trace.dropped, trace.stackCount = 1, 0, 0, 0
    trace.started, trace.untilTime = Now(), Now()+duration
    trace.enabled = true
    Install()
    Add("trace", "started; version=" .. tostring(EUI_FOREVER_VERSION))
    Capture("initial")
end
local function Report()
    local rows = {"Layout trace: " .. (Active() and "recording" or "stopped")
        .. "; max=" .. limit .. "; overwritten=" .. trace.dropped}
    local count = math.min(trace.total, limit)
    local first = trace.total > limit and trace.next or 1
    for offset=0,count-1 do
        rows[#rows+1] = trace.rows[(first+offset-1)%limit+1]
    end
    return table.concat(rows, "\n")
end
status.LayoutTraceReport = Report
status.LayoutTraceCommand = function(command)
    if command == "off" then
        trace.enabled=false
        if EllesmereUIDB then EllesmereUIDB._foreverTraceDisabled=true end
        print("EllesmereUI Forever: layout trace stopped.")
    elseif command == "status" then print(Report():match("^[^\n]+"))
    else
        Start()
        print("EllesmereUI Forever: recording layout changes for 3 minutes. Reproduce the jump, then /reload to save the trace.")
    end
end
local events = CreateFrame("Frame")
for _, event in ipairs({"PLAYER_LOGIN","PLAYER_LOGOUT","ADDON_LOADED","PLAYER_TARGET_CHANGED",
    "ACTIONBAR_SLOT_CHANGED","ACTIONBAR_SHOWGRID","ACTIONBAR_HIDEGRID",
    "PLAYER_REGEN_DISABLED","PLAYER_REGEN_ENABLED","GROUP_ROSTER_UPDATE","PLAYER_XP_UPDATE",
    "UPDATE_EXHAUSTION","UI_SCALE_CHANGED","DISPLAY_SIZE_CHANGED"}) do
    events:RegisterEvent(event)
end
events:SetScript("OnEvent", function(_, event, arg)
    if event == "PLAYER_LOGIN" then
        if not (EllesmereUIDB and EllesmereUIDB._foreverTraceDisabled) then Start(); Later("login") end
    elseif event == "PLAYER_LOGOUT" then
        if EllesmereUIDB then EllesmereUIDB._foreverLastLayoutTrace = Report() end
    elseif event == "ADDON_LOADED" then
        if Active() then Install(); Capture("ADDON_LOADED"); Later("ADDON_LOADED") end
    elseif Active() then
        if event == "GROUP_ROSTER_UPDATE" then Install() end
        Add(event, event == "ACTIONBAR_SLOT_CHANGED" and ("slot=" .. Value(arg)) or "event")
        Capture(event)
        Later(event)
    end
end)
