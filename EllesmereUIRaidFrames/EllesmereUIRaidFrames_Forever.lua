-- Forever: Blizzard owns unit assignment, secure clicks and combat state.
-- Do not pin this adapter to one beta build: skipping it lets the custom
-- module suppress native frames even when its secure headers cannot run.
if not EUI_FOREVER then return end
if EllesmereUIDB and EllesmereUIDB.foreverGroupRenderer == "official" then return end
EUI_FOREVER_NATIVE_GROUPS = true
local addon = EllesmereUI.Lite.NewAddon(...)
local EUI = EllesmereUI
local frames, hooked = setmetatable({}, { __mode = "k" }), setmetatable({}, { __mode = "k" })
local standardFrames = setmetatable({}, { __mode = "k" })
local textures, pending, applying, dirty
local Queue, Apply
local editModeSession = false
local function IsEditing()
    return editModeSession or (EditModeManagerFrame and EditModeManagerFrame.IsEditModeActive
        and EditModeManagerFrame:IsEditModeActive())
end
-- Supported defaults copied from the original EUI module. Profiles are sparse.
local defaults = {
    frameWidth=125, frameHeight=60, partyFrameWidth=125, partyFrameHeight=60,
    cellSpacing=-1, groupSpacing=-1, unitGrowth="DOWN", groupGrowth="RIGHT",
    partyHorizontal=false, healthBarTexture="atrocity", healthBarOpacity=100,
    customBgColor={r=17/255,g=17/255,b=17/255}, powerHeight=4, powerBgDarkness=40,
    powerBgColor={r=107/255,g=107/255,b=107/255}, nameSize=10, nameColorMode="custom",
    nameCustomColor={r=1,g=1,b=1}, namePosition="topleft", nameOffsetX=0, nameOffsetY=0,
    healthTextSize=9, borderSize=1, borderColor={r=0,g=0,b=0}, borderAlpha=1,
}
local sections = {
    healthBarTexture="healthBar", healthBarOpacity="healthBar", customBgColor="healthBar",
    powerHeight="powerBar", powerBgDarkness="powerBar", powerBgColor="powerBar",
    nameSize="textDisplay", nameColorMode="textDisplay", nameCustomColor="textDisplay",
    namePosition="textDisplay", nameOffsetX="textDisplay", nameOffsetY="textDisplay",
    healthTextSize="textDisplay", borderSize="indicators", borderColor="indicators", borderAlpha="indicators",
}
local function IsGroup(frame)
    if not frame or not frame.healthBar or not CompactRaidGroupTypeEnum then return false end
    return frame.groupType == CompactRaidGroupTypeEnum.Party or frame.groupType == CompactRaidGroupTypeEnum.Raid
end
local function IsParty(frame)
    return standardFrames[frame] ~= nil or frame.groupType == CompactRaidGroupTypeEnum.Party
end
local function Value(frame, key)
    local p, section = addon.db.profile, sections[key]
    if IsParty(frame) and section and p.partySyncSections and p.partySyncSections[section] == false
        and p["party_"..key] ~= nil then return p["party_"..key] end
    if p[key] ~= nil then return p[key] end
    return defaults[key]
end
local function Snap(value)
    local perfect = EUI.PP and EUI.PP.perfect
    if not perfect then return value end
    local pixel = perfect / UIParent:GetEffectiveScale()
    return math.floor(value / pixel + 0.501) * pixel
end
local function Size(party)
    local p = addon.db.profile
    return Snap(party and (p.partyFrameWidth or defaults.partyFrameWidth) or (p.frameWidth or defaults.frameWidth)),
        Snap(party and (p.partyFrameHeight or defaults.partyFrameHeight) or (p.frameHeight or defaults.frameHeight))
end
local function Font(fs, size)
    if not fs then return end
    fs:SetFont(EUI.GetFontPath and EUI.GetFontPath("raidFrames") or STANDARD_TEXT_FONT, size,
        EUI.GetFontOutlineFlag and EUI.GetFontOutlineFlag("raidFrames") or "")
end
local function Paint(frame)
    if not addon.db or not IsGroup(frame) then return end
    if IsEditing() then dirty=true; return end
    local d = frames[frame]
    if not d then d = {}; frames[frame] = d end
    local path = textures and textures[Value(frame, "healthBarTexture")]
    if type(path) == "string" then
        frame.healthBar:SetStatusBarTexture(path)
        if frame.powerBar then frame.powerBar:SetStatusBarTexture(path) end
    end
    -- Native class, disconnect, threat, death and power colors stay authoritative.
    frame.healthBar:SetAlpha((Value(frame, "healthBarOpacity") or 100)/100)
    local bg = Value(frame, "customBgColor")
    if frame.background and bg then
        frame.background:SetColorTexture(bg.r,bg.g,bg.b,1)
        frame.background:SetVertexColor(1,1,1)
    end
    if frame.powerBar and frame.powerBar.background then
        local c = Value(frame,"powerBgColor")
        frame.powerBar.background:SetColorTexture(c.r,c.g,c.b,(Value(frame,"powerBgDarkness") or 40)/100)
    end
    Font(frame.name,Value(frame,"nameSize")); Font(frame.statusText,Value(frame,"healthTextSize"))
    if frame.name and Value(frame,"nameColorMode") == "custom" then
        local c = Value(frame,"nameCustomColor"); frame.name:SetTextColor(c.r,c.g,c.b)
    end
    -- BORDER layer stays below native aggro and selection overlays.
    if not d.border and not InCombatLockdown() then
        d.border = {}; for i=1,4 do d.border[i] = frame:CreateTexture(nil,"BORDER",nil,7) end
    end
    if d.border then
        local c = Value(frame,"borderColor")
        for _, t in ipairs(d.border) do t:SetColorTexture(c.r,c.g,c.b,Value(frame,"borderAlpha")) end
    end
end
local positions = {topleft="TOPLEFT",top="TOP",topright="TOPRIGHT",left="LEFT",center="CENTER",right="RIGHT",bottomleft="BOTTOMLEFT",bottom="BOTTOM",bottomright="BOTTOMRIGHT"}
local function Geometry(frame)
    if InCombatLockdown() or IsEditing() or not IsGroup(frame) then return end
    local w,h = Size(IsParty(frame)); frame:SetSize(w,h)
    local power = frame.powerBar
    -- Keep native power visibility, including new modes and unassigned roles.
    local ph = power and power:IsShown() and Snap(Value(frame,"powerHeight")) or 0
    frame.healthBar:ClearAllPoints()
    frame.healthBar:SetPoint("TOPLEFT",frame,"TOPLEFT",1,-1)
    frame.healthBar:SetPoint("BOTTOMRIGHT",frame,"BOTTOMRIGHT",-1,1+ph)
    if power then
        power:ClearAllPoints()
        power:SetPoint("BOTTOMLEFT",frame,"BOTTOMLEFT",1,1)
        power:SetPoint("BOTTOMRIGHT",frame,"BOTTOMRIGHT",-1,1)
        power:SetHeight(math.max(1,ph))
    end
    -- Do not call native layout-state setters here: they write Lua fields later
    -- consumed by max-health and private-aura secure paths. Those overlays keep
    -- their native power-height/anchor settings while our bars use visual geometry.
    if frame.name then
        local point = positions[Value(frame,"namePosition")] or "TOPLEFT"
        local x,y = Value(frame,"nameOffsetX"),Value(frame,"nameOffsetY")
        if point:find("LEFT") then x=x+3 elseif point:find("RIGHT") then x=x-3 end
        if point:find("TOP") then y=y-3 elseif point:find("BOTTOM") then y=y+3 end
        frame.name:ClearAllPoints(); frame.name:SetPoint(point,frame.healthBar,point,x,y)
        frame.name:SetWidth(math.max(1,w-6))
        frame.name:SetJustifyH(point:find("LEFT") and "LEFT" or point:find("RIGHT") and "RIGHT" or "CENTER")
    end
    local border = frames[frame] and frames[frame].border
    if border then
        local size = math.max(0,Snap(Value(frame,"borderSize")))
        for _,t in ipairs(border) do t:ClearAllPoints() end
        border[1]:SetPoint("TOPLEFT"); border[1]:SetPoint("TOPRIGHT"); border[1]:SetHeight(size)
        border[2]:SetPoint("BOTTOMLEFT"); border[2]:SetPoint("BOTTOMRIGHT"); border[2]:SetHeight(size)
        border[3]:SetPoint("TOPLEFT"); border[3]:SetPoint("BOTTOMLEFT"); border[3]:SetWidth(size)
        border[4]:SetPoint("TOPRIGHT"); border[4]:SetPoint("BOTTOMRIGHT"); border[4]:SetWidth(size)
    end
end
local function Discover(fn)
    if CompactRaidFrameContainer and CompactRaidFrameContainer.ApplyToFrames then
        CompactRaidFrameContainer:ApplyToFrames("normal",fn)
    end
    if CompactPartyFrame then
        for _,frame in ipairs(CompactPartyFrame.memberUnitFrames or {}) do fn(frame) end
    end
end
-- Never call Edit Mode settings setters or native unit refresh from addon Lua.
-- OnSystemSettingChange -> UpdateAllFromEditMode -> UpdateHealthColor compares
-- secret status-bar colors under tainted execution in build 69913. Native events
-- own those paths; this adapter only paints and applies OOC geometry afterwards.
local function GroupSpacing(group)
    if IsEditing() then dirty=true; return end
    if InCombatLockdown() or not addon.db or not group or not group.memberUnitFrames then return end
    if group.groupType ~= CompactRaidGroupTypeEnum.Party and group.groupType ~= CompactRaidGroupTypeEnum.Raid then return end
    local horizontal = EditModeManagerFrame:ShouldRaidFrameUseHorizontalRaidGroups(group.groupType)
    local gap = Snap(addon.db.profile.cellSpacing or -1)
    local previous,shown = nil,0
    for _,member in ipairs(group.memberUnitFrames) do
        if previous then
            member:ClearAllPoints()
            if horizontal then member:SetPoint("LEFT",previous,"RIGHT",gap,0)
            else member:SetPoint("TOP",previous,"BOTTOM",0,-gap) end
        end
        previous = member; if member:IsShown() then shown=shown+1 end
    end
    -- Native layout just computed a fresh extent; preserve its title/border.
    if shown > 1 then
        if horizontal then group:SetWidth(group:GetWidth()+(shown-1)*gap)
        else group:SetHeight(group:GetHeight()+(shown-1)*gap) end
    end
end
local function HookObject(object,method)
    if not object or type(object[method]) ~= "function" then return end
    local methods = hooked[object] or {}; hooked[object] = methods
    if not methods[method] then hooksecurefunc(object,method,Queue); methods[method]=true end
end
local function StandardParty()
    local pool = PartyFrame and PartyFrame.PartyMemberFramePool
    if not pool or not pool.EnumerateActive or InCombatLockdown() or IsEditing() then return end
    HookObject(PartyFrame,"InitializePartyMemberFrames")
    for member in pool:EnumerateActive() do
        local health = member.HealthBarContainer and member.HealthBarContainer.HealthBar
        if health and member.ManaBar then
            -- These are native pool members, never nameplates or guessed globals.
            local d = standardFrames[member]
            if not d then d = {}; standardFrames[member] = d end
            HookObject(member,"UpdateArt")
            -- Standard party bars encode health/power colors in their native
            -- atlases (HealthBar.lockColor is true). Replacing the green atlas
            -- with an untinted EUI texture makes health white. Keep native art
            -- here; compact boxes use native class tint with our EUI textures.
            Font(member.Name,Value(member,"nameSize"))
            if member.Name and Value(member,"nameColorMode") == "custom" then
                local c = Value(member,"nameCustomColor"); member.Name:SetTextColor(c.r,c.g,c.b)
            end
            for _,bar in ipairs({member.HealthBarContainer,member.ManaBar}) do
                for _,key in ipairs({"CenterText","LeftText","RightText"}) do
                    Font(bar[key],Value(member,"healthTextSize"))
                end
            end
            -- Do not resize/reanchor native bars: Mainline/PartyFrameTemplates.xml
            -- HealthBar.OnSizeChanged enters UnitFrameHealPredictionBars_UpdateSize,
            -- which reads and compares secret health values. UpdateArt also refreshes
            -- units; we only posthook it and queue these cosmetics after native work.
            -- Keep native masks, portrait/vehicle art, aura/role/state overlays and
            -- secure clicks. Only our four border textures receive geometry changes.
            if not d.border then
                d.border = {}; for i=1,4 do d.border[i]=member:CreateTexture(nil,"BORDER",nil,7) end
            end
            local c,size = Value(member,"borderColor"),math.max(0,Snap(Value(member,"borderSize")))
            local border = d.border
            for _,t in ipairs(border) do
                t:SetColorTexture(c.r,c.g,c.b,Value(member,"borderAlpha")); t:ClearAllPoints()
            end
            border[1]:SetPoint("TOPLEFT"); border[1]:SetPoint("TOPRIGHT"); border[1]:SetHeight(size)
            border[2]:SetPoint("BOTTOMLEFT"); border[2]:SetPoint("BOTTOMRIGHT"); border[2]:SetHeight(size)
            border[3]:SetPoint("TOPLEFT"); border[3]:SetPoint("BOTTOMLEFT"); border[3]:SetWidth(size)
            border[4]:SetPoint("TOPRIGHT"); border[4]:SetPoint("BOTTOMRIGHT"); border[4]:SetWidth(size)
        end
    end
end
Apply = function()
    if not addon.db or applying then return end
    if InCombatLockdown() or IsEditing() then dirty=true; return end
    applying=true
    local ok,err = pcall(function()
        Discover(function(frame) Paint(frame); Geometry(frame) end)
        StandardParty()
        -- Blizzard Edit Mode owns group positions, including save/cancel and layout switches.
        HookObject(PartyFrame,"ApplySystemAnchor"); HookObject(PartyFrame,"Layout")
        HookObject(CompactRaidFrameContainer,"ApplySystemAnchor"); HookObject(CompactRaidFrameContainer,"Layout")
        HookObject(CompactPartyFrame,"UpdateLayout")
        dirty=false
    end)
    applying=false
    if not ok then error(err,0) end
end
Queue = function()
    if applying then return end
    dirty=true
    if pending or InCombatLockdown() or IsEditing() then return end
    pending=true
    C_Timer.After(0,function() pending=false; if dirty then Apply() end end)
end
function addon:OnInitialize()
    self.db = EUI.Lite.NewDB("EllesmereUIRaidFramesDB",{profile=defaults})
end
function addon:OnEnable()
    if EUI.BuildBarTextureTables then textures=EUI.BuildBarTextureTables(true) end
    if type(DefaultCompactUnitFrameSetup) == "function" then
        hooksecurefunc("DefaultCompactUnitFrameSetup",function(frame) if IsGroup(frame) then Paint(frame); Queue() end end)
    end
    for _,name in ipairs({"CompactUnitFrame_UpdateName","CompactUnitFrame_UpdateHealthColor"}) do
        if type(_G[name]) == "function" then hooksecurefunc(name,Paint) end
    end
    if type(CompactRaidGroup_UpdateLayout) == "function" then hooksecurefunc("CompactRaidGroup_UpdateLayout",GroupSpacing) end
    local events=CreateFrame("Frame")
    for _,event in ipairs({"PLAYER_ENTERING_WORLD","PLAYER_REGEN_ENABLED","GROUP_ROSTER_UPDATE","UI_SCALE_CHANGED","DISPLAY_SIZE_CHANGED"}) do events:RegisterEvent(event) end
    events:SetScript("OnEvent",Queue)
    if EventRegistry and EventRegistry.RegisterCallback then
        -- Native ExitEditMode clears editModeActive before resetting party units.
        -- Hold the latch through that reset; only the final Exit event releases it.
        editModeSession = IsEditing() and true or false
        EventRegistry:RegisterCallback("EditMode.Enter",function() editModeSession=true; dirty=true end,addon)
        EventRegistry:RegisterCallback("EditMode.Exit",function() editModeSession=false; Queue() end,addon)
    end
    Queue()
    EUI:RegisterModule("EllesmereUIRaidFrames",{
        title="Group Frames - Forever",
        description="EllesmereUI textures, text, borders and sizing on native compact group frames. Enable Use Raid-Style Party Frames in Blizzard Edit Mode for party boxes; class colors are controlled by Raid Frame Settings. Move and save party/raid positions in Blizzard Edit Mode. Standard portrait frames retain native bar art and colors. Styling pauses during Edit Mode. For the full official party/raid feature set, type /euigroups official and reload; /euigroups native restores this renderer. Your native Edit Mode layout is retained.",
        pages={"Compatibility"},
        buildPage=function(_,parent,y)
            EUI:ClearContentHeader()
            local _,h=EUI.Widgets:SectionHeader(parent,"Imported layout and visuals; native group controls",y)
            return h
        end,
    })
end
EUI_FOREVER_STATUS.groupFrames="Native standard party bar art/colors with EUI fonts/borders; compact class-colored boxes with EUI textures and OOC geometry; positions owned by Blizzard Edit Mode; select raid-style party in Edit Mode; max-health/private-aura spacing stays native; no addon-driven native unit refresh; custom sorting/click casting pending"
