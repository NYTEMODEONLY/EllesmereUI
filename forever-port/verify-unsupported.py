"""Forever exclusion regressions; Lua 5.1 via lupa, no game interaction."""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT.parent

def source(name):
    return (ADDONS / name).read_text(encoding='utf-8-sig')

excluded = {
    'EllesmereUI': ['Libs\\LibKeystone\\LibKeystone.lua'],
    'EllesmereUIQoL': ['EllesmereUIQoL_Keys.lua', 'EllesmereUIQoL_TeleportPrompt.lua', 'EUI_UpgradeCalc.lua'],
    'EllesmereUIBlizzardSkin': ['EllesmereUIBlizzardSkin_GreatVault.lua', 'EllesmereUIBlizzardSkin_DragonRiding.lua'],
    'EllesmereUIMythicTimer': ['EllesmereUIMythicTimer.lua', 'EUI_MythicTimer_TargetedSpellBars.lua', 'EUI_MythicTimer_TargetFocusBars.lua'],
    'EllesmereUIOptions': ['EUI_MythicTimer_Options.lua', 'EUI_UpgradeCalc_Options.lua'],
}
size = 0
for folder, names in excluded.items():
    toc = f'{folder}/{folder}.toc'
    if folder == 'EllesmereUIMythicTimer':
        assert not (ADDONS / toc).exists()
        toc += '.disabled'
    entries = {line.strip() for line in source(toc).splitlines() if line.strip() and not line.startswith('#')}
    for name in names:
        assert name not in entries, name
        size += (ADDONS / folder / name.replace('\\', '/')).stat().st_size
print(f'PASS: {sum(map(len, excluded.values()))} Retail-only files excluded from load ({size:,} source bytes)')

# Guarded standalone chunks must perform no initialization at all.
for name in ['EllesmereUIQoL/EllesmereUIQoL_TeleportPrompt.lua', 'EllesmereUIQoL/EUI_UpgradeCalc.lua', 'EllesmereUIOptions/EUI_UpgradeCalc_Options.lua']:
    lua = LuaRuntime()
    lua.execute('EUI_FOREVER = true; EUI_CLIENT_FOREVER = true; EllesmereUI = { IS_FOREVER = true }')
    lua.execute(source(name))
print('PASS: excluded chunks remain inert if manually loaded on Forever')

lua = LuaRuntime()
lua.execute('EUI_FOREVER = true; EUI_CLIENT_FOREVER = true; EllesmereUI = { IS_FOREVER = true }')
core = source('EllesmereUI/EllesmereUI.lua')
chunk = core[core.index('EllesmereUI.SEASON_PORTALS ='):core.index('--  Addon Groups')]
lua.execute(chunk + '\nassert(#EllesmereUI.SEASON_PORTALS == 0)\nfor _,v in ipairs(ADDON_ROSTER) do assert(v.folder ~= "EllesmereUIMythicTimer"); assert(v.syncFolder ~= "EllesmereUIDragonRiding") end')
print('PASS: no seasonal portals, Mythic sidebar module, or Skyriding sync control')
first = source('EllesmereUI/EllesmereUI_FirstInstall.lua')
lua.execute(core[core.index('EllesmereUI.FOREVER_HIDDEN_ADDONS ='):core.index('-- The profile import/export checklists')])
lua.execute(first[first.index('local GROUPS ='):first.index('local function IsAddonEnabled')]+'''
for _,g in ipairs(GROUPS) do for _,e in ipairs(g.entries) do assert(e.addon ~= "EllesmereUIMythicTimer") end end
''')
print('PASS: first-install picker does not offer the removed Mythic addon')

# Check migrated blocks, including stale fill/center pointers and re-imports.
bars = source('EllesmereUIDataBars/EllesmereUIDataBars.lua')
lua.execute('ns = {}')
lua.execute(bars[bars.index('ns.BLOCK_TYPES ='):bars.index('ns.BLOCK_DEFAULTS =')])
lua.execute(bars[bars.index('function ns.RemoveUnsupportedBlocks'):bars.index('function ns.BarsInOrder')])
lua.execute('''
    for _, b in ipairs(ns.BLOCK_TYPES) do assert(b.key ~= "greatvault" and b.key ~= "crests") end
    local keep1, keep2 = {id="a",type="clock"}, {id="d",type="micromenu"}
    local vault, crest = {id="b",type="greatvault",settings={custom=true}}, {id="c",type="crests"}
    local bar = {blocks={keep1,vault,crest,keep2},fillBlockId="b",centerBlockId="c",x=321}
    ns.RemoveUnsupportedBlocks(bar)
    assert(#bar.blocks == 2 and bar.blocks[1] == keep1 and bar.blocks[2] == keep2)
    assert(bar.x == 321 and bar.fillBlockId == nil and bar.centerBlockId == nil)
    assert(bar._foreverExcludedBlocks[1].block == vault and bar._foreverExcludedBlocks[1].index == 2)
    assert(bar._foreverExcludedBlocks[2].block == crest and bar._foreverExcludedBlocks[2].index == 3)
    ns.RemoveUnsupportedBlocks(bar); assert(#bar._foreverExcludedBlocks == 2)
    table.insert(bar.blocks, {id="new",type="greatvault"})
    ns.RemoveUnsupportedBlocks(bar); assert(#bar.blocks == 2 and #bar._foreverExcludedBlocks == 3)
    EUI_FOREVER=false
    local retail={blocks={vault,crest}}
    ns.RemoveUnsupportedBlocks(retail); assert(#retail.blocks == 2)
    EUI_FOREVER=true
''')
print('PASS: old/imported Vault and crest blocks removed without losing settings or normal blocks')

# Actual options builder and runtime share the two Forever logging trigger keys.
logging_options = source('EllesmereUIOptions/EUI_QoL_AutoLogging_Options.lua')
lua.execute(logging_options[logging_options.index('local TRIGGER_ITEMS ='):logging_options.index('local function Cfg()')] + '''
assert(#TRIGGER_ITEMS == 2 and TRIGGER_ITEMS[1].key == "logNormal" and TRIGGER_ITEMS[2].key == "log5pp")
''')
lua = LuaRuntime()
lua.execute('''
    EUI_FOREVER = true
    EllesmereUIDB = {autoLogging={enabled=true,delaystop=false}}
    frames={}
    function CreateFrame()
        local f={events={}}
        function f:RegisterEvent(e) self.events[e]=true end
        function f:UnregisterEvent(e) self.events[e]=nil end
        function f:SetScript(k,v) self[k]=v end
        frames[#frames+1]=f; return f
    end
    C_Timer={After=function(_,fn) fn() end}
    function GetCVar() return "1" end
    function SetCVar() error("unexpected CVar change") end
    logging=false
    function LoggingCombat(value) if value ~= nil then logging=value end; return logging end
    zoneType="none"; diff=1; mapID=33
    function GetInstanceInfo() return "instance",zoneType,diff,nil,5,nil,nil,mapID end
''')
lua.execute(source('EllesmereUIQoL/EllesmereUIQoL_AutoLogging.lua'))
lua.execute('''
    frames[1]:OnEvent("PLAYER_LOGIN")
    assert(frames[1].events.ZONE_CHANGED_NEW_AREA and not frames[1].events.CHALLENGE_MODE_START)
    assert(not logging)
    zoneType="party"; _EUI_AutoLogging_Check(); assert(logging)
    EllesmereUIDB.autoLogging.log5pp=false; _EUI_AutoLogging_Check(); assert(not logging)
    zoneType="raid"; _EUI_AutoLogging_Check(); assert(logging)
    EllesmereUIDB.autoLogging.logNormal=false; _EUI_AutoLogging_Check(); assert(not logging)
    zoneType="arena"; _EUI_AutoLogging_Check(); assert(not logging)
    EllesmereUIDB.autoLogging.enabled=false; _EUI_AutoLogging_Check()
    assert(not frames[1].events.ZONE_CHANGED_NEW_AREA)
    EUI_FOREVER=false; EllesmereUIDB.autoLogging={enabled=true,delaystop=false}
    zoneType="party"; diff=8; mapID=1594; _EUI_AutoLogging_Check(); assert(logging)
    diff=1; mapID=33; _EUI_AutoLogging_Check(); assert(not logging)
''')
print('PASS: Forever dungeons/raids log correctly; disabling stops logging/events; Retail rules retained')

lua = LuaRuntime()
lua.execute('EUI_FOREVER=true; EllesmereUI={IS_FOREVER=true}; ECHAT={DB=function() return {sidebarIconOrder={showPortals=-100}} end}')
chat = source('EllesmereUIChat/EllesmereUIChat.lua')
lua.execute(chat[chat.index('local SIDEBAR_CHAIN_KEYS ='):chat.index('function ECHAT.SidebarIconExists')])
lua.execute('''
    local order=ECHAT.ResolveSidebarIconOrder()
    assert(#order == 6)
    for _, key in ipairs(order) do assert(key ~= "showPortals") end
    -- Client-family chain is now captured once at module load.
    EUI_FOREVER=false; assert(#ECHAT.ResolveSidebarIconOrder() == 6)
''')
print('PASS: imported chat ordering cannot recreate a dungeon portal button')

lua = LuaRuntime()
lua.execute('EUI_FOREVER=true; WSkin={}; _windows={}')
engine=source('EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowEngine.lua')
lua.execute(engine[engine.index('function WSkin.RegisterWindow(entry)'):engine.index('local boot = CreateFrame', engine.index('function WSkin.RegisterWindow(entry)'))])
lua.execute('''
    for _, key in ipairs({"greatvault","itemupgrade","delvepicker"}) do WSkin.RegisterWindow({key=key}) end
    assert(#_windows == 0)
    for _, key in ipairs({"delves","housing","foreverbank","collections","catalyst"}) do WSkin.RegisterWindow({key=key}) end
    assert(#_windows == 5)
    EUI_FOREVER=false; WSkin.RegisterWindow({key="greatvault"}); assert(#_windows == 6)
''')
print('PASS: excluded skins never register; native companion, housing, collections and bank retained')

options=source('EllesmereUIOptions/EUI_QoL_BattleRes_Options.lua')
lua.execute('EUI_FOREVER=true')
lua.execute(options[options.index('local VIS_VALUES ='):options.index('local function MakeBorderColorSwatches')]+'''
    assert(#VIS_ORDER == 2 and VIS_VALUES.MPLUS == nil and VIS_VALUES.MPLUS_AND_RAID == nil)
    assert(DisplayVisibility("MPLUS_AND_RAID") == "RAID")
    assert(DisplayVisibility("MPLUS") == "NEVER")
    assert(DisplayVisibility("RAID") == "RAID")
''')
runtime=source('EllesmereUIQoL/EllesmereUIQoL_BattleRes.lua')
start=runtime.index('local function _activeKeystoneLevel()')
end=runtime.index('-- Unlock-mode loadPos/clearPos',start)
lua.execute('EUI_FOREVER=true; ns={}; C_ChallengeMode=setmetatable({}, {__index=function() error("must not query Mythic API") end}); function IsEncounterInProgress() return false end')
lua.execute(runtime[start:end]+"\nlocal st={}; ns.RefreshInstanceState(st); assert(not st.inChallenge); ns.ApplyInstanceEvent(st,'CHALLENGE_MODE_START'); assert(not st.inChallenge)")
bloodlust=source('EllesmereUIQoL/EllesmereUIQoL_Bloodlust.lua')
assert 'ns.RefreshInstanceState(_state)' in bloodlust and 'ns.ApplyInstanceEvent(_state, event)' in bloodlust
print('PASS: tracker options normalize imported Mythic modes; no keystone API probes on Forever')

print('Offline coverage only: rendering and protected execution require the live client.')
