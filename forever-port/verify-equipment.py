"""Equipment annotations against native-like read-only slots (Lua 5.1).

No live inventory/social/game access. Fixtures cover stale asynchronous data,
localized permanent enchants, secret values, native geometry/handler ownership,
and the six-pixel offhand/ranged gap. Rendering/taint require live validation.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverEquipment.lua'
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true; STANDARD_TEXT_FONT='native'; style='eui'; inspectStyle='eui'; combat=false
SECRET={}; function issecretvalue(v) return rawequal(v,SECRET) end
function InCombatLockdown() return combat end
EllesmereUI={GetFontPath=function(key) assert(key=='blizzardSkin'); return 'EUI-font' end}
EllesmereUIDB={}; Enum={TooltipDataLineType={ItemEnchantmentPermanent=15,ItemEnchantmentTemporary=16,GemSocketEnchantment=30}}
ENCHANTED_TOOLTIP_LINE='Enchanted: %s'
ITEM_QUALITY_COLORS={[2]={r=.1,g=1,b=.1},[3]={r=.1,g=.2,b=1}}
timers={}; created={}; nativeHooks={}; requests={}; inventory={}; items={}; inspectInventory={}; guids={target='Person-A',party1='Person-C'}
function UnitGUID(unit) return guids[unit] end
function GetLocale() return locale or 'enUS' end
function NotifyInspect() error('addon requested inspection') end
function ClearInspectPlayer() error('addon cleared inspection') end
function hooksecurefunc(obj,key,fn)
 if type(obj)=='string' then fn=key; key=obj; obj=_G end
 local original=obj[key]; obj[key]=function(...) local result=original(...); fn(...); return result end
end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function flush() local q=timers; timers={}; for _,fn in ipairs(q) do fn() end end
function native(id,x,w)
 local s={id=id,x=x or 0,w=w or 37,visible=true,alpha=.9,enabled=true,scripts={OnClick=function() end,OnEnter=function() end,OnDragStart=function() end}}
 function s:GetID() return self.id end
 function s:GetWidth() return self.w end
 function s:GetHeight() return 37 end
 function s:GetLeft() return self.x end
 function s:GetRight() return self.x+self.w end
 function s:GetFrameLevel() return 100 end
 function s:GetAlpha() return self.alpha end
 function s:IsEnabled() return self.enabled end
 function s:IsVisible() return self.visible end
 function s:HookScript(e,fn) nativeHooks[self]=nativeHooks[self] or {}; nativeHooks[self][e]=fn end
 for _,name in ipairs({'SetPoint','ClearAllPoints','SetAlpha','SetEnabled','Enable','Disable','Show','Hide','SetShown','SetSize','SetScript','SetParent','CreateTexture','CreateFontString'}) do
  s[name]=function() error('changed native slot/layout/state/handler: '..name) end
 end
 return s
end
PaperDollFrame=native(); PaperDollItemsFrame=native()
CharacterHeadSlot=native(1,0); CharacterHandsSlot=native(10,240)
CharacterWristSlot=native(9,0); CharacterSecondaryHandSlot=native(17,120)
CharacterRangedSlot=native(18,163); CharacterAmmoSlot=native(0,219,27); CharacterAmmoSlot.visible=false
function region(parent)
 local r={parent=parent,shown=true,alpha=1}
 function r:SetText(t) assert(not issecretvalue(t)); self.text=t end
 function r:SetFont(path,size,flags) self.font={path,size,flags} end
 function r:SetTextColor(...) self.color={...} end
 function r:SetShadowColor(...) self.shadow={...} end
 function r:SetShadowOffset() end
 function r:SetWordWrap() end
 function r:SetMaxLines() end
 function r:SetJustifyH(v) self.justify=v end
 function r:SetPoint(...) self.anchor={...} end
 function r:SetAllPoints(p) self.allPoints=p end
 function r:SetWidth(w) self.w=w end
 function r:SetSize(w,h) self.w=w; self.h=h end
 function r:SetTexture(t) assert(not issecretvalue(t)); self.texture=t end
 function r:SetAlpha(a) self.alpha=a end
 function r:Show() self.shown=true end
 function r:Hide() self.shown=false end
 function r:SetShown(v) self.shown=v end
 return r
end
function CreateFrame(_,_,parent)
 local f=region(parent); f.scripts={}; f.events={}; f.children={}; f.fonts={}; f.textures={}
 function f:EnableMouse(v) self.mouse=v end
 function f:SetFrameLevel(v) self.level=v end
 function f:SetScript(e,fn) self.scripts[e]=fn end
 function f:RegisterEvent(e) self.events[e]=true end
 function f:CreateFontString() local r=region(self); self.fonts[#self.fonts+1]=r; return r end
 function f:CreateTexture() local r=region(self); self.textures[#self.textures+1]=r; return r end
 if parent and parent.children then parent.children[#parent.children+1]=f end
 created[#created+1]=f; return f
end
function event(e,...)
 for _,f in ipairs(created) do if f.events[e] then f.scripts.OnEvent(f,e,...) end end
end
function host(slot) for _,f in ipairs(created) do if f.allPoints==slot then return f end end end
function unitInventory(unit) if unit=='player' then return inventory end; return inspectInventory[guids[unit]] or {} end
function GetInventoryItemLink(unit,id) if linkError then error('unavailable') end; return unitInventory(unit)[id] end
function GetInventoryItemQuality(unit,id) local item=items[unitInventory(unit)[id]]; return item and item.quality end
C_Item={
 GetDetailedItemLevelInfo=function(link) return items[link] and items[link].level end,
 RequestLoadItemDataByID=function(id) requests[id]=(requests[id] or 0)+1 end,
 GetItemNumSockets=function(link) return items[link] and items[link].sockets or 0 end,
 GetItemGemID=function(link,index) local i=items[link]; return i and i.gems and i.gems[index] end,
 GetItemIconByID=function(id) return items[id] and items[id].icon end,
}
C_TooltipInfo={GetInventoryItem=function(unit,id)
 if tooltipError then error('unavailable tooltip') end
 local i=items[unitInventory(unit)[id]]; return i and i.tooltip
end}
GameTooltip={}
function GameTooltip:IsOwned(f) return self.owner==f end
function GameTooltip:SetOwner(f) self.owner=f end
function GameTooltip:SetText(s) assert(not issecretvalue(s)); self.text=s; self.inventory=nil end
function GameTooltip:SetInventoryItem(unit,id) self.inventory={unit,id}; self.text=nil end
function GameTooltip:Show() self.shown=true end
function GameTooltip:Hide() self.shown=false; self.owner=nil end
NS={WSkin={Theme={}}}
function NS.WSkin.GetStyle(key) return key=='inspect' and inspectStyle or style end
function NS.WSkin.WindowCallback(key,fn) assert(key=='charsheet' or key=='inspect'); return function(...) if NS.WSkin.GetStyle(key)~='off' then return fn(...) end end end
function NS.WSkin.OnLooksChanged(fn) looksChanged=fn end

wrist='item:100:321:0:0:0:0:0:0'
items[wrist]={level=12,quality=2,tooltip={lines={{type=15,leftText='|cff00ff00Enchanted: Stamina +2|r'}}}}
inventory[9]=wrist
offhand='item:101:654:0:0:0:0:0:0'; items[offhand]={level=25,quality=3,tooltip={lines={{type=15,leftText='Enchanted: Weapon'}}}}
inventory[17]=offhand
''')
lua.execute('assert(loadstring(...))("EllesmereUIBlizzardSkin", NS)', SOURCE.read_text(encoding='utf-8'))
lua.execute(r'''
local click,enter,drag=CharacterWristSlot.scripts.OnClick,CharacterWristSlot.scripts.OnEnter,CharacterWristSlot.scripts.OnDragStart
NS.ForeverEquipment()
local w=host(CharacterWristSlot); local weapon=host(CharacterSecondaryHandSlot); local hit=w.children[1]
assert(w.shown and w.fonts[1].text=='12' and w.fonts[1].color[2]==1)
assert(hit.shown and not hit.textures[1].shown)
assert(w.fonts[2].shown and w.fonts[2].text=='+2 Stam','default shows real abbreviated enchant text')
assert(w.fonts[2].color[1]==.1 and w.fonts[2].color[2]==1 and w.fonts[2].color[3]==.1,'enchant text must be green')
assert(w.fonts[1].anchor[4]==5 and w.fonts[2].anchor[4]==5,'labels too far from slot')
hit.scripts.OnEnter(hit); assert(GameTooltip.text=='|cff00ff00Enchanted: Stamina +2|r' and GameTooltip.shown)
event('GET_ITEM_INFO_RECEIVED',999,true); flush(); assert(GameTooltip.shown and GameTooltip:IsOwned(hit),'same-item refresh closed tooltip')
assert(CharacterWristSlot.scripts.OnClick==click and CharacterWristSlot.scripts.OnEnter==enter and CharacterWristSlot.scripts.OnDragStart==drag)

EllesmereUIDB.charSheetEnchantNames=true; EllesmereUIDB.charSheetItemLevelSize=20
NS.ForeverEquipment(); assert(w.fonts[2].shown and not hit.textures[1].shown and w.fonts[2].text:find('Stamina %+2'))
assert(weapon.children[1].w==37 and weapon.fonts[2].shown and weapon.fonts[2].text=='Weapon','weapon names must be visible and bounded')
assert(weapon.children[1].anchor[1]=='BOTTOM' and weapon.children[1].anchor[3]=='TOP' and weapon.children[1].anchor[4]==0)
assert(weapon.fonts[1].anchor[1]=='BOTTOM' and weapon.fonts[1].w==37 and weapon.fonts[1].font[2]<=14)
assert(weapon.fonts[1].anchor[5]==2,'weapon item level too far from slot')
assert(weapon.children[1].anchor[5]>weapon.fonts[1].anchor[5]+weapon.fonts[1].font[2],'weapon text overlaps level')

-- Cached nil tooltip never suppresses the actual enchant indicator.
items[wrist].tooltip=nil; NS.ForeverEquipment(); assert(hit.textures[1].shown and not w.fonts[2].shown)
hit.scripts.OnEnter(hit); assert(GameTooltip.inventory[2]==9)
items[wrist].tooltip={lines={{type=0,leftText='Verzaubert (+): Ausdauer +2'}}}; ENCHANTED_TOOLTIP_LINE='Verzaubert (+): %s'
event('TOOLTIP_DATA_UPDATE',123); flush(); assert(w.fonts[2].text=='Ausdauer +2')
assert(GameTooltip.shown and GameTooltip.text=='Verzaubert (+): Ausdauer +2','localized late tooltip did not refresh')
items[wrist].tooltip={lines={{type=30,leftText='Verzaubert (+): Socket bonus'},{type=16,leftText='Verzaubert (+): Temporary'}}}
NS.ForeverEquipment(); assert(hit.textures[1].shown and not w.fonts[2].shown,'socket bonus/temporary enchant treated as permanent name')

-- Sparse filled sockets must clear on swap (empty socket 1, filled socket 2).
items[wrist].sockets=2; items[wrist].gems={[2]=777}; items[777]={icon=12345}
NS.ForeverEquipment(); local gem=w.textures[1]; assert(gem.shown and gem.texture==12345)
EllesmereUIDB.charSheetItemLevelSize=24; EllesmereUIDB.charSheetEnchantSize=24
EllesmereUI._refreshCharSheetSlotLabels(); EllesmereUI._applyCharSheetTextSizes(); flush()
assert(w.fonts[1].font[2]<24 and w.fonts[2].font[2]<24,'large armor fonts were not bounded')
assert(w.fonts[1].anchor[5]+w.fonts[1].font[2]/2<=19.5)
assert(hit.anchor[5]+hit.h/2 < w.fonts[1].anchor[5]-w.fonts[1].font[2]/2)
assert(gem.anchor[5]-4.5>=-19.5,'gem row overlaps next slot')
assert(EllesmereUIDB.charSheetItemLevelSize==24 and EllesmereUIDB.charSheetEnchantSize==24,'saved font preference changed')
items[wrist].gems={}; NS.ForeverEquipment(); assert(not gem.shown,'sparse stale gem leaked')
items[wrist].gems={[2]=888}; items[888]={}
NS.ForeverEquipment(); NS.ForeverEquipment(); assert(requests[888]==1 and not gem.shown)
local plain='item:200:0:0:0:0:0:0:0'; items[plain]={level=7,quality=2}; inventory[9]=plain
items[888].icon=54321; event('ITEM_DATA_LOAD_RESULT',888,true); flush()
assert(not gem.shown and not hit.shown and w.fonts[1].text=='7','old item completion painted new equipment')
assert(not GameTooltip.shown)

-- Missing item data refreshes from current inventory; no link-specific callbacks.
items[plain].level=nil; NS.ForeverEquipment(); assert(requests[200]==1 and not w.fonts[1].shown)
items[plain].level=9; event('GET_ITEM_INFO_RECEIVED',200,true); flush(); assert(w.fonts[1].text=='9')
inventory[9]=nil; event('PLAYER_EQUIPMENT_CHANGED',9,false); flush(); assert(not w.shown)
inventory[9]=wrist; items[wrist].tooltip={lines={{type=15,leftText='Enchanted: Stamina +2'}}}; NS.ForeverEquipment()

EllesmereUIDB.charSheetColorItemLevel=false; NS.ForeverEquipment(); assert(w.fonts[1].color[1]==1 and w.fonts[1].color[2]==1)
EllesmereUIDB.charSheetItemLevelUseColor=true; EllesmereUIDB.charSheetItemLevelColor={r=.3,g=.4,b=.5}; NS.ForeverEquipment(); assert(w.fonts[1].color[1]==.3)
assert(w.fonts[2].color[1]==.1 and w.fonts[2].color[2]==1,'item-level custom color must not recolor enchants')
EllesmereUIDB.showItemLevel=false; EllesmereUIDB.showEnchants=false; EllesmereUIDB.showGems=false
NS.ForeverEquipment(); assert(not w.fonts[1].shown and not hit.shown and not gem.shown)
EllesmereUIDB={}; NS.ForeverEquipment()
style='off'; looksChanged(); assert(not w.shown and not weapon.shown)
style='eui'; looksChanged(); assert(w.shown)
PaperDollFrame.visible=false; nativeHooks[PaperDollFrame].OnHide(); assert(not w.shown)
PaperDollFrame.visible=true; nativeHooks[PaperDollFrame].OnShow(); flush(); assert(w.shown)
CharacterWristSlot.visible=false; nativeHooks[CharacterWristSlot].OnHide(); flush(); assert(not w.shown)
CharacterWristSlot.visible=true; CharacterWristSlot.enabled=false; NS.ForeverEquipment(); assert(w.alpha==.45 and not hit.mouse)
CharacterWristSlot.enabled=true
combat=true; NS.ForeverEquipment(); assert(not w.shown); combat=false; event('PLAYER_REGEN_ENABLED'); flush(); assert(w.shown)

inventory[9]=SECRET; NS.ForeverEquipment(); assert(not w.shown)
inventory[9]=wrist; items[wrist].level=SECRET; items[wrist].quality=SECRET; items[wrist].tooltip={lines={{type=15,leftText=SECRET}}}
NS.ForeverEquipment(); assert(w.shown and not w.fonts[1].shown and hit.textures[1].shown)
items[wrist].tooltip=SECRET; NS.ForeverEquipment()
tooltipError=true; NS.ForeverEquipment(); tooltipError=false
linkError=true; NS.ForeverEquipment(); assert(not w.shown); linkError=false
local calls=#timers; event('UNIT_INVENTORY_CHANGED','target'); assert(#timers==calls)
items[wrist].level=12; NS.ForeverEquipment(); local lines={}; NS.ForeverEquipmentEvidence(lines)
assert(#lines==2 and not lines[1]:find('Stamina') and not lines[1]:find('item:'))
assert(not host(CharacterAmmoSlot),'hidden native ammo exposed')

-- All real enchants use readable names, with localized wrapper stripping.
ENCHANTED_TOOLTIP_LINE='Enchanted: %s'; EllesmereUIDB={}
items[wrist].tooltip={lines={{type=15,leftText='Enchanted: +2 Stamina'}}}; NS.ForeverEquipment()
assert(w.fonts[2].text=='+2 Stam')
items[wrist].tooltip.lines[1].leftText='Enchanted: Minor Speed'; NS.ForeverEquipment()
assert(w.fonts[2].text=='Minor Speed','unknown effect fabricated a numeric bonus')
locale='deDE'; ENCHANTED_TOOLTIP_LINE='Verzaubert (+): %s'
items[wrist].tooltip.lines[1].leftText='Verzaubert (+): Ausdauer +2'; NS.ForeverEquipment()
assert(w.fonts[2].text=='Ausdauer +2','localized unknown wording changed')
locale='enUS'; ENCHANTED_TOOLTIP_LINE='Enchanted: %s'
items[wrist].tooltip.lines[1].leftText='Enchanted: Stamina +2'

-- Native Inspect loads later and owns requests, target, visibility and scripts.
InspectFrame=native(); InspectFrame.visible=false
InspectPaperDollFrame=native(); InspectPaperDollFrame.visible=false
-- Exact Camelot 338x424 layout: 37px slots, 4px side pitch, weapons
-- bottom-left(116,16) with 5px gaps. Coordinates use frame-top y=0.
InspectHeadSlot=native(1,8); InspectHeadSlot.top=-62
InspectHandsSlot=native(10,291); InspectHandsSlot.top=-62
InspectWristSlot=native(9,8); InspectWristSlot.top=-349
InspectTrinket1Slot=native(14,291); InspectTrinket1Slot.top=-349
InspectMainHandSlot=native(16,116); InspectMainHandSlot.top=-371
InspectSecondaryHandSlot=native(17,158); InspectSecondaryHandSlot.top=-371
InspectRangedSlot=native(18,200); InspectRangedSlot.top=-371
InspectShirtSlot=native(4,8); InspectShirtSlot.top=-267
nativeRequests=0
function InspectFrame_Show(unit)
 nativeRequests=nativeRequests+1
 InspectFrame.visible=false; InspectPaperDollFrame.visible=false
 if nativeHooks[InspectFrame] then nativeHooks[InspectFrame].OnHide() end
 InspectFrame.unit=unit
end
function InspectFrame:UnitChanged() nativeRequests=nativeRequests+1 end
event('ADDON_LOADED','Blizzard_InspectUI'); flush()
inspectInventory['Person-A']={[9]=wrist,[14]=offhand,[16]=offhand,[17]=offhand,[18]=offhand,[4]=wrist}
InspectFrame_Show('target'); flush()
assert(not host(InspectWristSlot),'inspection painted before native readiness')
-- Native OnShow can run before our INSPECT_READY handler; the queue must wait.
InspectFrame.visible=true; InspectPaperDollFrame.visible=true
nativeHooks[InspectFrame].OnShow(); nativeHooks[InspectPaperDollFrame].OnShow(); flush()
assert(not host(InspectWristSlot),'OnShow bypassed inspection readiness')
event('INSPECT_READY','Person-A'); flush()
local iw=host(InspectWristSlot); local ih=iw.children[1]; local ib=host(InspectSecondaryHandSlot)
assert(iw.shown and w.shown and iw.fonts[2].text=='+2 Stam')
assert(iw.fonts[2].color[1]==.1 and iw.fonts[2].color[2]==1 and iw.fonts[2].color[3]==.1,'Inspect enchant text must be green')
local inspectGem=iw.textures[1]; assert(inspectGem and inspectGem.shown)
assert(host(InspectShirtSlot).fonts[2].shown,'actual enchant on unusual slot omitted')
assert(iw.fonts[1].anchor[4]==5 and ib.fonts[1].anchor[5]==2)
assert(ib.children[1].w==37 and ib.children[1].anchor[3]=='TOP','inspect weapon label escapes below frame or into ranged slot')
-- Cross-row rectangle checks: wrist/trinket labels used to intersect mainhand
-- and ranged enchant names even though each individual weapon fit its slot.
local function rect(region)
 local p,s,a,x,y=unpack(region.anchor)
 local width,height=region.w,region.h or region.font[2]
 local cx,cy=s.x+s.w/2,s.top-37/2
 if p=='LEFT' and a=='RIGHT' then return {s.x+s.w+x,cy+y-height/2,s.x+s.w+x+width,cy+y+height/2} end
 if p=='RIGHT' and a=='LEFT' then return {s.x+x-width,cy+y-height/2,s.x+x,cy+y+height/2} end
 assert(p=='BOTTOM' and a=='TOP')
 return {cx+x-width/2,s.top+y,cx+x+width/2,s.top+y+height}
end
local function intersects(a,b) return a[1]<b[3] and b[1]<a[3] and a[2]<b[4] and b[2]<a[4] end
local function regions(slot)
 local h=host(slot); local result={h.fonts[1],h.fonts[2],h.children[1]}
 for _,r in ipairs(h.textures) do if r.shown then result[#result+1]=r end end
 return result
end
local function checkBottomRows()
 for _,side in ipairs({InspectWristSlot,InspectTrinket1Slot}) do
  for _,r in ipairs(regions(side)) do
   local bounds=rect(r)
   if side==InspectWristSlot then assert(bounds[1]>=50 and bounds[3]<=94,'left gem/text escaped lane')
   else assert(bounds[1]>=242 and bounds[3]<=286,'right gem/text escaped lane') end
   for _,weaponSlot in ipairs({InspectMainHandSlot,InspectSecondaryHandSlot,InspectRangedSlot}) do
    for _,weaponRegion in ipairs(regions(weaponSlot)) do
     assert(not intersects(bounds,rect(weaponRegion)),'Inspect side/weapon annotations overlap')
    end
   end
  end
 end
end
checkBottomRows()
items[wrist].sockets=8; items[offhand].sockets=8
items[wrist].gems={}; items[offhand].gems={}
for i=1,8 do items[wrist].gems[i]=777; items[offhand].gems[i]=777 end
NS.ForeverEquipment(); checkBottomRows()
EllesmereUIDB.charSheetItemLevelSize=24; EllesmereUIDB.charSheetEnchantSize=24; EllesmereUIDB.charSheetEnchantNames=true
NS.ForeverEquipment(); checkBottomRows()
EllesmereUIDB={}; NS.ForeverEquipment()
ih.scripts.OnEnter(ih); assert(GameTooltip.text=='Enchanted: Stamina +2')
event('ITEM_DATA_LOAD_RESULT',100,true); flush(); assert(GameTooltip:IsOwned(ih))
inspectStyle='off'; looksChanged(); assert(not iw.shown and w.shown)
inspectStyle='eui'; looksChanged(); assert(iw.shown)
style='off'; looksChanged(); assert(not w.shown and iw.shown)
style='eui'; looksChanged()
EllesmereUIDB.inspectShowEnchants=false; EllesmereUIDB.inspectShowItemLevel=false
NS.ForeverEquipment(); assert(not ih.shown and not iw.fonts[1].shown and w.fonts[1].shown and hit.shown)
EllesmereUIDB={}; NS.ForeverEquipment()

-- Same token now denotes another player. Old ready/data events may not revive A.
guids.target='Person-B'; inspectInventory['Person-B']={[9]=plain}
event('INSPECT_READY','Person-A')
assert(not iw.shown and not GameTooltip.shown,'stale ready event kept previous player visible')
event('ITEM_DATA_LOAD_RESULT',100,true); flush(); assert(not iw.shown)
ih.scripts.OnEnter(ih); assert(not GameTooltip.shown,'stale tooltip exposed previous person')
event('INSPECT_READY','Person-B'); flush()
assert(iw.shown and iw.fonts[1].text=='9' and not ih.shown,'old enchant leaked into new inspected person')
assert(not inspectGem.shown,'old inspected gem survived character change')
event('ITEM_DATA_LOAD_RESULT',888,true); flush(); assert(not inspectGem.shown,'late old gem repainted previous person')
assert(not ib.shown,'old inspected weapon survived unequip')
assert(w.shown and hit.shown,'inspected swap affected own equipment')

-- Closing/reopening same GUID must also wait for the new native request.
InspectFrame_Show('target'); flush(); assert(not iw.shown)
InspectFrame.visible=true; InspectPaperDollFrame.visible=true
nativeHooks[InspectFrame].OnShow(); flush(); assert(not iw.shown)
event('INSPECT_READY','Person-A'); flush(); assert(not iw.shown)
event('INSPECT_READY','Person-B'); flush(); assert(iw.shown)
InspectPaperDollFrame.visible=false; nativeHooks[InspectPaperDollFrame].OnHide(); assert(not iw.shown and w.shown)
InspectPaperDollFrame.visible=true; nativeHooks[InspectPaperDollFrame].OnShow(); flush(); assert(iw.shown,'native inspect tab switch lost completed data')
event('PLAYER_TARGET_CHANGED'); assert(not iw.shown)
event('GET_ITEM_INFO_RECEIVED',200,true); flush(); assert(not iw.shown)

InspectFrame_Show('party1'); inspectInventory['Person-C']={[9]=wrist}
InspectFrame.visible=true; InspectPaperDollFrame.visible=true
event('INSPECT_READY','Person-C'); flush(); assert(iw.shown and iw.fonts[2].text=='+2 Stam')
event('GROUP_ROSTER_UPDATE'); assert(not iw.shown)
event('INSPECT_READY','Person-C'); flush(); assert(iw.shown)
guids.party1=SECRET; event('TOOLTIP_DATA_UPDATE'); flush(); assert(not iw.shown)
guids.party1='Person-C'; event('INSPECT_READY',SECRET); flush(); assert(not iw.shown)
InspectFrame.unit=SECRET; NS.ForeverEquipment(); assert(not iw.shown)
InspectFrame.unit='party1'; event('INSPECT_READY','Person-C'); flush(); assert(iw.shown)
-- Last synchronous identity guard catches a GUID swap during item reads too.
local savedRead=C_TooltipInfo.GetInventoryItem
C_TooltipInfo.GetInventoryItem=function(unit,id)
 local data=savedRead(unit,id); if unit=='party1' then guids.party1='Person-D' end; return data
end
NS.ForeverEquipment(); assert(not iw.shown,'identity changed during paint but old person shown')
C_TooltipInfo.GetInventoryItem=savedRead; flush()
assert(nativeRequests==3,'addon invoked native inspection request methods')
assert(InspectWristSlot.scripts.OnClick and InspectWristSlot.scripts.OnEnter,'native inspect handlers lost')

-- Closing inspection clears its owned tooltip without affecting own equipment.
guids.party1='Person-C'; event('INSPECT_READY','Person-C'); flush()
ih.scripts.OnEnter(ih); assert(GameTooltip.shown)
InspectFrame.visible=false; InspectFrame.unit=nil; nativeHooks[InspectFrame].OnHide()
assert(not iw.shown and not GameTooltip.shown and w.shown)
''')
print('PASS: real abbreviated/full localized enchants, compact geometry/all slots, sparse/async gems, Inspect readiness/GUID freshness/stale events and Character coexistence, native handlers/state, independent settings/styles, secret/error guards and cached evidence.')
