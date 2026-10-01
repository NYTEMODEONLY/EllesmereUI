"""Forever buff detector regressions. No game input or SavedVariables execution.

Runs the entire new detector, not copied implementations. Main-chunk integration
and options callbacks are checked separately below. Does not certify live combat.
"""
from pathlib import Path
import re
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT/'EllesmereUIAuraBuffReminders/EllesmereUIABR_Forever.lua').read_text(encoding='utf-8-sig')
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
clock=100; combat=false; locked=false; knownIDs={[25780]=true,[465]=true,[21084]=true,[19740]=true,[19838]=true}
auras={player={}}; forms={}; enchants={}; itemCounts={}; unitNames={}; visible={}; frames={}; timers={}
spellNames={[25780]='Righteous Fury',[465]='Devotion Aura',[21084]='Seal of Righteousness',
 [19740]='Blessing of Might',[19838]='Blessing of Might',[25782]='Greater Blessing of Might',
 [19705]='Well Fed',[19706]='Well Fed',[17626]='Flask of the Titans',[433]='Food'}
class='PALADIN'; role='NONE'; members=0; raid=false; weaponID=123; queryErrors={}; blockedSpells={}; queryCount=0
SECRET=setmetatable({secret=true},{__index=function() error('read protected field') end})
function issecretvalue(v) return type(v)=='table' and rawget(v,'secret')==true end
function GetTime() return clock end
function InCombatLockdown() return combat end
function UnitClass() return class,class end
function UnitGroupRolesAssigned() return role end
function IsInGroup() return members>0 end
function IsInRaid() return raid end
function GetNumGroupMembers() return members end
function GetNumSubgroupMembers() return members end
function UnitExists(u) return unitNames[u] ~= nil end
function UnitIsConnected(u) return unitNames[u] ~= 'offline' end
function UnitIsDeadOrGhost(u) return unitNames[u] == 'dead' end
function UnitIsVisible(u) return visible[u] ~= false end
function UnitIsUnit(a,b) return a==b end
function UnitName(u) return unitNames[u] end
function GetInventoryItemID() return weaponID end
function GetInventoryItemTexture() return 99 end
function GetNumShapeshiftForms() return #forms end
function GetShapeshiftFormInfo(i) return 99,forms[i].active,true,forms[i].id end
Enum={SpellBookSpellBank={Player=0},WeaponSlot={MainHand=0},ItemEnchantType={Permanent=1,Temporary=2,Imbue=3}}
C_Spell={GetSpellInfo=function(id) return {name=spellNames[id] or ('Spell '..id)} end}
C_SpellBook={IsSpellKnown=function(id) return knownIDs[id] or false end}
C_Secrets={ShouldAurasBeSecret=function() return locked end,
 ShouldSpellAuraBeSecret=function(id) return blockedSpells[id] or false end}
C_UnitAuras={
 GetAuraDataByIndex=function(u,i) queryCount=queryCount+1; if locked then error('locked scan') end; return (auras[u] or {})[i] end,
 GetPlayerAuraBySpellID=function(id)
   if queryErrors[id] then error('restricted lookup') end
   if blockedSpells[id] then error('forbidden lookup must not happen') end
   for _,a in ipairs(auras.player) do if a.spellId==id then return a end end
 end,
 GetUnitAuraBySpellID=function(u,id)
   for _,a in ipairs(auras[u] or {}) do if a.spellId==id then return a end end
 end}
C_Item={GetWeaponEnchantInfo=function() return enchants end,
 GetItemCount=function(id) return itemCounts[id] or 0 end,GetItemIconByID=function() return 10 end,
 GetItemInfoInstant=function(id) return id,nil,nil,nil,nil,0,id==1 and 5 or 6 end,
 GetItemNameByID=function(id) return 'Item '..id end}
C_Container={GetContainerNumSlots=function(bag) return bag==0 and 2 or 0 end,GetContainerItemID=function(_,slot) return slot end}
C_Timer={NewTimer=function(delay,fn)
 local t={due=clock+delay,callback=fn,Cancel=function(self) self.cancelled=true end}; timers[#timers+1]=t; return t
end}
function CreateFrame()
 local f={events={}}
 function f:RegisterEvent(e) self.events[e]=true end
 function f:RegisterUnitEvent(e,u) self.events[e]=u end
 function f:UnregisterEvent(e) self.events[e]=nil end
 function f:SetScript(_,fn) self.callback=fn end
 frames[#frames+1]=f; return f
end
EllesmereUI={IS_FOREVER=true}; ns={}
''')
lua.execute(source, 'EllesmereUIAuraBuffReminders', lua.globals().ns)
lua.execute(r'''
F=ns.ForeverReminders; refreshCount=0; F.Init(function() refreshCount=refreshCount+1 end)
function clean()
 F.CancelTimer(); combat=false; locked=false; blockedSpells={}; queryErrors={}; auras={player={}}; forms={}; enchants={}
 config={camp=false,food=false,flask='off',elixir='off',weapon=false,aura='off',seal='off',blessing='off',tankMode='on'}
 class='PALADIN'; role='NONE'; members=0; unitNames={}; visible={}; weaponID=123; itemCounts={}
end
function shows(where,instance)
 return not (where and ((not instance and where.open_world==false) or (combat and where.in_combat==false)))
end
function collect(instance)
 F.CancelTimer(); missing={}
 F.Collect(config,missing,function() return {} end,function(id) return id end,shows,instance or false,false)
 return missing
end
function find(key)
 for _,e in ipairs(missing) do if e.dismissKey=='forever:'..key then return e end end
end
function aura(id,exp,dur,n) return {spellId=id,name=n or spellNames[id] or ('Spell '..id),expirationTime=exp or 0,duration=dur or 0} end
clean(); collect(); assert(find('rf') and find('rf').mode=='spell' and find('rf').spellID==25780)
auras.player={aura(25780,200,1800)};collect();assert(not find('rf'));assert(F.timer and math.abs(F.timer.due-170.05)<.01)
clock=171; collect();assert(find('rf').label=='Righteous Fury soon');assert(F.status.rf=='expiring')
config.warnSeconds=0;collect();assert(not find('rf'));assert(F.timer and math.abs(F.timer.due-200.05)<.01)
clock=201;auras.player={};combat=true;locked=true;collect();assert(find('rf') and F.status.rf=='missing')
auras.player={aura(25780,300,1800)};collect();assert(not find('rf')) -- refreshed in combat, no stale snapshot
blockedSpells[25780]=true;collect();assert(not find('rf') and F.status.rf=='unknown')
config.unknown=true;collect();assert(find('rf').silent and find('rf').mode=='texture' and F.status.rf=='unknown')
config.unknown=false;collect();assert(not find('rf'))
config.unknown=true;blockedSpells={};queryErrors[25780]=true;collect();assert(F.status.rf=='unknown')
clean(); auras.player={aura(25780)}; auras.player[1].duration=SECRET;auras.player[1].expirationTime=SECRET
collect();assert(not find('rf') and not F.timer) -- secret timer does not destroy readable presence
auras.player={SECRET}; locked=false;queryErrors[25780]=true; collect(); assert(F.status.rf=='unknown')
clean();config.tankMode='auto';collect();assert(not find('rf'));role='TANK';collect();assert(find('rf'))
config.tankMode='off';collect();assert(not find('rf'))
class='MAGE';config.tankMode='on';collect();assert(not find('rf'))
class='PALADIN';knownIDs[25780]=false;collect();assert(not find('rf'));knownIDs[25780]=true
clean();config.customIDs={25780};collect();assert(#missing==1) -- no duplicate RF
config.tankMode='off';collect();assert(find('25780')) -- explicit old custom entry is preserved
clean();config.aura='devotion';forms={{id=465,active=false}};collect();assert(find('aura').mode=='spell')
forms[1].active=true;collect();assert(not find('aura'))
forms={};auras.player={aura(465)};collect();assert(F.status.aura=='unknown') -- someone else's aura is not your stance
-- Retired seals stay absent for fresh and existing profiles, in/out of combat.
for _,saved in ipairs({'unset','any','righteousness','command','wisdom','light','justice','crusader','off'}) do
 for _,fighting in ipairs({false,true}) do
  for _,restricted in ipairs({false,true}) do
   clean();combat=fighting;locked=restricted
   config.seal=saved~='unset' and saved or nil
   local old=config.seal
   collect();assert(not find('seal') and F.status.seal==nil and not F.timer)
   assert(config.seal==old) -- no migration/reset of dormant preferences
  end
 end
end
clean();config.blessing='might';auras.player={aura(999999,0,0,'Blessing of Might')}
collect();assert(not find('blessing')) -- localized client-rank matching remains
config.blessing='any';auras.player={};collect();assert(find('blessing').mode=='texture')
assert(F.defaults.seal==nil and F.seals==nil)
clean();config.blessing='might';auras.player={aura(25782)};collect();assert(not find('blessing'))
auras.player={};collect();assert(find('blessing').spellID==19838) -- highest learned normal rank
clean();config.food=true;collect(false);assert(not find('food'));collect(true);assert(find('food'))
auras.player={aura(19706)};collect(true);assert(not find('food'))
auras.player={aura(987654,0,0,'Well Fed')};collect(true);assert(not find('food'))
auras.player={aura(433,clock+20,30)};collect(true);assert(not find('food')) -- don't nag while eating
auras.player={};config.foodItem=1;itemCounts[1]=3;collect(true);assert(find('food').mode=='item' and find('food').itemID==1)
itemCounts[1]=0;collect(true);assert(find('food').mode=='texture')
config.foodBuff=999;auras.player={aura(999)};collect(true);assert(not find('food'))
combat=true;collect(true);assert(not find('food')) -- consumable combat default off
clean();config.flask='any';auras.player={aura(17628)};collect(true);assert(not find('flask'))
config.flask='titans';collect(true);assert(find('flask'));itemCounts[13510]=1;collect(true);assert(find('flask').itemID==13510)
config.flaskBuff=998;collect(true);assert(find('flask').mode=='texture') -- custom effect never consumes wrong preset
auras.player={aura(998)};collect(true);assert(not find('flask'))
clean();config.elixir='intellect';itemCounts[9179]=1;collect(true);assert(find('elixir').itemID==9179)
auras.player={aura(11396)};collect(true);assert(not find('elixir'))
clean();config.weapon=true;enchants={{hasEnchant=true,enchantType=1,timeLeft=0}};collect(true);assert(find('weapon'))
enchants={{hasEnchant=true,enchantType=2,timeLeft=600000}};collect(true);assert(not find('weapon'))
enchants={{hasEnchant=true,enchantType=3,timeLeft=10000}};collect(true);assert(F.status.weapon=='expiring')
enchants={{hasEnchant=SECRET,enchantType=2}};collect(true);assert(F.status.weapon=='unknown')
enchants={};config.oilItem=2;itemCounts[2]=1;collect(true);assert(find('weapon').macro=='/use item:2\n/use 16')
weaponID=nil;collect(true);assert(not find('weapon'))
clean();config.groupBlessing='might';members=3;unitNames={party1='Alice',party2='Bob',party3='dead'}
auras.party1={aura(25782)};collect();assert(find('group').unit=='party2' and find('group').groupTotal==2 and find('group').groupHave==1)
assert(find('group').detail:find('Bob'));assert(F.events.events.UNIT_AURA)
visible.party2=false;collect();assert(F.status.group=='unknown' and not find('group'))
config.unknown=true;collect();assert(find('group').silent and not find('group').unit)
combat=true;collect();assert(not find('group') and not F.events.events.UNIT_AURA)
config.groupBlessing='off';combat=false;collect();assert(not F.events.events.UNIT_AURA)
clean();config.whereToShow={open_world=false};collect();assert(#missing==0 and not F.timer)
config.whereToShow={};auras.player={aura(25780,clock+100,1800)};collect();local t=F.timer;F.CancelTimer();assert(t.cancelled and not F.timer)
local v,o=F.BagChoices('food',55);assert(v[1] and not v[2] and v[55])
v,o=F.BuffChoices(44);assert(v[44]) -- out-of-context preferences survive
config.sentinel={x=42};collect();assert(config.sentinel.x==42 and config.food==false)
F.events.callback(nil,'PLAYER_EQUIPMENT_CHANGED');assert(refreshCount==1)
''')
print('PASS: entire Forever detector: RF/expiry/recast, protected/unknown states, roles, ranks, auras, retired seals, blessings, consumables, group coverage, timers, preferences')

main=(ROOT/'EllesmereUIAuraBuffReminders/EllesmereUIAuraBuffReminders.lua').read_text(encoding='utf-8-sig')
toc=(ROOT/'EllesmereUIAuraBuffReminders/EllesmereUIAuraBuffReminders.toc').read_text(encoding='utf-8-sig')
assert toc.index('EllesmereUIABR_Forever.lua') < toc.index('\nEllesmereUIAuraBuffReminders.lua')
assert 'EABR.ForeverSupport.Collect(db.profile.forever' in main
assert 'EABR.ForeverSupport.Init(RequestRefresh)' in main
assert 'e.detail = nil; e.silent = nil' in main
assert 'not missing[i].silent' in main
assert 'btn._tooltipDetail = m.detail or nil' in main
assert 'f._tooltipDetail = m.detail or nil' in main
# Execute the actual collector adapter and timer/early-return hook (no reimplementation).
lua.execute('EABR={ForeverSupport=F}; db={profile={forever=config}}; AcquireEntry=function() return {} end; Tex=function(id) return id end; EABR.SectionShows=shows')
adapter=main[main.index('function EABR.CollectForever('):main.index('\nlocal function Refresh()',main.index('function EABR.CollectForever('))]
lua.execute(adapter)
lua.execute("clean(); db.profile.forever=config; list={}; EABR.CollectForever(list,false,false,false); assert(#list==1)")
# Actual refresh entry cancels timers/subscriptions even on an early return.
refresh=main[main.index('local function Refresh()'):main.index('\nlocal REFRESH_THROTTLE_COMBAT')]
lua.execute(refresh.replace('local function Refresh()', 'function TestedRefresh()', 1))
lua.execute(r'''
auras.player={aura(25780,clock+100,1800)};collect(); local t=F.timer
F.SetGroup(true); db=nil; TestedRefresh()
assert(t.cancelled and not F.timer and not F.events.events.UNIT_AURA)
db={profile={forever=config,display={}}}
''')
# Exercise the real pooled-entry reset, not just a textual assertion.
pool_start=main.index('    AcquireEntry = function()')
pool_end=main.index('    ApplySetup = function',pool_start)
lua.execute('pool={};inUse=0;'+main[pool_start:pool_end])
lua.execute('local e=AcquireEntry();e.detail="old";e.silent=true;e.unit="party1";ResetEntryPool();local reused=AcquireEntry();assert(reused==e and not reused.detail and not reused.silent and not reused.unit)')
print('PASS: manifest load order, core adapter, timer hook, silent unknown alerts and pooled tooltip reset integration')

options=(ROOT/'EllesmereUIOptions/EUI_AuraBuffReminders_Options.lua').read_text(encoding='utf-8-sig')
begin=options.index('            -- Same EUI widgets')
end=options.index('            y = BuildForeverCustomRows',begin)
lua.execute(r'''
clean(); config={camp=false,customIDs={77},seal='righteousness',sentinel='preserved'}; controls={}; y=0; parent={}
ns.ForeverReminders=F
function FDB() return config end
function RefreshAll() end
FOREVER_WHERE_ITEMS={}
W={}
function W:SectionHeader(_,text,_) return {},24 end
function W:DualRow(_,_,left,right)
 for _,cfg in ipairs({left,right}) do
  assert(cfg.type=='dropdown' or cfg.type=='toggle' or cfg.type=='slider')
  controls[cfg.text]=cfg
  if cfg.getValue then cfg.getValue() end
 end
 return {},50
end
function SectionControlRow(_,_,cfg) cfg.whereStore(); return {},50 end
C_Timer.After=function(_,fn) fn() end
EllesmereUI.RefreshPage=function() end
''')
lua.execute(options[begin:end])
lua.execute(r'''
assert(controls['Show Unavailable Status'].getValue()==false)
controls['Show Unavailable Status'].setValue(true);assert(config.unknown==true)
controls['Show Unavailable Status'].setValue(false);assert(config.unknown==false)
assert(controls['Show in Cities / Inns'].getValue()==false)
controls['Show in Cities / Inns'].setValue(true);assert(config.showRested==true)
controls['Show in Cities / Inns'].setValue(false);assert(config.showRested==false)
assert(controls['Righteous Fury'].getValue()=='on')
controls['Righteous Fury'].setValue('off');assert(config.tankMode=='off')
assert(not controls['Preferred Seal'] and config.seal=='righteousness')
controls['Personal Blessing'].setValue('might');assert(config.blessing=='might')
controls['Group Blessing'].setValue('wisdom');assert(config.groupBlessing=='wisdom')
controls['Refresh Warning (seconds)'].setValue(60);assert(config.warnSeconds==60)
controls['Food Buff'].setValue(false);assert(config.food==false)
controls['Flask'].setValue('titans');assert(config.flask=='titans')
controls['Flask Effect'].setValue(998);assert(config.flaskBuff==998)
controls['Food to Use'].setValue(1);assert(config.foodItem==1)
controls['Oil / Stone to Use'].setValue(2);assert(config.oilItem==2)
controls['Add Active Buff'].setValue(44);controls['Add Active Buff'].setValue(44)
assert(#config.customIDs==2 and config.customIDs[1]==77 and config.customIDs[2]==44)
assert(config.camp==false and config.sentinel=='preserved')
assert(config.consumablesWhere.open_world==false and config.consumablesWhere.in_combat==false)
assert(F.defaults.consumablesWhere.open_world==false)
config.consumablesWhere.open_world=true;assert(F.defaults.consumablesWhere.open_world==false)
class='MAGE'; controls={}
''')
lua.execute(options[begin:end])
lua.execute("assert(not controls['Righteous Fury'] and controls['Food Buff'])")
print('PASS: actual EUI options builder/callbacks, class gating, selection persistence, custom-buff deduplication and independent location settings')

# Compile all changed Lua with the actual client language version.
compile_lua=lua.eval('function(s,n) local f,e=loadstring(s,n); assert(f,e) end')
for rel in ['EllesmereUIAuraBuffReminders/EllesmereUIAuraBuffReminders.lua','EllesmereUIAuraBuffReminders/EllesmereUIABR_Forever.lua','EllesmereUIOptions/EUI_AuraBuffReminders_Options.lua']:
    compile_lua((ROOT/rel).read_text(encoding='utf-8-sig'),rel)
print('PASS: changed chunks compile under Lua 5.1')

# Duplicate built-in/custom spell-family reminders retain one visual owner.
lua.execute(r'''
clean();forms={{id=465,active=false}};config.aura='devotion';config.customIDs={465,465,777,777};collect()
assert(find('aura') and not find('465') and find('777'))
local n=0;for _,e in ipairs(missing) do if e.dismissKey=='forever:777' then n=n+1 end end;assert(n==1)
config.aura='off';collect();assert(find('465'))
config.blessing='might';config.customIDs={19838};collect();assert(find('blessing') and not find('19838'))
config.blessing='off';collect();assert(find('19838'))
config.customIDs={25780,25780};config.tankMode='off';collect();assert(#missing==1 and find('25780'))
assert(#config.customIDs==2) -- saved custom entries are never discarded
''')
print('PASS: built-in/custom ranks and repeated IDs produce one reminder; disabling builtin restores custom coverage without data loss')

# Unknown never becomes an automatic rebuff prompt; current readable state wins.
lua.execute(r"""
for _,fighting in ipairs({false,true}) do
 clean();combat=fighting;locked=true;blockedSpells[25780]=true
 auras.player={aura(25780,clock+3600,3600)};collect()
 assert(F.status.rf=='unknown' and not find('rf') and config.unknown==nil)
 config.unknown=true;collect();assert(find('rf').silent and not find('rf').unit)
 config.unknown=false;collect();assert(not find('rf'))
 blockedSpells={};collect();assert(F.status.rf=='present' and not find('rf'))
 auras.player={};collect();assert(F.status.rf=='missing' and find('rf') and not find('rf').silent)
 auras.player={aura(25780,clock+10,3600)};collect();assert(F.status.rf=='expiring' and find('rf'))
 auras.player={aura(25780,clock+3600,3600)};collect();assert(not find('rf'))
end
""")
print('PASS: unavailable states opt-in, explicit settings preserved, readable present/missing/expiry/recast transitions')

# Execute all three real display paths and the native badge logic on pooled frames.
render=LuaRuntime(unpack_returned_tuples=True)
render.execute(r"""
EABR={};db={profile={display={showText=false,showCount=true}}};floor=math.floor;ICON_SIZE=36
function widget()
 local w={}
 function w:SetText(v) self.text=v end
 function w:SetTextColor(...) self.color={...} end
 function w:SetTexture(v) self.texture=v end
 function w:SetDesaturated(v) self.desaturated=v end
 function w:SetVertexColor(...) self.tint={...} end
 function w:Show() self.visible=true end
 function w:Hide() self.visible=false end
 return w
end
frame={_icon=widget(),_text=widget(),_bagCount=widget()}
function frame:GetWidth() return 36 end
function frame:Show() self.visible=true end
function GetOrCreateIcon() return frame end
GetOrCreateCombatIcon=GetOrCreateIcon;GetOrCreateCursorIcon=GetOrCreateIcon
function InCombat() return true end -- skip irrelevant secure click-routing setup
function Tex(id) return id end
function ApplySetup() end
function ResolveGlowTint() return 1,1,1 end
function RemoveGlow(f) f.glow=false end
function ApplyGlow(f) f.glow=true end
EABR.ApplyEatingVisual=function() end
EABR.ApplyIconTooltipData=function() end
EABR.ApplyIconQuality=function() end
EABR.CreateIconBagCountOverlay=function() end
EABR.SizeIconBagCount=function() end
combatActiveIcons={};cursorActiveIcons={};activeIcons={}
""")
for start,end in [
 ('function EABR.ApplyIconBagCount(', 'function EABR.ApplyIconGroupCoverage('),
 ('function EABR.ApplyReminderAvailability(', 'function EABR.ApplyEatingVisual('),
 ('local function ShowCombatIcon(', 'local function LayoutCombatIcons('),
 ('local function ShowCursorIcon(', 'local function LayoutCursorIcons('),
 ('local function ShowIcon(', 'local function CollectRaidBuffs('),
]:
 chunk=main[main.index(start):main.index(end,main.index(start))]
 render.execute(chunk.replace('local function Show','function Show',1))
render.execute(r"""
for _,show in ipairs({ShowCombatIcon,ShowCursorIcon,ShowIcon}) do
 -- Genuine out-of-stock consumable still has its red zero.
 show(1,{texture=1,desaturated=true});assert(frame._bagCount.text=='0' and frame._outOfStock)
 -- Unknown buff clears the old stock badge, has no glow, and is visibly dim.
 show(1,{texture=2,desaturated=true,silent=true})
 assert(not frame._bagCount.visible and frame._bagCount.text=='' and not frame._outOfStock)
 assert(frame._icon.desaturated and frame._icon.tint[1]==0.55)
 if show==ShowIcon then assert(not frame.glow) end
 -- The same frame becomes an ordinary readable reminder without stale gray state.
 show(1,{texture=3});assert(not frame._icon.desaturated and frame._icon.tint[1]==1)
 show(1,{texture=4,bagCount=7});assert(frame._bagCount.text==7 and frame._bagCount.visible)
 show(1,{texture=5,desaturated=true});assert(frame._bagCount.text=='0')
end
""")
print('PASS: actual secure/combat/cursor renderers distinguish unavailable buffs from item stock and reset pooled appearance')
