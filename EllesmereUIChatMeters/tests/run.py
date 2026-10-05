"""Run with Python + lupa (includes a Lua 5.1 runtime); never loaded by WoW."""
from pathlib import Path
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute((root / "tests" / "mock_wow.lua").read_text())
lua.execute((root / "ChatMeters.lua").read_text())
lua.execute((root / "SettingsIntegration.lua").read_text())
lua.execute((root / "tests" / "scenarios.lua").read_text())
lua.execute((root / "tests" / "ownership_scenarios.lua").read_text())
lua.execute((root / "tests" / "settings_scenarios.lua").read_text())
print("PASS: Lua 5.1 syntax and all companion lifecycle scenarios")

# Fresh runtimes model login/reload without remembered window references.
for left, right in [(0, "THREAT"), ("THREAT", 2), (5, "THREAT"),
                    ("THREAT", "THREAT"), (2, 5), (0, 2)]:
    restored = LuaRuntime(unpack_returned_tuples=True)
    restored.execute((root / "tests" / "mock_wow.lua").read_text(encoding="utf-8-sig"))
    restored.globals().RESTORE_LEFT = left
    restored.globals().RESTORE_RIGHT = right
    restored.execute((root / "ChatMeters.lua").read_text(encoding="utf-8-sig"))
    restored.execute((root / "tests" / "mode_restore_scenarios.lua").read_text(encoding="utf-8-sig"))
print("PASS: fresh-login pane restoration, mode switching and profile rebuild across six mode pairs")

# Persist both explicit choices; delayed host creation must not discard them.
for selected in [True, False]:
    restored = LuaRuntime(unpack_returned_tuples=True)
    restored.execute((root / "tests" / "mock_wow.lua").read_text(encoding="utf-8-sig"))
    restored.globals().SAVED_SELECTION = selected
    restored.execute((root / "ChatMeters.lua").read_text(encoding="utf-8-sig"))
    restored.execute('''
        EllesmereUIChatMetersDB={metersSelected=SAVED_SELECTION}
        local A=EllesmereUIChatMeters
        local windows=DM._windows; DM._windows=nil
        Event("PLAYER_LOGIN")
        assert(A.pendingRestore==SAVED_SELECTION)
        DM._windows=windows; A.pendingAuto=true; A:Tick()
        assert(A.active==SAVED_SELECTION and A.body:IsVisible()==SAVED_SELECTION)
        assert(A.pendingRestore==nil and A.pendingAuto==nil)
        A:SetActive(not SAVED_SELECTION)
        assert(EllesmereUIChatMetersDB.metersSelected==not SAVED_SELECTION)
        A:Tick()
        assert(A.active==not SAVED_SELECTION, "Restore only once; keep live switching")
    ''')
print("PASS: saved Meters/Chat selection restores after delayed login and stays switchable")

# Current hosts publish read-only core modules. Companion settings must never
# even read that registry when the supported plugin API is present.
modern = LuaRuntime(unpack_returned_tuples=True)
modern.execute((root / 'tests/mock_wow.lua').read_text())
modern.execute((root / 'ChatMeters.lua').read_text())
modern.execute('''
local e=EllesmereUI
e._modules=setmetatable({}, {__index=function() error('read private core pages') end,
    __newindex=function() error('write private core pages') end})
registrations=0; opened=0; rows={}
e.RegisterPlugin=function(id,spec)
    assert(id=='EllesmereUIChatMeters' and spec.label=='Grimlight Meters')
    registrations=registrations+1; plugin=spec; return true
end
e.OpenPlugin=function(id,key,page)
    assert(id=='EllesmereUIChatMeters' and key=='ChatEmbedding' and page=='Embedding')
    if combat then return false end
    opened=opened+1; return true
end
e.Widgets={SectionHeader=function() return {},30 end,
    DualRow=function(_,parent,y,left,right) rows[#rows+1]={left,right}; return {},40 end}
''')
modern.execute((root / 'SettingsIntegration.lua').read_text())
modern.execute('''
Event('PLAYER_LOGIN')
local A=EllesmereUIChatMeters
local saved=A.db
for i=1,3 do A:IntegrateOptions(); Event('ADDON_LOADED','EllesmereUIOptions') end
assert(registrations==1 and A.db==saved)
local module=plugin.modules[1]
assert(module.pages[1]=='Embedding' and module.buildPage('Embedding',{},-10)==120)
assert(#rows==2)
rows[1][1].setValue(true); rows[1][2].setValue(false)
rows[2][1].setValue(false); rows[2][2].setValue(true)
assert(A.db.enabled and not A.db.returnOnExit and not A.db.autoDungeon and A.db.autoRaid)
assert(A.db==saved and A.ready and A.left.frame:GetParent()==A.body)
A:OpenOptions(); assert(opened==1 and not A.optionsOpenTicker)
combat=true; A:OpenOptions(); assert(opened==1 and not A.optionsOpenTicker)
combat=false
-- Search builds only controls; it does not move panes or change saved choices.
local parents=A.left.frame.parentChanges
module.buildPage('Embedding',{},0)
assert(A.left.frame.parentChanges==parents and A.db==saved and A.db.autoRaid)
''')
print('PASS: plugin settings register once, preserve saves/embedding, avoid private pages and honor host combat handling')
