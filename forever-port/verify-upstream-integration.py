"""9.2.1 integration: real bootstrap/lifecycle, persistence and load ownership.

Uses Lua 5.1 via lupa. This does not emulate rendering or WoW secure execution.
"""
from pathlib import Path
import re
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT.parent
def source(name):
    return (ADDONS / name).read_text(encoding='utf-8-sig')

def runtime(version='1.60.1', iface=16001, compiler=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().version = version
    lua.globals().iface = iface
    lua.execute('''
        frames = {}; timers = {}; logged = false
        function GetBuildInfo() return version, '69913', 'test', iface end
        function CreateFrame()
            local f = { events = {} }
            function f:RegisterEvent(e) self.events[e] = true end
            function f:UnregisterEvent(e) self.events[e] = nil end
            function f:UnregisterAllEvents() self.events = {} end
            function f:SetScript(k,v) self[k] = v end
            frames[#frames+1] = f
            return f
        end
        function Fire(e,...)
            if e == 'PLAYER_LOGIN' then logged = true end
            for _,f in ipairs(frames) do
                if f.events[e] then f:OnEvent(e,...) end
            end
        end
        function IsLoggedIn() return logged end
        function CopyTable(t)
            if type(t) ~= "table" then return t end
            local copy = {}; for k,v in pairs(t) do copy[k] = CopyTable(v) end; return copy
        end
        function wipe(t) for k in pairs(t) do t[k] = nil end return t end
        function geterrorhandler() return function(e) error(e,0) end end
        C_Timer = { After = function(_,f) timers[#timers+1] = f end }
        function Flush() while #timers > 0 do table.remove(timers,1)() end end
        UISpecialFrames = {}
        -- WoW's xpcall forwards arguments; stock Lua 5.1 does not.
        local nativeXpcall = xpcall
        function xpcall(f,h,...)
            local args = {...}
            return nativeXpcall(function() return f(unpack(args)) end,h)
        end
    ''')
    if compiler:
        lua.execute('loadstring_untainted = function() error("probe must never run a snippet") end')
    lua.execute(source('EllesmereUI/EllesmereUI_ClientGate.lua'))
    lua.execute('assert(loadstring(...))("EllesmereUI", {})', source('EllesmereUI/EllesmereUI_Lite.lua'))
    return lua

for version, iface, expected in [('1.60.1',16001,True), ('1.61.0',16100,True),
                                ('12.1.0',120100,False), ('1.15.8',11508,False)]:
    lua = runtime(version,iface)
    assert bool(lua.globals().EUI_FOREVER) == expected
    assert bool(lua.globals().EUI_CLIENT_FOREVER) == expected
    if not lua.globals().EUI_CLIENT_BLOCKED:
        assert bool(lua.globals().EllesmereUI.IS_FOREVER) == expected
        assert lua.globals().EllesmereUI.FOREVER_SV_BUG is False
        assert lua.eval('EllesmereUI.SecureSnippetsOK()') == (not expected)
lua = runtime(compiler=True)
assert lua.eval('EllesmereUI.SecureSnippetsOK()') is True
print('PASS: upstream/local Forever flags agree; capability check never executes snippets')

lua = runtime()
lua.execute('''
    EllesmereUIDB = { activeProfile = 'Personal', profiles = { Personal = {
        addons = { EllesmereUIActionBars = { size = 47, barPositions = { MainBar = { x = 17 } } } }
    } } }
    original = EllesmereUIDB
    untouched = original.profiles.Personal.addons.EllesmereUIActionBars
    EllesmereUIChatScrollDB = { sentinel = true }
    Fire('ADDON_LOADED','EllesmereUI')
    db = EllesmereUI.Lite.NewDB('EllesmereUIActionBarsDB', {profile={size=36,spacing=4}}, true)
    assert(db.profile == untouched and db.profile.size == 47 and db.profile.spacing == 4)
    db.profile.size = 51
    native = EllesmereUI.Lite.NewAddon('NativeAdapter')
    native.OnEnable = function(self) self.didEnable = true end
    secure = EllesmereUI.Lite.NewAddon('SecureAdapter')
    secure.requiresSecureSnippets = true
    secure.OnEnable = function() error('unsupported secure addon enabled') end
    Fire('ADDON_LOADED','NativeAdapter')
    Fire('PLAYER_LOGIN'); Flush()
    assert(native.didEnable and secure.standDown == 'snippets')
    Fire('PLAYER_LOGOUT')
    assert(EllesmereUIDB == original and EllesmereUIDB.activeProfile == 'Personal')
    local stored = EllesmereUIDB.profiles.Personal.addons.EllesmereUIActionBars
    assert(stored.size == 51 and stored.barPositions.MainBar.x == 17)
    assert(stored.spacing == nil) -- Lite strips defaults from a copy at logout.
    assert(untouched.size == 51 and untouched.barPositions.MainBar.x == 17)
    assert(EllesmereUIChatScrollDB.sentinel)
''')
print('PASS: real Lite login/logout preserves profile identity, changes and chat store; native adapter enables')

def entries(folder):
    return [s.strip() for s in source(folder+'/'+folder+'.toc').splitlines()
            if s.strip() and not s.lstrip().startswith('#')]
core = entries('EllesmereUI')
assert 'EllesmereUI_ForeverLayout.lua' not in core
assert not any('LibKeystone' in p or 'LibSpecialization' in p for p in core)
skin = entries('EllesmereUIBlizzardSkin')
assert 'EllesmereUIBlizzardSkin_CharacterSheetForever.lua' in skin
assert skin.index('EllesmereUIBlizzardSkin_ForeverCharacter.lua') < skin.index('EllesmereUIBlizzardSkin_CharacterSheetForever.lua')
assert 'EllesmereUIBlizzardSkin_FriendsForever.lua' not in skin
assert 'EllesmereUIBlizzardSkin_ForeverCharacter.lua' in skin
assert 'EllesmereUIBlizzardSkin_ForeverItemLevel.lua' in skin
for folder, adapter in [('EllesmereUIActionBars','EllesmereUIActionBars_Forever.lua'),
                        ('EllesmereUIRaidFrames','EllesmereUIRaidFrames_Forever.lua')]:
    toc=source(folder+'/'+folder+'.toc')
    assert '## AllowLoadGameType: standard' not in toc
    assert entries(folder).index(adapter) < entries(folder).index(folder+'.lua')
assert '## AllowLoadGameType: standard' not in source('EllesmereUIFriends/EllesmereUIFriends.toc')
assert 'EUI_ResourceBars_SwingTimer.lua' in entries('EllesmereUIResourceBars')
assert 'EllesmereUIQoL_Swing.lua' not in entries('EllesmereUIQoL')
assert 'EUI_Style_Options.lua' in entries('EllesmereUIOptions')
assert 'EUI_UnitFrames_ForeverPrediction.lua' in entries('EllesmereUIUnitFrames')
assert 'EUI_UnitFrames_WeaponEnchants.lua' not in entries('EllesmereUIUnitFrames')
print('PASS: single layout/skin owners; local adapters and upstream swing/style options load')

lua = LuaRuntime()
lua.execute('EUI_CLIENT_FOREVER = true; EllesmereUI = {}')
text=source('EllesmereUI/EllesmereUI.lua')
start=text.index('EllesmereUI._FOREVER_ICON =')
end=text.index('\nend', text.index('function EllesmereUI.ClientIcon', start))+4
lua.execute(text[start:end])
lua.execute('''
    assert(EllesmereUI.ClientIcon(7548911) == 133975)
    assert(EllesmereUI.ClientIcon(7549094) == 136249)
    assert(EllesmereUI.ClientIcon(7548925) == 134332)
    assert(EllesmereUI.ClientIcon(42) == 42)
    EUI_CLIENT_FOREVER = false
    assert(EllesmereUI.ClientIcon(7548911) == 7548911)
''')
print('PASS: upstream missing-art substitutions apply only on Forever')
