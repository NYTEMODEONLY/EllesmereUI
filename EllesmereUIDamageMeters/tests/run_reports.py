"""Run with Python + lupa. Tests never call the live WoW client."""
import os
from pathlib import Path

from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
os.chdir(root)
lua = LuaRuntime(unpack_returned_tuples=True)
compile_lua = lua.eval("function(source, name) local f, err = loadstring(source, name); assert(f, err); return true end")
for path in root.glob("*.lua"):
    compile_lua(path.read_text(encoding="utf-8-sig"), str(path))
print("PASS: all meter files compile with Lua 5.1 (including local/upvalue limits)")
lua.execute((root / "tests/report_scenarios.lua").read_text(encoding="utf-8"))

source = (root / "EllesmereUIDamageMeters.lua").read_text(encoding="utf-8-sig")
start = source.index("function ns.ResetAllMeterData()")
end = source.index('if not _G["EllesmereUIDMResetBindBtn"]', start)
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().RESET_HELPER_SOURCE = source[start:end]
# Exercise the installed house popup's real dismissal handlers, so the modal
# regression checks do not duplicate their implementation in the test mock.
core = (root.parent / "EllesmereUI/EllesmereUI.lua").read_text(encoding="utf-8-sig")
compile_lua(core, "EllesmereUI.lua")
escape_start = core.index("local function WirePopupEscape(")
escape_end = core.index("local function CreateConfirmPopup()", escape_start)
mouse_start = core.index('    dimmer:SetScript("OnMouseDown", function()', escape_end)
mouse_end = core.index("    -- Close on Escape", mouse_start)
lua.globals().POPUP_HANDLERS_SOURCE = (
    core[escape_start:escape_end]
    + "return function(popup, dimmer)\n"
    + core[mouse_start:mouse_end]
    + "WirePopupEscape(popup, dimmer)\nend"
)
options_start = core.index("    popup._onCancel = opts.onDismiss or opts.onCancel or nil")
options_end = core.index("    -- Single-button mode:", options_start)
lua.globals().POPUP_INPUT_OPTIONS_SOURCE = (
    "return function(popup, opts)\n" + core[options_start:options_end] + "end"
)
lua.execute((root / "tests/dungeon_reset_scenarios.lua").read_text(encoding="utf-8"))

# If the user's chat companion is installed, exercise its existing lifecycle
# scenarios with a sixth header control on every initial/replacement window.
companion = root.parent / "EllesmereUIChatMeters"
if (companion / "tests/mock_wow.lua").exists():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute((companion / "tests/mock_wow.lua").read_text(encoding="utf-8-sig"))
    lua.execute('''
        local original = NewWindow
        local function addReport(w)
            w.reportBtn = CreateFrame("Button", nil, w.header)
            table.insert(w.hdrBtns, 4, w.reportBtn)
            return w
        end
        for _, w in ipairs(DM._windows) do addReport(w) end
        NewWindow = function(...) return addReport(original(...)) end
    ''')
    for name in ("ChatMeters.lua", "SettingsIntegration.lua", "tests/scenarios.lua",
                 "tests/ownership_scenarios.lua", "tests/settings_scenarios.lua"):
        lua.execute((companion / name).read_text(encoding="utf-8-sig"))
    print("PASS: chat companion lifecycle, ownership, and settings scenarios with six header controls")
