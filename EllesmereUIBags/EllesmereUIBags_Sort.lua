if EUI_CLIENT_BLOCKED then return end
if not EllesmereUI then return end

-- Physical bag operations are server transactions. Plan from a snapshot, then
-- confirm BOTH endpoints and their locks before sending the next transaction.
local Sort = {}
EllesmereUI._BagSort = Sort
local frame, active
local Pump
local C = C_Container

local function Read(bag, slot)
    local info = C.GetContainerItemInfo(bag, slot)
    if not info then return nil, false end
    local link = info.hyperlink or C.GetContainerItemLink(bag, slot)
    return { itemID = info.itemID, link = link, count = info.stackCount, bound = info.isBound }, info.isLocked
end

local function Same(a, b)
    if not a or not b then return a == b end
    return a.itemID == b.itemID and a.link == b.link and a.count == b.count and a.bound == b.bound
end

local function Count(item, count)
    if count == 0 then return nil end
    return { itemID = item.itemID, link = item.link, count = count, bound = item.bound }
end

local function Finish(reason)
    local run = active
    if not run then return end
    active = nil
    if run.timer then run.timer:Cancel() end
    frame:UnregisterAllEvents()
    run.options.onDone(reason, run.skippedLocked or 0)
end

local function Schedule(delay)
    local run = active
    if not run or run.timer then return end
    run.timer = C_Timer.NewTimer(delay, function()
        if active ~= run then return end
        run.timer = nil
        local ok, err = pcall(Pump)
        if not ok then
            if run.ownsCursor and CursorHasItem() then ClearCursor() end
            run.ownsCursor = nil
            Finish("Sorting stopped after an unexpected error.")
            geterrorhandler()(err)
        end
    end)
end

local function Ignored(bag)
    if bag == 0 then return C.GetBackpackAutosortDisabled() end
    return C.GetBagSlotFlag(bag, Enum.BagSlotFlags.DisableAutoSort)
end

local function Snapshot(run)
    local groups, byFamily, bags = {}, {}, {}
    local skippedLocked = 0
    for bag = 0, NUM_TOTAL_EQUIPPED_BAG_SLOTS do
        local size = C.GetContainerNumSlots(bag)
        if size > 0 and not Ignored(bag) then
            local _, family = C.GetContainerNumFreeSlots(bag)
            -- Unknown families stay isolated; never assume an unknown bag can
            -- accept ordinary items. Reagent containers remain independent too.
            local key = family or ("bag" .. bag)
            if bag == Enum.BagIndex.ReagentBag then key = "reagent" end
            local group = byFamily[key]
            if not group then
                group = { family = family, reagent = bag == Enum.BagIndex.ReagentBag }
                groups[#groups + 1] = group; byFamily[key] = group
            end
            bags[#bags + 1] = { bag = bag, size = size, family = family }
            for slot = 1, size do
                local item, locked = Read(bag, slot)
                if locked then
                    -- Forever can keep individual stacks locked while idle.
                    -- Reserve their physical slots, but sort all other slots.
                    -- Never represent these as empty destinations in the plan.
                    skippedLocked = skippedLocked + 1
                elseif item and (not item.link or not item.itemID or not item.count) then
                    return nil, "Item information is still loading. Try sorting again shortly."
                else
                    group[#group + 1] = { bag = bag, slot = slot, item = item }
                end
            end
        end
    end
    run.bags = bags
    run.skippedLocked = skippedLocked
    return groups
end

local function AddMove(moves, source, target, afterSource, afterTarget)
    moves[#moves + 1] = {
        source = source, target = target, beforeSource = source.item,
        beforeTarget = target.item, afterSource = afterSource, afterTarget = afterTarget,
    }
    source.item, target.item = afterSource, afterTarget
end

local function Consolidate(groups, moves, maxStacks)
    for _, group in ipairs(groups) do
        local partials = {}
        for _, slot in ipairs(group) do
            local item = slot.item
            if item then
                local max = maxStacks[item.link]
                if not max then
                    max = select(8, C_Item.GetItemInfo(item.link))
                    if not max then return "Item information is still loading. Try sorting again shortly." end
                    maxStacks[item.link] = max
                end
                if max > 1 and item.count < max then
                    local key = item.link .. (item.bound and "\001bound" or "\001unbound")
                    local list = partials[key]
                    if not list then list = {}; partials[key] = list end
                    list[#list + 1] = slot
                end
            end
        end
        for _, list in pairs(partials) do
            table.sort(list, function(a, b) return a.item.count < b.item.count end)
            local lo, hi = 1, #list
            local max = maxStacks[list[1].item.link]
            while lo < hi do
                local source, target = list[lo], list[hi]
                local amount = math.min(source.item.count, max - target.item.count)
                AddMove(moves, source, target, Count(source.item, source.item.count - amount),
                    Count(target.item, target.item.count + amount))
                if not source.item then lo = lo + 1 end
                if target.item.count == max then hi = hi - 1 end
            end
        end
    end
end

local function FillProfessionBags(groups, moves, maxStacks)
    local destinations = {}
    for _, group in ipairs(groups) do
        -- A profession bag may occupy the dedicated reagent slot on Forever.
        -- Its actual family still restricts which profession's supplies fit.
        if group.family and (group.family > 0 or group.reagent) then
            destinations[#destinations + 1] = group
        end
    end
    if #destinations == 0 then return end
    local metadata = {}
    for _, group in ipairs(groups) do
        if group.family == 0 and not group.reagent then
            for _, source in ipairs(group) do
                local item = source.item
                if item then
                    local data = metadata[item.link]
                    if not data then
                        local family = C_Item.GetItemFamily(item.link)
                        local name, _, _, _, _, _, _, _, equipLoc, _, _, _, _, _, _, _, reagent = C_Item.GetItemInfo(item.link)
                        if family == nil or not name then
                            return "Item information is still loading. Try sorting again shortly."
                        end
                        -- For an unequipped bag, GetItemFamily describes its
                        -- contents, not permission to nest it in another bag.
                        data = { family = family, reagent = reagent, isBag = equipLoc == "INVTYPE_BAG" }
                        metadata[item.link] = data
                    end
                    if not data.isBag then
                        for _, destination in ipairs(destinations) do
                            local compatible = destination.family > 0
                                and bit.band(data.family, destination.family) ~= 0
                                or destination.family == 0 and destination.reagent and data.reagent
                            if compatible then
                                -- Top up matching stacks before consuming an
                                -- empty slot. Never displace an unrelated item.
                                for _, target in ipairs(destination) do
                                    local current, incoming = target.item, source.item
                                    if not incoming then break end
                                    if current and current.link == incoming.link and current.bound == incoming.bound then
                                        local amount = math.min(incoming.count, maxStacks[incoming.link] - current.count)
                                        if amount > 0 then
                                            AddMove(moves, source, target, Count(incoming, incoming.count - amount),
                                                Count(current, current.count + amount))
                                        end
                                    end
                                end
                                for _, target in ipairs(destination) do
                                    if not source.item then break end
                                    if not target.item then AddMove(moves, source, target, nil, source.item) end
                                end
                            end
                            if not source.item then break end
                        end
                    end
                end
            end
        end
    end
end

local function Plan(run, consolidate)
    local groups, reason = Snapshot(run)
    if not groups then return nil, reason end
    local moves, maxStacks = {}, {}
    if consolidate then
        reason = Consolidate(groups, moves, maxStacks)
        if reason then return nil, reason end
        reason = FillProfessionBags(groups, moves, maxStacks)
        if reason then return nil, reason end
        -- Transfers can leave partial stacks behind in ordinary bags.
        reason = Consolidate(groups, moves, maxStacks)
        if reason then return nil, reason end
    else
        for _, group in ipairs(groups) do
            local items = {}
            for _, slot in ipairs(group) do
                if slot.item then
                    items[#items + 1] = { bag = slot.bag, slot = slot.slot,
                        itemLink = slot.item.link, info = { itemID = slot.item.itemID,
                        stackCount = slot.item.count }, item = slot.item }
                end
            end
            local desired = {}
            if run.options.random then
                for i, slot in ipairs(group) do desired[i] = slot.item or false end
                for i = #desired, 2, -1 do
                    local j = math.random(i)
                    desired[i], desired[j] = desired[j], desired[i]
                end
            else
                run.options.order(items)
                local offset = run.options.bottom and (#group - #items) or 0
                for i = 1, #group do desired[i] = false end
                for i, item in ipairs(items) do desired[i + offset] = item.item end
            end
            -- Equivalent links need no swap (including unequal stack counts).
            -- Walking the remaining suffix preserves already-finished slots.
            for i = 1, #group do
                local target, want = group[i], desired[i]
                if (target.item and target.item.link or false) ~= (want and want.link or false) then
                    for j = i + 1, #group do
                        local source = group[j]
                        if (source.item and source.item.link or false) == (want and want.link or false) then
                            if source.item then
                                AddMove(moves, source, target, target.item, source.item)
                            else
                                AddMove(moves, target, source, nil, target.item)
                            end
                            break
                        end
                    end
                end
            end
        end
    end
    return moves
end

Pump = function()
    local run = active
    if not run then return end
    if InCombatLockdown() then Finish("Sorting stopped because combat started."); return end
    if GetCursorInfo() then Finish("Sorting stopped because the cursor is in use."); return end
    if GetTime() > run.deadline then Finish("Sorting timed out. Please try again."); return end
    local move = run.moves and run.moves[run.index]
    if run.pending then
        local source, sl = Read(move.source.bag, move.source.slot)
        local target, tl = Read(move.target.bag, move.target.slot)
        if not sl and not tl and Same(source, move.afterSource) and Same(target, move.afterTarget) then
            run.pending = false
            run.index = run.index + 1
            run.waitSince = GetTime()
            move = run.moves[run.index]
        elseif GetTime() - run.waitSince > 4 then
            Finish("The server did not complete a bag move. Sorting stopped; please try again.")
            return
        else
            Schedule(0.1); return
        end
    end
    if not move then
        if run.phase == "sort" then Finish(); return end
        local consolidate = run.phase == nil and not run.options.random
        run.phase = consolidate and "merge" or "sort"
        local reason
        run.moves, reason = Plan(run, consolidate)
        if not run.moves then Finish(reason); return end
        run.index = 1
        run.waitSince = GetTime()
        Schedule(0.05)
        return
    end
    -- A bag replacement or changed ignore flag invalidates the plan.
    for _, bag in ipairs(run.bags) do
        local _, family = C.GetContainerNumFreeSlots(bag.bag)
        if C.GetContainerNumSlots(bag.bag) ~= bag.size or family ~= bag.family or Ignored(bag.bag) then
            Finish("Your bags changed while sorting. Please try again."); return
        end
    end
    local source, sl = Read(move.source.bag, move.source.slot)
    local target, tl = Read(move.target.bag, move.target.slot)
    if sl or tl then
        if GetTime() - run.waitSince > 4 then Finish("An item is still locked. Sorting stopped.")
        else Schedule(0.1) end
        return
    end
    if not Same(source, move.beforeSource) or not Same(target, move.beforeTarget) then
        Finish("Your items changed while sorting. Please try again."); return
    end
    run.pending = true
    run.waitSince = GetTime()
    C.PickupContainerItem(move.source.bag, move.source.slot)
    if not CursorHasItem() then Finish("The item could not be picked up. Sorting stopped."); return end
    run.ownsCursor = true
    C.PickupContainerItem(move.target.bag, move.target.slot)
    -- Return only the displaced item / stack remainder from OUR transaction.
    if CursorHasItem() then ClearCursor() end
    run.ownsCursor = nil
    Schedule(0.1)
end

function Sort:IsRunning() return active ~= nil end

function Sort:Start(options)
    if active then return false end
    if InCombatLockdown() then options.onDone("You cannot sort bags during combat."); return false end
    if GetCursorInfo() then options.onDone("Clear your cursor before sorting bags."); return false end
    if not frame then
        frame = CreateFrame("Frame")
        frame:SetScript("OnEvent", function(_, event)
            if event == "PLAYER_REGEN_DISABLED" then Finish("Sorting stopped because combat started.")
            elseif event == "PLAYER_LEAVING_WORLD" then Finish()
            else Schedule(0.05) end
        end)
    end
    active = { options = options, deadline = GetTime() + 120, index = 1 }
    frame:RegisterEvent("BAG_UPDATE_DELAYED")
    frame:RegisterEvent("ITEM_LOCK_CHANGED")
    frame:RegisterEvent("PLAYER_REGEN_DISABLED")
    frame:RegisterEvent("PLAYER_LEAVING_WORLD")
    options.onStart()
    Schedule(0.05)
    return true
end
