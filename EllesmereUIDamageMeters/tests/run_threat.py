"""Actual native threat provider and extracted production row renderer under Lua5.1."""
from pathlib import Path
from lupa.lua51 import LuaRuntime
root=Path(__file__).resolve().parents[1]
lua=LuaRuntime(unpack_returned_tuples=True)
compile_lua=lua.eval('function(s,n) local f,e=loadstring(s,n); assert(f,e); return f end')
for p in root.glob('*.lua'): compile_lua(p.read_text(encoding='utf-8-sig'),p.name)
lua.execute(r'''
local realtype=type
local protectedValues={}
function secret(v)
 local s=setmetatable({}, {__lt=function() error('secret comparison') end,
 __le=function() error('secret comparison') end,__add=function() error('secret arithmetic') end,
 __tostring=function() error('secret formatting') end})
 protectedValues[s]={v}; return s
end
function issecretvalue(v) return protectedValues[v]~=nil end
function type(v) return protectedValues[v] and realtype(protectedValues[v][1]) or realtype(v) end
function native(v) return protectedValues[v] and protectedValues[v][1] or v end
now=0; timers={}; calls=0; damageCalls=0
function GetTime() return now end
function debugprofilestop() return 0 end
function frameMock()
 local f={shown=true,scroll=0,height=200,width=300,hooks={}}
 function f:Hide() self.shown=false; if self.hooks.OnHide then self.hooks.OnHide() end end
 function f:Show() self.shown=true; if self.hooks.OnShow then self.hooks.OnShow() end end
 function f:IsShown() return self.shown end
 function f:SetShown(v) self.shown=v end
 function f:HookScript(e,fn) self.hooks[e]=fn end
 function f:SetScript(e,fn) self[e]=fn end
 function f:RegisterEvent(e) self.events=self.events or {}; self.events[e]=true end
 function f:GetHeight() return self.height end
 function f:GetWidth() return self.width end
 function f:SetHeight(h) self.height=h end
 function f:GetEffectiveScale() return 1 end
 function f:GetVerticalScroll() return self.scroll end
 function f:SetVerticalScroll(n) self.scroll=n end
 function f:SetMinMaxValues(a,b) self.min=a;self.max=native(b) end
 function f:SetValue(n) self.value=native(n) end
 function f:SetText(t) self.text=t end
 function f:SetFormattedText(fmt,...) local args={...}; for i=1,#args do args[i]=native(args[i]) end; self.text=string.format(fmt,unpack(args)) end
 function f:SetFont(_,height) assert(height>0,'font height') end
 function f:SetTextColor(...) self.color={...} end
 function f:CreateFontString() return frameMock() end
 for _,name in ipairs({'SetPoint','ClearAllPoints','SetAlpha','SetStatusBarColor','SetTexture','SetWidth','SetJustifyH'}) do f[name]=function() end end
 return f
end
frames={}
function CreateFrame() local f=frameMock(); frames[#frames+1]=f; return f end
C_Timer={NewTicker=function(rate,fn)
 local t={rate=rate,fn=fn}; function t:Cancel() self.cancelled=true end
 timers[#timers+1]=t; return t
end,After=function(_,fn) fn() end}
function lastTick() now=now+.15; local t=timers[#timers]; if t and not t.cancelled then t.fn() end end
exists={player=true,pet=true,party1=true,partypet1=true,target=true}
guids={player='self',pet='pet',party1='dps',partypet1='dpspet'}
dead={}; names={target='Spider',player='Tank',party1='DPS',pet='My pet',partypet1='DPS pet'}
raid=false; groupCount=2; fighting=true; hostile=true
function UnitExists(u) return exists[u] or false end
function UnitGUID(u) return guids[u] or u end
function UnitName(u) return names[u] or u end
function UnitCanAttack() return hostile end
function UnitIsDeadOrGhost(u) return dead[u] or false end
function UnitIsConnected() return true end
function UnitClass() return 'Warrior','WARRIOR' end
function UnitIsUnit(a,b) return a==b or UnitGUID(a)==UnitGUID(b) end
function IsInRaid() return raid end
function IsInGroup() return groupCount>1 end
function GetNumGroupMembers() return groupCount end
function UnitAffectingCombat() return fighting end
function UnitDetailedThreatSituation(u,m)
 assert(m=='target'); calls=calls+1; return unpack(data[u] or {})
end
data={player={true,3,100,100,243},party1={false,0,52,58,140}}
Enum={DamageMeterType={DamageDone=0,HealingDone=1,Deaths=2,Interrupts=3,Dispels=4,EnemyDamageTaken=5},DamageMeterSessionType={Current=0,Overall=1}}
EllesmereUI={L=function(s) return s end,Lf=function(_,s) return 'Overall '..s end,
 GetClassColor=function() return {r=.78,g=.61,b=.43} end,
 ShowWidgetTooltip=function(_,text) tooltip=text end,HideWidgetTooltip=function() tooltip=nil end}
EUI=EllesmereUI; L=EUI.L; ns={}
RAID_CLASS_COLORS={WARRIOR={r=.78,g=.61,b=.43}}
function MakeRow()
 return {row=frameMock(),fill=frameMock(),classIcon=frameMock(),label=frameMock(),amount=frameMock(),pos=frameMock(),ApplyBg=function() end}
end
frame=frameMock();viewport=frameMock();content=frameMock();winIdx=2
W={curDMType='THREAT',curSession=0,frame=frame,rowPool={},FitTitle=function() end,UpdateSticky=function() end}
W.timerText=frameMock()
ns._windows={W}
for i=1,40 do W.rowPool[i]=MakeRow() end
BAR_POOL_SIZE=40;RANK_STRINGS={};PEAK_BUDGET=1.5
DM_TYPE_NAMES={[0]='Damage Done',[1]='Healing Done',THREAT='Threat'}
cfg={iconStyle='none',barHeight=18,barSpacing=2,showClassColor=true,fontSize=11}
function DB() return cfg end
function ns._RowMetrics(h,s) return h,s,h+s,1 end
function GetBarTexturePath() return 'house','house' end
function ApplyBarTexture() end
function SetDMFont(f,n) f:SetFont('house',n) end
function ResolveIcon() return 0 end
function GetAccentRGB() return .5,.5,.5 end
function StripRealm(s) return s end
function FormatBarValue(n) return 'DMG '..n end
function AbbrevNumber(n) return tostring(n) end
function RecalcViewport(n) viewport.count=n end
function GetCurrentViewDuration() return 5 end
function FormatTimer() return '0:05' end
C_DamageMeter={GetCombatSessionFromType=function(_,kind)
 damageCalls=damageCalls+1; assert(kind~='THREAT','Threat must never be passed to damage API')
 return {combatSources={{name='Tank',classFilename='WARRIOR',isLocalPlayer=true,totalAmount=240,amountPerSecond=48}}}
end}
''')
compile_lua((root/'EllesmereUIDamageMeters_Threat.lua').read_text(),'threat')('EllesmereUIDamageMeters',lua.globals().ns)
source=(root/'EllesmereUIDamageMeters.lua').read_text(encoding='utf-8-sig')
start=source.index('    RefreshUI = function(session)')
end=source.index('    function W.RefreshBreakdown()',start)
lua.execute(source[start:end])
lua.execute(r'''
W.Refresh(); assert(damageCalls==0 and W.visibleCount==2)
assert(W.rowPool[1].label.text=='Tank' and W.rowPool[1].amount.text=='100%')
assert(W.rowPool[2].amount.text=='52%' and W.rowPool[2].fill.max==100 and W.rowPool[2].fill.value==52)
assert(W._fullTitle=='Threat - Spider' and W.timerText.text=='')
assert(timers[#timers].rate==.15)
local firstCalls=calls; W.Refresh(); assert(calls==firstCalls,'same tick snapshot cache')
for _,v in ipairs({65,80,95,99}) do
 data.party1={false,1,v,100,200}; lastTick()
 assert(W.rowPool[1].amount.text=='100%' and W.rowPool[2].fill.value==v)
end
data.player={false,0,45,59,100}; data.party1={true,3,100,120,250}; lastTick()
assert(W.rowPool[1].label.text=='DPS' and W.rowPool[2].amount.text=='45%')
-- Protected fields go to native sinks; protected tables never receive numeric ranks.
data.player={secret(true),secret(3),secret(100),secret(100),secret(300)}
data.party1={secret(false),secret(0),secret(87),secret(90),secret(250)}
data.partypet1={false,0,33,40,90}; lastTick()
assert(W.visibleCount==3 and W.rowPool[1].amount.text=='100%' and W.rowPool[2].amount.text=='87%')
assert(W.rowPool[2].fill.value==87 and W.rowPool[2].pos.text=='')
local snapshot,err=ns.Threat.ReportSnapshot(); assert(snapshot==nil and err:find('protected'))
ns.Threat.Tooltip(W.rowPool[2]); assert(tooltip:find('progress toward pulling')); ns.Threat.HideTooltip(); assert(tooltip==nil)
-- One absent percentage remains unavailable, not a fabricated category value.
data.party1={false,0}; lastTick(); assert(W.rowPool[2].amount.text=='--' and W.rowPool[2].fill.value==0)
-- Raid players + pets beyond 40 remain scrollable in the native pool.
raid=true; groupCount=40; guids.raid1='self'; guids.raidpet1='pet'
for i=1,40 do exists['raid'..i]=true; exists['raidpet'..i]=true
 data['raid'..i]={false,0,i,50,100}; data['raidpet'..i]={false,0,i,50,100}
end
data.pet={false,0,5,5,10}; lastTick()
assert(W.visibleCount==80 and #W.rowPool==80)
viewport.scroll=1400; lastTick(); assert(W.rowPool[79].amount.text)
-- Return to a normal meter without leaving threat ranks, empty state or percentages.
W.curDMType=0; W._barCacheKey=nil; viewport.scroll=0; W.Refresh()
assert(damageCalls==1 and W.rowPool[1].amount.text=='DMG 240')
assert(not W.rowPool[79].row.shown and timers[#timers].cancelled)
-- Old deferred session data must not overwrite a different selected mode.
local old=W.rowPool[1].amount.text; RefreshUI({threat=true,combatSources={}}); assert(W.rowPool[1].amount.text==old)
W.curDMType='THREAT'; W._barCacheKey=nil; RefreshUI({combatSources={}}); assert(W.rowPool[1].amount.text==old)
-- Target clears and target deaths immediately remove old bars and show the native empty state.
exists.target=false; ns.Threat.Invalidate(); W.Refresh()
assert(W.visibleCount==0 and W._threatEmpty.shown and W._threatEmpty.text=='Select an enemy')
assert(not W.rowPool[1].row.shown and timers[#timers].cancelled)
exists.target=true; dead.target=true; ns.Threat.Invalidate(); W.Refresh(); assert(W.visibleCount==0)
dead.target=nil; raid=false; groupCount=2; data={}; fighting=false
ns.Threat.Invalidate(); W.Refresh(); assert(W._threatEmpty.text=='No threat on this target')
local before=calls; lastTick(); assert(calls==before,'no out-of-combat idle ticker')
-- Restore data via target event. Visible window starts polling; hidden one stops.
data={player={true,3,100},party1={false,0,52}}; fighting=true
local driver=frames[1]; driver.OnEvent(driver,'PLAYER_TARGET_CHANGED')
assert(W.visibleCount==2 and not timers[#timers].cancelled)
ns.Threat.Watch(W); W.frame:Hide(); assert(timers[#timers].cancelled)
W.frame:Show(); assert(not timers[#timers].cancelled)
local snap=ns.Threat.ReportSnapshot(); assert(snap.threat and snap.rows[2].amount==52 and snap.total==100)
print('PASS: production threat provider + row renderer; native fonts/bars/percentages, encroachment, handoff, protected sinks and ranks, pets/80-row raid, cache/ticker, target/death/idle cleanup, hidden windows, normal-mode restoration and deferred refresh isolation.')
''')
# Production mode menu and selection closure, including persistence + home exit.
start=source.index('    function W.SetDMType(dmType)')
end=source.index('    -- Set mode icon to current DM type icon',start)
lua.execute('''
wdb={}; DM_TYPE_ICONS={}; closed=0; homeClosed=0
_hoverPollFrame=frameMock(); function HideBarTooltip() end
function W.CloseSource() closed=closed+1 end
function W.HideHome() homeClosed=homeClosed+1 end
function ShowEDMMenu(items) menu=items end
function MakeHeaderBtn(_,_,_,fn) return {click=fn} end
btnSize=20;btnPad=2
'''+source[start:end]+'''
W.modeBtn.click(); assert(menu[4].text=='Threat'); menu[4].onClick()
assert(W.curDMType=='THREAT' and wdb.curDMType=='THREAT' and closed==1 and homeClosed==1)
menu[2].onClick(); assert(W.curDMType==Enum.DamageMeterType.HealingDone)
print('PASS: native Damage / Healing / Actions / Threat menu selection and persisted mode.')
''')
# Exercise the actual pinned-self renderer with secret values as well.
a=source.index('    function W.UpdateSticky(sources, visibleCount)')
b=source.index('    RefreshUI = function(session)',a)
lua.execute(source[a:b])
lua.execute(r'''
ci=1; _playerGUID='self';header=frameMock();W.stickyPlayer=MakeRow();W.stickySep=frameMock()
function GetHeaderH() return 22 end
function ResetScrollAnchors() end
cfg.showPinnedSelf=true;W.curDMType='THREAT';W._stickyCacheKey=nil
viewport.scroll=100
ns.Threat.Invalidate(); data.player={secret(true),secret(3),secret(100)}
local sess=ns.Threat.GetSession(); W._lastSession=sess
W.UpdateSticky(sess.combatSources,2)
assert(W.stickyPlayer.row.shown and W.stickyPlayer.amount.text=='100%')
assert(W.stickyPlayer.fill.max==100 and W.stickyPlayer.pos.text=='')
viewport.scroll=0; W.UpdateSticky(sess.combatSources,2); assert(not W.stickyPlayer.row.shown)
print('PASS: actual pinned-self renderer uses native protected percentages and unpins when visible.')
''')
lua.execute("ns.ReportContext={TypeNames=DM_TYPE_NAMES,Abbreviate=tostring}; data={player={true,3,100},party1={false,0,52}}; W.curDMType='THREAT'; ns.Threat.Invalidate()")
compile_lua((root/'EllesmereUIDamageMeters_Report.lua').read_text(encoding='utf-8-sig'),'reports')('EllesmereUIDamageMeters',lua.globals().ns)
lua.execute(r'''
local before=damageCalls
local snapshot,err=ns.Report.Snapshot(W)
assert(snapshot and not err and damageCalls==before)
local lines=ns.Report.Lines(snapshot,5)
assert(lines[2]:find('100.0%%') and lines[3]:find('52.0%%'))
assert(not lines[3]:find('34.2%%'),'Threat must never be reported as a share of the group total')
data.party1={secret(false),secret(0),secret(52)}; ns.Threat.Invalidate()
local blocked,why=ns.Report.Snapshot(W); assert(not blocked and why:find('protected'))
print('PASS: native report preview uses live threat percentages, never damage API/total shares, and refuses protected exports.')
''')
print('PASS: every meter Lua file compiles, including Lua5.1 local/upvalue limits.')

# Official meter capabilities absorbed into the existing embedded renderer.
lua.execute(r"""
ns.EDM={DB=function() return cfg end};cfg.foreverThreat={};W.frame:Show();W.curDMType='THREAT'
local T=ns.Threat
local anchorBar=MakeRow();local restored=0
anchorBar.label.SetPoint=function(_,...) anchorBar.anchor={...} end
anchorBar.ApplyTextOffsets=function() restored=restored+1 end
cfg.leftTextOffsetY=4;cfg.rightTextOffsetY=1
T.PaintAmount(anchorBar,{threatPercent=50},1,true,false)
assert(anchorBar.anchor[1]=='RIGHT' and anchorBar.anchor[2]==anchorBar.amount and anchorBar.anchor[5]==3)
T.RestoreTextLayout(anchorBar);T.RestoreTextLayout(anchorBar);assert(restored==1)
cfg.leftTextOffsetY=nil;cfg.rightTextOffsetY=nil
hostiles={target=true,focus=true,targettarget=true,focustarget=true}
function UnitCanAttack(_,u) return hostiles[u] or false end
function UnitDetailedThreatSituation(u,m) calls=calls+1;lastMob=m;return unpack(data[u] or {}) end
exists={player=true,pet=true,party1=true,partypet1=true,target=true,focus=true}
guids={target='mobA',focus='mobB'};dead={};raid=false;groupCount=2;fighting=true
names.focus='Focused Enemy'
data={player={false,0,80,88,800},party1={true,3,100,100,1000},pet={false,0,25,28,250}}
T.Set('source','focus');assert(lastMob=='focus' and W._lastSession.threatTitle:find('Focused Enemy'))
hostiles.focus=false;exists.focustarget=true;T.Invalidate();W.Refresh();assert(lastMob=='focustarget')
exists.focustarget=false;T.Invalidate();W.Refresh();assert(W.visibleCount==0)
hostiles.focus=true;T.Set('source','target');hostiles.target=false;exists.targettarget=true
T.Invalidate();W.Refresh();assert(lastMob=='targettarget')
hostiles.target=true;T.Set('pets',false);assert(#T.GetSession().combatSources==2)
T.Set('pets',true);assert(#T.GetSession().combatSources==3)
T.Set('percentMode','tank');T.Set('showValue',true)
local bar=MakeRow();T.PaintAmount(bar,T.GetSession().threatPlayer,1,true,false);assert(bar.amount.text=='800 / 88%')
T.Set('showPercent',false);T.PaintAmount(bar,T.GetSession().threatPlayer,1,true,false);assert(bar.amount.text=='800')
T.Set('showValue',false);T.PaintAmount(bar,T.GetSession().threatPlayer,1,true,false);assert(bar.amount.text=='')
T.Set('showPercent',true);data.player={secret(false),secret(0),secret(80),secret(88),secret(800)}
T.Invalidate();T.PaintAmount(bar,T.GetSession().threatPlayer,1,false,false);assert(bar.amount.text=='88%')
data.player={false,0,80,nil,800};T.Invalidate();T.PaintAmount(bar,T.GetSession().threatPlayer,1,true,false)
assert(bar.amount.text=='--','missing tank percentage must not fall back to pull percentage')
data.player={false,0,80,88,800};T.Set('pullBar',true)
local sess=T.GetSession();local pull
for _,e in ipairs(sess.combatSources) do if e.threatPull then pull=e end end
assert(pull and pull.threatRaw==1000 and pull.threatRawPercent==110 and pull.totalAmount==100)
local report=T.ReportSnapshot();assert(#report.rows==3)
data.player={true,3,100,100,800};T.Invalidate();assert(not T.GetSession().threatPull)
data.player={secret(false),0,secret(80),88,secret(800)};T.Invalidate();assert(not T.GetSession().threatPull)
-- Warning edge, re-arm, target switch, tank role/form, protected and hidden.
sounds=0;role='NONE';form=0
function PlaySound(id,channel) assert(id==8959 and channel=='Master');sounds=sounds+1 end
function UnitGroupRolesAssigned() return role end
function GetShapeshiftFormID() return form end
data.player={false,0,85,94,850};T.Set('warnSound',true);assert(sounds==1)
lastTick();lastTick();assert(sounds==1)
data.player[3]=70;lastTick();data.player[3]=85;lastTick();assert(sounds==2)
guids.target='mobC';frames[1].OnEvent(frames[1],'PLAYER_TARGET_CHANGED');assert(sounds==3)
role='TANK';guids.target='mobD';lastTick();assert(sounds==3)
role='NONE';form=18;lastTick();assert(sounds==3)
form=0;data.player[3]=secret(90);lastTick();assert(sounds==3)
data.player[3]=90;W.frame:Hide();T.Invalidate();T.GetSession();T.Wake();assert(sounds==3)
W.frame:Show();assert(sounds==4)
T.Set('warnSound',false);guids.target='mobE';lastTick();assert(sounds==4)
-- Menu is the only settings owner; callbacks persist in the meter profile.
local menu=T.Menu();local byText={};for _,e in ipairs(menu) do if type(e)=='table' then byText[e.text]=e end end
assert(byText['Show Pets'].isActive and not byText['Warning Sound'].isActive)
byText['Show Pets'].onClick();assert(cfg.foreverThreat.pets==false)
byText['Warn At (%)'].setValue(150);assert(cfg.foreverThreat.warnAt==100)
byText['Warn At (%)'].setValue(0);assert(cfg.foreverThreat.warnAt==1)
-- Preview is explicit, bounded, never exports and ends on combat or hiding.
exists.target=false;exists.targettarget=false;T.Preview();assert(W._lastSession.threatPreview and W.visibleCount==4)
local no,why=T.ReportSnapshot();assert(not no and why:find('Preview'))
now=now+11;lastTick();assert(W.visibleCount==0 and timers[#timers].cancelled)
T.Preview();frames[1].OnEvent(frames[1],'PLAYER_REGEN_DISABLED');assert(not W._lastSession.threatPreview)
T.Preview();W.frame:Hide();assert(timers[#timers].cancelled);W.frame:Show();assert(not W._lastSession.threatPreview)
-- Full raid, pets, and optional pull marker use 81 native scrollable rows.
exists.target=true;raid=true;groupCount=40;guids.raid1='self';guids.player='self';guids.pet='pet';guids.raidpet1='pet'
for i=1,40 do exists['raid'..i]=true;exists['raidpet'..i]=true
 data['raid'..i]={false,0,40,44,400};data['raidpet'..i]={false,0,20,22,200} end
data.player={false,0,80,88,800};data.pet={false,0,20,22,200};cfg.foreverThreat.pets=true
T.Refresh();assert(W.visibleCount==81 and #W.rowPool==81)
T.Set('pullBar',false);assert(W.visibleCount==80 and not W.rowPool[81].row.shown)
print('PASS: absorbed focus/friendly sources, pet toggle, Tank%/raw/native secret text, readable pull line and 81-row pool, report isolation, warning edges/roles/protection, persisted menu and preview lifecycle')
""")
