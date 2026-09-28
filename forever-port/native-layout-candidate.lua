-- Offline candidate construction only: intentionally absent from every TOC.
-- No game APIs, persistence, frame mutation, serialization, or activation.
-- Build(activeLayout, ownedAnchors, copyName, layoutType, isSecretValue)
-- returns an independent layout table or raises a validation error.
-- The caller must supply the secret detector (issecretvalue in a live context).
-- ownedAnchors is a dense array of {system, systemIndex?, anchorInfo,
-- anchorInfo2?}. Omit anchorInfo2 to preserve it; false explicitly removes it.
-- Coordinates are NATIVE STORED OFFSETS, not frame-local SetPoint offsets:
-- native ApplySystemAnchor divides both offsets by the receiving frame's scale.
-- Numeric IDs/types are caller-reviewed native identities, not Retail defaults.
-- This produces input for ConvertLayoutInfoToString and user-driven native
-- Import. It does not establish that imported layouts are combat-stable.
local Candidate = {}
local points = {
    TOPLEFT=true, TOP=true, TOPRIGHT=true, LEFT=true, CENTER=true,
    RIGHT=true, BOTTOMLEFT=true, BOTTOM=true, BOTTOMRIGHT=true,
}

local function fail(message)
    error("native layout candidate: " .. message, 0)
end

local function finite(value)
    return type(value) == "number" and value == value
        and value ~= math.huge and value ~= -math.huge
end

-- Validate secrets BEFORE comparisons, table indexing, formatting, or arithmetic.
-- Only data tables accepted by native layout serialization belong in a candidate.
local function copyData(value, isSecretValue, copies, visiting)
    if isSecretValue(value) then fail("secret input") end
    local kind = type(value)
    if kind == "number" then
        if not finite(value) then fail("nonfinite input") end
        return value
    elseif kind == "nil" or kind == "string" or kind == "boolean" then
        return value
    elseif kind ~= "table" then
        fail("unsupported input value type")
    end
    if getmetatable(value) ~= nil then fail("metatable on input data") end
    if visiting[value] then fail("cyclic input data") end
    if copies[value] then return copies[value] end
    local result = {}
    copies[value] = result
    visiting[value] = true
    for key, child in pairs(value) do
        local safeKey = copyData(key, isSecretValue, copies, visiting)
        if type(safeKey) ~= "string" and type(safeKey) ~= "number" then
            fail("unsupported input key type")
        end
        result[safeKey] = copyData(child, isSecretValue, copies, visiting)
    end
    visiting[value] = nil
    return result
end

local function integer(value)
    return finite(value) and value % 1 == 0
end

local function denseArray(array, label)
    if type(array) ~= "table" then fail(label .. " must be an array") end
    local count, maximum = 0, 0
    for key in pairs(array) do
        if not integer(key) or key < 1 then fail(label .. " has a non-array key") end
        count = count + 1
        if key > maximum then maximum = key end
    end
    if count ~= maximum then fail(label .. " contains holes") end
    return count
end

local function identity(record)
    if type(record) ~= "table" or not integer(record.system) or record.system < 0 then
        fail("missing or invalid system identity")
    end
    if record.systemIndex ~= nil and not integer(record.systemIndex) then
        fail("invalid systemIndex")
    end
    -- An absent index remains distinct from an explicit numeric index (even -1).
    return string.format("%.0f", record.system) .. ":"
        .. (record.systemIndex == nil and "absent" or string.format("%.0f", record.systemIndex))
end

local function anchor(value)
    if type(value) ~= "table" then fail("missing anchorInfo") end
    if type(value.point) ~= "string" or not points[value.point]
        or type(value.relativePoint) ~= "string" or not points[value.relativePoint] then
        fail("unsupported anchor point")
    end
    if type(value.relativeTo) ~= "string" or not value.relativeTo:match("^[%a_][%w_]*$") then
        fail("relativeTo must be a named native frame")
    end
    if not finite(value.offsetX) or not finite(value.offsetY) then
        fail("anchor coordinates must be finite numbers")
    end
end

function Candidate.Build(activeLayout, ownedAnchors, copyName, layoutType, isSecretValue)
    if type(isSecretValue) ~= "function" then fail("secret detector is required") end
    -- Copy and validate all data before looking at any individual field.
    local copied = copyData({activeLayout=activeLayout, ownedAnchors=ownedAnchors,
        copyName=copyName, layoutType=layoutType}, isSecretValue, {}, {})
    local result, owned = copied.activeLayout, copied.ownedAnchors
    if type(result) ~= "table" then fail("active layout must be a table") end
    if type(copied.copyName) ~= "string" or not copied.copyName:match("%S")
        or copied.copyName:find("[%z\1-\31\127]") then fail("invalid copy name") end
    if copied.copyName == result.layoutName then fail("copy must have a distinct name") end
    if not integer(copied.layoutType) or copied.layoutType < 0 then fail("invalid layoutType") end
    local systemCount = denseArray(result.systems, "systems")
    local ownedCount = denseArray(owned, "ownedAnchors")
    if systemCount == 0 or ownedCount == 0 then fail("systems and ownedAnchors must not be empty") end
    local systems, seen = {}, {}
    for _, system in ipairs(result.systems) do
        local key = identity(system)
        if systems[key] then fail("duplicate source system identity") end
        systems[key] = system
        anchor(system.anchorInfo)
        if system.anchorInfo2 ~= nil then anchor(system.anchorInfo2) end
    end
    for _, record in ipairs(owned) do
        local key = identity(record)
        if seen[key] then fail("duplicate owned system identity") end
        seen[key] = true
        local system = systems[key]
        if not system then fail("owned system not present in active layout") end
        for field in pairs(record) do
            if field ~= "system" and field ~= "systemIndex" and field ~= "anchorInfo"
                and field ~= "anchorInfo2" then fail("unsupported owned record field") end
        end
        anchor(record.anchorInfo)
        system.anchorInfo = record.anchorInfo
        if record.anchorInfo2 == false then
            system.anchorInfo2 = nil
        elseif record.anchorInfo2 ~= nil then
            anchor(record.anchorInfo2)
            system.anchorInfo2 = record.anchorInfo2
        end
        system.isInDefaultPosition = false
    end
    result.layoutName = copied.copyName
    result.layoutType = copied.layoutType
    return result
end

return Candidate
