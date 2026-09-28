-- Persist adapter-owned anchors through the native layout API. OOC SetPoint
-- repairs cannot prevent Blizzard's default stack from moving bars in combat.
-- Never change live systemInfo/manager flags or call native refresh methods.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
if tostring(select(2, GetBuildInfo())) ~= "69913" then return end
local Layout = {}
EUI_FOREVER_CombatLayout = Layout
local owned, queued, busy, editing, failed = {}, false, false, false, false
local bindings, editSnapshot = {}, nil
local points = { TOPLEFT=true, TOP=true, TOPRIGHT=true, LEFT=true, CENTER=true,
    RIGHT=true, BOTTOMLEFT=true, BOTTOM=true, BOTTOMRIGHT=true }
local function Plain(v) return not (issecretvalue and issecretvalue(v)) end
local function Number(v)
    return Plain(v) and type(v)=="number" and v==v and v>-math.huge and v<math.huge
end
local function Copy(v, seen)
    assert(Plain(v), "secret layout value")
    if type(v)~="table" then
        assert(type(v)=="nil" or type(v)=="string" or type(v)=="boolean" or Number(v), "invalid layout value")
        return v
    end
    seen = seen or {}
    assert(not seen[v] and getmetatable(v)==nil, "invalid layout table")
    seen[v]=true
    local out={}
    for k,x in pairs(v) do out[Copy(k,seen)]=Copy(x,seen) end
    seen[v]=nil
    return out
end
local function Equal(a,b)
    if type(a)~=type(b) then return false end
    if type(a)~="table" then return a==b end
    for k,v in pairs(a) do if not Equal(v,b[k]) then return false end end
    for k in pairs(b) do if a[k]==nil then return false end end
    return true
end
local function SameAnchor(a,b)
    -- Native persistence may round offsets to float precision. Do not fail the
    -- save or rewrite it on every event for subpixel representation differences.
    return a and b and a.point==b.point and a.relativePoint==b.relativePoint
        and a.relativeTo==b.relativeTo and Number(a.offsetX) and Number(a.offsetY)
        and math.abs(a.offsetX-b.offsetX)<0.01 and math.abs(a.offsetY-b.offsetY)<0.01
end
local function Key(system,index) return tostring(system)..":"..tostring(index) end
local function State()
    EUIForeverCombatLayoutState = EUIForeverCombatLayoutState or {}
    return EUIForeverCombatLayoutState
end
local function Status(message)
    EUI_FOREVER_STATUS.combatLayout=message
end
local function Safe()
    local m=EditModeManagerFrame
    return not InCombatLockdown() and not editing and m
        and m.IsInitialized and m:IsInitialized() and not m.layoutApplyInProgress
        and not m:IsEditModeActive() and not m.overrideLayoutInfo
        and not (m.HasActiveChanges and m:HasActiveChanges())
end
local function ReadLayouts()
    local info=Copy(C_EditMode.GetLayouts())
    local presets=Copy(EditModePresetLayoutManager:GetCopyOfPresetLayouts())
    local presetCount=#presets
    local combined={layouts=presets,activeLayout=info.activeLayout}
    for _,layout in ipairs(info.layouts) do combined.layouts[#combined.layouts+1]=layout end
    assert(combined.layouts[combined.activeLayout], "native active layout is unavailable")
    return combined,info,presetCount
end
local function Find(info,name,kind)
    local found
    for i,layout in ipairs(info.layouts) do
        if layout.layoutName==name and layout.layoutType==kind then
            assert(not found, "duplicate native layout name")
            found=i
        end
    end
    return found
end
local function Run()
    local api=C_EditMode
    assert(api and api.GetLayouts and api.SaveLayouts and api.SetActiveLayout
        and api.OnLayoutAdded and api.ConvertLayoutInfoToString and api.ConvertStringToLayoutInfo
        and api.IsValidLayoutName and EditModePresetLayoutManager, "native layout API unavailable")
    local combined,before,presetCount=ReadLayouts()
    local state=State()
    if state.disabled then Status("disabled; /euicombatlayout retry to enable"); return end
    local kind=Enum.EditModeLayoutType.Character
    local identity=state.name or state.pending
    local index=identity and Find(combined,identity,kind)
    -- Respect a deliberate native layout selection after the initial migration.
    if state.name and index~=combined.activeLayout then
        Status("inactive; select "..state.name.." in Edit Mode")
        return
    end
    if state.pending and state.previous and combined.activeLayout~=index
        and combined.activeLayout~=Find(combined,state.previous.name,state.previous.kind) then
        Status("pending copy retained; previous native layout is no longer selected")
        return
    end
    local active=combined.layouts[combined.activeLayout]
    local candidate=Copy(index and combined.layouts[index] or active)
    local matched,changed=0,false
    for _,system in ipairs(candidate.systems) do
        local desired=owned[Key(system.system,system.systemIndex)]
        if desired then
            matched=matched+1
            if system.isInDefaultPosition~=false or system.anchorInfo2~=nil or not SameAnchor(system.anchorInfo,desired) then changed=true end
            system.anchorInfo=Copy(desired)
            system.anchorInfo2=nil
            system.isInDefaultPosition=false
        end
    end
    local expected=0
    for _ in pairs(owned) do expected=expected+1 end
    assert(matched==expected and matched>0, "owned systems missing from native layout")
    -- Some beta sessions lost the character SavedVariables while the native
    -- layout survived. Recover only the already-selected, exactly matching
    -- adapter copy. Never select another layout or infer a rollback target.
    local activeName=active.layoutName
    if not identity and not changed and active.layoutType==kind
        and type(activeName)=="string" and (activeName=="Ellesmere Forever Combat"
            or activeName:match("^Ellesmere Forever Combat %d+$")) then
        assert(Find(combined,activeName,kind)==combined.activeLayout, "ambiguous recovered layout")
        state.name=activeName
        index=combined.activeLayout
    end
    if state.name and index and not changed then Status("active: "..state.name.." ("..matched.." anchors)"); return end
    local creating=not index
    if creating then
        local count=0
        for _,layout in ipairs(before.layouts) do if layout.layoutType==kind then count=count+1 end end
        assert(count<Constants.EditModeConsts.EditModeMaxLayoutsPerType, "character Edit Mode layout slots are full")
        local name="Ellesmere Forever Combat"
        local suffix=1
        while Find(combined,name,kind) do suffix=suffix+1; name="Ellesmere Forever Combat "..suffix end
        assert(api.IsValidLayoutName(name), "native layout name rejected")
        candidate.layoutName=name
        candidate.layoutType=kind
        index=#combined.layouts+1
    end
    -- Validate native serialization before persistence, retaining native settings.
    local serialized=api.ConvertLayoutInfoToString(candidate)
    local decoded=api.ConvertStringToLayoutInfo(serialized)
    assert(type(serialized)=="string" and serialized~="" and decoded and decoded.systems, "native layout serialization failed")
    combined.layouts[index]=candidate
    local previous=combined.activeLayout
    if creating then
        state.previous={name=active.layoutName,kind=active.layoutType,index=previous}
        -- Save can succeed even when subsequent verification fails. Retain its
        -- identity before the call so retry repairs that same additive copy.
        state.pending=candidate.layoutName
    end
    api.SaveLayouts(combined)
    if creating then api.OnLayoutAdded(index,false,true) end
    local after,rawAfter=ReadLayouts()
    local actual=Find(after,candidate.layoutName,kind)
    assert(actual==index and after.activeLayout==previous, "native layout save verification failed")
    -- A migration is additive; a sync replaces only our active layout.
    assert(#rawAfter.layouts==#before.layouts+(creating and 1 or 0), "native layout count changed unexpectedly")
    for i,layout in ipairs(before.layouts) do
        if creating or i+presetCount~=index then
            assert(Equal(layout,rawAfter.layouts[i]), "unrelated native layout changed")
        end
    end
    local saved=after.layouts[index]
    local verified=0
    for _,system in ipairs(saved.systems) do
        local desired=owned[Key(system.system,system.systemIndex)]
        if desired then
            assert(system.isInDefaultPosition==false and system.anchorInfo2==nil and SameAnchor(system.anchorInfo,desired), "saved native anchor did not round trip")
            verified=verified+1
        end
    end
    assert(verified==matched, "saved native system missing")
    if index~=previous then api.SetActiveLayout(index) end
    local applied=ReadLayouts()
    assert(applied.activeLayout==index, "native layout activation failed")
    state.name=candidate.layoutName
    state.pending=nil
    Status("active: "..state.name.." ("..matched.." anchors)")
end
function Layout.Queue()
    if queued or busy or failed or not next(owned) then return end
    queued=true
    C_Timer.After(0.5,function()
        queued=false
        if not Safe() then return end
        busy=true
        local ok,err=pcall(Run)
        busy=false
        if not ok then
            failed=true
            Status("pending: "..tostring(err))
            print("|cff0cd29fEllesmereUI:|r Combat layout could not be applied: "..tostring(err)..". /euicombatlayout retry retries it.")
        end
    end)
end
function Layout.Register(frame,position,scale,onSaved)
    if not frame or not position or InCombatLockdown() or editing then return end
    local system,index=frame.system,frame.systemIndex
    if not Number(system) or (index~=nil and not Number(index)) then return end
    scale=scale or 1
    if not Number(scale) or scale<=0 or not Number(position.x) or not Number(position.y) then return end
    local point,relativePoint=position.point or "CENTER",position.relPoint or "CENTER"
    local relativeTo=position.relativeTo or "UIParent"
    if not points[point] or not points[relativePoint] or type(relativeTo)~="string" then return end
    local desired={point=point,relativePoint=relativePoint,relativeTo=relativeTo,
        offsetX=position.x*scale,offsetY=position.y*scale}
    local key=Key(system,index)
    bindings[key]={position=position,scale=scale,onSaved=onSaved}
    if not Equal(owned[key],desired) then owned[key]=desired; Layout.Queue() end
end
local driver=CreateFrame("Frame")
driver:RegisterEvent("PLAYER_ENTERING_WORLD")
driver:RegisterEvent("PLAYER_REGEN_ENABLED")
driver:RegisterEvent("EDIT_MODE_LAYOUTS_UPDATED")
driver:SetScript("OnEvent",function() Layout.Queue() end)
if EventRegistry then
    EventRegistry:RegisterCallback("EditMode.Enter",function()
        editing=true
        editSnapshot=nil
        local ok,info=pcall(ReadLayouts)
        if ok then editSnapshot=info.layouts[info.activeLayout] end
    end,Layout)
    EventRegistry:RegisterCallback("EditMode.SavedLayouts",function()
        if not editing or not editSnapshot or InCombatLockdown() then return end
        local ok,err=pcall(function()
            local info=ReadLayouts()
            local current=info.layouts[info.activeLayout]
            local previous={}
            for _,system in ipairs(editSnapshot.systems) do previous[Key(system.system,system.systemIndex)]=system end
            for _,system in ipairs(current.systems) do
                local key=Key(system.system,system.systemIndex)
                local old,binding=previous[key],bindings[key]
                if binding and old and (not SameAnchor(old.anchorInfo,system.anchorInfo)
                    or not Equal(old.anchorInfo2,system.anchorInfo2)
                    or old.isInDefaultPosition~=system.isInDefaultPosition) then
                    local a=system.anchorInfo
                    local p={point=a.point,relPoint=a.relativePoint,relativeTo=a.relativeTo,
                        x=a.offsetX/binding.scale,y=a.offsetY/binding.scale}
                    if binding.onSaved then binding.onSaved(p)
                    else for k,v in pairs(p) do binding.position[k]=v end end
                    owned[key]=Copy(a)
                end
            end
            editSnapshot=current
        end)
        if not ok then Status("native saved position adoption: "..tostring(err)) end
    end,Layout)
    EventRegistry:RegisterCallback("EditMode.Exit",function() editing=false; editSnapshot=nil; Layout.Queue() end,Layout)
end
SLASH_EUIFOREVERCOMBATLAYOUT1="/euicombatlayout"
SlashCmdList.EUIFOREVERCOMBATLAYOUT=function(command)
    if command=="retry" then
        failed=false; State().disabled=nil; Layout.Queue()
    elseif command=="restore" then
        if not Safe() then print("EllesmereUI: Leave combat and Edit Mode before restoring the previous layout."); return end
        local state=State()
        if not state.previous then return end
        local ok,err=pcall(function()
            local info=ReadLayouts()
            local index=Find(info,state.previous.name,state.previous.kind)
            assert(index,"previous native layout is no longer available")
            state.disabled=true
            C_EditMode.SetActiveLayout(index)
            Status("previous native layout restored; automatic synchronization disabled")
        end)
        if not ok then print("EllesmereUI: "..tostring(err)) end
    end
    print("EllesmereUI combat layout: "..(EUI_FOREVER_STATUS.combatLayout or "waiting for native frames"))
end
Status("waiting for native frames")
