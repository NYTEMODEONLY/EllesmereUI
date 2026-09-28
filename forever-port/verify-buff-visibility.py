"""Exercise the real Refresh path through collection and icon dispatch.

Reproduces missing reminders in a rested city despite Where to Show: All.
No saved data, game input, or claims about live rendered pixels.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT=Path(__file__).resolve().parents[2]
main=(ROOT/'EllesmereUIAuraBuffReminders/EllesmereUIAuraBuffReminders.lua').read_text(encoding='utf-8-sig')
detector=(ROOT/'EllesmereUIAuraBuffReminders/EllesmereUIABR_Forever.lua').read_text(encoding='utf-8-sig')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
ns={}; EllesmereUI={IS_FOREVER=true,SetElementVisibility=function(f,v) f.visible=v end}
EABR={FOREVER=true}; rested=true; dead=false; vehicle=false; euiPanelOpen=false
iconAnchor={}; auras={}; displayed={}; clock=100; unitClass='PALADIN'; eventFrames={}
function GetTime() return clock end
function IsResting() return rested end
function UnitIsDeadOrGhost() return dead end
function UnitInVehicle() return vehicle end
function IsMounted() return false end
function IsFlying() return false end
function InCombatLockdown() return false end
function InCombat() return false end
function GetPlayerClass() return unitClass end
function UnitClass() return unitClass,unitClass end
function UnitGroupRolesAssigned() return 'NONE' end
function IsInGroup() return false end
function GetSpecID() return 1 end
function InRealInstancedContent() return false end
function InMythicPlusKey() return false end
function InPvPInstance() return false end
function CacheInstanceInfo() end
function BuildPlayerAuraCache() end
function GetNumShapeshiftForms() return 1 end
function GetShapeshiftFormInfo() return 465,false,true,465 end
function HideAllIcons() displayed={};iconAnchor.visible=false end
function HideCombatIcons() end
function HideCursorIcons() end
function LayoutIcons() end
function ShowIcon(_,entry) displayed[entry.dismissKey]=entry end
function AcquireEntry() return {} end
function ResetEntryPool() end
function Tex(id) return id end
function wipe(t) for k in pairs(t) do t[k]=nil end end
function CreateFrame()
 local f={events={}};eventFrames[#eventFrames+1]=f
 function f:RegisterEvent(e) self.events[e]=true end
 function f:UnregisterEvent(e) self.events[e]=nil end
 function f:RegisterUnitEvent(e,u) self.events[e]=u end
 function f:SetScript(_,fn) self.callback=fn end
 return f
end
EABR.HandleAppearSounds=function() end
EABR.SyncProviderCastSpell=function() end
EABR.ParkProviderCastButton=function() end
function EABR.SectionShows(where,instance)
 return not (where and not instance and where.open_world==false)
end
_refreshMissing={};_dismissedUntilLoad={}
Enum={SpellBookSpellBank={Player=0}}
C_Spell={GetSpellInfo=function(id) return {name='Spell '..id} end}
C_SpellBook={IsSpellKnown=function(id) return id==25780 or id==465 or id==21084 or id==19742 end}
C_Secrets={ShouldAurasBeSecret=function() return false end,ShouldSpellAuraBeSecret=function() return false end}
C_UnitAuras={GetAuraDataByIndex=function(_,i) return auras[i] end}
C_Timer={NewTimer=function(_,fn) return {Cancel=function() end} end}
db={profile={display={remindersEnabled=true},forever={camp=false,customIDs={},tankMode='on',aura='any',seal='any',blessing='wisdom',
 groupBlessing='kings',food=false,flask='off',weapon=false}}}
''')
lua.execute(detector,'EllesmereUIAuraBuffReminders',lua.globals().ns)
lua.execute('EABR.ForeverSupport=ns.ForeverReminders')
adapter=main[main.index('function EABR.CollectForever('):main.index('\nlocal function Refresh()',main.index('function EABR.CollectForever('))]
lua.execute(adapter)
refresh=main[main.index('local function Refresh()'):main.index('\nlocal REFRESH_THROTTLE_COMBAT')]
lua.execute(refresh.replace('local function Refresh()','function TestedRefresh()',1))
lua.execute(r'''
TestedRefresh();assert(not next(displayed), 'Existing quiet-city default changed')
db.profile.forever.showRested=true;TestedRefresh()
assert(displayed['forever:rf'], 'RF suppressed despite explicitly allowing rested areas')
assert(displayed['forever:aura'] and not displayed['forever:seal'] and displayed['forever:blessing'])
assert(iconAnchor.visible)
db.profile.forever.showRested=false;TestedRefresh();assert(not next(displayed))
rested=false;TestedRefresh();assert(displayed['forever:rf'])
rested=true;db.profile.forever.showRested=true;TestedRefresh();assert(displayed['forever:rf'])
db.profile.forever.whereToShow={open_world=false};TestedRefresh();assert(not next(displayed))
db.profile.forever.whereToShow={};db.profile.forever.paladinWhere={open_world=false}
TestedRefresh();assert(not next(displayed))
db.profile.forever.paladinWhere={}
db.profile.display.remindersEnabled=false;TestedRefresh();assert(not next(displayed))
db.profile.display.remindersEnabled=true;euiPanelOpen=true;TestedRefresh();assert(not next(displayed))
euiPanelOpen=false;TestedRefresh();assert(displayed['forever:rf'])
dead=true;TestedRefresh();assert(not next(displayed));dead=false
vehicle=true;TestedRefresh();assert(not next(displayed));vehicle=false
EABR.FOREVER=false;TestedRefresh();assert(not next(displayed)) -- Retail suppression unchanged
EABR.FOREVER=true
auras={{spellId=25780,name='Spell 25780',duration=0,expirationTime=0}}
TestedRefresh();assert(not displayed['forever:rf'] and displayed['forever:blessing'])
auras={};refreshes=0;EABR.ForeverSupport.Init(function() refreshes=refreshes+1;TestedRefresh() end)
assert(EABR.ForeverSupport.events.events.PLAYER_UPDATE_RESTING)
EABR.ForeverSupport.events.callback(nil,'PLAYER_UPDATE_RESTING')
assert(refreshes==1 and displayed['forever:rf'])
assert(db.profile.forever.blessing=='wisdom' and db.profile.forever.groupBlessing=='kings')
''')
print('PASS: real Refresh -> Forever collector -> icon dispatch in rested cities; opt-out, global/section location, master, panel, death, vehicle, Retail, aura updates and resting event')
