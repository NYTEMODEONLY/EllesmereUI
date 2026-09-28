"""Offline Lua 5.1 syntax and bootstrap regression tests; requires lupa.

Set PYTHONPATH to a directory containing lupa, then run this file.
These tests do not emulate WoW rendering, secure execution, or combat.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT.parent


def runtime(version="1.60.1", interface=16001):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().test_version = version
    lua.globals().test_interface = interface
    lua.execute('''
        frames = {}
        function GetBuildInfo() return test_version, "69913", "Sep 17 2026", test_interface end
        function CreateFrame()
            local f = {events = {}}
            function f:RegisterEvent(event) self.events[event] = true end
            function f:UnregisterAllEvents() self.events = {} end
            function f:SetScript(kind, callback) self[kind] = callback end
            frames[#frames+1] = f
            return f
        end
        function Fire(event, ...)
            for _, f in ipairs(frames) do
                if f.events[event] and f.OnEvent then f:OnEvent(event, ...) end
            end
        end
        SlashCmdList = {}
        UISpecialFrames = {}
        C_SpecializationInfo = {
            GetSpecialization = function() return 1 end,
            GetSpecializationInfo = function() return 12345, "Forever Paladin" end,
            GetActiveSpecGroup = function() return 1 end,
            GetNumSpecializationsForClassID = function() return 3 end,
        }
        C_Item = {
            GetItemInfo = function() return "Native item" end,
            GetItemInfoInstant = function() return 42 end,
            GetItemQualityColor = function() return 0, 1, 0, "ff00ff00" end,
            IsEquippableItem = function() return true end,
        }
        forwarded = 0
        handler = function() forwarded = forwarded + 1 end
        function geterrorhandler() return handler end
        function seterrorhandler(fn) handler = fn end
        function debugstack() return "test stack" end
    ''')
    return lua


def run(lua, name):
    lua.execute((ROOT / name).read_text(encoding="utf-8-sig"))


lua = runtime()
compile_lua = lua.eval('function(s, name) local f,e = loadstring(s,name); return f ~= nil,e end')
files = [p for folder in ADDONS.glob("Ellesmere*") for p in folder.rglob("*.lua")]
failures = []
for path in files:
    ok, error = compile_lua(path.read_text(encoding="utf-8-sig"), str(path))
    if not ok:
        failures.append((str(path), error))
assert not failures, failures
print(f"PASS: Lua 5.1 syntax for {len(files)} suite files")

for version, interface, forever, blocked in [
    ("1.60.1", 16001, True, False),
    ("1.60.2", 16002, True, False),
    ("1.15.8", 11508, False, True),
    ("5.5.0", 50500, False, True),
    ("12.0.7", 120007, False, True),
    ("12.1.0", 120100, False, False),
    ("1.60.1", 11508, False, True),
]:
    state = runtime(version, interface)
    run(state, "EllesmereUI_ClientGate.lua")
    assert bool(state.globals().EUI_FOREVER) == forever
    assert bool(state.globals().EUI_CLIENT_BLOCKED) == blocked
    assert state.globals().EllesmereUIDB is None
print("PASS: Forever accepted; older Classic/Retail gates retained; DB untouched")

run(lua, "EllesmereUI_ClientGate.lua")
run(lua, "EllesmereUI_Forever.lua")
lua.execute('''
    assert(GetSpecialization() == 1)
    assert(GetSpecializationInfo(1) == 12345)
    assert(WOW_PROJECT_ID == nil) -- Never spoof project identity.
    assert(GetItemInfo == C_Item.GetItemInfo)
    assert(GetItemInfoInstant == C_Item.GetItemInfoInstant)
    assert(GetItemQualityColor == C_Item.GetItemQualityColor)
    assert(IsEquippableItem == C_Item.IsEquippableItem)
    geterrorhandler()("EllesmereUI test error")
    geterrorhandler()("OtherAddon test error")
    assert(forwarded == 2)
    assert(#EUI_FOREVER_STATUS.errors == 1)
    assert(EUI_FOREVER_STATUS.Report():find("EllesmereUI test error", 1, true))
''')
existing = runtime()
run(existing, "EllesmereUI_ClientGate.lua")
existing.execute('GetSpecialization = function() return 99 end')
run(existing, "EllesmereUI_Forever.lua")
assert existing.eval("GetSpecialization()") == 99
print("PASS: aliases preserve native globals; diagnostics forward original errors")

protected_errors = runtime()
run(protected_errors, "EllesmereUI_ClientGate.lua")
protected_errors.execute('''
    -- Lua 5.1 has no WoW secret strings: use opaque values that throw on any
    -- inspection/conversion, and verify they only reach the native handler.
    secret = setmetatable({}, {
        __index=function() error("inspected secret") end,
        __tostring=function() error("converted secret") end,
        __concat=function() error("concatenated secret") end,
    })
    function issecretvalue(value) return rawequal(value,secret) end
    forwardedValues={}
    handler=function(err) forwardedValues[#forwardedValues+1]=err; return "native-result" end
    function debugstack(_,_,locals) assert(locals==0); return secret end
''')
run(protected_errors, "EllesmereUI_Forever.lua")
protected_errors.execute('''
    assert(handler("EllesmereUI original failure")=="native-result")
    assert(#EUI_FOREVER_STATUS.errors==1)
    assert(EUI_FOREVER_STATUS.errors[1]=="EllesmereUI original failure\\n<protected>")
    handler("EllesmereUI original failure")
    assert(EUI_FOREVER_STATUS.errorCounts[1]==2)
    assert(handler(secret)=="native-result" and forwardedValues[3]==secret)
    function debugstack() error("stack getter failed") end
    assert(handler("EllesmereUI getter failure")=="native-result")
    assert(forwardedValues[4]=="EllesmereUI getter failure")
    function debugstack() return "[Interface/AddOns/EllesmereUI/test.lua]:9" end
    handler("AnotherAddon invoked EllesmereUI")
    assert(#EUI_FOREVER_STATUS.errors==2)
    assert(EUI_FOREVER_STATUS.errorSites[2]["[Interface/AddOns/EllesmereUI/test.lua]:9"])
    assert(#forwardedValues==5)
''')
print("PASS: protected error/stack values and throwing stack getters never mask original errors; no locals requested")

run(lua, "EllesmereUI_ForeverProfile.lua")
lua.execute('''
    Fire("ADDON_LOADED", "UnrelatedAddon")
    assert(EllesmereUIDB == nil)
    Fire("ADDON_LOADED", "EllesmereUI")
    assert(EllesmereUIDB.activeProfile == "Pickme - Forever")
    local source = EllesmereUIDB.profiles.Pickme
    local copy = EllesmereUIDB.profiles["Pickme - Forever"]
    local function Equal(a,b)
        if type(a) ~= type(b) then return false end
        if type(a) ~= "table" then return a == b end
        for k,v in pairs(a) do if not Equal(v,b[k]) then return false end end
        for k,v in pairs(b) do if not Equal(v,a[k]) then return false end end
        return true
    end
    assert(Equal(source,copy), "Visual profile changed during copy")
    assert(source ~= copy and source.addons ~= copy.addons)
    copy.addons.EllesmereUIUnitFrames.player.__test = true
    assert(source.addons.EllesmereUIUnitFrames.player.__test == nil)
    assert(next(EllesmereUIDB.spellAssignments.profiles["Pickme - Forever"].specProfiles) == nil)
    assert(next(EllesmereUIDB.spellAssignments.profiles.Pickme.specProfiles) ~= nil)
    local original = EllesmereUIDB
    Fire("ADDON_LOADED", "EllesmereUI")
    assert(EllesmereUIDB == original)
''')
run(existing, "EllesmereUI_ForeverProfile.lua")
existing.execute('''
    EllesmereUIDB = { sentinel = true, activeProfile = "Existing beta" }
    local original = EllesmereUIDB
    Fire("ADDON_LOADED", "EllesmereUI")
    assert(EllesmereUIDB == original and EllesmereUIDB.sentinel)
    assert(EllesmereUIDB.activeProfile == "Existing beta")
''')
print("PASS: profile copy matches Pickme; spell stores isolated; existing DB and reloads preserved")

manifests = []
for folder in ADDONS.glob("Ellesmere*"):
    toc = folder / (folder.name + ".toc")
    if not toc.exists():
        continue
    text = toc.read_text(encoding="utf-8-sig")
    assert "16001" in text.splitlines()[0], toc
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            assert (folder / line).exists(), (toc, line)
    manifests.append(toc)
lines = (ROOT / "EllesmereUI.toc").read_text().splitlines()
assert lines.index("EllesmereUI_ClientGate.lua") < lines.index("EllesmereUI_Forever.lua")
assert lines.index("EllesmereUI_ForeverProfile.lua") < lines.index("EllesmereUI_Lite.lua")
print(f"PASS: {len(manifests)} manifests, referenced files, bootstrap ordering")

# Camelot's side tabs are Frames without GetChecked. Verify that the adapter
# leaves native selection to its original SetChecked without extra square art,
# moving/hiding panels, changing inventory slots, or taking over progression.
native = LuaRuntime(unpack_returned_tuples=True)
native.execute('''
    EUI_FOREVER = true
    EUI_FOREVER_STATUS = {}
    EllesmereUI = {}
    windows = {}
    function texture()
        return { SetPoint=function() end, SetWidth=function() end,
            SetColorTexture=function() end, SetShown=function(t,v) t.shown=v end }
    end
    function panel()
        return { CreateTexture=function() error("shared adapter added tab art") end }
    end
    function tab(selected)
        local t=panel()
        t.SelectedTexture={shown=selected,IsShown=function(self) return self.shown end}
        t.SetChecked=function(self,v) self.nativeSelected=v; self.SelectedTexture.shown=v end
        t.OnMouseUp=function() end
        return t
    end
    function hooksecurefunc(t,k,fn)
        local old=t[k]
        t[k]=function(...) old(...); fn(...) end
    end
    CharacterFrame=panel()
    CharacterFrame.ModeTabs={Tabs={}}
    CharacterFrame.RightPaneHost=panel()
    CharacterFrame.LeftPaneHost=panel()
    CharacterFrame.RefreshDisplay=function() end
    nativeRefresh=CharacterFrame.RefreshDisplay
    for i=1,6 do CharacterFrame.ModeTabs.Tabs[i]=tab(i==1) end
    InspectFrame=panel()
    LegacySystemFrame=panel()
    LegacySystemFrame.Tabs={tab(true),tab(false),tab(false)}
    local W={Theme={accR=1,accG=0.5,accB=0}, Shell=function() end,
        AddBorder=function() error("shared adapter added square border") end, CloseButton=function() end, Font=function() end,
        WindowCallback=function(_,f) return f end,
        RegisterWindow=function(e) windows[#windows+1]=e end,
        OnLooksChanged=function(f) repaint=f end}
    ns={WSkin=W}
''')
adapter = (ADDONS / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_Forever.lua').read_text()
native.execute('return function(...)\n' + adapter + '\nend')('EllesmereUIBlizzardSkin', native.globals().ns)
native.execute('''
    for _,e in ipairs(windows) do e.apply() end
    assert(CharacterFrame.RefreshDisplay==nativeRefresh)
    for _,list in ipairs({CharacterFrame.ModeTabs.Tabs,LegacySystemFrame.Tabs}) do
        assert(list[1].SelectedTexture:IsShown() and not list[2].SelectedTexture:IsShown())
        local handler=list[2].OnMouseUp
        for i,t in ipairs(list) do t:SetChecked(i==2) end
        if repaint then repaint() end
        assert(not list[1].SelectedTexture:IsShown() and list[2].SelectedTexture:IsShown())
        assert(list[2].nativeSelected and list[2].OnMouseUp==handler)
    end
''')
print('PASS: six character modes and three Legacy tabs preserve native selection and handlers')
