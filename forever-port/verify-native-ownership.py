"""Real production ownership handoffs; no live game or SavedVariables writes."""
from pathlib import Path
import runpy
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
EUI_FOREVER=true; ns={Engine={SetPainter=function() end},
 UF_HEAL_PRED_UNITS={player=true,target=true,focus=true}}
function CreateFrame() error('duplicate local heal frame allocated') end
''')
lua.execute((root/'EllesmereUIUnitFrames/EUI_UnitFrames_ForeverPrediction.lua').read_text(), 'UF', lua.globals().ns)
lua.execute('''
for _,unit in ipairs({'player','target','focus'}) do
 local settings={healPrediction=false,sentinel=42,showPlayerAbsorb='none'}
 local frame={}
 ns.ForeverCreateHealPrediction(frame,unit,function() return settings end)
 assert(settings.healPrediction and settings.foreverOfficialHealMigrated)
 assert(settings.sentinel==42 and settings.showPlayerAbsorb=='none')
 assert(frame.ForeverIncomingHeal==nil)
 settings.healPrediction=false
 ns.ForeverCreateHealPrediction({},unit,function() return settings end)
 assert(settings.healPrediction==false,'later OFF choice overwritten')
end
''')
uf=(root/'EllesmereUIUnitFrames/EllesmereUIUnitFrames.lua').read_text()
assert 'if frame.ForeverIncomingHeal then channels[#channels + 1] = "incomingHeal" end' in uf
print('PASS: official heal units migrate once, later OFF persists, no duplicate calculator/overlay/channel; unrelated settings retained')

# Existing fixtures already forbid edits to native slot geometry and handlers.
fixture=runpy.run_path(str(root/'EllesmereUI/forever-port/verify-equipment.py'))
lua=fixture['lua']
lua.execute('''
style='eui'; combat=false; EllesmereUIDB={}
EllesmereUI.IS_FOREVER=true
EllesmereUI.BlizzSkinPadStandDown=function() return false end
EllesmereUI.L=function(s) return s end
EllesmereUI.PrimeFontShadow=function() end
EllesmereUI.GetEnchantText=function() error('duplicate official enchant reader') end
NS.ForeverCharacter=function() end
NS.WSkin.Shell=function() error('duplicate official shell') end
NS.WSkin.FadeRegions=function() error('official skin touched custom art') end
NS.WSkin.OnLooksChanged=function(fn) officialLooks=fn end
CharacterFrame={}
function PaperDollItemSlotButton_Update() end
function CharacterRangedSlot:IsShown() return true end
function CharacterAmmoSlot:IsShown() return false end
Enum.ItemClass={Weapon=2}
local oldRegion=region
function region(parent)
 local r=oldRegion(parent)
 function r:ClearAllPoints() self.anchor=nil end
 function r:GetStringWidth() return #(self.text or '')*6 end
 function r:GetStringHeight() return 11 end
 return r
end
for _,f in ipairs(created) do
 for _,r in ipairs(f.fonts or {}) do function r:ClearAllPoints() self.anchor=nil end end
end
local oldCreate=CreateFrame
function CreateFrame(...)
 local f=oldCreate(...)
 function f:UnregisterEvent(e) self.events[e]=nil end
 return f
end
inventory={[9]=wrist,[17]=offhand}
items[wrist]={level=12,quality=2,stats={ITEM_MOD_INTELLECT_SHORT=5,ITEM_MOD_STAMINA_SHORT=3},tooltip={lines={{type=15,leftText='Enchanted: Stamina +2'}}}}
items[offhand]={level=25,quality=3,weapon=true,stats={ITEM_MOD_DAMAGE_PER_SECOND_SHORT=6.3},tooltip={lines={{type=15,leftText='Enchanted: Weapon'}}}}
function GetInventoryItemID(unit,slot) local link=GetInventoryItemLink(unit,slot); return link and tonumber(link:match('item:(%d+)')) end
C_Item.GetItemStats=function(link) return items[link] and items[link].stats end
C_Item.GetItemInfoInstant=function(link) return nil,nil,nil,nil,nil,items[link].weapon and 2 or 4 end
C_Item.IsItemDataCachedByID=function(id) return not missing end
''')
source=(root/'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_CharacterSheetForever.lua').read_text()
lua.execute('assert(loadstring(...))("Skin",NS)', source)
lua.execute('''
assert(NS.ForeverOfficialCharacterStats)
NS.ForeverRefreshOfficialCharacterStats()
local overlay
for _,f in ipairs(created) do if f.allPoints==PaperDollItemsFrame then overlay=f end end
assert(overlay and overlay.shown)
local function countText(text)
 local n=0; for _,fs in ipairs(overlay.fonts) do if fs.text==text then n=n+1 end end; return n
end
assert(countText('+5 Int / +3 Stam')==1 and countText('6.3 Dps')==1)
assert(countText('Enchanted: Weapon')==0,'duplicate enchant text')
NS.ForeverEquipment()
local w=host(CharacterWristSlot)
assert(w.fonts[1].anchor[1]=='TOPRIGHT' and w.fonts[1].text=='12')
assert(w.fonts[2].shown and w.fonts[2].color[2]==1,'custom enchant lost')
local oldCount=#created
NS.ForeverRefreshOfficialCharacterStats()
assert(#created==oldCount,'repeat refresh allocated duplicate labels')
EllesmereUIDB.showUpgradeTrack=false
EllesmereUI._refreshUpgradeTrackVisibility()
assert(countText('+5 Int / +3 Stam')==0 and countText('6.3 Dps')==0)
EllesmereUIDB.showUpgradeTrack=true
EllesmereUI._refreshUpgradeTrackVisibility()
assert(countText('6.3 Dps')==1)
style='off'; officialLooks(); assert(not overlay.shown)
style='eui'; officialLooks(); assert(overlay.shown)
missing=true; inventory[9]='item:200:0'; items[inventory[9]]={quality=2,stats={RESISTANCE0_NAME=25}}
PaperDollItemSlotButton_Update(CharacterWristSlot)
assert(countText('+5 Int / +3 Stam')==0)
missing=false; event('GET_ITEM_INFO_RECEIVED',200,true)
assert(countText('25 Armor')==1,'late item data did not repaint official stats')
''')
print('PASS: actual official stats/DPS paint once, keep custom enchant/item levels and native geometry, support settings, skin off/on and asynchronous data')

# The old timer adapter is inert before accessing any UI on the current build.
lua=LuaRuntime()
lua.execute('EUI_FOREVER=true; function GetBuildInfo() return "1.60.1","70009" end; function CreateFrame() error("old action adapter ran") end')
for name in ('ForeverCombatLayout','Forever','ForeverHUD'):
    lua.execute((root/f'EllesmereUIActionBars/EllesmereUIActionBars_{name}.lua').read_text())
lua.execute('assert(EUI_FOREVER_NATIVE_ACTIONS==nil and EUI_FOREVER_CombatLayout==nil)')
print('PASS: old action bar/countdown/HUD adapters allocate nothing on build 70009')
