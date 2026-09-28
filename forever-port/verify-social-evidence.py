"""Execute the real read-only social diagnostic with native iterator semantics."""
import os
from pathlib import Path
from lupa.lua51 import LuaRuntime

folder = Path(__file__).resolve().parent
source = (folder.parent / "EllesmereUI_Forever.lua").read_text(encoding="utf-8-sig")
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["LOCALAPPDATA"]) / "Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns"))

def between(text, first, last):
    start = text.index(first)
    return text[start:text.index(last, start)]

helper = between(source, "local function DiagnosticValue(value)", "local function WindowEvidence(lines)")
scroll = (native / "Blizzard_SharedXML/Shared/Scroll/ScrollBox.lua").read_text(encoding="utf-8-sig")
view = (native / "Blizzard_SharedXML/Shared/Scroll/ScrollBoxListView.lua").read_text(encoding="utf-8-sig")
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
ScrollBoxListMixin={}; ScrollBoxListViewMixin={}
privateReads=0; writes=0; geometryReads=0
function forbidden()
 privateReads=privateReads+1; error('identity/message/private data access forbidden')
end
function mutation()
 writes=writes+1; error('diagnostics mutated native state')
end
local secretMT={__eq=forbidden,__lt=forbidden,__le=forbidden,__add=forbidden,
 __sub=forbidden,__mul=forbidden,__div=forbidden,__mod=forbidden,__tostring=forbidden,__concat=forbidden}
function opaque() return setmetatable({_secret=true},secretMT) end
function issecretvalue(value) return type(value)=='table' and rawget(value,'_secret')==true end
local optional={IsVisible=true,GetID=true,GetTabID=true,GetAlpha=true,GetFrameLevel=true,GetRect=true,GetDataProvider=true,
 EnumerateFrames=true,ScrollBox=true,FriendsDisabledText=true,UnavailableLabel=true,
 UnavailableInfoFrame=true,selectedTab=true,GetTabButton=true}
function readonly(methods)
 return setmetatable({}, {
  __index=function(_,key)
   if methods[key]~=nil then return methods[key] end
   if optional[key] then return nil end
   if key:match('^Set') or key=='Show' or key=='Hide' or key=='Click' or key=='Refresh' then return mutation end
   error('unexpected/private field read: '..key)
  end,
  __newindex=mutation,
 })
end
function frame(config,extra)
 config=config or {}; local m=extra or {}
 m.IsShown=function() geometryReads=geometryReads+1; if config.shown==nil then return true end; return config.shown end
 if not config.minimal then
  m.IsVisible=function() if config.visible==nil then return config.shown~=false end; return config.visible end
  m.GetID=m.GetID or function() return config.id or 0 end
  if config.tabID~=nil then m.GetTabID=function() return config.tabID end end
  if config.alpha~=nil then m.GetAlpha=function() return config.alpha end end
  m.GetFrameLevel=function() return config.level or 10 end
  m.GetRect=function() return unpack(config.rect or {30,40,300,400}) end
 end
 return readonly(m)
end
local forbiddenProviderFields={GetCollection=true,Enumerate=true,EnumerateEntireRange=true,
 FindElementDataByPredicate=true,GetElementData=true,Flush=true,Insert=true,Remove=true}
function provider(count)
 return setmetatable({}, {__index=function(_,key)
  if key=='GetSize' then return function() return count end end
  if forbiddenProviderFields[key] then return forbidden end
  error('unexpected provider access: '..key)
 end,__newindex=mutation})
end
function setup(count,rows,scrollConfig)
 local data=provider(count)
 local nativeView={GetFrames=function() return rows end}
 setmetatable(nativeView,{__index=ScrollBoxListViewMixin,__newindex=mutation})
 local sb=frame(scrollConfig,{
  GetDataProvider=function() return data end,
  GetView=function() return nativeView end,
  EnumerateFrames=ScrollBoxListMixin.EnumerateFrames,
 })
 FriendsFrame=frame({id=0},{selectedTab=2})
 -- Camelot's real names deliberately differ from their numeric tab IDs.
 FriendsFrameTab1=frame({id=1}); FriendsFrameTab2=nil
 FriendsFrameTab3=frame({id=2,rect={345,12,74,26}})
 FriendsFrameTab4=frame({id=3,shown=false,visible=false})
 FriendsListFrame=frame({}, {ScrollBox=sb,FriendsDisabledText=frame({shown=false,visible=false,minimal=true})})
 RecentAlliesFrame=frame({shown=false}); RecruitAFriendFrame=frame({shown=false})
 RaidFrame=frame({shown=true}); QuickJoinFrame=frame({shown=false})
 FriendsFrameBattlenetFrame=readonly({UnavailableLabel=frame({shown=true,minimal=true}),
  UnavailableInfoFrame=frame({shown=false})})
 -- Native TabSystemButtonMixin stores its ID separately from Frame:GetID().
 local tabs={[10]=frame({id=0,tabID=10}),[23]=frame({id=0,tabID=23,shown=false}),[54]=frame({id=0,tabID=54,shown=false})}
 FriendsTabHeader={friendsTabID=10,recentAlliesTabID=23,recruitAFriendTabID=54,
  TabSystem=readonly({GetTabButton=function(_,id) assert(tabs[id]); return tabs[id] end})}
 BNConnected=function() return true end
 C_FriendList={IsLegacyFriendSystemEnabled=function() return true end,
  GetFriendInfoByIndex=forbidden,GetSelectedFriend=forbidden,AddFriend=mutation,RemoveFriend=mutation}
 C_SocialRestrictions={IsFriendsDisabled=function() return false end}
 C_BattleNet={GetFriendAccountInfo=forbidden,GetAccountInfoByID=forbidden}
 BNGetInfo=forbidden; BNGetFriendInfo=forbidden; BNGetFriendInfoByID=forbidden
 BNSendWhisper=mutation; SendChatMessage=mutation; FriendsList_Update=mutation
 return sb
end
function has(report,text) return report:find(text,1,true)~=nil end
''')
lua.execute(between(scroll, "function ScrollBoxListMixin:EnumerateFrames()", "function ScrollBoxListMixin:ReinitializeFrames()"))
lua.execute(between(view, "function ScrollBoxListViewMixin:EnumerateFrames()", "function ScrollBoxListViewMixin:FindFrame("))
lua.execute(helper + "\nfunction Evidence() local lines={}; SocialEvidence(lines); return table.concat(lines,'\\n') end")
lua.execute(r'''
-- No panel: no UI is loaded or opened, and no ancillary API is queried.
FriendsFrame=nil; BNConnected=forbidden
assert(Evidence()=='')

setup(0,{})
local empty=Evidence()
assert(has(empty,'Social native provider rows=0'))
assert(not has(empty,'Social first rendered row'))
assert(has(empty,'FriendsFrameTab3 shown=true visible=true id=2'))
assert(has(empty,'FriendsFrameTab4 shown=false visible=false id=3'))
assert(not has(empty,'FriendsFrameTab2'))
assert(has(empty,'Social selected bottom tab=2'))
assert(has(empty,'Social header recentAlliesTabID shown=false visible=false id=23'))
assert(has(empty,'Social header recruitAFriendTabID shown=false visible=false id=54'))
assert(has(empty,'Social unavailable notice shown=false visible=false')==false) -- optional IsVisible absent on label
assert(has(empty,'Social unavailable notice shown=false'))
assert(has(empty,'Social Battle.net unavailable label shown=true'))

-- Existing data + hidden frames are distinguishable from truly empty data.
local hiddenRow=frame({shown=true,visible=false,rect={0,0,300,34}}, {GetID=forbidden,GetTabID=forbidden})
setup(5,{hiddenRow},{shown=false,visible=false})
local hidden=Evidence()
assert(has(hidden,'Social native provider rows=5'))
assert(has(hidden,'Social scroll shown=false visible=false'))
assert(has(hidden,'Social first rendered row shown=true visible=false'))
assert(hidden~=empty)

-- Native ipairs iterator returns index,frame. Only first frame may be inspected;
-- neither frame data, displayed text nor provider entries may be read.
local misplaced=frame({shown=true,visible=true,rect={-9000,-8000,300,34},level=13}, {GetID=forbidden,GetTabID=forbidden})
local second=readonly({IsShown=forbidden})
setup(5,{misplaced,second},{shown=true,visible=true,rect={20,30,320,350}})
local offset=Evidence()
assert(has(offset,'Social first rendered row shown=true visible=true level=13 rect=-9000,-8000,300,34'))
assert(has(offset,'Social scroll shown=true visible=true level=10 rect=20,30,320,350'))
assert(offset~=hidden)
local _,first=offset:find('Social first rendered row',1,true)
assert(not offset:find('Social first rendered row',first+1,true),'more than one row logged')

-- No Lua tostring/arithmetic/comparison is permitted on protected values.
local s=opaque()
setup(s,{frame({shown=s,visible=s,alpha=s,level=s,rect={s,s,s,s}}, {GetID=forbidden,GetTabID=forbidden})})
FriendsFrame=frame({shown=s,visible=s,alpha=s,level=s,rect={s,s,s,s}},{selectedTab=s,GetID=forbidden,GetTabID=forbidden})
FriendsFrameTab1=frame({id=s})
BNConnected=function() return s end
local protected=Evidence()
assert(has(protected,'Social native provider rows=<protected>'))
assert(has(protected,'Social selected bottom tab=<protected>'))
assert(has(protected,'shown=<protected> visible=<protected> alpha=<protected> level=<protected> rect=<protected>,<protected>,<protected>,<protected>'))
assert(has(protected,'FriendsFrameTab1 shown=true visible=true id=<protected>'))
assert(not has(protected,'table:'))

-- Alpha-hidden rows can still report shown/visible true; preserve that distinction.
setup(5,{frame({shown=true,visible=true,alpha=0})})
assert(has(Evidence(),'Social first rendered row shown=true visible=true alpha=0'))

-- Partly exposed beta APIs and missing child panels are optional, not errors.
setup(0,{})
BNConnected=nil; C_FriendList={}; C_SocialRestrictions=nil
FriendsFrame=frame({minimal=true})
FriendsFrameTab1=nil; FriendsFrameTab3=nil; FriendsFrameTab4=nil
FriendsListFrame=frame({minimal=true},{ScrollBox=frame({minimal=true})})
RecentAlliesFrame=nil; RecruitAFriendFrame=nil; RaidFrame=nil; QuickJoinFrame=nil
FriendsFrameBattlenetFrame=nil; FriendsTabHeader={TabSystem={}}
local partial=Evidence()
assert(has(partial,'Social window shown=true') and has(partial,'Social scroll shown=true'))
assert(not has(partial,'provider rows=') and not has(partial,'Battle.net connected'))
FriendsListFrame=nil; FriendsTabHeader=nil
assert(Evidence()=='Social window shown=true\nSocial selected bottom tab=nil')

assert(privateReads==0 and writes==0,'diagnostic touched protected/private state or mutated frames')
''')
print("PASS social evidence: real native row iterator, sparse actual tab IDs, provider counts, hidden/mispositioned rows, optional beta APIs/panels, secret formatting, no identity/message reads or native mutations")
