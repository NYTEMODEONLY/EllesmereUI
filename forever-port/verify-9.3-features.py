"""v9.3 integration: real moved menu definitions, opt-ins, owners, load graph."""
from pathlib import Path
import re
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2]
def source(n):return (ROOT/n).read_text(encoding='utf-8-sig')
toc=source('EllesmereUIDataBars/EllesmereUIDataBars.toc')
assert 'EllesmereUIDataBars_Blocks.lua' not in toc
assert toc.index('Blocks\\Shared.lua')<toc.index('Blocks\\MicroMenu.lua')
for line in toc.splitlines():
    if line.strip() and not line.startswith('#'):assert (ROOT/'EllesmereUIDataBars'/line.replace('\\','/')).is_file(),line
menu=source('EllesmereUIDataBars/Blocks/MicroMenu.lua')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
EUI_FOREVER=true;EllesmereUI={IS_FOREVER=true};ns={L={},MEDIA="",BlockKit={},BlockFactories={}}
function CreateFrame() error('menu definitions must not allocate native frames') end
function InCombatLockdown() return false end
''')
lua.execute(menu+'\nreturn mmButtonDefs,mmButtonOrder,MM_MICRO_BUTTON_NAMES,MMElementEnabled','DataBars',lua.globals().ns)
defs,order,names,enabled=lua.execute(menu+'\nreturn mmButtonDefs,mmButtonOrder,MM_MICRO_BUTTON_NAMES,MMElementEnabled','DataBars',lua.globals().ns)
keys=[defs[i]['key'] for i in range(1,len(defs)+1)]
assert len(keys)==len(set(keys)),'duplicate moved/upstream menu entries'
for key,native in [('ach','LegacyMicroButton'),('spell','SpellbookMicroButton'),('talent','TalentMicroButton'),('professions','ProfessionMicroButton')]:assert names[key]==native
settings=lua.table_from({'ach':False,'talent':False,'professions':False})
for key in ('ach','talent','professions'):assert not enabled(settings,key)
for key in ('talent','professions'):assert enabled(lua.table(),key)
assert [order[i] for i in range(1,len(order)+1)]==keys
assert 'if EUI_FOREVER_NATIVE_ACTIONS then return end' in menu
assert 'MMElementEnabled(mm, def.key)' in menu and 'MMElementEnabled(mm, key)' in menu
assert 'native.disabledTooltip' in menu and 'LEGACY_REWARD_TRACK_FACTION_ID' in menu
assert '"/click " .. microRef:GetName()' in menu
for block in ('Crests','GreatVault'):
    lua.execute(source('EllesmereUIDataBars/Blocks/'+block+'.lua'),'DataBars',lua.globals().ns)
assert lua.globals().ns.BlockFactories.crests is None and lua.globals().ns.BlockFactories.greatvault is None
travel=source('EllesmereUIDataBars/Blocks/Travel.lua')
assert 'not EllesmereUI.IS_FOREVER and D().clickableTeleports ~= false' in travel
ilvl=source('EllesmereUIDataBars/Blocks/ItemLevel.lua')
assert 'CharacterMicroButton' in ilvl and 'combatlock' in ilvl and 'PLAYER_REGEN_ENABLED' in ilvl
print('PASS: production split menu has unique native endpoints, false settings survive; unsupported blocks inactive; secure ilvl entry retained')
coretoc=source('EllesmereUI/EllesmereUI.toc')
assert 'EllesmereUI_ManaRegenSpark.lua' in coretoc
assert not any(x.strip()=='EllesmereUI_ForeverLayout.lua' for x in coretoc.splitlines())
assert not (ROOT/'EllesmereUIMythicTimer/EllesmereUIMythicTimer.toc').exists()
abr=source('EllesmereUIAuraBuffReminders/EllesmereUIAuraBuffReminders.lua')
assert 'growDirection = "CENTER"' in abr and 'EllesmereUIABR_Forever' in source('EllesmereUIAuraBuffReminders/EllesmereUIAuraBuffReminders.toc')
uf=source('EllesmereUIUnitFrames/EllesmereUIUnitFrames.lua')
assert 'manaRegenSpark = false' in uf
sheet=source('EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_CharacterSheetForever.lua')
assert 'not ns.ForeverOfficialCharacterStats and ns.CharSheetForever()' in sheet
skin=source('EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin.lua')
adopt=skin[skin.index('local function AdoptForeverCharSheetStyle'):skin.index('local seedFrame',skin.index('local function AdoptForeverCharSheetStyle'))]
lua.execute('EUI_FOREVER=true; EllesmereUI={IS_FOREVER=true}')
fn=lua.execute(adopt+'\nreturn AdoptForeverCharSheetStyle')
db=lua.table_from({'profiles':lua.table_from({'existing':lua.table_from({'windowSkinLook':'blizzard'})})})
fn(db);assert db.foreverCharSheetStyleAdopted is None and db.profiles.existing.charSheetUseBlizzardStyle is None
print('PASS: existing custom character owner survives stock-style migration; new spark/reminder/layout load contracts retained')
meter=source('EllesmereUIDamageMeters/EllesmereUIDamageMeters.lua')
assert 'local maxAmt = isThreat and 100 or' in meter
assert 'count = math.min(#sources, limit)' in meter
empty=meter[meter.index('W._barSources={}'):]
assert empty.index('W.UpdateSticky(nil, 0)')<1000
assert 'for i = 1, #W.rowPool do W.rowPool[i].row:Hide() end' in empty[:1000]
print('PASS: custom 80-row Threat scaling and upstream empty/pinned cleanup retained')
