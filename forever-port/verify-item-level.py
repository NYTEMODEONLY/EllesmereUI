"""Native-average values and inspect identity/lifecycle regressions (Lua 5.1)."""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["LOCALAPPDATA"]) / "Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns"))
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
EUI_FOREVER=true; STANDARD_TEXT_FONT='native-font'; frames={}; timers={}; requests=0; calls=0
function fail() error('addon attempted native mutation or manual inventory calculation') end
function new(parent,isNative)
 local f={parent=parent,native=isNative,shown=true,hooks={},scripts={},events={}}
 function f:IsShown() return self.shown end
 function f:IsVisible() return self.shown and (not self.parent or self.parent:IsVisible()) end
 function f:SetPoint(...) assert(not self.native); self.point={...} end
 function f:SetSize(w,h) assert(not self.native); self.width=w; self.height=h end
 function f:SetAllPoints(p) assert(not self.native); self.allPoints=p end
 function f:SetParent() fail() end
 function f:EnableMouse(v) assert(not self.native); self.mouse=v end
 function f:CreateFontString() assert(not self.native); return new(self) end
 function f:SetJustifyH(v) self.justify=v end
 function f:SetJustifyV(v) self.justifyV=v end
 function f:SetWordWrap(v) self.wrap=v end
 function f:SetFont(...) self.font={...} end
 function f:SetText(v) self.text=v end
 function f:HookScript(k,fn) self.hooks[k]=fn end
 function f:SetScript(k,fn) assert(not self.native); self.scripts[k]=fn end
 function f:RegisterEvent(k) self.events[k]=true end
 function f:Show()
  assert(not self.native or nativeAction); self.shown=true
  if self.hooks.OnShow then self.hooks.OnShow(self) end
 end
 function f:Hide()
  assert(not self.native or nativeAction); self.shown=false
  if self.hooks.OnHide then self.hooks.OnHide(self) end
 end
 return f
end
function CreateFrame(_,_,parent) local f=new(parent); frames[#frames+1]=f; return f end
function hooksecurefunc(name,fn)
 local original=_G[name]
 _G[name]=function(...) local result={original(...)}; fn(...); return unpack(result) end
end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function flush() local q=timers; timers={}; for _,fn in ipairs(q) do fn() end end
function event(name,arg) for _,f in ipairs(frames) do if f.events[name] then f.scripts.OnEvent(f,name,arg) end end end
styles={}; W={Theme={accR=.1,accG=.8,accB=.6}}
function W.GetStyle(key) return styles[key] or 'full' end
function W.Font(fs,...) fs.color={...} end
function W.OnLooksChanged(fn) W.looks=fn end
ns={WSkin=W}
PaperDollFrame=new(nil,true); PaperDollItemsFrame=new(PaperDollFrame,true)
CharacterModelScene={ControlFrame=new(PaperDollFrame,true)}
function characterCard() for _,f in ipairs(frames) do if f.parent==PaperDollItemsFrame then return f end end end
function inspectCard() for _,f in ipairs(frames) do if f.parent==InspectPaperDollFrame then return f end end end
function inspectText(card)
 assert(card.label.text=='Equipped' and card.value,'inspect value must have a separate FontString')
 assert(not card.value.text:find('\n',1,true),'inspect value must occupy one line')
 return card.label.text..'\n'..card.value.text
end
local secretMT={__tostring=fail,__eq=fail,__lt=fail,__le=fail,__add=fail,__sub=fail,__div=fail,__mul=fail}
function secret() return setmetatable({_secret=true},secretMT) end
function issecretvalue(v) return type(v)=='table' and rawget(v,'_secret')==true end
overall=26.876; equipped=18.125; inspectLevel=42.375; targetGUID='A'; focusGUID='B'
function GetAverageItemLevel() calls=calls+1; return overall,equipped,1000 end
function UnitGUID(unit) if unit=='target' then return targetGUID elseif unit=='focus' then return focusGUID end end
C_PaperDollInfo={GetInspectItemLevel=function(unit)
 assert(unit==InspectFrame.unit); return inspectLevel
end}
function NotifyInspect(unit) assert(nativeAction,'addon sent inspect request'); requests=requests+1 end
ClearInspectPlayer=fail; GetInventoryItemLink=fail; GetInventoryItemID=fail
C_Container={GetContainerNumSlots=fail,GetContainerItemInfo=fail}
GameTooltip={lines={}}
function GameTooltip:SetOwner(owner) self.owner=owner; self.lines={} end
function GameTooltip:IsOwned(owner) return self.owner==owner end
function GameTooltip:SetText(v) self.title=v end
function GameTooltip:AddLine(v) table.insert(self.lines,v) end
function GameTooltip:Show() self.shown=true end
function GameTooltip:Hide() self.shown=false; self.owner=nil end
STAT_AVERAGE_ITEM_LEVEL_TOOLTIP='Native localized overall-average explanation.'
''')
source = root.parent / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverItemLevel.lua"
lua.execute('assert(loadstring(...))("test",ns)', source.read_text(encoding="utf-8"))
lua.execute(r'''
flush()
local card=characterCard(); assert(card and card:IsVisible())
assert(card.label.text=='Equipped 18.12   |   Overall 26.88','native return order or precision wrong')
assert(card.parent==PaperDollItemsFrame and card.point[2]==CharacterModelScene.ControlFrame)
assert(card.point[3]=='BOTTOM' and card.point[5]==-2 and card.height==14)
assert(card.width==280 and card.label.wrap==false)
card.scripts.OnEnter(card)
assert(GameTooltip.lines[2]==STAT_AVERAGE_ITEM_LEVEL_TOOLTIP)
card.scripts.OnLeave(card); assert(not GameTooltip.shown)
-- Native whole-account average is authoritative: bag events repaint exact values,
-- and must never scan duplicate gear or invent a minimum-floor correction.
equipped=0; overall=7.5; event('BAG_UPDATE_DELAYED'); flush()
assert(card.label.text=='Equipped 0.00   |   Overall 7.50')
equipped=11.876; overall=25.001; event('PLAYER_AVG_ITEM_LEVEL_UPDATE'); flush()
assert(card.label.text=='Equipped 11.88   |   Overall 25.00')
local oldcalls=calls; event('UNIT_INVENTORY_CHANGED','party1'); flush(); assert(calls==oldcalls)
event('UNIT_INVENTORY_CHANGED','player'); flush(); assert(calls>oldcalls)
equipped=secret(); overall=secret(); event('PLAYER_EQUIPMENT_CHANGED'); flush()
assert(card.label.text=='Equipped Unavailable   |   Overall Unavailable')
equipped=nil; overall=nil; event('ITEM_DATA_LOAD_RESULT'); flush()
assert(card.label.text=='Equipped Loading...   |   Overall Loading...')
equipped=0/0; overall=math.huge; event('GET_ITEM_INFO_RECEIVED'); flush()
assert(card.label.text=='Equipped Unavailable   |   Overall Unavailable')
local original=GetAverageItemLevel; GetAverageItemLevel=nil; ns.ForeverItemLevel()
assert(card.label.text=='Equipped Unavailable   |   Overall Unavailable')
GetAverageItemLevel=function() error('unsupported beta API') end; ns.ForeverItemLevel()
assert(card.label.text=='Equipped Unavailable   |   Overall Unavailable')
GetAverageItemLevel=original; equipped=18.125; overall=26.876
styles.charsheet='off'; W.looks(); assert(not card.shown)
styles.charsheet='full'; W.looks(); assert(card.shown)
nativeAction=true; PaperDollItemsFrame:Hide(); nativeAction=false
assert(not card.shown,'player averages shown in pet/other character mode')
nativeAction=true; PaperDollItemsFrame:Show(); nativeAction=false; flush(); assert(card.shown)
-- Inspect is loaded later, exactly as the real Blizzard_InspectUI addon is.
InspectFrame=new(nil,true); InspectFrame.shown=false
InspectPaperDollFrame=new(InspectFrame,true)
InspectModelFrame={controlFrame=new(InspectPaperDollFrame,true)}
function HideUIPanel(f) f:Hide(); f.unit=nil end
function CanInspect() return true end
function ShowUIPanel(f) f:Show() end
function InspectFrame:UpdateTabLayout() assert(nativeAction); self.layoutUpdated=true end
function InspectFrame:SetupModeTabs() assert(nativeAction); self.modeTabsUpdated=true end
function InspectFrame:UpdateTabs() assert(nativeAction); self.tabsUpdated=true end
INSPECTFRAME_SUBFRAMES={'InspectPaperDollFrame'}; INSPECT_MODE_TAB_FRAMES={}
function PanelTemplates_GetSelectedTab() return 1 end
function PanelTemplates_SetTab(frame,id) assert(nativeAction); frame.selectedTab=id end
event('ADDON_LOADED','Blizzard_InspectUI'); flush()
''')
# Actual Camelot request/tab switch keeps the window hidden until its OnEvent
# receives a matching INSPECT_READY. Exercise both native/addon event orders.
inspect = (native / "Blizzard_InspectUI/Camelot/Blizzard_InspectUI.lua").read_text(encoding="utf-8-sig")
lua.execute('InspectFrameMixin={}')
start = inspect.index("function InspectFrame_Show(unit)")
lua.execute(inspect[start:inspect.index("function InspectFrameMixin:OnLoad", start)])
start = inspect.index("function InspectFrameMixin:OnEvent(")
lua.execute(inspect[start:inspect.index("function InspectFrameMixin:UnitChanged", start)])
start = inspect.index("function InspectSwitchTabs(")
lua.execute(inspect[start:inspect.index("function InspectFrameTab_OnClick", start)])
lua.execute(r'''
function nativeEvent(name,arg,addonFirst)
 nativeAction=true
 if addonFirst then event(name,arg) end
 InspectFrameMixin.OnEvent(InspectFrame,name,arg)
 if not addonFirst then event(name,arg) end
 nativeAction=false
end
nativeAction=true; InspectFrame_Show('target'); nativeAction=false; flush()
assert(not InspectFrame:IsVisible() and not inspectCard(),'summary opened the panel before native INSPECT_READY')
assert(InspectFrame.layoutUpdated and InspectFrame.modeTabsUpdated)
nativeEvent('INSPECT_READY','B'); flush(); assert(not inspectCard(),'wrong GUID opened inspect')
nativeEvent('INSPECT_READY','A',true); flush()
local card=inspectCard(); assert(card and card:IsVisible() and inspectText(card)=='Equipped\n42.38')
assert(requests==1 and card.point[2]==InspectModelFrame.controlFrame and card.point[5]==-4)
assert(card.width==60 and card.height==26 and card.label.font[2]==10,'inspect summary escaped narrow center lane')
assert(card.label.width==60 and card.label.height==12 and card.label.point[2]==card)
assert(card.value.width==60 and card.value.height==14 and card.value.font[2]==10)
assert(card.value.point[2]==card.label and card.value.point[3]=='BOTTOM')
assert(card.label.height+card.value.height==card.height,'inspect rows clip outside the summary')
assert(card.value.wrap==false and card.value.justifyV=='MIDDLE')
assert(InspectFrame.tabsUpdated)
assert(not inspectText(card):find('Overall',1,true),'inspect leaked local overall average')
card.scripts.OnEnter(card); assert(#GameTooltip.lines==1 and GameTooltip.lines[1]:find('not available',1,true))
-- Same character requested again: the old value must vanish before data arrives.
nativeAction=true; NotifyInspect('target'); nativeAction=false
assert(not card.shown); flush(); assert(inspectText(card)=='Equipped\nLoading...')
nativeEvent('INSPECT_READY','A'); flush(); assert(inspectText(card)=='Equipped\n42.38')
-- Different identity, then out-of-order completion of old request.
nativeAction=true; InspectFrame_Show('focus'); nativeAction=false; flush()
nativeEvent('INSPECT_READY','A'); flush(); assert(not card:IsVisible())
inspectLevel=63.987; nativeEvent('INSPECT_READY','B'); flush(); assert(inspectText(card)=='Equipped\n63.99')
-- A unit token changes while the API executes. Never publish its old result.
local original=C_PaperDollInfo.GetInspectItemLevel
C_PaperDollInfo.GetInspectItemLevel=function() focusGUID='C'; return 999 end
ns.ForeverItemLevel(); assert(inspectText(card)=='Equipped\nLoading...')
C_PaperDollInfo.GetInspectItemLevel=original
nativeEvent('INSPECT_READY','C'); inspectLevel=secret(); flush(); assert(inspectText(card)=='Equipped\nUnavailable')
inspectLevel=0; nativeEvent('INSPECT_READY','C'); flush(); assert(inspectText(card)=='Equipped\n0.00')
-- Secret GUID/event never compared or stringified by addon code.
focusGUID=secret(); event('INSPECT_READY',secret()); flush(); assert(inspectText(card)=='Equipped\nLoading...')
focusGUID='D'; nativeEvent('GROUP_ROSTER_UPDATE'); flush(); assert(not card:IsVisible() and InspectFrame.unit==nil)
nativeAction=true; InspectFrame_Show('focus'); nativeAction=false; flush(); assert(not card:IsVisible())
nativeEvent('INSPECT_READY','D',true); flush(); assert(inspectText(card)=='Equipped\n0.00')
styles.inspect='off'; W.looks(); assert(not card.shown)
styles.inspect='full'; W.looks(); assert(card.shown)
C_PaperDollInfo={}; ns.ForeverItemLevel(); assert(inspectText(card)=='Equipped\nUnavailable')
nativeAction=true; InspectFrame:Hide(); nativeAction=false; assert(not card.shown)
assert(requests==4,'addon initiated an inspect request')
local lines={}; local oldcalls=calls; ns.ForeverItemLevelEvidence(lines)
assert(calls==oldcalls and #lines==3,'diagnostics queried live inventory')
assert(lines[1]=='Native item-level APIs: player=true inspect=false')
assert(lines[3]=='Item-level summary inspect: visible=false last rendered=Equipped / Unavailable')
''')
# Check the authoritative geometry used for the reserved character summary band.
import xml.etree.ElementTree as ET
def element(path, tag, name):
    tree = ET.parse(native / path)
    return next(e for e in tree.iter() if e.tag.endswith('}'+tag) and e.get('name') == name)
control = element("Blizzard_SharedXML/ModelSceneControlFrame.xml", "Frame", "ModelSceneControlFrameTemplate")
size = next(e for e in control if e.tag.endswith('}Size'))
paper = ET.parse(native / "Blizzard_UIPanels_Game/Camelot/PaperDollFrame.xml")
model = next(e for e in paper.iter() if e.get('name') == "CharacterModelScene")
control_ref = next(e for e in model.iter() if e.get('parentKey') == "ControlFrame")
control_anchor = next(e for e in control_ref.iter() if e.tag.endswith('}Anchor'))
head = next(e for e in paper.iter() if e.get('name') == "CharacterHeadSlot")
head_anchor = next(e for e in head.iter() if e.tag.endswith('}Anchor'))
bottom = float(control_anchor.get('y')) - float(size.get('y')) - 2 - 14
assert bottom > float(head_anchor.get('y')), "summary overlaps first native equipment row"
# Inspect has no wide reserved band: its annotation lanes flank the model.
# Resolve native XML geometry and the production equipment adapter's lane width.
import re
shared = "Blizzard_SharedXML/Mainline/SharedUIPanelTemplates.xml"
base_frame = element(shared, "Frame", "PortraitFrameBaseTemplate")
window_width = float(next(e for e in base_frame if e.tag.endswith('}Size')).get('x'))
button_frame = element(shared, "Frame", "ButtonFrameTemplate")
inset = next(e for e in button_frame.iter() if e.get('parentKey') == "Inset")
inset_points = {e.get('point'): e for e in inset.iter() if e.tag.endswith('}Anchor')}
inspect_xml = "Blizzard_InspectUI/Camelot/InspectPaperDollFrame.xml"
head = element(inspect_xml, "ItemButton", "InspectHeadSlot")
hands = element(inspect_xml, "ItemButton", "InspectHandsSlot")
head_point = next(e for e in head.iter() if e.tag.endswith('}Anchor'))
hands_point = next(e for e in hands.iter() if e.tag.endswith('}Anchor'))
model = element(inspect_xml, "PlayerModel", "InspectModelFrame")
model_size = next(e for e in model if e.tag.endswith('}Size'))
model_point = next(e for e in model.iter() if e.tag.endswith('}Anchor'))
center = float(model_point.get('x')) + float(model_size.get('x')) / 2
equipment = (root.parent / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverEquipment.lua").read_text(encoding="utf-8-sig")
lane = float(re.search(r'local width = (\d+)', equipment).group(1))
offset = float(re.search(r'local side, anchor, offset = "LEFT", "RIGHT", (\d+)', equipment).group(1))
card_width = lua.eval('inspectCard().width')
for slot_width in (37, 40):  # built-in ItemButton dimensions; test both native-sized fixtures
    lane_left = float(inset_points['TOPLEFT'].get('x')) + float(head_point.get('x')) + slot_width + offset + lane
    lane_right = window_width + float(inset_points['BOTTOMRIGHT'].get('x')) + float(hands_point.get('x')) - slot_width - offset - lane
    assert center - card_width / 2 > lane_left and center + card_width / 2 < lane_right, "inspect summary/hover frame covers armor annotations"
print("PASS item-level: native averages/2 decimals, bag/gear/data events, Camelot delayed panel show/both event orders/GUID races, missing/secret APIs, zero/loading, modes/styles, character band and narrow inspect lane")
