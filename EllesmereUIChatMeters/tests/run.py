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
