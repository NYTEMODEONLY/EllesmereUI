local A, e = EllesmereUIChatMeters, EllesmereUI
local MODULE = "EllesmereUIDamageMeters"
local sections, rows, nativeCalls, invalidations = {}, {}, {}, 0
local shown, active = false, nil
e._modules = {}
e.Widgets = {
    SectionHeader=function(_,parent,title,y)
        sections[#sections+1]={title=title,y=y}
        return {},30
    end,
    DualRow=function(_,parent,y,left,right)
        rows[#rows+1]={left,right,y=y}
        return {},40
    end,
}
e.InvalidateModulePageCache=function(_,module)
    assert(module==MODULE); invalidations=invalidations+1
end
e.IsShown=function() return shown end
e.GetActiveModule=function() return active end
e.RefreshPage=function() NATIVE_PAGE_REFRESHED=true end
local function NativeBuilder(page,parent,y,extra)
    nativeCalls[#nativeCalls+1]={page=page,y=y,extra=extra}
    if not e._prebuilding then
        DM._optionsOpen=true
        for _,w in ipairs(DM._windows) do w.frame:Show() end
    end
    return math.abs(y)+500,"original return"
end
local onReset=function() end
local onLeave=function() end
local config={pages={"Damage Meters","Spell History"},buildPage=NativeBuilder,
    onReset=onReset,onModuleLeave=onLeave}
e._modules[MODULE]=config
Event("ADDON_LOADED","EllesmereUIOptions")
assert(invalidations==1 and config.buildPage~=NativeBuilder, "Extend LOD registered page")
assert(config.onReset==onReset and config.onModuleLeave==onLeave, "Preserve upstream callbacks")
local height,extra=config.buildPage("Damage Meters",{},-10,"forwarded")
assert(height==620 and extra=="original return", "Scroll height includes section; preserve return values")
assert(#sections==1 and sections[1].title=="CHAT METERS (CUSTOM)" and #rows==2)
assert(nativeCalls[1].y==-120 and nativeCalls[1].extra=="forwarded", "Shift native controls and forward args")
assert(rows[1][1].getValue()==false, "Read companion state from previous tests")
rows[1][1].setValue(true)
assert(A.db.enabled and rows[1][1].getValue(), "Native-style toggle controls embedding")
assert(A.ready and A.left.frame:GetParent()==A.body and A.right.frame:GetParent()==A.body,
    "Enabling embedding while settings are open keeps meters in chat")
rows[2][1].setValue(false); rows[2][2].setValue(false); rows[1][2].setValue(true)
assert(not A.db.autoDungeon and not A.db.autoRaid and A.db.returnOnExit)
assert(SAVED.width==375 and SAVED.position.x==1000, "Controls leave upstream profile unchanged")
local builder=config.buildPage
for i=1,3 do A:IntegrateOptions() end
assert(config.buildPage==builder and invalidations==1, "Repeated integration never duplicates the section")
local sectionCount=#sections
height=config.buildPage("Spell History",{},-12)
assert(height==512 and #sections==sectionCount, "Other pages unchanged")
DM._optionsOpen=false; e._prebuilding=true
config.buildPage("Damage Meters",{},0)
assert(not DM._optionsOpen, "Search prebuild does not force meter previews")
e._prebuilding=false
local widgets=e.Widgets; e.Widgets=nil
height=config.buildPage("Damage Meters",{},-10)
assert(height==510, "Missing widget API leaves original page usable")
e.Widgets=widgets
local replacement={pages={"Damage Meters"},buildPage=NativeBuilder}
e._modules[MODULE]=replacement
shown,active=true,MODULE
Event("ADDON_LOADED","EllesmereUIOptions")
assert(replacement.buildPage~=NativeBuilder and invalidations==2 and NATIVE_PAGE_REFRESHED,
    "Replacement registrations invalidate cached settings")
local selectedPage,scrolled
e.SelectPage=function(_,page) selectedPage=page end
e.ScrollToTop=function() scrolled=true end
e.ShowModule=function(_,module) active=module; shown=true end
A:OpenOptions()
assert(selectedPage=="Damage Meters" and scrolled, "Right-click and slash open embedded settings")
active,shown,selectedPage=nil,false,nil
e.ShowModule=function() end -- simulate deferred first open
A:OpenOptions()
local timer=A.optionsOpenTicker
assert(timer and not timer.cancelled)
active,shown=MODULE,true
timer.callback(timer)
assert(timer.cancelled and selectedPage=="Damage Meters" and not A.optionsOpenTicker,
    "Deferred first open selects the right page after completion")
InCombatLockdown=function() return true end
local combatAttempts=0
e.ShowModule=function() combatAttempts=combatAttempts+1 end
A:OpenOptions()
assert(combatAttempts==1 and not A.optionsOpenTicker, "Honor normal combat lock on opening settings")
InCombatLockdown=nil
local left,right=A.left,A.right
local leftRecord,rightRecord=A.records[left],A.records[right]
local leftParents,rightParents=left.frame.parentChanges,right.frame.parentChanges
A:SetActive(true)
for _,page in ipairs({"Damage Meters","Spell History","Damage Meters"}) do
    -- Normal open / module navigation / cached-page preview all set this flag
    -- and Show the existing meter frames. None should expose standalone frames.
    shown=true; active=MODULE
    NativeBuilder(page,{},0)
    A:Tick()
    assert(A.ready and A.active and left.frame:IsVisible() and right.frame:IsVisible(),
        "Opening and navigating settings keeps visible meters embedded")
    assert(A.records[left]==leftRecord and A.records[right]==rightRecord)
    shown=false; DM._optionsOpen=false
    left.UpdateVisibility(); right.UpdateVisibility(); Flush(); A:Tick()
    assert(left.frame:GetParent()==A.body and right.frame:GetParent()==A.body,
        "Closing settings does not detach or reattach meters")
end
A:SetActive(false)
shown=true; NativeBuilder("Damage Meters",{},0); A:Tick()
assert(A.ready and not left.frame:IsVisible() and not right.frame:IsVisible(),
    "Settings preview must not reveal meters while chat is selected")
shown=false; DM._optionsOpen=false; A:Tick()
assert(left.frame.parentChanges==leftParents and right.frame.parentChanges==rightParents,
    "Settings open/close/navigation never reparents the meter windows")
DM._optionsOpen=false
A:SetOption("enabled",false)
