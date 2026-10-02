"""Execute the real visibility module: Questie ownership, recovery and hover races."""
from pathlib import Path
from itertools import product
import os
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2]
if not (root / "EllesmereUIQuestTracker").is_dir():
    root = Path(__file__).resolve().parents[1]  # public repository layout
source = (root / "EllesmereUIQuestTracker/EllesmereUIQuestTracker_Visibility.lua").read_text(encoding="utf-8-sig")
# Exercise the installed Questie native visibility contract if available. Public
# source-only checkouts use the same small contract mock, with no Questie bundle.
questie_path = root / "Questie/Modules/QuestieCompat.lua"
compat_source = None
if not questie_path.exists():
    installed = os.environ.get("EUI_QUESTIE_SOURCE_ROOT")
    if installed:
        questie_path = Path(installed) / "Modules/QuestieCompat.lua"
if questie_path.exists():
    compat = questie_path.read_text(encoding="utf-8-sig")
    compat_source = compat[compat.index("-- Forever's objective tracker can show itself"):compat.index("---Returns Blizzard's quest tracker anchor")]
for stock, startup in product((False, True), ("absent", "enabled", "disabled")):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().stock = stock
    lua.globals().startup = startup
    lua.execute(r'''
EUI_CLIENT_BLOCKED=false; combat=false; instance="none"; timers={}; frames={}
UIParent={}; cfg={enabled=true,visibility="always",forceOnScreen=true}
local methods={}
function methods:IsShown() return self.shown end
function methods:GetAlpha() return self.alpha end
function methods:SetAlpha(a) self.alpha=a end
function methods:Show()
 if self==ObjectiveTrackerFrame then
  assert(not combat,'protected Show in combat'); nativeShows=nativeShows+1
 end
 self.shown=true
 if self.scripts.OnShow then self.scripts.OnShow(self) end
end
function methods:Hide()
 if self==ObjectiveTrackerFrame then
  assert(not combat,'protected Hide in combat'); nativeHides=nativeHides+1
 end
 self.shown=false
 if self.scripts.OnHide then self.scripts.OnHide(self) end
end
function methods:HookScript(k,fn)
 local previous=self.scripts[k]
 self.scripts[k]=function(...) if previous then previous(...) end; fn(...) end
end
function methods:SetScript(k,fn) self.scripts[k]=fn end
function methods:RegisterEvent(e) self.events[e]=true end
function methods:UnregisterEvent(e) self.events[e]=nil end
function methods:UnregisterAllEvents() self.events={} end
function methods:GetFrameStrata() return 'MEDIUM' end
function methods:GetFrameLevel() return 2 end
function methods:SetFrameStrata() end
function methods:SetFrameLevel() end
function methods:GetEffectiveScale() return 1 end
function methods:GetObjectType() return 'Frame' end
function methods:IsMouseOver() return true end
function methods:GetRect() return 1,2,3,4 end
function methods:SetPoint() end
function methods:ClearAllPoints() end
function methods:SetClampedToScreen() end
function methods:SetHeight() end
function methods:SetAllPoints() end
function methods:SetColorTexture() end
function methods:Update() self:Show() end
function methods:CreateTexture() return CreateFrame('Texture') end
function CreateFrame(_,name)
 local f=setmetatable({shown=true,alpha=1,scripts={},events={}},{__index=methods})
 frames[#frames+1]=f; if name then _G[name]=f end; return f
end
nativeShows=0; nativeHides=0
ObjectiveTrackerFrame=CreateFrame('Frame')
ObjectiveTrackerFrame.modules={CreateFrame('Frame')}
function InCombatLockdown() return combat end
function GetInstanceInfo() return '',instance end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function hooksecurefunc(obj,key,fn)
 local original=obj[key]
 obj[key]=function(...) original(...); fn(...) end
end
ns={EQT={}}
local EQT=ns.EQT
EQT.DB=function() return cfg end
EQT.Cfg=function(k) return cfg[k] end
EQT.Blizz=function() return stock end
EQT.ApplyTrackerMouse=function(on) mouse=on end
EllesmereUI={
 EvalVisibility=function(c) if not c.enabled then return false end; return c.visibility end,
 RegisterVisibilityUpdater=function(fn) dispatch=fn end,
 RegisterMouseoverTarget=function(proxy,predicate) hover=proxy; hoverWanted=predicate end,
 VisWantsMouseover=function(c) return c.enabled and c.visibility=='mouseover' end,
}
tracker={Toggle=function() Questie.db.profile.trackerEnabled=not Questie.db.profile.trackerEnabled end}
local contractFrame=CreateFrame('Frame')
QuestieCompat={ShowWatchFrame=function()
 if combat then contractFrame:RegisterEvent('PLAYER_REGEN_ENABLED'); return end
 contractFrame:UnregisterAllEvents(); ObjectiveTrackerFrame:Update()
end, HideWatchFrame=function() ObjectiveTrackerFrame:Hide() end}
contractFrame:SetScript('OnEvent',function() QuestieCompat.ShowWatchFrame() end)
QuestieLoader={ImportModule=function(_,name)
 if name=='QuestieCompat' then return QuestieCompat end
 assert(name=='QuestieTracker'); return tracker
end}
function MakeQuestie(enabled)
 Questie={db={profile={trackerEnabled=enabled}},active=true,API={},IsForever=true}
 function Questie:IsEnabled() return self.active end
 function Questie:OnEnable() self.active=true end
 function Questie:OnDisable() self.active=false end
 function Questie:RefreshConfig() end
 Questie.API.RegisterOnReady=function(fn) ready=fn end
end
function Fire(event)
 for _,f in ipairs(frames) do
  if f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f,event) end
 end
end
function CheckOwned()
 assert(ObjectiveTrackerFrame.alpha==0 and mouse==false,'Questie competes or hidden tracker takes clicks')
 assert(not EQT.TrackerIsVisible(ObjectiveTrackerFrame))
 assert(not hoverWanted(),'mouseover can reveal the competing tracker')
 if EllesmereUIQTBackground then assert(not EllesmereUIQTBackground.shown,'orphan tracker background') end
end
''')
    if compat_source:
        lua.execute('isForever=true; assert(loadstring(...))()', compat_source)
    lua.execute('assert(loadstring(...))("EllesmereUIQuestTracker",ns)', source)
    lua.execute(r'''
EQT=ns.EQT
if startup~='absent' then
 MakeQuestie(startup=='enabled')
 if startup=='enabled' then QuestieCompat.HideWatchFrame() end
end
nativeShows=0; nativeHides=0
EQT.InitVisibility(); EQT.UpdateVisibility()
if startup=='enabled' then CheckOwned()
else assert(ObjectiveTrackerFrame.alpha==1 and mouse==true,'fallback tracker broken') end
if not Questie then MakeQuestie(true) else Questie.db.profile.trackerEnabled=true end
Fire('ADDON_LOADED'); CheckOwned()
assert(nativeShows==0 and nativeHides==0,'EUI changed native visibility while Questie owns it')
ready(); assert(EQT.QuestieOwnsTracker()); QuestieCompat.HideWatchFrame()
-- Native re-show, queued background work and stale mouseover calls cannot win.
ObjectiveTrackerFrame:Show(); CheckOwned()
hover:SetAlpha(1); hover:Show(); CheckOwned()
for _,fn in ipairs(timers) do fn() end; timers={}; CheckOwned()
combat=true; nativeShows=0; nativeHides=0
dispatch(); Fire('PLAYER_ENTERING_WORLD'); CheckOwned()
assert(nativeShows==0 and nativeHides==0,'protected visibility called in combat')
combat=false
tracker:Toggle()
assert(ObjectiveTrackerFrame.alpha==1 and mouse==true,'toggle did not restore EUI')
assert(ObjectiveTrackerFrame.shown,'Questie native suppression still latched after toggle')
assert(cfg.enabled and cfg.visibility=='always' and cfg.forceOnScreen,'preferences changed')
tracker:Toggle(); CheckOwned()
QuestieCompat.HideWatchFrame(); combat=true; nativeShows=0; nativeHides=0
tracker:Toggle()
assert(nativeShows==0 and nativeHides==0,'toggle restoration bypassed combat deferral')
combat=false; Fire('PLAYER_REGEN_ENABLED'); dispatch()
assert(ObjectiveTrackerFrame.shown and ObjectiveTrackerFrame.alpha==1 and mouse==true)
tracker:Toggle(); CheckOwned()
Questie:OnDisable()
assert(ObjectiveTrackerFrame.alpha==1 and mouse==true,'disabled addon still owns tracker')
Questie:OnEnable(); CheckOwned()
Questie.db.profile={trackerEnabled=false}; Questie:RefreshConfig()
assert(ObjectiveTrackerFrame.alpha==1 and mouse==true,'profile switch did not restore EUI')
cfg.enabled=false; EQT.UpdateVisibility()
assert(ObjectiveTrackerFrame.alpha==0 and mouse==false,'disabled EUI preference lost')
cfg.enabled=true; cfg.visibility='mouseover'; EQT.UpdateVisibility()
assert(hoverWanted()); hover:SetAlpha(1); hover:Show()
assert(ObjectiveTrackerFrame.alpha==1 and mouse==true,'EUI hover fallback broken')
Questie.db.profile.trackerEnabled=true; Questie:RefreshConfig(); CheckOwned()
hover:SetAlpha(1); hover:Show(); CheckOwned()
Questie.db.profile.trackerEnabled=false; Questie:RefreshConfig()
instance='raid'; cfg.hideInRaidMode='always'; Fire('ZONE_CHANGED_NEW_AREA')
assert(not ObjectiveTrackerFrame.shown,'raid auto-hide lost')
MakeQuestie(true); EQT.UpdateVisibility(); CheckOwned()
Questie.db.profile.trackerEnabled=false; instance='none'; Fire('ZONE_CHANGED_NEW_AREA')
assert(ObjectiveTrackerFrame.shown,'zone-out restoration lost')
Questie=nil; cfg.visibility='always'; EQT.UpdateVisibility()
assert(ObjectiveTrackerFrame.alpha==1 and mouse==true,'missing Questie fallback broken')
Questie={}; EQT.UpdateVisibility()
assert(not EQT.QuestieOwnsTracker(),'uninitialized Questie claimed tracker')
''')
print("Questie priority: actual Lua 5.1 visibility module, both styles, late loading/readiness, toggle/profile/addon recovery, combat, hover races, chrome and retained EUI settings passed; Questie native visibility=" + ("installed source" if compat_source else "contract mock"))
