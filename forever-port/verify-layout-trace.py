"""Read-only layout trace regression tests using the actual Lua 5.1 module.

Mock time/frame APIs exercise synchronous and deferred evidence capture. This
does not simulate WoW's protected execution or perform any game interaction.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EllesmereUI_ForeverDiagnostics.lua"
code = SOURCE.read_text(encoding="utf-8")
assert "EllesmereUI_ForeverDiagnostics.lua" in (ROOT / "EllesmereUI.toc").read_text(encoding="utf-8")
fixture = r'''
EUI_FOREVER=true
EUI_FOREVER_VERSION="test"
EUI_FOREVER_STATUS={}
local clock=0
local timers={}
local events
local nativeCall=false
local hookCount=0
local stackCount=0
local printed={}
local db={_foreverLastLayoutTrace="previous-session"}
local snapshots={}
EllesmereUIDB=setmetatable({}, {
    __index=db,
    __newindex=function(_,key,value)
        if key=="_foreverLastLayoutTrace" then
            assert(currentEvent=="PLAYER_LOGOUT","trace snapshot saved outside logout")
            snapshots[#snapshots+1]=value
        else assert(key=="_foreverTraceDisabled","unexpected saved-variable mutation") end
        db[key]=value
    end,
})
function GetTime() return clock end
function issecretvalue(value) return type(value)=="table" and value.secret==true end
function debugstack(skip,lines,locals)
    assert(skip==3 and lines==5 and locals==0,"trace requested locals or excessive stack")
    stackCount=stackCount+1; return "native-layout.lua:25\nUI-layout.lua:40"
end
function print(message) printed[#printed+1]=message end
local function forbidden() error("diagnostics invoked gameplay/input/data or a native setter") end
for _,name in ipairs({"UnitName","UnitGUID","UnitHealth","UnitExists","GetUnitName","SendChatMessage","TargetUnit","SetCVar","GetCVar","GetCVarBool","UnitClass","UnitRace"}) do _G[name]=forbidden end
C_ChatInfo=setmetatable({}, {__index=forbidden})
C_Timer={After=function(delay,callback) timers[#timers+1]={due=clock+delay,callback=callback} end}
local function advance(delta)
    clock=clock+delta
    local again=true
    while again do
        again=false
        for i,timer in ipairs(timers) do
            if timer.due<=clock then table.remove(timers,i); timer.callback(); again=true; break end
        end
    end
end
local function frame(name)
    local f={name=name,x=0,y=0,width=100,height=40,scale=1,shown=true,points=1,scripts={},hooks={},nativeCalls=0}
    f.nativeOnShow=function() f.nativeShows=(f.nativeShows or 0)+1 end
    f.scripts.OnShow=f.nativeOnShow
    function f:GetName() if self.throwName then error("getter failure contains no player data") end; return self.name end
    function f:GetPoint() if self.throwPoint then error("point getter failure") end; return "CENTER",self.relative,"CENTER",self.x,self.y end
    function f:GetParent() return self.parent end
    function f:IsShown() return self.shown end
    function f:GetWidth() return self.width end
    function f:GetHeight() return self.height end
    function f:GetScale() return self.scale end
    function f:GetAlpha() return self.alpha or 1 end
    function f:HookScript(event,fn)
        self.hooks[event]=self.hooks[event] or {}; table.insert(self.hooks[event],fn)
    end
    for _,method in ipairs({"SetPoint","SetPointBase"}) do
        f[method]=function(self,x,y) assert(nativeCall,"trace called native position setter"); self.nativeCalls=self.nativeCalls+1; self.x,self.y=x,y end
    end
    function f:SetSize(w,h) assert(nativeCall,"trace called native size setter"); self.nativeCalls=self.nativeCalls+1; self.width,self.height=w,h end
    function f:SetWidth(w) assert(nativeCall); self.width=w end
    function f:SetHeight(h) assert(nativeCall); self.height=h end
    function f:SetScale(scale) assert(nativeCall,"trace called native scale setter"); self.nativeCalls=self.nativeCalls+1; self.scale=scale end
    f.SetScaleBase=f.SetScale
    function f:SetAlpha(alpha) assert(nativeCall,"trace called native alpha setter"); self.alpha=alpha end
    for _,method in ipairs({"Show","Hide","SetShown","SetParent","ClearAllPoints","SetFrameLevel","SetScript","SetAttribute","RegisterForClicks"}) do f[method]=forbidden end
    return f
end
local function native(frame,method,...)
    nativeCall=true; frame[method](frame,...); nativeCall=false
end
local function visibility(frame,shown)
    frame.shown=shown
    local event=shown and "OnShow" or "OnHide"
    if frame.scripts[event] then frame.scripts[event]() end
    for _,hook in ipairs(frame.hooks[event] or {}) do hook(frame) end
end
function hooksecurefunc(object,method,callback)
    if type(object)=="string" then callback=method; method=object; object=_G end
    local original=object[method]; assert(type(original)=="function")
    object[method]=function(...)
        original(...)
        local wasNative=nativeCall; nativeCall=false
        callback(...)
        nativeCall=wasNative
    end
    hookCount=hookCount+1
end
function CreateFrame()
    assert(not events,"diagnostics unexpectedly created another frame")
    events={registered={}}
    function events:RegisterEvent(event) self.registered[event]=true end
    function events:SetScript(event,callback) assert(event=="OnEvent"); self.callback=callback end
    return events
end
local function event(name)
    assert(events.registered[name],"unexpected event fixture")
    currentEvent=name; events.callback(events,name); currentEvent=nil
end
UIParent=frame("UIParent")
ObjectiveTrackerFrame=frame("ObjectiveTrackerFrame"); ObjectiveTrackerFrame.parent=UIParent; ObjectiveTrackerFrame.relative=UIParent
local tracker=ObjectiveTrackerFrame
local managerNative=0
function ManageFramePositions() assert(nativeCall); managerNative=managerNative+1 end
function HideUIPanel() assert(nativeCall); managerNative=managerNative+1 end
function CloseAllWindows() assert(nativeCall); managerNative=managerNative+1 end
EditModeManagerFrame={UpdateBottomActionBarPositions=function() assert(nativeCall); managerNative=managerNative+1 end,UpdateRightActionBarPositions=function() assert(nativeCall); managerNative=managerNative+1 end}
local function report() return EUI_FOREVER_STATUS.LayoutTraceReport() end
local function records()
    local rows={}
    for row in report():gmatch("[^\n]+") do if row:sub(1,1)=="+" then rows[#rows+1]=row end end
    return rows
end
local function geometryCount()
    local n=0; for _,row in ipairs(records()) do if row:find("parent=",1,true) then n=n+1 end end; return n
end
function verify()
    assert(report():find("stopped",1,true)); assert(#snapshots==0)
    event("PLAYER_LOGIN")
    assert(report():find("recording",1,true) and report():find("initial | ObjectiveTrackerFrame",1,true))
    assert(tracker.scripts.OnShow==tracker.nativeOnShow and tracker.nativeCalls==0)
    local initial=geometryCount()
    native(tracker,"SetPoint",0,0); advance(0); advance(.1)
    assert(geometryCount()==initial,"unchanged geometry was recorded twice")
    -- Both fleeting positions must be recorded synchronously, even though the
    -- next-frame sample sees the original anchor again.
    native(tracker,"SetPoint",25,5); native(tracker,"SetPoint",0,0)
    local snapshot=report()
    assert(snapshot:find("offset=25.000,5.000",1,true))
    assert(geometryCount()==initial+2,"transient move-and-restore was lost")
    tracker.x=30; advance(0)
    assert(report():find("layout:next-frame | ObjectiveTrackerFrame",1,true))
    tracker.x=35; advance(.1)
    assert(report():find("layout:settled | ObjectiveTrackerFrame",1,true))
    assert(tracker.nativeCalls==3 and #snapshots==0)
    local before=geometryCount(); visibility(tracker,false); visibility(tracker,true)
    assert(geometryCount()==before+2 and tracker.nativeShows==1 and tracker.scripts.OnShow==tracker.nativeOnShow)
    -- An addon arriving later gets a baseline and hooks without asking the
    -- native window to relayout, open, or expose any gameplay data.
    BagsBar=frame("BagsBar"); BagsBar.x=42; event("ADDON_LOADED")
    assert(report():find("ADDON_LOADED | BagsBar",1,true) and BagsBar.nativeCalls==0)
    local previousHooks=hookCount; event("ADDON_LOADED"); assert(hookCount==previousHooks,"duplicate hooks installed")
    native(BagsBar,"SetPoint",43,0); assert(report():find("offset=43.000,0.000",1,true))
    local protected={secret=true}
    BagsBar.width,BagsBar.relative,BagsBar.parent=protected,protected,protected
    native(BagsBar,"SetPoint",protected,protected)
    assert(report():find("offset=<protected>,<protected>",1,true) and report():find("size=<protected>x40.000",1,true))
    assert(report():find("parent=<protected>",1,true))
    BagsBar.throwPoint=true; native(BagsBar,"SetSize",105,40)
    assert(report():find("BagsBar geometry unavailable",1,true))
    local failures=#records(); native(BagsBar,"SetSize",106,40); assert(#records()==failures,"identical getter failure spammed trace")
    BagsBar.throwPoint=false; BagsBar.parent=UIParent; BagsBar.relative=UIParent; BagsBar.x=0; BagsBar.y=0
    UIParent.throwName=true; native(BagsBar,"SetSize",107,40)
    UIParent.throwName=false; native(BagsBar,"SetSize",108,40)
    assert(report():find("size=108.000x40.000",1,true),"trace did not recover after throwing getter")
    -- Target-change records an event and geometric deltas, never target queries.
    event("PLAYER_TARGET_CHANGED")
    event("ACTIONBAR_SLOT_CHANGED"); event("ACTIONBAR_SHOWGRID"); event("ACTIONBAR_HIDEGRID")
    native(tracker,"SetAlpha",0.5)
    assert(report():find("ACTIONBAR_SLOT_CHANGED",1,true) and report():find("ACTIONBAR_SHOWGRID",1,true) and report():find("ACTIONBAR_HIDEGRID",1,true))
    assert(report():find("alpha=0.500",1,true),"native alpha flicker was not captured")
    native(tracker,"SetAlpha",1)
    nativeCall=true; ManageFramePositions(); EditModeManagerFrame:UpdateBottomActionBarPositions(); nativeCall=false
    assert(managerNative==2 and report():find("ManageFramePositions",1,true))
    -- Restart while an older zero-delay pass is still pending. New samples
    -- must survive the old generation being invalidated.
    EUI_FOREVER_STATUS.LayoutTraceCommand("on")
    native(tracker,"SetPoint",51,0)
    EUI_FOREVER_STATUS.LayoutTraceCommand("on")
    native(tracker,"SetPoint",52,0); tracker.x=53; advance(0)
    assert(report():find("layout:next-frame | ObjectiveTrackerFrame",1,true) and report():find("offset=53.000",1,true))
    tracker.x=54; advance(.1); assert(report():find("layout:settled | ObjectiveTrackerFrame",1,true))
    EUI_FOREVER_STATUS.LayoutTraceCommand("on")
    local stacksBefore=stackCount
    for i=1,270 do clock=clock+.001; native(tracker,"SetPoint",i,0) end
    local rows=records()
    assert(#rows==240 and report():find("max=240",1,true),"ring is not bounded to 240 records")
    assert(rows[1]:find("offset=31.000,0.000",1,true) and rows[240]:find("offset=270.000,0.000",1,true),"ring order/latest evidence incorrect")
    assert(stackCount-stacksBefore==20,"stack capture wasn't bounded to 20")
    assert(report():find("overwritten=34",1,true),"overwrite counter incorrect")
    local total=#records(); clock=clock+181; native(tracker,"SetPoint",999,0)
    assert(#records()==total and report():find("stopped",1,true),"trace didn't expire after three minutes")
    EUI_FOREVER_STATUS.LayoutTraceCommand("status"); assert(printed[#printed]:find("stopped",1,true) and not printed[#printed]:find("\n",1,true))
    EUI_FOREVER_STATUS.LayoutTraceCommand("on"); EUI_FOREVER_STATUS.LayoutTraceCommand("off")
    assert(db._foreverTraceDisabled==true)
    local stopped=report(); native(tracker,"SetPoint",1000,0); advance(.2); assert(report()==stopped)
    assert(db._foreverLastLayoutTrace=="previous-session" and #snapshots==0)
    event("PLAYER_LOGOUT"); assert(#snapshots==1 and db._foreverLastLayoutTrace==report())
    EUI_FOREVER_STATUS.LayoutTraceCommand("on"); assert(db._foreverTraceDisabled==nil and report():find("recording",1,true))
end
function prepareDisabled() db._foreverTraceDisabled=true end
function verifyDisabled()
    event("PLAYER_LOGIN"); assert(report():find("stopped",1,true) and hookCount==0 and #records()==0)
    EUI_FOREVER_STATUS.LayoutTraceCommand("on"); assert(report():find("recording",1,true) and hookCount>0 and db._foreverTraceDisabled==nil)
end
function verifyParty()
    PartyFrame=frame("PartyFrame")
    CompactRaidFrameContainer=frame("CompactRaidFrameContainer")
    function CompactPartyFrame_Generate()
        assert(nativeCall)
        CompactPartyFrame=frame("CompactPartyFrame")
        for i=1,5 do _G["CompactPartyFrameMember"..i]=frame("CompactPartyFrameMember"..i) end
    end
    event("PLAYER_LOGIN")
    assert(report():find("initial | PartyFrame",1,true))
    nativeCall=true; CompactPartyFrame_Generate(); nativeCall=false
    assert(report():find("party-created | CompactPartyFrameMember5",1,true))
    local member=CompactPartyFrameMember2
    native(member,"SetPoint",30,40)
    native(member,"SetWidth",125); native(member,"SetHeight",60)
    native(member,"SetAlpha",.25); visibility(member,false); visibility(member,true)
    local text=report()
    for _,method in ipairs({"SetPoint","SetWidth","SetHeight","SetAlpha","OnHide","OnShow"}) do
        assert(text:find(method.." | CompactPartyFrameMember2",1,true),"party change missing: "..method)
    end
    assert(text:find("size=125.000x60.000",1,true) and text:find("alpha=0.250",1,true))
    local hooks=hookCount; event("GROUP_ROSTER_UPDATE"); assert(hookCount==hooks)
    assert(member.nativeCalls==1 and #snapshots==0)
end
function verifyProtectedStack()
    event("PLAYER_LOGIN")
    local protected=setmetatable({secret=true},{__index=function() error("secret stack indexed") end,
        __tostring=function() error("secret stack converted") end})
    function debugstack() return protected end
    native(tracker,"SetPoint",111,0)
    assert(report():find("caller: <protected>",1,true))
    function debugstack() error("stack getter failure") end
    native(tracker,"SetPoint",112,0)
    assert(report():find("caller: <stack unavailable>",1,true))
    function debugstack() return "ordinary-stack" end
    native(tracker,"SetPoint",113,0)
    assert(report():find("offset=113.000,0.000",1,true) and report():find("caller: ordinary-stack",1,true))
end
function verifyProgression()
    local container=frame(nil)
    local xp=frame(nil); xp.StatusBar=frame(nil)
    container.bars={[4]=xp}
    StatusTrackingBarInfo={BarsEnum={Experience=4}}
    StatusTrackingBarManager=frame("StatusTrackingBarManager")
    StatusTrackingBarManager.barContainers={container}
    -- No XP or health values should be read by the geometry observer.
    UnitXP=forbidden; UnitXPMax=forbidden; GetXPExhaustion=forbidden
    event("PLAYER_LOGIN")
    assert(report():find("initial | Progression1.Container",1,true))
    assert(report():find("initial | Progression1.XPFill",1,true))
    native(container,"SetPoint",50,20)
    native(xp.StatusBar,"SetSize",398,18)
    native(container,"SetAlpha",.4); visibility(xp,false); visibility(xp,true)
    event("PLAYER_XP_UPDATE"); event("UPDATE_EXHAUSTION")
    local text=report()
    assert(text:find("SetPoint | Progression1.Container",1,true))
    assert(text:find("SetSize | Progression1.XPFill",1,true))
    assert(text:find("SetAlpha | Progression1.Container",1,true))
    assert(text:find("OnHide | Progression1.XP",1,true) and text:find("OnShow | Progression1.XP",1,true))
    assert(text:find("PLAYER_XP_UPDATE",1,true) and text:find("UPDATE_EXHAUSTION",1,true))
end
'''
lua = LuaRuntime()
lua.execute(fixture)
lua.execute(code)
lua.eval("verify")()
disabled = LuaRuntime()
disabled.execute(fixture)
disabled.eval("prepareDisabled")()
disabled.execute(code)
disabled.eval("verifyDisabled")()
party = LuaRuntime()
party.execute(fixture)
party.execute(code)
party.eval("verifyParty")()
protected = LuaRuntime()
protected.execute(fixture)
protected.execute(code)
protected.eval("verifyProtectedStack")()
progression = LuaRuntime()
progression.execute(fixture)
progression.execute(code)
progression.eval("verifyProgression")()
print("PASS: layout trace ring/expiry, transient and settled geometry, restart generations, late frames, protected/throwing getters, native handlers, persisted opt-out and logout-only snapshots")
print("PASS: late-created party frames, roster discovery, movement, width/height, opacity and visibility tracing without native writes")
print("PASS: protected and throwing stack getters are redacted and tracing continues")
print("PASS: anonymous XP container/bar/fill tracing and XP event correlation without reading gameplay values")
