-- Execute the entry controller and real reset helper without touching WoW.
local checks = 0
local function check(value, message) assert(value, message); checks = checks + 1 end
local frames, timers = {}, {}
local F = {}
function CreateFrame()
    local f = setmetatable({events={}, scripts={}, shown=false}, {__index=F})
    frames[#frames+1] = f
    return f
end
function F:RegisterEvent(event) self.events[event] = true end
function F:SetScript(event, callback) self.scripts[event] = callback end
function F:HookScript(event, callback)
    local old = self.scripts[event]
    self.scripts[event] = function(...) if old then old(...) end; callback(...) end
end
function F:IsShown() return self.shown end
function F:IsMouseOver() return false end
function F:EnableMouse(enabled) self.mouse=enabled end
function F:EnableMouseWheel(enabled) self.mouseWheel=enabled end
function F:EnableKeyboard(enabled) self.keyboard=enabled end
function F:SetPropagateKeyboardInput(enabled) self.propagateKeyboard=enabled end
function F:Show() self.shown=true end
function F:Hide()
    local was=self.shown; self.shown=false
    if was and self.scripts.OnHide then self.scripts.OnHide(self) end
end
local function fire(event, ...)
    for _, frame in ipairs(frames) do
        if frame.events[event] then frame.scripts.OnEvent(frame,event,...) end
    end
end
local function flush()
    local queued=timers; timers={}
    for _, callback in ipairs(queued) do callback() end
end
C_Timer = {After=function(delay, callback)
    check(delay==0, "only defer shared popup reuse to the next event turn")
    timers[#timers+1] = callback
end}
local kind, id, difficulty, combat = "none", 0, 0, false
function IsInInstance() return kind~="none",kind end
function GetInstanceInfo() return "Test Dungeon",kind,difficulty,0,0,0,0,id end
function InCombatLockdown() return combat end
local secret={}
function issecretvalue(value) return value==secret end
local shown, opts = 0, nil
local wirePopupHandlers = assert(loadstring(POPUP_HANDLERS_SOURCE))()
local applyPopupInputOptions = assert(loadstring(POPUP_INPUT_OPTIONS_SOURCE))()
EllesmereUI={L=function(text) return text end,
    PadHint=function(frame,key) check(key=="nodepass", "controller hint preserves mouse input"); frame.padHint=key end,
    RegisterEscapeClose=function(frame,opts) frame.padEscape=opts end}

function EllesmereUI:ShowConfirmPopup(options)
    if not EUIConfirmDimmer then
        EUIConfirmDimmer=CreateFrame()
        EUIConfirmPopup=CreateFrame()
        EUIConfirmPopup._dimmer=EUIConfirmDimmer
        EUIConfirmPopup:EnableMouse(true)
        wirePopupHandlers(EUIConfirmPopup,EUIConfirmDimmer)
    end
    opts=options; shown=shown+1
    applyPopupInputOptions(EUIConfirmPopup,options)
    EUIConfirmDimmer:Show()
end
local function answer(yes)
    local callback=yes and opts.onConfirm or opts.onCancel
    EUIConfirmDimmer:Hide()
    if callback then callback() end
    flush()
end
local ns = {}
local resets, refreshes, closedSources, cancelledReports = 0,0,0,0
local windows={}
for i=1,2 do
    windows[i]={curSession=1,curDMType=i,curSessionID=42,cachedSources={},_barSources={},_cachedTargets={},
        Refresh=function() refreshes=refreshes+1 end,
        CloseSource=function() closedSources=closedSources+1 end}
end
ns.Report={Cancel=function() cancelledReports=cancelledReports+1 end}
EllesmereUIDMReport=CreateFrame(); EllesmereUIDMReport:Show()
C_DamageMeter={ResetAllCombatSessions=function() resets=resets+1; fire("DAMAGE_METER_RESET") end}
local env=setmetatable({ns=ns,_windows=windows,_combatEndTime=99,_curViewFrozenDur=99},{__index=_G})
local resetHelper=assert(loadstring(RESET_HELPER_SOURCE))
setfenv(resetHelper,env); resetHelper()
assert(loadfile("EllesmereUIDamageMeters_DungeonReset.lua"))("EllesmereUIDamageMeters",ns)
local function zone(newKind,newId,newDifficulty,reload)
    kind,id,difficulty=newKind,newId,newDifficulty
    fire("PLAYER_ENTERING_WORLD",false,reload or false)
    flush()
end
zone("none",0,0)
check(shown==0 and resets==0, "outdoor entry does nothing")
zone("party",100,24)
check(shown==1 and EUIConfirmDimmer:IsShown(), "Timewalking entry opens the house confirmation")
check(opts.confirmText=="Yes" and opts.cancelText=="No", "Yes and No choices")
check(opts.message:find("You just entered an instance.",1,true), "wording covers every instance")
check(not EUIConfirmDimmer.mouse and not EUIConfirmDimmer.mouseWheel,
    "full-screen overlay must not capture world clicks, camera drags, or zoom")
check(EUIConfirmPopup.mouse, "dialog itself still accepts Yes and No clicks")
EUIConfirmDimmer.scripts.OnMouseDown(EUIConfirmDimmer)
check(EUIConfirmDimmer:IsShown() and resets==0, "outside clicks keep the prompt open without resetting")
EUIConfirmPopup.scripts.OnKeyDown(EUIConfirmPopup,"ESCAPE")
check(EUIConfirmDimmer:IsShown() and not EUIConfirmPopup.propagateKeyboard,
    "Escape cannot dismiss the modal prompt")
EUIConfirmPopup.scripts.OnKeyDown(EUIConfirmPopup,"W")
check(EUIConfirmPopup.propagateKeyboard, "movement keys still reach the game")
check(resets==0, "entering a dungeon never resets automatically")
fire("ZONE_CHANGED_NEW_AREA"); fire("PLAYER_ENTERING_WORLD",false,false)
check(shown==1, "duplicate zone events do not repeat the prompt")
answer(false)
check(resets==0 and windows[1].curSessionID==42, "No retains all data and selected segments")
fire("ZONE_CHANGED_NEW_AREA")
check(shown==1 and not EUIConfirmDimmer:IsShown(), "No persists for the visit")
zone("none",0,0); zone("party",100,24)
check(shown==2, "re-entering starts another visit")
answer(true)
check(resets==1 and refreshes==2 and closedSources==2, "Yes resets once and refreshes both meters")
check(windows[1].curSessionID==nil and windows[2]._barSources==nil, "reset clears invalid historical references")
check(windows[1].curSession==1 and windows[2].curDMType==2, "reset preserves metric and overall selection")
check(cancelledReports==1 and not EllesmereUIDMReport:IsShown(), "reset cancels old report and closes preview")
check(env._combatEndTime==0 and env._curViewFrozenDur==0, "reset clears frozen timer state")
local before=shown
zone("party",100,24,true); fire("ZONE_CHANGED_NEW_AREA")
check(shown==before, "reload inside a dungeon does not ask again")
zone("party",200,2)
local old=opts
zone("none",0,0)
check(EUIConfirmDimmer:IsShown(), "zone changes do not dismiss an unanswered prompt")
answer(false)
old.onConfirm()
check(resets==1, "stale Yes after No cannot clear data")
combat=true; zone("party",300,1)
before=shown
check(not EUIConfirmDimmer:IsShown(), "entry during combat defers the prompt")
combat=false; fire("PLAYER_REGEN_ENABLED")
check(shown==before+1 and EUIConfirmDimmer:IsShown(), "prompt appears when combat ends")
old=opts
combat=true; fire("PLAYER_REGEN_DISABLED"); flush()
check(not EUIConfirmDimmer:IsShown(), "combat starting hides the prompt")
old.onConfirm()
check(resets==1, "dismissed combat prompt cannot reset through a stale callback")
combat=false; fire("PLAYER_REGEN_ENABLED")
check(not EUIConfirmDimmer:IsShown(), "combat dismissal does not reopen the prompt")
zone("none",0,0); combat=true; zone("party",400,23)
fire("CHALLENGE_MODE_START"); combat=false; fire("PLAYER_REGEN_ENABLED")
check(not EUIConfirmDimmer:IsShown(), "keystone reset cancels a pending prompt")
zone("party",401,23); fire("CHALLENGE_MODE_START")
check(EUIConfirmDimmer:IsShown(), "keystone start leaves the user's open question in place")
answer(false)
zone("party",402,1); fire("DAMAGE_METER_RESET")
check(EUIConfirmDimmer:IsShown(), "another reset does not dismiss an open question")
answer(false)
for i, instanceKind in ipairs({"raid","pvp","arena","scenario"}) do
    before=shown
    zone(instanceKind,500+i,1)
    check(shown==before+1 and EUIConfirmDimmer:IsShown(), instanceKind.." entry prompts")
    answer(false)
end
before=shown
zone("party",0,1)
check(shown==before, "incomplete instance info does not invent a visit")
id=900; fire("ZONE_CHANGED_NEW_AREA")
check(shown==before+1, "zone event with resolved instance data prompts")
answer(false)
zone("none",0,0)
EllesmereUI:ShowConfirmPopup({onCancel=function() end})
local other=opts
zone("party",901,1)
check(opts==other, "entry never overwrites another feature's confirmation")
answer(false)
check(opts~=other and EUIConfirmDimmer:IsShown(), "entry prompt waits until existing confirmation finishes")
old=opts
-- A click racing the combat event must still preserve meter data.
combat=true; answer(true)
check(resets==1, "Yes rechecks combat at click time")
combat=false; fire("PLAYER_REGEN_ENABLED")
check(not EUIConfirmDimmer:IsShown(), "combat-raced Yes does not queue another prompt")
zone("none",0,0)
EllesmereUI:ShowConfirmPopup({onCancel=function() end})
check(EUIConfirmDimmer.mouse and EUIConfirmDimmer.mouseWheel,
    "next shared popup restores its default mouse and wheel capture")
EUIConfirmDimmer.scripts.OnMouseDown(EUIConfirmDimmer)
check(not EUIConfirmDimmer:IsShown(), "unrelated non-modal popups retain outside dismissal")
print("PASS: "..checks.." instance reset checks (Lua ".._VERSION..")")
