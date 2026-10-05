"""Official 9.3.6 feature kit, split owners, custom defaults and native glyphs.

Synthetic checks only: no native secure execution or visual acceptance implied.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2]
def source(name):return (ROOT/name).read_text(encoding='utf-8-sig')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
ns={}; frames={}; EllesmereUIDB={}; UIParent={}
EllesmereUI={_ModuleNS={},Lite={NewAddon=function() return {} end},
 MakeUnlockElement=function(t) return t end,
 RegisterUnlockElements=function(_,v) unlock=v[1] end,
 PP={Snap=function(v) return v end}}
function CreateFrame()
 local f={}; frames[#frames+1]=f
 function f:RegisterEvent(e) self.event=e end
 function f:SetScript(_,fn) self.callback=fn end
 function f:UnregisterAllEvents() self.event=nil end
 return f
end
''')
lua.execute(source('EllesmereUIForeverEssentials/EllesmereUIForeverEssentials.lua'),'EllesmereUIForeverEssentials',lua.globals().ns)
lua.execute('''
local defaults={enabled=false,width=300,flag=true}
local defaultPos={point='CENTER',x=0,y=10}
local f=ns.Feature('testFeature',defaults,defaultPos)
assert(not f.Enabled() and f.Get('width')==300 and next(EllesmereUIDB)==nil)
local saved={enabled=false,width=413,flag=false,pos={point='TOP',x=23,y=-17},unknown='preserve'}
EllesmereUIDB.testFeature=saved
assert(f.Read()==saved and f.Get('flag')==false and f.Get('width')==413)
local built=0
local frame={ClearAllPoints=function() end,SetPoint=function(_,p,owner,r,x,y) point={p,r,x,y} end}
f.Start(function() applied=true end,{key='test',label='Test',order=1,minWidth=100,
 frame=function(create) if create then built=built+1 end;return frame end,
 height=function() return 30 end,applyStyle=function() styled=true end})
frames[1].callback(frames[1])
assert(applied and unlock.isHidden() and unlock.getFrame()==nil)
unlock.applyPos();assert(built==0,'disabled feature allocated visual frames')
saved.enabled=true;unlock.applyPos();assert(built==1 and point[1]=='TOP' and point[3]==23)
unlock.savePos(nil,'BOTTOM','BOTTOM',15,20)
assert(saved.pos.point=='BOTTOM' and point[3]==15 and saved.unknown=='preserve')
unlock.setWidth(nil,70);assert(saved.width==100 and styled)
saved.enabled=false;assert(not f.Enabled() and EllesmereUIDB.testFeature==saved)
''')
print('PASS: real official feature kit, false/unknown/save preservation, disabled allocation and unlock geometry')

# The renamed existing menu keys still draw the native glyph in either icon style.
menu=source('EllesmereUIDataBars/Blocks/MicroMenu.lua')
glyph=menu[menu.index('local function ApplyMicroIcon('):menu.index('-- Blizzard art keeps its own colors')]
lua.execute('''
EUI_FOREVER=true; mmButtonDefsByKey={professions={nativeIcon=true},talent={nativeIcon=true},ach={nativeIcon=true}}
function SetBlizzardArt(icon,key) icon.native=key;return 'micro' end
function FitBlizzardMicroIcon(icon,key) icon.fitted=true end
''')
lua.execute(glyph+'\nTestGlyph=ApplyMicroIcon')
lua.execute('''
for _,key in ipairs({'professions','talent','ach'}) do
 for _,style in ipairs({false,true}) do
  local icon={};TestGlyph(icon,key,style)
  assert(icon.native==key and icon.fitted,'native endpoint tried missing generic asset')
 end
end
''')
print('PASS: preserved Legacy/Talents/Professions native art with both menu icon styles')

assert 'npEnemyBuffFilter = "important"' in source('EllesmereUINameplates/EllesmereUINameplates.lua')
assert 'defaults.profile.showEquippedBorder = false' in source('EllesmereUIActionBars/EllesmereUIActionBars.lua')
assert 'threatPctFocus    = true' in source('EllesmereUIUnitFrames/EllesmereUIUnitFrames.lua')
assert 'bagAllowWindowsOverBags = false' in source('EllesmereUIBags/EllesmereUIBags_DB.lua')
assert 'ForeverRefreshHealPrediction(frame, frame._euiUnit, "SettingsChanged")' in source('EllesmereUIUnitFrames/EUI_UnitFrames_Reload.lua')
assert source('EllesmereUIOptions/RaidFrames_Options/VisualIndicators_Options.lua').count('SVal("showMissingBuffs", false)')==3
assert 'EllesmereUIBlizzardSkin_ChatBubbles.lua' in source('EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin.toc')
assert 'EllesmereUIForeverEssentials_LootFeed.lua' in source('EllesmereUIForeverEssentials/EllesmereUIForeverEssentials_Camelot.toc')
assert 'EllesmereUIQoL_SelfCombatText.lua' in source('EllesmereUIQoL/EllesmereUIQoL.toc')
assert 'EllesmereUIBags_List.lua' in source('EllesmereUIBags/EllesmereUIBags.toc')
assert not (ROOT/'EllesmereUIMythicTimer/EllesmereUIMythicTimer.toc').exists()
print('PASS: preserved defaults, relocated hooks, optional new-feature load graph and disabled Mythic loader')
