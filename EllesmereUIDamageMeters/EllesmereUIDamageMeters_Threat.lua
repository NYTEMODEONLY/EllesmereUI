if EUI_CLIENT_BLOCKED then return end
-- Native live-target source for the existing meter renderer. No external addon.
local _, ns = ...
local EUI = EllesmereUI
local T = { TYPE = "THREAT", LIMIT = 80 }
ns.Threat = T
local function Plain(v)
    if issecretvalue and issecretvalue(v) then return nil end
    return v
end
local function Number(v)
    v=Plain(v)
    if type(v)=="number" and v==v and v>=0 and v<math.huge then return v end
end
local function Numeric(v)
    return type(v)=="number" and ((issecretvalue and issecretvalue(v)) or Number(v)~=nil)
end
local DEFAULTS = { source="target", pets=true, percentMode="pull", showValue=false,
    showPercent=true, pullBar=false, warnSound=false, warnAt=80, warnSkipTank=true,
    warnSoundKey="raidWarning" }
local EMPTY = {}
local function Config()
    local db = ns.EDM and ns.EDM.DB and ns.EDM.DB()
    return db and db.foreverThreat or EMPTY
end
function T.Get(key)
    local v=Config()[key]
    if v==nil then return DEFAULTS[key] end
    return v
end
local function Enemy(unit)
    return Plain(UnitExists(unit))==true and Plain(UnitCanAttack("player",unit))==true
        and Plain(UnitIsDeadOrGhost(unit))~=true
end
function T.ResolveSource()
    local unit=T.Get("source")=="focus" and "focus" or "target"
    if Enemy(unit) then return unit end
    if Plain(UnitExists(unit))==true and Plain(UnitCanAttack("player",unit))==false
        and Enemy(unit.."target") then return unit.."target" end
end
local function TargetValid() return T.ResolveSource()~=nil end
local previewUntil
local function Previewing() return previewUntil and GetTime()<previewUntil end
local function Roster()
    local units,seen={},{}
    local function Add(unit,owner)
        if owner and not T.Get("pets") then return end
        if Plain(UnitExists(unit))~=true then return end
        local guid=Plain(UnitGUID(unit))
        if guid and seen[guid] then return end
        if unit~="player" and Plain(UnitIsUnit(unit,"player"))==true then return end
        if unit~="pet" and Plain(UnitIsUnit(unit,"pet"))==true then return end
        if guid then seen[guid]=true end
        units[#units+1]={unit=unit,owner=owner}
    end
    Add("player"); Add("pet","player")
    if IsInRaid() then
        for i=1,GetNumGroupMembers() do Add("raid"..i); Add("raidpet"..i,"raid"..i) end
    elseif IsInGroup() then
        for i=1,math.max(0,GetNumGroupMembers()-1) do Add("party"..i); Add("partypet"..i,"party"..i) end
    end
    return units
end
local cached, sampledAt, ticker
function T.Invalidate() cached=nil end
function T.GetSession()
    local now=GetTime()
    if cached and now-sampledAt<0.12 then return cached end
    local session={combatSources={},threat=true,threatTitle="Threat",threatEmpty="Select an enemy",threatRanked=true}
    cached=session; sampledAt=now; T.hasData=false
    if Previewing() then
        session.threatPreview=true; session.threatTitle="Threat - Preview"
        for i,pct in ipairs({100,82,55,30}) do
            session.combatSources[i]={name=i==1 and "Preview: Player" or "Preview: Member "..i,
                classFilename="WARRIOR",isLocalPlayer=i==1,totalAmount=pct,threatPercent=pct,
                threatRawPercent=pct,threatRaw=pct*10,threatHolding=i==1,threatStatus=i==1 and 3 or 0,
                threatValue=pct,threatOrder=i,threatUnit=i==1 and "player" or "party"..i}
        end
        return session
    end
    local mob=T.ResolveSource()
    if not mob then
        if T.Get("source")=="focus" then session.threatEmpty="Set an enemy focus or focus its tank" end
        return session
    end
    session.threatMob=mob; session.threatGUID=Plain(UnitGUID(mob))
    local name=Plain(UnitName(mob))
    session.threatTitle="Threat - "..(type(name)=="string" and name or "Target")
    session.threatEmpty="No threat on this target"
    if type(UnitDetailedThreatSituation)~="function" then
        session.threatEmpty="Threat data unavailable"; return session
    end
    for _,member in ipairs(Roster()) do
        local unit=member.unit
        if Plain(UnitIsDeadOrGhost(unit))~=true and Plain(UnitIsConnected(unit))~=false then
            local ok,holding,status,scaled,rawPct,raw=pcall(UnitDetailedThreatSituation,unit,mob)
            if ok and (Numeric(scaled) or type(holding)=="boolean" or type(status)=="number") then
                local readable=Number(scaled)
                local owns=Plain(holding)
                local _,class=UnitClass(member.owner or unit); class=Plain(class)
                local unitName=Plain(UnitName(unit))
                if type(unitName)~="string" then unitName=unit end
                local source={name=unitName,
                    classFilename=type(class)=="string" and class or "UNKNOWN",
                    isLocalPlayer=unit=="player", totalAmount=Numeric(scaled) and scaled or 0,
                    threatPercent=scaled, threatHolding=holding, threatStatus=status,
                    threatRaw=raw, threatRawPercent=rawPct, threatUnit=unit,
                    threatPet=member.owner~=nil, threatValue=readable, threatOrder=#session.combatSources+1}
                session.combatSources[#session.combatSources+1]=source
                if unit=="player" then session.threatPlayer=source end
                if readable==nil or type(owns)~="boolean" then session.threatRanked=false end
                if (readable and readable>0) or owns==true or (Number(raw) or 0)>0
                    or (issecretvalue and issecretvalue(scaled)) then T.hasData=true end
            end
        end
    end
    -- Official pull-line formula, only from readable native values. The row
    -- marks your 100% pull threshold; the existing bar scale remains 0-100.
    local me=session.threatPlayer
    if T.Get("pullBar") and me and Plain(me.threatHolding)==false then
        local scaled,raw=Number(me.threatPercent),Number(me.threatRaw)
        if scaled and scaled>0 and raw and raw>0 then
            local pull=raw*100/scaled
            if Number(pull) then
                local relative=Number(me.threatRawPercent)
                relative=relative and relative*100/scaled or nil
                session.combatSources[#session.combatSources+1]={name="Pull aggro",classFilename="UNKNOWN",
                    totalAmount=100,threatPercent=100,threatRaw=pull,threatRawPercent=Number(relative),
                    threatHolding=false,threatValue=100,threatOrder=81,threatPull=true}
                session.threatPull=true
            end
        end
    end
    -- Sort only fully readable tables; otherwise stable roster order avoids
    -- presenting protected members as zero or a falsely authoritative rank.
    if session.threatRanked then
        table.sort(session.combatSources,function(a,b)
            local ah,bh=Plain(a.threatHolding)==true,Plain(b.threatHolding)==true
            if ah~=bh then return ah end
            if a.threatValue~=b.threatValue then return a.threatValue>b.threatValue end
            return a.threatOrder<b.threatOrder
        end)
    end
    return session
end

function T.PaintAmount(bar,source,rank,ranked,hideNumbers)
    -- Native anchoring reserves exactly the amount text's rendered width,
    -- including opaque values, without reading its protected geometry in Lua.
    local db=ns.EDM and ns.EDM.DB and ns.EDM.DB() or EMPTY
    bar.label:SetPoint("RIGHT",bar.amount,"LEFT",-6,(db.leftTextOffsetY or 0)-(db.rightTextOffsetY or 0))
    bar._threatTextLayout=true
    local pct=source.threatPercent
    if T.Get("percentMode")=="tank" then pct=source.threatRawPercent end
    local value,percent=T.Get("showValue"),T.Get("showPercent")
    if value and percent and Numeric(source.threatRaw) and Numeric(pct) then
        bar.amount:SetFormattedText("%.0f / %.0f%%",source.threatRaw,pct)
    elseif value and not percent and Numeric(source.threatRaw) then
        bar.amount:SetFormattedText("%.0f",source.threatRaw)
    elseif not value and percent and Numeric(pct) then bar.amount:SetFormattedText("%.0f%%",pct)
    elseif not value and not percent then bar.amount:SetText("")
    else bar.amount:SetText("--") end
    bar._cachedAmtText=nil
    if hideNumbers or not ranked then bar.pos:SetText("")
    else bar.pos:SetText(rank..".") end
end

function T.RestoreTextLayout(bar)
    if not bar._threatTextLayout then return end
    bar._threatTextLayout=nil
    if bar.ApplyTextOffsets then bar.ApplyTextOffsets() end
end

function T.Tooltip(bar)
    if not bar._src or not EUI.ShowWidgetTooltip then return end
    local s=bar._src
    local text=s.name..(s.threatPet and " (pet)" or "")
    local pct=Number(s.threatPercent)
    if pct then text=text..string.format("\nThreat: %.1f%%",pct) end
    if Plain(s.threatHolding)==true then text=text.."\nHolding aggro. 100% is not a safety margin."
    else text=text.."\nPercentage shows progress toward pulling aggro." end
    local tankPct=Number(s.threatRawPercent)
    if tankPct then text=text..string.format("\nTank threat: %.1f%%",tankPct) end
    if s.threatPull then text=text.."\nYour pull threshold from the native threat reading." end
    local raw=Number(s.threatRaw)
    if raw then text=text..string.format("\nRaw threat: %.0f",raw) end
    text=text.."\nLive on the tracked enemy; bars show pull progress, not group share."
    EUI.ShowWidgetTooltip(bar.row,text)
end
function T.HideTooltip()
    if EUI.HideWidgetTooltip then EUI.HideWidgetTooltip() end
end

function T.ReportSnapshot()
    T.Invalidate()
    local s=T.GetSession()
    if s.threatPreview then return nil,"Preview data cannot be reported." end
    if #s.combatSources==0 then return nil,s.threatEmpty end
    local rows={}
    for _,src in ipairs(s.combatSources) do
        if not src.threatPull then
        local n=Number(src.threatPercent)
        if not n then return nil,"Live threat is protected; it can be displayed but cannot be copied to chat." end
        rows[#rows+1]={name=src.name,amount=n}
        end
    end
    return {title=s.threatTitle.." (live)",rows=rows,threat=true,total=100}
end

local function Active(W)
    return W.curDMType==T.TYPE and W.frame
        and (W.frame.IsVisible and W.frame:IsVisible() or not W.frame.IsVisible and W.frame:IsShown())
end
local warned, warnedMob
local soundPaths,soundNames,soundOrder
function T.Sounds()
    if not soundPaths then
        if EUI.BuildAlertSoundTables then
            soundPaths,soundNames,soundOrder=EUI.BuildAlertSoundTables()
            if EUI.AppendSharedMediaSounds then EUI.AppendSharedMediaSounds(soundPaths,soundNames,soundOrder) end
        else soundPaths,soundNames,soundOrder={},{},{} end
        soundPaths.raidWarning=8959; soundNames.raidWarning="Raid Warning"
        table.insert(soundOrder,1,"raidWarning")
    end
    return soundPaths,soundNames,soundOrder
end
local function CheckWarning(active)
    local s=cached
    if not active or not T.Get("warnSound") or not s or s.threatPreview then
        warned,warnedMob=false,nil; return
    end
    local guid=s.threatGUID
    if not guid then warned,warnedMob=false,nil;return end
    if guid~=warnedMob then warned,warnedMob=false,guid end
    local me=s.threatPlayer
    local pct=me and Number(me.threatPercent)
    local threshold=Number(T.Get("warnAt")) or 80
    local over=pct and pct>=threshold and Plain(me.threatHolding)==false
    if T.Get("warnSkipTank") then
        local role=UnitGroupRolesAssigned and Plain(UnitGroupRolesAssigned("player"))
        local form=GetShapeshiftFormID and Plain(GetShapeshiftFormID())
        if role=="TANK" or form==5 or form==8 or form==18 then over=false end
    end
    if over and not warned then
        local sound=T.Sounds()[T.Get("warnSoundKey")]
        if type(sound)=="number" and sound~=1 and PlaySound then PlaySound(sound,"Master")
        elseif type(sound)=="string" and PlaySoundFile then PlaySoundFile(sound,"Master") end
    end
    warned=over and true or false
end
function T.Wake()
    local active=false
    for _,W in ipairs(ns._windows or {}) do if Active(W) then active=true; break end end
    CheckWarning(active)
    local mob=T.ResolveSource()
    local busy=Plain(UnitAffectingCombat("player"))==true or Plain(UnitAffectingCombat("pet"))==true
        or (mob and Plain(UnitAffectingCombat(mob))==true) or T.hasData
    if not active and previewUntil then previewUntil=nil;T.Invalidate() end
    if not active or (not Previewing() and (not mob or not busy)) then
        if ticker then ticker:Cancel(); ticker=nil end
    elseif not ticker then
        ticker=C_Timer.NewTicker(0.15,function()
            T.Invalidate()
            for _,W in ipairs(ns._windows or {}) do if Active(W) then W.Refresh() end end
            T.Wake()
        end)
    end
end
function T.Watch(W)
    W.frame:HookScript("OnShow",function()
        if W.curDMType==T.TYPE then W.Refresh() end
        T.Wake()
    end)
    W.frame:HookScript("OnHide",T.Wake)
end

function T.Refresh()
    T.Invalidate()
    for _,W in ipairs(ns._windows or {}) do
        if Active(W) then W._barCacheKey=nil;W._stickyCacheKey=nil;W.Refresh() end
    end
    T.Wake()
end
function T.Set(key,value)
    local db=ns.EDM and ns.EDM.DB and ns.EDM.DB()
    if not db then return end
    db.foreverThreat=db.foreverThreat or {};db.foreverThreat[key]=value
    previewUntil=nil;T.Refresh()
end
function T.Preview()
    if InCombatLockdown and InCombatLockdown() then return end
    previewUntil=GetTime()+10;T.Refresh()
end
function T.Menu()
    local function choose(key,value,label,tip)
        return {text=label,isActive=T.Get(key)==value,tooltip=tip,onClick=function() T.Set(key,value) end}
    end
    local function toggle(key,label,tip)
        local item=choose(key,not T.Get(key),label,tip);item.isActive=T.Get(key)==true;return item
    end
    local sounds={}
    local _,names,order=T.Sounds()
    for _,key in ipairs(order) do sounds[#sounds+1]=choose("warnSoundKey",key,names[key] or key) end
    return {
        {text="Live Threat (all Threat windows)",isHeader=true},
        choose("source","target","Track Target","A friendly target follows the enemy it is fighting."),
        choose("source","focus","Track Focus","A friendly focus follows the enemy it is fighting."),
        "---",
        toggle("pets","Show Pets"),
        {text="Percentage",children={choose("percentMode","pull","Pull %"),choose("percentMode","tank","Tank %")},
            tooltip="Tank % compares threat to the current holder. Bars always show native pull progress."},
        toggle("showPercent","Show Percentage"),toggle("showValue","Show Raw Threat"),
        toggle("pullBar","Show Pull Aggro Row","Only shown when your readable threat can establish your pull threshold."),
        "---",toggle("warnSound","Warning Sound"),
        {text="Warn At (%)",isInput=true,min=1,getValue=function() return T.Get("warnAt") end,
            setValue=function(v) T.Set("warnAt",math.max(1,math.min(100,tonumber(v) or 80))) end},
        toggle("warnSkipTank","Skip Tank Warnings"),{text="Warning Sound Choice",children=sounds},
        "---",{text="Preview (10 seconds)",isDisabled=function() return InCombatLockdown and InCombatLockdown() end,onClick=T.Preview},
    }
end

local driver=CreateFrame("Frame")
for _,event in ipairs({"PLAYER_TARGET_CHANGED","PLAYER_FOCUS_CHANGED","UNIT_TARGET","GROUP_ROSTER_UPDATE","UNIT_PET",
    "UNIT_THREAT_LIST_UPDATE","UNIT_THREAT_SITUATION_UPDATE","PLAYER_REGEN_DISABLED",
    "PLAYER_REGEN_ENABLED","PLAYER_ENTERING_WORLD"}) do driver:RegisterEvent(event) end
driver:SetScript("OnEvent",function(_,event,unit)
    if event=="UNIT_THREAT_LIST_UPDATE" or event=="UNIT_THREAT_SITUATION_UPDATE" then
        local token=Plain(unit)
        if token~=T.ResolveSource() and token~="player" and token~="pet"
            and not (type(token)=="string" and (token:match("^party") or token:match("^raid"))) then return end
    end
    if event=="UNIT_TARGET" and Plain(unit)~="target" and Plain(unit)~="focus" then return end
    if event=="PLAYER_REGEN_DISABLED" then previewUntil=nil end
    T.Refresh()
end)
