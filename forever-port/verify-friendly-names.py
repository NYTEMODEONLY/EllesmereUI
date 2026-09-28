"""Imported friendly-name visibility and existing native/guild rendering paths."""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime
root=Path(__file__).resolve().parents[1]
source=(root.parent/'EllesmereUINameplates/EllesmereUINameplatesFriendly.lua').read_text(encoding='utf-8-sig')
native=Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['LOCALAPPDATA'])/'Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns'))
def between(text,start,end):
    a=text.index(start); return text[a:text.index(end,a)]
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
EUI_FOREVER=true; ns={pendingUnits={}}; friendlyPlates={}; timers={}; writes={}
fp={showFriendlyPlayers=true,friendlyNameOnly=true,classColorFriendly=true,friendlyBelowName='guild'}
function FP() return fp end
function InCombatLockdown() return combat end
function GetInstanceInfo() return '',instanceType or 'none' end
function IsInFollowerDungeon() return follower end
function issecretvalue(v) return type(v)=='table' and v.secret end
function opaque() return setmetatable({secret=true},{__tostring=function() error('secret string conversion') end}) end
function GetCVar(key) return cvars[key] end
function SetCVar(key,value)
 assert(not combat,'CVar changed in combat'); writes[#writes+1]={key,value}
 if reject then error('rejected CVar') end
 if not ignore then cvars[key]=tostring(value) end
end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function CreateFrame() return {RegisterEvent=function() end,SetScript=function() end} end
''')
block=between(source,'local FRIENDLY_VIS_CVARS =','--- Follower dungeons force friendly plates off')
lua.execute(block+r'''
function migrate() MigrateForeverFriendlyVisibility() end
function snapshot() CacheForeverFriendlyEvidence() end
function reset()
 _liveVisCVar=nil; writes={}; combat=false; follower=false; instanceType='none'
 reject=false; ignore=false; EUI_FOREVER=true
 EllesmereUIDB={friendlyPlateVisSeeded=true}
 fp.showFriendlyPlayers=true
 cvars={nameplateShowFriendlyPlayers='0',nameplateShowOnlyNameForFriendlyPlayerUnits='1',nameplateUseClassColorForFriendlyPlayerUnitNames='1'}
end
''')
lua.execute(r'''
reset(); migrate()
assert(#writes==1 and writes[1][1]=='nameplateShowFriendlyPlayers' and writes[1][2]==1)
assert(EllesmereUIDB.friendlyPlateVisSeeded and EllesmereUIDB._foreverFriendlyVisibilityMigrated)
-- Preserve subsequent deliberate user visibility choices, including relog.
cvars.nameplateShowFriendlyPlayers='0'; migrate(); assert(#writes==1 and cvars.nameplateShowFriendlyPlayers=='0')
reset(); cvars.nameplateShowFriendlyPlayers='1'; migrate(); assert(#writes==0 and EllesmereUIDB._foreverFriendlyVisibilityMigrated)
reset(); combat=true; migrate(); assert(#writes==0 and not EllesmereUIDB._foreverFriendlyVisibilityMigrated)
combat=false; migrate(); assert(#writes==1)
for _,kind in ipairs({'party','raid','scenario','arena','pvp'}) do
 reset(); instanceType=kind; migrate(); assert(#writes==0 and not EllesmereUIDB._foreverFriendlyVisibilityMigrated)
 instanceType='none'; migrate(); assert(#writes==1)
end
reset(); follower=true; migrate(); assert(#writes==0)
reset(); fp.showFriendlyPlayers=false; migrate(); assert(#writes==0)
reset(); EUI_FOREVER=false; migrate(); assert(#writes==0)
reset(); reject=true; migrate(); assert(not EllesmereUIDB._foreverFriendlyVisibilityMigrated)
reset(); ignore=true; migrate(); assert(not EllesmereUIDB._foreverFriendlyVisibilityMigrated)
reset(); cvars={}; migrate(); assert(#writes==0 and not EllesmereUIDB._foreverFriendlyVisibilityMigrated)
reset(); cvars.nameplateShowFriendlyPlayers=nil; cvars.nameplateShowFriends='0'; migrate()
assert(#writes==1 and writes[1][1]=='nameplateShowFriends')
reset(); cvars.nameplateShowFriendlyPlayers=opaque(); migrate(); assert(#writes==0)
reset(); migrate()
ns.pendingUnits={a={UnitFrame={IsForbidden=function() return false end,name={}}},
 b={UnitFrame=setmetatable({IsForbidden=function() return true end},{__index=function() error('forbidden frame read') end})}}
friendlyPlates={one={}}
snapshot(); local lines={}; GetGuildInfo=function() error('diagnostic identity read') end
UnitName=GetGuildInfo; ns.ForeverFriendlyEvidence(lines)
assert(#lines==8 and lines[8]=='Friendly frames: tracked=2 accessibleNames=1 custom=1')
assert(lines[2]=='Friendly CVar nameplateShowFriendlyPlayers=1')
cvars.nameplateShowFriendlyPlayers='0'; lines={}; ns.ForeverFriendlyEvidence(lines)
assert(lines[2]=='Friendly CVar nameplateShowFriendlyPlayers=1','report did not use snapshot')
snapshot(); lines={}; ns.ForeverFriendlyEvidence(lines); assert(lines[2]=='Friendly CVar nameplateShowFriendlyPlayers=0')
''')
# Camelot's shared native nameplate methods support these exact presentation CVars.
native_source=(native/'Blizzard_NamePlates/Blizzard_NamePlateUnitFrame.lua').read_text(encoding='utf-8-sig')
constants=(native/'Blizzard_NamePlates/Camelot/Blizzard_NamePlateConstants.lua').read_text(encoding='utf-8-sig')
assert('nameplateShowOnlyNameForFriendlyPlayerUnits' in constants and 'nameplateUseClassColorForFriendlyPlayerUnitNames' in constants)
lua.execute(r'''
NamePlateUnitFrameMixin={}; NamePlateConstants={SHOW_ONLY_NAME_FOR_FRIENDLY_PLAYER_UNITS_CVAR='nameplateShowOnlyNameForFriendlyPlayerUnits',USE_CLASS_COLOR_FOR_FRIENDLY_PLAYER_UNIT_NAMES_CVAR='nameplateUseClassColorForFriendlyPlayerUnitNames'}
CVarCallbackRegistry={GetCVarValueBool=function(_,key) return cvars[key]=='1' end}
function CompactUnitFrame_UpdateName(self) self.nativeNameRefreshed=true end
function CompactUnitFrame_UpdatePlayerLevelDiff() end
local function widget() return {SetShowOnlyName=function(self,v) self.onlyName=v end} end
uf={IsFriend=function() return true end,IsPlayer=function() return true end,HealthBarsContainer={healthBar=widget()},CastBarsContainer={castBar=widget()},
 AurasFrame=widget(),ClassificationFrame=widget(),RaidTargetFrame=widget(),UpdateAnchors=function() end,UpdateHitTestArea=function() end}
''')
lua.execute(between(native_source,'function NamePlateUnitFrameMixin:UpdateShowOnlyName()','function NamePlateUnitFrameMixin:UpdateHitTestArea('))
lua.execute(between(native_source,'function NamePlateUnitFrameMixin:UpdateNameClassColor()','function NamePlateUnitFrameMixin:UpdateNameRealmDisplay('))
lua.execute(r'''
reset(); migrate(); NamePlateUnitFrameMixin.UpdateShowOnlyName(uf); NamePlateUnitFrameMixin.UpdateNameClassColor(uf)
assert(uf.showOnlyName and uf.colorNameWithClassColor and uf.nativeNameRefreshed)
assert(uf.HealthBarsContainer.healthBar.onlyName and uf.RaidTargetFrame.onlyName)
''')
# Execute existing EUI composition and the driver posthook. No replacement
# nameplate/world-name implementation is needed; native coloring owns name color.
lua.execute(r'''
EllesmereUI={WithSurname=function(n) return n end}
nameFSUnits={}; nameFSText={}; hookedNameText={}; _titledNameGuard=false
function GetBelowNameMode() return fp.friendlyBelowName end
function ModeHasTitle(mode) return mode=='title' or mode=='both' end
function ModeHasGuild(mode) return mode=='guild' or mode=='both' end
function GetTitledName() return 'Title NativeName' end
function UnitName() return 'NativeName' end
function GetGuildInfo() return guild end
function UnitExists() return true end
function UnitIsPlayer() return true end
function UnitCanAttack() return hostile end
function UnitIsUnit() return false end
function EnsureNameUnconstrained() end
function GetSubTextColor() return .8,.8,.8 end
function hooksecurefunc(obj,key,fn)
 local original=obj[key]; obj[key]=function(...) if original then original(...) end; fn(...) end
end
nameFS={SetWordWrap=function(self,v) self.wrap=v end,SetMaxLines=function(self,v) self.maxLines=v end,
 SetFormattedText=function(self,fmt,...) self.text=string.format(fmt,...) end,SetText=function(self,v) self.text=v end}
''')
lua.execute(between(source,'local function ForeverFriendlyUnitAccessible(unit)','-- Sweep all visible friendly player plates')+'\n_G.AttachNameOnlyText=AttachNameOnlyText; _G.ForeverFriendlyUnitAccessible=ForeverFriendlyUnitAccessible')
lua.execute(r'''
function IsFriendlyEnabled() return false end
function IsNameOnlyMode() return true end
function IsFriendlyNPCEnabled() return false end
function IsInInstance() return false end
function ScheduleNameSizeReapply() end
NamePlateDriverFrame={OnNamePlateAdded=function() end}
uf.name=nameFS; uf.IsForbidden=function() return false end
uf.UnregisterAllEvents=function() error('Camelot native events erased') end
uf.RegisterEvent=uf.UnregisterAllEvents; uf.RegisterUnitEvent=uf.UnregisterAllEvents
C_NamePlate={GetNamePlateForUnit=function() return {UnitFrame=uf} end}
''')
lua.execute(between(source,'hooksecurefunc(NamePlateDriverFrame, "OnNamePlateAdded",','hooksecurefunc(NamePlateDriverFrame, "OnNamePlateRemoved",'))
lua.execute(r'''
guild='NativeGuild'; NamePlateDriverFrame:OnNamePlateAdded('nameplate1')
assert(nameFS.text=='NativeName\n|cffcccccc<NativeGuild>|r' and nameFS.wrap and nameFS.maxLines==2)
guild=nil; nameFS:SetText('NativeName'); assert(nameFS.text=='NativeName' and nameFS.maxLines==1)
guild='ChangedGuild'; nameFS:SetText('NativeName'); assert(nameFS.text:find('ChangedGuild',1,true))
hostile=true; nameFS:SetText('NativeEnemyName'); assert(nameFS.text=='NativeEnemyName','recycled hostile plate recomposed')
hostile=false; uf.IsForbidden=function() return true end
nameFS.text='native restricted name'; NamePlateDriverFrame:OnNamePlateAdded('nameplate1')
assert(nameFS.text=='native restricted name','forbidden plate modified')
uf.IsForbidden=function() return false end
local oldIsPlayer=UnitIsPlayer; UnitIsPlayer=function() return opaque() end
NamePlateDriverFrame:OnNamePlateAdded('nameplate1'); assert(nameFS.text=='native restricted name')
UnitIsPlayer=oldIsPlayer
nameFS.IsForbidden=function() return true end; AttachNameOnlyText(nameFS,'nameplate1')
assert(nameFS.text=='native restricted name')
''')
print('PASS friendly names: one-time client CVar migration/readback, later user toggles, combat/instance/restriction guards, cached anonymous evidence, native name-only/class-color paths, guild composition, recycled hostile plates, preserved Camelot events')
