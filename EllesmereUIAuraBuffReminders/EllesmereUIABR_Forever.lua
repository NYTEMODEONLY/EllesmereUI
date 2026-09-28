if EUI_CLIENT_BLOCKED or not (EllesmereUI and EllesmereUI.IS_FOREVER) then return end
local _, ns = ...
-- Forever's own detector. No inferred timers, protected-value reconstruction,
-- pre-combat truth cache, or PallyPower code. All casts remain player actions.
local F = {}
ns.ForeverReminders = F
local spellInfoCache = {}
local function secret(v) return issecretvalue and issecretvalue(v) end
local function number(v) return not secret(v) and type(v) == "number" end
local function info(id)
    if spellInfoCache[id] then return spellInfoCache[id] end
    if not C_Spell or not C_Spell.GetSpellInfo then return end
    local ok, v = pcall(C_Spell.GetSpellInfo, id)
    if ok and not secret(v) and type(v) == "table" then
        if not secret(v.name) and v.name then spellInfoCache[id]=v end
        return v
    end
end
local function name(id, fallback)
    local v = info(id)
    return v and not secret(v.name) and v.name or fallback
end
F.Name = name
F.auras = {
    {key="devotion", id=465, label="Devotion Aura", ids={465,10290,643,10291,1032,10292,10293}},
    {key="retribution", id=7294, label="Retribution Aura", ids={7294,10298,10299,10300,10301}},
    {key="concentration", id=19746, label="Concentration Aura", ids={19746}},
    {key="shadow", id=19876, label="Shadow Resistance Aura", ids={19876,19895,19896}},
    {key="frost", id=19888, label="Frost Resistance Aura", ids={19888,19897,19898}},
    {key="fire", id=19891, label="Fire Resistance Aura", ids={19891,19899,19900}},
    {key="sanctity", id=20218, label="Sanctity Aura", ids={20218}},
}
-- Seals are short combat spells, not automatic maintenance reminders.
-- Existing saved seal preferences remain dormant.
F.blessings = {
    {key="might", id=19740, label="Blessing of Might", ids={19740,19834,19835,19836,19837,19838,25291}, greater={25782,25916}},
    {key="wisdom", id=19742, label="Blessing of Wisdom", ids={19742,19850,19852,19853,19854,25290}, greater={25894,25918}},
    {key="kings", id=20217, label="Blessing of Kings", ids={20217}, greater={25898}},
    {key="sanctuary", id=20911, label="Blessing of Sanctuary", ids={20911,20912,20913,20914}, greater={25899}},
    {key="light", id=19977, label="Blessing of Light", ids={19977,19978,19979}, greater={25890}},
    {key="salvation", id=1038, label="Blessing of Salvation", ids={1038}, greater={25895}},
}
F.flasks = {
    {key="titans", id=17626, label="Flask of the Titans", ids={17626}, item=13510},
    {key="wisdom", id=17627, label="Flask of Distilled Wisdom", ids={17627}, item=13511},
    {key="power", id=17628, label="Flask of Supreme Power", ids={17628}, item=13512},
    {key="resistance", id=17629, label="Flask of Chromatic Resistance", ids={17629}, item=13513},
}
F.elixirs = {
    {key="mongoose", id=17538, label="Elixir of the Mongoose", ids={17538}, item=13452},
    {key="fortitude", id=3593, label="Elixir of Fortitude", ids={3593}, item=3825},
    {key="defense", id=11348, label="Elixir of Superior Defense", ids={11348}, item=13445},
    {key="intellect", id=11396, label="Elixir of Greater Intellect", ids={11396}, item=9179},
    {key="arcane", id=17539, label="Greater Arcane Elixir", ids={17539}, item=13454},
    {key="mageblood", id=24363, label="Mageblood Potion", ids={24363}, item=20007},
}
local rf = {id=25780, label="Righteous Fury", ids={25780}}
local food = {id=19705, label="Well Fed", ids={19705,19706,19708,19709,19710,19711,18125,18141,18191,18192,18193,18194,18222,22730,25661,1225779}}
local camp = {id=1229741, label="Camp Benefits", ids={1229741}}
local function known(id)
    local query = C_SpellBook and C_SpellBook.IsSpellKnown
    if query then
        local ok, v = pcall(query, id, Enum and Enum.SpellBookSpellBank and Enum.SpellBookSpellBank.Player)
        if ok and not secret(v) then return v == true end
    end
    query = IsPlayerSpell or IsSpellKnown
    if query then local ok,v=pcall(query,id); return ok and not secret(v) and v == true end
    return false
end
local function castSpell(def)
    for i=#def.ids,1,-1 do if known(def.ids[i]) then return def.ids[i] end end
end
F.CastSpell = castSpell
local defaults = {tankMode="on", aura="any", blessing="any", groupBlessing="off",
    warnSeconds=30, food=true, flask="any", elixir="off", weapon=true,
    consumablesWhere={open_world=false, in_combat=false}, paladinWhere={},
    foodItem=0, oilItem=0, foodBuff=0, flaskBuff=0, unknown=false, showRested=false}
F.defaults = defaults
function F.Get(fo, key)
    if fo[key] ~= nil then return fo[key] end
    return defaults[key]
end
function F.Choices(kind)
    local values, order = {off="Off", any="Any"}, {"off", "any"}
    if kind == "elixirs" then values.any=nil; order={"off"} end
    for _,def in ipairs(F[kind]) do
        if kind == "flasks" or kind == "elixirs" or castSpell(def) then
            values[def.key]=name(def.id,def.label); order[#order+1]=def.key
        end
    end
    return values, order
end
-- Scans are restricted by the client's official predicate. A secret or failed
-- result is UNKNOWN, never "missing". Direct spell queries are permitted only
-- for spells the native secrecy API explicitly marks readable when restricted.
local function restricted()
    if C_Secrets and C_Secrets.ShouldAurasBeSecret then
        local ok,v=pcall(C_Secrets.ShouldAurasBeSecret)
        if not ok or secret(v) or v then return true end
    end
    return false
end
local function readable(id)
    if C_Secrets and C_Secrets.ShouldSpellAuraBeSecret then
        local ok,v=pcall(C_Secrets.ShouldSpellAuraBeSecret,id)
        return ok and not secret(v) and v == false
    end
    return not restricted() and not InCombatLockdown()
end
local nextAt, config, makeEntry, texture, snapshots = nil, nil, nil, nil, {}
F.status = {}
local function schedule(at)
    if at > GetTime() and (not nextAt or at < nextAt) then nextAt=at end
end
local function auraState(a, threshold)
    if secret(a) or type(a) ~= "table" then return "unknown" end
    local dur, exp = a.duration, a.expirationTime
    if not number(dur) or not number(exp) then return "present" end -- presence is readable; timer is not
    if dur <= 0 or exp <= 0 then return "present" end -- permanent aura
    local remaining=exp-GetTime()
    if remaining <= 0 then return "unknown" end -- wait for native removal, never invent absence
    schedule(exp)
    if threshold > 0 and dur > threshold then
        if remaining <= threshold then return "expiring", remaining end
        schedule(exp-threshold)
    end
    return "present", remaining
end
local function scan(unit)
    if snapshots[unit] then return snapshots[unit] end
    local out={auras={}, complete=false}; snapshots[unit]=out
    if restricted() or not (C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return out end
    for i=1,255 do
        local ok,a=pcall(C_UnitAuras.GetAuraDataByIndex,unit,i,"HELPFUL")
        if not ok or secret(a) then return out end
        if a == nil then out.complete=true; return out end
        if type(a) ~= "table" or secret(a.spellId) or secret(a.name) then return out end
        out.auras[#out.auras+1]=a
    end
    return out
end
local function family(def)
    if def._ids then return def._ids,def._names end
    local ids,names={},{}
    for _,list in ipairs({def.ids,def.greater or {}}) do
        for _,id in ipairs(list) do
            ids[id]=true
            local n=name(id); if n then names[n]=true end
        end
    end
    -- Do not cache: early-login spell data can still be loading.
    return ids,names
end
local function state(def, unit, threshold)
    unit=unit or "player"
    local ids,names=family(def)
    local s=scan(unit)
    local best, remain="missing",nil
    for _,a in ipairs(s.auras) do
        if ids[a.spellId] or names[a.name] then
            local st,r=auraState(a,threshold)
            if st == "present" then return st,r end
            if st == "expiring" then best,remain=st,r end
        end
    end
    if best == "expiring" then return best,remain end
    if s.complete then return "missing" end
    -- A partial/blocked scan can still be answered by explicitly readable IDs.
    local allReadable=true
    for id in pairs(ids) do
        if readable(id) then
            local query=C_UnitAuras and (unit == "player" and C_UnitAuras.GetPlayerAuraBySpellID or C_UnitAuras.GetUnitAuraBySpellID)
            local ok,a
            if query then
                if unit == "player" then ok,a=pcall(query,id) else ok,a=pcall(query,unit,id) end
            end
            if not ok or secret(a) then allReadable=false
            elseif a ~= nil then
                local st,r=auraState(a,threshold)
                if st == "present" then return st,r end
                if st == "expiring" then best,remain=st,r end
            end
        else allReadable=false end
    end
    if best == "expiring" then return best,remain end
    return allReadable and "missing" or "unknown"
end
F.State = state
function F.CancelTimer()
    if F.timer then F.timer:Cancel(); F.timer=nil end
    nextAt=nil
end
local coveredSpells = {}
local function emit(missing,key,label,def,st,cast,item,unit)
    F.status[key]=st
    -- Built-in personal reminders own their spell family even when present.
    -- Group coverage is a different target and must remain independent.
    if key ~= "group" and def then
        if def.id then coveredSpells[def.id] = true end
        for _, id in ipairs(def.ids or {}) do coveredSpells[id] = true end
    end
    if st == "present" or st == "off" or (st == "unknown" and not F.Get(config,"unknown")) then return end
    local e=makeEntry()
    e.cat="forever"; e.dismissKey="forever:"..key
    e.mode="texture"; e.spellID=def and def.id; e.texture=def and texture(def.id) or 134400
    e.label=label; e.silent=st == "unknown"; e.desaturated=e.silent
    e.detail=st == "unknown" and "Buff information is unavailable in this context. This is not a missing-buff warning."
        or (st == "expiring" and "Expires soon. " or "Missing. ").."Click to refresh out of combat; use your action bar during combat."
    if st == "unknown" then e.label=label.." ?"
    elseif st == "expiring" then e.label=label.." soon" end
    if st ~= "unknown" then
        if cast then e.mode="spell"; e.spellID=cast; e.unit=unit or "player"
        elseif item and item > 0 then
            local count=C_Item and C_Item.GetItemCount and C_Item.GetItemCount(item,false,false,false) or 0
            e.tooltipItem=item
            if number(count) and count > 0 then e.mode="item"; e.itemID=item
            else e.detail="Missing buff. The selected item is not in your bags." end
            if C_Item and C_Item.GetItemIconByID then e.texture=C_Item.GetItemIconByID(item) or e.texture end
        end
    end
    missing[#missing+1]=e
    return e
end
local function chosen(kind,key)
    for _,d in ipairs(F[kind]) do if d.key == key then return d end end
end
local function selection(kind,key,threshold)
    local list=key == "any" and F[kind] or {chosen(kind,key)}
    local selected,unknown,expiring,cast
    for _,d in ipairs(list) do
        local c=castSpell(d)
        if c or kind == "flasks" or kind == "elixirs" then
            selected=selected or d; cast=cast or c
            local st=state(d,"player",threshold)
            if st == "present" then return st,d,c end
            if st == "expiring" then expiring=d end
            if st == "unknown" then unknown=true end
        end
    end
    if expiring then return "expiring",expiring,castSpell(expiring) end
    if not selected then return "off" end
    -- "Any" never picks an arbitrary aura/blessing to cast.
    return unknown and "unknown" or "missing",selected,key ~= "any" and cast or nil
end
local function auraSelection(key)
    if not GetNumShapeshiftForms or not GetShapeshiftFormInfo then return "unknown" end
    local ok,n=pcall(GetNumShapeshiftForms)
    if not ok or not number(n) then return "unknown" end
    local found, target
    for _,d in ipairs(F.auras) do if (key == "any" or key == d.key) and castSpell(d) then target=target or d end end
    if not target then return "off" end
    for i=1,n do
        local success,_,active,_,id=pcall(GetShapeshiftFormInfo,i)
        if not success or secret(active) or secret(id) then return "unknown",target end
        for _,d in ipairs(F.auras) do
            local ids,names=family(d)
            if id and (ids[id] or names[name(id)]) then
                found=true
                if active and (key == "any" or key == d.key) then return "present",d end
            end
        end
    end
    return found and "missing" or "unknown",target,key ~= "any" and castSpell(target) or nil
end
local function weaponState(threshold)
    local inventoryID=GetInventoryItemID and GetInventoryItemID("player",16)
    if secret(inventoryID) then return "unknown" end
    if not inventoryID then return "off" end
    if C_Item and C_Item.GetItemInfoInstant then
        local _,_,_,_,_,class,sub=C_Item.GetItemInfoInstant(inventoryID)
        if not secret(class) and not secret(sub) and class == 2 and sub == 20 then return "off" end -- fishing pole
    end
    if not (C_Item and C_Item.GetWeaponEnchantInfo and Enum and Enum.WeaponSlot and Enum.ItemEnchantType) then return "unknown" end
    local slot=Enum.WeaponSlot.MainHand
    if slot == nil then return "unknown" end
    local ok,enchants=pcall(C_Item.GetWeaponEnchantInfo,slot)
    if not ok or secret(enchants) or type(enchants) ~= "table" then return "unknown" end
    local unknown=false
    for _,e in pairs(enchants) do
        if secret(e) or type(e) ~= "table" or secret(e.hasEnchant) or secret(e.enchantType) then unknown=true
        elseif e.hasEnchant and (e.enchantType == Enum.ItemEnchantType.Temporary or e.enchantType == Enum.ItemEnchantType.Imbue) then
            if not number(e.timeLeft) then return "present" end
            if e.timeLeft > 0 then
                local remaining=e.timeLeft/1000
                schedule(GetTime()+remaining)
                if threshold>0 then
                    if remaining<=threshold then return "expiring" end
                    schedule(GetTime()+remaining-threshold)
                end
                return "present"
            end
            return "present"
        end
    end
    return unknown and "unknown" or "missing"
end
local function groupCoverage(missing,key,threshold)
    local d=chosen("blessings",key)
    if not d or not castSpell(d) or not IsInGroup() then return end
    local inRaid=IsInRaid(); local total=inRaid and GetNumGroupMembers() or GetNumSubgroupMembers()
    local have,count,unknown,first=0,0,0,nil
    local needs={}
    for i=1,total do
        local unit=(inRaid and "raid" or "party")..i
        if UnitExists(unit) and UnitIsConnected(unit) and not UnitIsDeadOrGhost(unit) and not UnitIsUnit(unit,"player") then
            if UnitIsVisible and not UnitIsVisible(unit) then unknown=unknown+1
            else
                local st=state(d,unit,threshold)
                count=count+1
                if st == "present" then have=have+1
                elseif st == "unknown" then unknown=unknown+1
                else
                    first=first or unit
                    local n=UnitName(unit)
                    if not secret(n) and n then needs[#needs+1]=n end
                end
            end
        end
    end
    local st=first and "missing" or (unknown > 0 and "unknown" or "present")
    local e=emit(missing,"group","Group "..name(d.id,d.label),d,st,first and castSpell(d),nil,first)
    if e then
        e.groupHave=have; e.groupTotal=count
        e.detail="Normal blessing only; no automatic assignments. "..(#needs>0 and ("Needs refresh: "..table.concat(needs,", ")..". ") or "")
            ..(unknown>0 and (unknown.." member(s) unavailable. ") or "").."Click out of combat to bless the first listed player."
    end
end
function F.Collect(fo,missing,acquire,tex,shows,inInstance,inPvP)
    config=fo; makeEntry=acquire; texture=tex; snapshots={}; F.status={}; coveredSpells={}
    if not fo or not shows(fo.whereToShow,inInstance) then F.SetGroup(false); return end
    local threshold=tonumber(F.Get(fo,"warnSeconds")) or 30
    threshold=math.max(0,math.min(300,threshold))
    local paladin=select(2,UnitClass("player")) == "PALADIN"
    local personal=paladin and shows(F.Get(fo,"paladinWhere"),inInstance)
    local mode=F.Get(fo,"tankMode")
    local role=UnitGroupRolesAssigned and UnitGroupRolesAssigned("player")
    local tank=mode == "on" or (mode == "auto" and not secret(role) and role == "TANK")
    if personal then
        if tank and known(25780) then emit(missing,"rf","Righteous Fury",rf,state(rf,"player",threshold),25780) end
        for _,pair in ipairs({{"auras","aura","Aura"},{"blessings","blessing","Blessing"}}) do
            local key=F.Get(fo,pair[2])
            if key ~= "off" then
                local st,d,cast
                if pair[2] == "aura" then st,d,cast=auraSelection(key) else st,d,cast=selection(pair[1],key,threshold) end
                if d then emit(missing,pair[2],key == "any" and pair[3] or name(d.id,d.label),d,st,cast) end
            end
        end
    end
    local group=personal and F.Get(fo,"groupBlessing") ~= "off" and IsInGroup() and not InCombatLockdown()
    F.SetGroup(group)
    if group then groupCoverage(missing,F.Get(fo,"groupBlessing"),threshold) end
    if not inPvP and shows(F.Get(fo,"consumablesWhere"),inInstance) then
        if F.Get(fo,"food") then
            local id=F.Get(fo,"foodBuff"); local def=id > 0 and {id=id,ids={id},label="Food"} or food
            local st=state(def,"player",threshold)
            local eating=state({id=433,ids={433},label="Food"},"player",0)
            if eating ~= "present" then emit(missing,"food","Food",def,st,nil,F.Get(fo,"foodItem")) end
        end
        for _,pair in ipairs({{"flasks","flask","Flask"},{"elixirs","elixir","Elixir"}}) do
            local key=F.Get(fo,pair[2])
            if key ~= "off" then
                local st,d=selection(pair[1],key,threshold)
                if pair[2] == "flask" and F.Get(fo,"flaskBuff") > 0 then
                    d={id=F.Get(fo,"flaskBuff"),ids={F.Get(fo,"flaskBuff")},label="Flask"}; st=state(d,"player",threshold)
                end
                if d then emit(missing,pair[2],pair[3],d,st,nil,key ~= "any" and d.item or nil) end
            end
        end
        if F.Get(fo,"weapon") then
            local st=weaponState(threshold)
            local e=emit(missing,"weapon","Weapon Oil",nil,st)
            if e then
                e.texture=GetInventoryItemTexture and GetInventoryItemTexture("player",16) or 134400
                local item=F.Get(fo,"oilItem")
                local count=item>0 and C_Item and C_Item.GetItemCount and C_Item.GetItemCount(item,false,false,false) or 0
                if st ~= "unknown" and number(count) and count>0 then
                    e.mode="macro"; e.macro="/use item:"..item.."\n/use 16"; e.tooltipItem=item
                end
                e.detail="Main-hand temporary enchant (oil or stone). Permanent enchants do not satisfy this reminder. Select an oil/stone item to apply it with a click out of combat."
            end
        end
    end
    if fo.camp ~= false and not inPvP then emit(missing,"camp","Camp",camp,state(camp,"player",0)) end
    for _,id in ipairs(fo.customIDs or {}) do
        if number(id) and id>0 and id~=25780 and not coveredSpells[id] then
            local d={id=id,ids={id},label=name(id,tostring(id))}
            emit(missing,tostring(id),d.label,d,state(d,"player",threshold),known(id) and id or nil)
        elseif id==25780 and not coveredSpells[id] then
            emit(missing,tostring(id),"Righteous Fury",rf,state(rf,"player",threshold),known(id) and id or nil)
        end
    end
    if nextAt then F.timer=C_Timer.NewTimer(math.max(.1,nextAt-GetTime()+.05),function() F.timer=nil; if F.refresh then F.refresh() end end) end
end
function F.SetGroup(on)
    if not F.events or F.group == on then return end
    F.group=on
    if on then F.events:RegisterEvent("UNIT_AURA") else F.events:UnregisterEvent("UNIT_AURA") end
end
function F.Init(refresh)
    F.refresh=refresh
    if F.events then return end
    F.events=CreateFrame("Frame")
    for _,ev in ipairs({"SPELLS_CHANGED","UPDATE_SHAPESHIFT_FORM","UPDATE_SHAPESHIFT_FORMS","PLAYER_ROLES_ASSIGNED","ROLE_CHANGED_INFORM","GROUP_ROSTER_UPDATE","BAG_UPDATE_DELAYED","PLAYER_EQUIPMENT_CHANGED","PLAYER_UPDATE_RESTING","GET_ITEM_INFO_RECEIVED"}) do F.events:RegisterEvent(ev) end
    F.events:RegisterUnitEvent("UNIT_INVENTORY_CHANGED","player")
    F.events:SetScript("OnEvent",function(_,ev,unit)
        if ev == "UNIT_AURA" and (not F.group or type(unit) ~= "string" or not (unit:match("^party%d+$") or unit:match("^raid%d+$"))) then return end
        if ev == "SPELLS_CHANGED" then spellInfoCache={} end
        refresh()
    end)
end

-- Select real items/effects by name in settings. A previously chosen item stays
-- selectable when out of stock, so visiting settings cannot reset preferences.
function F.BagChoices(kind,selected)
    local values,order={[0]="Reminder only"},{0}
    if C_Container and C_Item and C_Item.GetItemInfoInstant then
        for bag=0,4 do
            for slot=1,C_Container.GetContainerNumSlots(bag) do
                local id=C_Container.GetContainerItemID(bag,slot)
                if id and not secret(id) then
                    local _,_,_,_,_,class,sub=C_Item.GetItemInfoInstant(id)
                    local valid=class == 0 and ((kind == "food" and sub == 5) or (kind == "oil" and (sub == 6 or sub == 15)))
                    if valid and not values[id] then
                        values[id]=(C_Item.GetItemNameByID and C_Item.GetItemNameByID(id)) or ("Item "..id)
                        order[#order+1]=id
                    end
                end
            end
        end
    end
    if selected and selected>0 and not values[selected] then
        values[selected]=(C_Item and C_Item.GetItemNameByID and C_Item.GetItemNameByID(selected)) or ("Item "..selected)
        order[#order+1]=selected
    end
    return values,order
end
function F.BuffChoices(selected)
    snapshots={}
    local values,order={[0]="Automatic"},{0}
    for _,a in ipairs(scan("player").auras) do
        if number(a.spellId) and a.name and not values[a.spellId] then
            values[a.spellId]=a.name; order[#order+1]=a.spellId
        end
    end
    if selected and selected>0 and not values[selected] then
        values[selected]=name(selected,"Spell "..selected); order[#order+1]=selected
    end
    return values,order
end
