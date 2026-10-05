"""LFG last-equipped tooltip: asynchronous identity, ownership and pooling."""
from pathlib import Path
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2]
source = (root / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverGroupFinder.lua').read_text(encoding='utf-8')
source = source[source.index('-- Last-equipped inspection for the hovered Forever LFG listing.'):]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
now=0; timers={}; drivers={}; sent={}; reads={}; names={}; levels={}; blocked={}; combat=false
W={Theme={accR=.1,accG=.8,accB=.7},Font=function() end,OnLooksChanged=function(fn) looks=fn end}
function GetTime() return now end
function InCombatLockdown() return combat end
function wipe(t) for k in pairs(t) do t[k]=nil end end
function issecretvalue(v) return type(v)=='table' and v.secret end
secret=setmetatable({secret=true},{__tostring=function() error('secret formatted') end,__eq=function() error('secret compared') end})
function frame()
 local f={shown=true,width=200,hooks={},events={},children={}}
 function f:IsShown() return self.shown end
 function f:Show() self.shown=true end
 function f:Hide() self.shown=false; if self.hooks.OnHide then self.hooks.OnHide() end end
 function f:HookScript(k,fn) self.hooks[k]=fn end
 function f:RegisterEvent(e) self.events[e]=true end
 function f:SetScript(k,fn) self[k]=fn end
 function f:CreateFontString() local c=frame(); self.children[#self.children+1]=c; return c end
 function f:SetJustifyH() end
 function f:SetWordWrap() end
 function f:SetText(t) self.text=t end
 function f:GetText() return self.text end
 function f:GetStringWidth() return #(self.text or '')*6 end
 function f:GetWidth() return self.width end
 function f:SetWidth(w) self.width=w end
 function f:ClearAllPoints() self.points={} end
 function f:SetPoint(...) self.points[#self.points+1]={...} end
 return f
end
function member(name)
 local f=frame(); f.Name=frame(); f.Name.text=name; f.Name.width=90
 f.Level=frame(); f.Level.text='Lvl 30'; f.Role={unchanged=true}; return f
end
function CreateFrame() local f=frame(); drivers[#drivers+1]=f; return f end
function hooksecurefunc(name,fn)
 local original=_G[name]; _G[name]=function(...) local r={original(...)}; fn(...); return unpack(r) end
end
C_Timer={NewTimer=function(delay,fn)
 local t={at=now+delay,fn=fn}; function t:Cancel() self.cancelled=true end
 timers[#timers+1]=t; return t
end}
function advance(dt)
 local untilTime=now+dt
 for n=1,1000 do
  local first
  for _,t in ipairs(timers) do if not t.cancelled and t.at<=untilTime and (not first or t.at<first.at) then first=t end end
  if not first then now=untilTime; return end
  now=first.at; first.cancelled=true; first.fn()
 end
 error('unbounded timers')
end
function event(e,arg) for _,f in ipairs(drivers) do if f.events[e] then f.OnEvent(f,e,arg) end end end
function UnitGUID(name) return names[name] end
function CanInspect(name) return not blocked[name] end
function NotifyInspect(name) sent[#sent+1]=name; if requestError then error('native refusal') end end
function ClearInspectPlayer() end
C_PaperDollInfo={GetInspectItemLevel=function(name) reads[#reads+1]=name; return levels[name] end}
C_LFGList={GetSearchResultInfo=function(id) return {numMembers=#listing,isDelisted=delisted} end,
 GetSearchResultLeaderInfo=function() return {name=listing[1]} end,
 GetSearchResultPlayerInfo=function(id,i) return {name=listing[i]} end}
LFGBrowseSearchEntryTooltip=frame(); LFGBrowseSearchEntryTooltip.shown=false
LFGBrowseSearchEntryTooltip.memberPool={EnumerateActive=function() return ipairsMembers end}
local active={}; local pos
function ipairsMembers() pos=pos+1; return active[pos] end
LFGBrowseSearchEntryTooltip.memberPool.EnumerateActive=function() pos=0; return ipairsMembers end
pool={}
function LFGBrowseSearchEntryTooltip_UpdateAndShow(t,id)
 t:SetWidth(200); t:Show(); t.Leader=t.Leader or member(listing[1]); t.Leader.Name.text=listing[1]
 active={}
 for i=2,#listing do
  pool[i]=pool[i] or member(listing[i]); pool[i].Name.text=listing[i]; active[#active+1]=pool[i]
 end
end
function hover(...)
 listing={...}; LFGBrowseSearchEntryTooltip_UpdateAndShow(LFGBrowseSearchEntryTooltip,1)
end
function label(row) return row.children[1] end
function leaderText() return label(LFGBrowseSearchEntryTooltip.Leader).text end
function check(v,msg) assert(v,msg) end
''')
lua.execute(source)
lua.execute(r'''
-- Remote name is deliberately absent from all target/party tokens. No range,
-- visibility, distance or UI-opening API exists in this fixture.
names['Remote Surname']='GUID-A'; levels['Remote Surname']=30
hover('Remote Surname'); check(leaderText()=='Equipped: Loading...','initial loading')
advance(.19); check(#sent==0,'hover debounce'); advance(.02)
check(sent[1]=='Remote Surname','native full-name request')
event('INSPECT_READY','GUID-WRONG'); check(#reads==0,'foreign result rejected')
event('INSPECT_READY','GUID-A'); check(leaderText()=='Equipped: 30.00','equipped native result')
check(LFGBrowseSearchEntryTooltip.width>200,'tooltip accommodates extra column')
check(LFGBrowseSearchEntryTooltip.Leader.Level.text=='Lvl 30','native level preserved')
check(#label(LFGBrowseSearchEntryTooltip.Leader).points==1,'single non-stretching text anchor')
hover('Remote Surname'); advance(2); check(#sent==1,'cache suppresses repeated request')
print('PASS: remote full-name request, delayed identity, native value, layout and cache')

names.B='GUID-B'; levels.B=42.125; names.C='GUID-C'; levels.C=18
hover('B'); advance(.21); hover('C'); event('INSPECT_READY','GUID-B')
check(leaderText()=='Equipped: Loading...','old reply never labels new hover')
advance(1.6); check(sent[#sent]=='C','current hover proceeds'); event('INSPECT_READY','GUID-C')
check(leaderText()=='Equipped: 18.00','correct new hover value')
hover('B'); check(leaderText()=='Equipped: 42.12','old reply cached only under its own name')
print('PASS: rapid hover swaps keep replies attached to their original player')

hover('NoReply'); advance(1.6); advance(5.1)
check(leaderText()=='Equipped: Unavailable','bounded timeout')
local calls=#sent; advance(2); check(#sent==calls,'no timeout retry loop')
blocked.Denied=true; hover('Denied'); advance(.21)
check(leaderText()=='Equipped: Unavailable' and #sent==calls,'native eligibility preserved')
print('PASS: timeout and native refusal never fabricate zero or poll continuously')

names.Manual='GUID-M'; levels.Manual=70
InspectFrame={unit='target',IsShown=function() return true end}
hover('Manual'); advance(2); check(#sent==calls,'manual UI wins')
InspectFrame=nil; combat=true; advance(2); check(#sent==calls,'combat deferred')
combat=false; event('PLAYER_REGEN_ENABLED'); advance(.6); check(sent[#sent]=='Manual','deferred request resumes')
NotifyInspect('External'); levels.Manual=999; event('INSPECT_READY','GUID-M')
check(leaderText()=='Equipped: Loading...','external request cancels ownership')
LFGBrowseSearchEntryTooltip:Hide(); local afterHide=#sent; advance(10)
check(#sent==afterHide,'no hidden requests'); check(InspectFrame==nil,'no native UI writes')
print('PASS: manual inspection, external ownership, combat and hidden cleanup')

hover('Remote Surname','B'); advance(.21)
check(label(pool[2]).text=='Equipped: 42.12','group member gets own value')
hover('C'); check(not label(pool[2]).shown,'pooled member label cleaned')
delisted=true; hover('Remote Surname'); check(not label(LFGBrowseSearchEntryTooltip.Leader).shown,'delisted cleanup'); delisted=false
hover(secret); advance(2); check(not label(LFGBrowseSearchEntryTooltip.Leader).shown,'secret name skipped')
names.Secret='GUID-S'; levels.Secret=secret; hover('Secret'); advance(.21); event('INSPECT_READY','GUID-S')
check(leaderText()=='Equipped: Unavailable','secret average rejected')
print('PASS: group identities, pooling, delisted entries and restricted values')

hover('Unresolved'); advance(1.6); event('INSPECT_READY','GUID-U')
check(leaderText()=='Equipped: Loading...','unresolved response cannot be misassigned')
names.Unresolved='GUID-U'; levels.Unresolved=33; event('INSPECT_READY','GUID-U')
check(leaderText()=='Equipped: 33.00','identity may resolve on remote response')
names.Zero='GUID-Z'; levels.Zero=0; hover('Zero'); advance(1.6); event('INSPECT_READY','GUID-Z')
check(leaderText()=='Equipped: 0.00','readable native zero preserved')
print('PASS: late name resolution and native zero')

function GetNormalizedRealmName() return 'HomeRealm' end
function GetPlayerInfoByGUID(guid) return 'Warrior','WARRIOR','Human','Human',2,'Far Away','HomeRealm' end
levels['Far Away']=55.5; hover('Far Away'); advance(1.6); event('INSPECT_READY','GUID-FAR')
check(leaderText()=='Equipped: 55.50','remote response identity without a world unit')
function GetPlayerInfoByGUID() return 'Warrior','WARRIOR','Human','Human',2,'RealmTest','OtherRealm' end
levels.RealmTest=99; hover('RealmTest'); advance(1.6); event('INSPECT_READY','GUID-OTHER')
check(leaderText()=='Equipped: Loading...','different realm does not match bare name')
ClearInspectPlayer(); LFGBrowseSearchEntryTooltip:Hide(); advance(2)
print('PASS: exact server-returned remote identity and cross-realm collision guard')

names.Failure='GUID-F'; requestError=true; hover('Failure'); advance(1.6); requestError=false
check(leaderText()=='Equipped: Unavailable','request error bounded')
LFGBrowseSearchEntryTooltip:Hide(); advance(61); hover('Remote Surname'); advance(.21)
check(sent[#sent]=='Remote Surname' and leaderText()=='Equipped: Loading...','expired cache refreshes')
looks(); check(leaderText()=='Equipped: Loading...','theme refresh stable')
print('PASS: request failure, cache expiry and theme refresh')
''')
print('PASS: LFG item-level asynchronous regression suite (Lua 5.1)')
