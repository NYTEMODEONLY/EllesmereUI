"""Regression fixtures for Camelot Friends tab identities and layout ownership.

Runs extracted production Lua with a small anchor resolver and real native tab
click method. No game connection, social data or actions. Live rendering remains
separate from these geometry/lifecycle checks.
"""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT.parent / 'EllesmereUIFriends/EllesmereUIFriends.lua').read_text(encoding='utf-8')
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_FriendsFrame/Camelot'
native_source = (native / 'FriendsFrame.lua').read_text(encoding='utf-8')

def part(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]

tabs = part(source, '    -- Restyle Blizzard\'s tabs in-place', '\n    GetFFD(frame).updateCustomTabs =')
layout = part(source, '    local TAB_H = 26', '\n    local closeBtn = frame.CloseButton')
headers = part(source, '        local function UpdateSubTabWidths()', '\n        GetFFD(frame).updateSubTabs =')
status = part(source, '    -- BattleNet ID bar reskin', '\n    -- UnitIsDND/UnitIsAFK')
ignore = part(source, '    if frame.IgnoreListWindow then', '\n    if _G.RaidInfoFrame then')
overlay = part(source, '    -- Border/bg live on frames we own', '\n    -- Bottom buttons:')
recruit = part(source, '    local contactsHeaderOffset =', '\n    if frame.NineSlice then')
click = part(native_source, 'function FriendsFrameTabMixin:OnClick()', '\nfunction FriendsListFrame_OnShow')
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true; FRIEND_TAB_RAID=2; FRIEND_TAB_QUICK_JOIN=3
PP={mult=1,DisablePixelSnap=function() end,CreateBorder=function() end}
EG={r=.1,g=.8,b=.6}; EllesmereUI={RegAccent=function() end}
EBS={db={profile={friends={enabled=true,accentColors=true}}}}
FRAME_BG_R=.05; FRAME_BG_G=.05; FRAME_BG_B=.05
timers={}; FFD={}; combat=false; queued=0
function GetFFD(f) if not FFD[f] then FFD[f]={} end; return FFD[f] end
function QueueApplyAll() queued=queued+1 end
function InCombatLockdown() return combat end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function flush() local q=timers; timers={}; for _,fn in ipairs(q) do fn() end end
function hooksecurefunc(obj,key,fn)
 if type(obj)=='string' then local old=_G[obj]; local after=key; _G[obj]=function(...) old(...); after(...) end
 else local old=obj[key]; obj[key]=function(...) old(...); fn(...) end end
end
function region()
 local r={shown=true,alpha=1,text='Native'}
 function r:SetText(s) self.text=s end
 function r:GetText() return self.text end
 function r:GetStringWidth() return #self.text*6 end
 function r:SetFont() end
 function r:SetTextColor(...) self.color={...} end
 function r:SetPoint(...) self.point={...} end
 function r:ClearAllPoints() self.point=nil end
 function r:SetAllPoints() end
 function r:SetColorTexture(...) self.fill={...} end
 function r:SetTexture(s) self.texture=s end
 function r:SetAtlas(s) self.atlas=s end
 function r:SetHeight(h) self.h=h end
 function r:SetWidth(w) self.w=w end
 function r:SetSize(w,h) self.w=w; self.h=h end
 function r:SetBlendMode() end
 function r:SetJustifyH() end
 function r:SetDrawLayer() end
 function r:SetParent(f) self.parent=f end
 function r:SetAlpha(a) self.alpha=a end
 function r:SetShown(v) self.shown=v end
 function r:Show() self.shown=true end
 function r:Hide() self.shown=false end
 return r
end
function obj(id,shown)
 local f={id=id,shown=shown~=false,w=72,h=26,alpha=1,enabled=true,mouse=true,scripts={},hooks={},points={},level=2,label=region()}
 function f:GetID() return self.id end
 function f:IsShown() return self.shown end
 function f:IsEnabled() return self.enabled end
 function f:Show() self.shown=true; if self.hooks.OnShow then self.hooks.OnShow() end end
 function f:Hide() self.shown=false; if self.hooks.OnHide then self.hooks.OnHide() end end
 function f:SetShown(v) if v then self:Show() else self:Hide() end end
 function f:HookScript(e,fn) self.hooks[e]=fn end
 function f:GetFontString() return self.label end
 function f:GetRegions() return end
 function f:GetHighlightTexture() return nil end
 function f:CreateTexture() return region() end
 function f:CreateFontString() return region() end
 function f:SetPushedTextOffset() end
 function f:SetHeight(h) self.h=h end
 function f:SetWidth(w) self.w=w end
 function f:SetSize(w,h) self.w=w; self.h=h end
 function f:ClearAllPoints() self.points={} end
 function f:SetPoint(...) self.points[#self.points+1]={...} end
 function f:GetWidth()
  if self==FriendsFrame then return self.w end
  local a=self.points[1]; local b=self.points[2]
  if a and b and b[1]=='RIGHT' then return b[2]:GetRight()+b[4]-self:GetLeft() end
  return self.w
 end
 function f:GetLeft()
  if self==FriendsFrame or self==FriendsListFrame then return 0 end
  local a=self.points[1]; if not a then return 0 end
  local rel=a[2]; local right=a[3]=='TOPRIGHT' or a[3]=='RIGHT'
  return (right and rel:GetRight() or rel:GetLeft())+(a[4] or 0)
 end
 function f:GetRight() return self:GetLeft()+self:GetWidth() end
 function f:GetFrameLevel() return self.level end
 function f:SetFrameLevel(v) self.level=v end
 function f:SetFrameStrata(v) self.strata=v end
 function f:SetParent(p) self.parent=p end
 function f:SetAlpha(v) self.alpha=v end
 function f:EnableMouse(v) self.mouse=v end
 return f
end
function CreateFrame(_,_,parent) local f=obj(); f.parent=parent; return f end
function StripTextures(f) f.chromeStripped=true end
function PanelTemplates_GetSelectedTab(f) return f.selectedTab end
function PanelTemplates_UpdateTabs() end
function PanelTemplates_Tab_OnClick(tab,f) f.selectedTab=tab:GetID(); PanelTemplates_UpdateTabs(f) end
function FriendsFrame_OnShow() nativeShows=(nativeShows or 0)+1 end
FriendsFrameTabMixin={}
frame=obj(); FriendsFrame=frame; frame.w=345; frame.numTabs=3; frame.selectedTab=1
FriendsListFrame=obj(); FriendsListFrame.level=frame.level+1
FriendsTabHeader={GetTab=function() return headerSelection or 1 end}
FriendsFrameTab1=obj(1); FriendsFrameTab3=obj(2); FriendsFrameTab4=obj(3,false)
FriendsFrameTab1.label.text='Contacts'; FriendsFrameTab3.label.text='Raid'; FriendsFrameTab4.label.text='Quick Join'
frame.IgnoreListWindow=obj(); frame.IgnoreListWindow.parent=frame
''')
lua.execute(click)
lua.execute(r'''
FriendsFrameTab1.OnClick=FriendsFrameTabMixin.OnClick
FriendsFrameTab3.OnClick=FriendsFrameTabMixin.OnClick
FriendsFrameTab4.OnClick=FriendsFrameTabMixin.OnClick
''')
lua.execute(tabs + '\nALL_TABS=customTabs; RefreshTabs=UpdateCustomTabs\n' + layout)
lua.execute(r'''
assert(#ALL_TABS==3 and ALL_TABS[2]==FriendsFrameTab3 and ALL_TABS[3]==FriendsFrameTab4)
assert(FriendsFrameTab1:GetWidth()==172.5 and FriendsFrameTab3:GetLeft()==172.5 and FriendsFrameTab3:GetRight()==345)
assert(not FriendsFrameTab4.shown and FriendsFrameTab3.OnClick==FriendsFrameTabMixin.OnClick)
FriendsFrameTab3:OnClick(); flush()
assert(frame.selectedTab==2 and GetFFD(FriendsFrameTab3).underline.shown and not GetFFD(FriendsFrameTab1).underline.shown)
FriendsFrameTab4:Show(); flush()
assert(FriendsFrameTab1:GetWidth()==115 and FriendsFrameTab3:GetLeft()==115 and FriendsFrameTab4:GetLeft()==230 and FriendsFrameTab4:GetRight()==345)
FriendsFrameTab4:OnClick(); flush(); assert(frame.selectedTab==3 and GetFFD(FriendsFrameTab4).underline.shown)
FriendsFrameTab3:Hide(); flush(); assert(FriendsFrameTab4:GetLeft()==172.5 and not FriendsFrameTab3.shown)
FriendsFrameTab4:Hide(); flush(); assert(FriendsFrameTab1:GetWidth()==345)
frame.w=420; frame:Show(); flush(); assert(FriendsFrameTab1:GetWidth()==420)
combat=true; FriendsFrameTab3:Show(); flush(); assert(queued==1 and not GetFFD(FriendsFrameTab3).lastLayout)
combat=false; GetFFD(frame).layoutCustomTabs(); assert(FriendsFrameTab1:GetWidth()==210 and FriendsFrameTab3:GetRight()==420)
assert(frame.selectedTab==3 and EBS.db.profile.friends.enabled==true)
''')
lua.execute(r'''
customSubTabs={}; contactsHeaderOffset=30; frame.selectedTab=1
for i=1,4 do local ct=obj(); ct._label=region(); ct._label.text='Section'..i; customSubTabs[i]=ct end
nativeHeaders={obj(1),obj(2,false),obj(3,false)}
for i=1,3 do GetFFD(customSubTabs[i]).nativeTab=nativeHeaders[i] end
''')
lua.execute(headers + '\nLayoutHeaders=UpdateSubTabWidths')
lua.execute(r'''
LayoutHeaders()
assert(customSubTabs[1].shown and not customSubTabs[2].shown and not customSubTabs[3].shown and customSubTabs[4].shown)
assert(customSubTabs[4].points[1][2]==customSubTabs[1] and customSubTabs[1].points[1][5]==-100)
nativeHeaders[2]:Show(); LayoutHeaders(); assert(customSubTabs[2].shown and customSubTabs[4].points[1][2]==customSubTabs[2])
frame.selectedTab=2; LayoutHeaders(); for _,ct in ipairs(customSubTabs) do assert(not ct.shown) end
assert(nativeHeaders[1].shown and nativeHeaders[2].shown and not nativeHeaders[3].shown)
''')

lua.execute(r'''
FriendsFrameStatusDropdown=obj(); local bnet=obj(); FriendsFrameBattlenetFrame=bnet
bnet.Tag=region(); bnet.UnavailableLabel=region(); bnet.UnavailableLabel.shown=true
bnet.UnavailableInfoButton=obj(); bnet.UnavailableInfoFrame=obj(0,false); bnet.BroadcastFrame=obj(0,false)
bnet.ContactsMenuButton=obj(); bnet.BroadcastFrame.parent=bnet; bnet.BroadcastFrame.scripts.OnShow=function() end
bnet.h=29
''')
lua.execute(status + ignore + overlay)
lua.execute(r'''
local b=FriendsFrameBattlenetFrame
assert(b.h==29 and b.points[1][1]=='TOP' and b.points[1][5]==-30)
assert(b.Tag.alpha==0 and b.UnavailableLabel.alpha==1 and b.UnavailableLabel.shown)
assert(b.UnavailableInfoButton.mouse and b.UnavailableInfoButton.alpha==1)
assert(not b.UnavailableInfoFrame.shown and b.UnavailableInfoFrame.alpha==1)
assert(b.ContactsMenuButton.mouse and b.BroadcastFrame.mouse and b.BroadcastFrame.parent==b and not b.BroadcastFrame.shown)
assert(FriendsFrameStatusDropdown.alpha==1 and FriendsFrameStatusDropdown.mouse)
assert(frame.IgnoreListWindow.parent==frame)
assert(GetFFD(frame).listOverlay.level<FriendsListFrame.level)
assert(GetFFD(frame).listOverlay.points[1][5]==-122)
-- The separate BNet row spans y30..59; invite field y70, sections y100,
-- and list y122 leave actual warning/help text clear of the custom controls.
assert(-b.points[1][5]+b.h < 40+contactsHeaderOffset)
''')

lua.execute(r'''
timers={}; p=EBS.db.profile.friends; RecruitAFriendFrame=nil
function LegacyFriendsRetired() return false end
local baseCreate=CreateFrame
function CreateFrame(...)
 local f=baseCreate(...); f.events={}
 function f:RegisterEvent(e) self.events[e]=true end
 function f:UnregisterEvent(e) self.events[e]=nil end
 function f:SetScript(e,fn) self.scripts[e]=fn end
 loader=f; return f
end
''')
lua.execute(recruit)
lua.execute(r'''
assert(loader.events.ADDON_LOADED)
loader.scripts.OnEvent(loader,'ADDON_LOADED','Unrelated'); flush(); assert(RecruitAFriendFrame==nil)
RecruitAFriendFrame=obj(); RecruitAFriendFrame.parent=frame; RecruitAFriendFrame.shown=false
RecruitAFriendFrame.scripts.OnShow=function() end
local nativeShow=RecruitAFriendFrame.scripts.OnShow
loader.scripts.OnEvent(loader,'ADDON_LOADED','Blizzard_RecruitAFriend'); flush()
local raf=RecruitAFriendFrame
assert(not loader.events.ADDON_LOADED and raf.parent==frame and not raf.shown and raf.scripts.OnShow==nativeShow)
assert(raf.points[1][4]==11 and raf.points[1][5]==-39 and raf.points[2][4]==-8)
assert(-raf.points[1][5]+83==122,'native RAF content overlapped contacts header')
raf:Show(); flush(); assert(raf.points[1][5]==-39 and raf.scripts.OnShow==nativeShow)
combat=true; raf:ClearAllPoints(); GetFFD(frame).fitForeverRecruit(); assert(#raf.points==0)
combat=false; GetFFD(frame).fitForeverRecruit(); assert(#raf.points==2)
p.enabled=false; raf:ClearAllPoints(); GetFFD(frame).fitForeverRecruit(); assert(#raf.points==0); p.enabled=true
''')

lua.eval('function(s) local f,e=loadstring(s); assert(f,e) end')(source)
assert 'local who = not EUI_FOREVER and WhoFrame' in source
assert 'if lastSubTab and not EUI_FOREVER then' in source
assert 'info.id == tabHeader.recruitAFriendTabID' in source
assert 'local raidTabID = EUI_FOREVER and FRIEND_TAB_RAID or 3' in source
assert 'C_Timer.After(0, GetFFD(frame).updateSubTabs)' in source
print('PASS: sparse Camelot globals/IDs, visible-tab geometry/resize/combat, native clicks, gated header proxies, native status/warnings/popups, late Recruit layout, no Who takeover and wash below native text; Lua 5.1 syntax.')
