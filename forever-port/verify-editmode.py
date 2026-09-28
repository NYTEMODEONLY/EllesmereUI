"""Isolated Lua 5.1 checks for Forever Edit Mode cosmetics, not secure-client proof.

No game API is available here. Native setters/actions deliberately raise; fixture
state covers layout, enabled/checked previews, pooled settings, glyphs and fonts.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "EllesmereUIBlizzardSkin" / "EllesmereUIBlizzardSkin_ForeverEditMode.lua"
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true
local style="off"
local function forbidden() error("adapter invoked a native action/setter") end
local function texture()
    local t={alpha=.7,shown=true,color={.5,.5,.5,1},text="native",atlas="native"}
    function t:SetAlpha(a) self.alpha=a end
    function t:GetAlpha() return self.alpha end
    function t:SetColorTexture(...) self.fill={...} end
    function t:SetAllPoints() end
    function t:GetTextColor() return unpack(self.color) end
    function t:SetTextColor(...) self.color={...} end
    t.SetText=forbidden
    return t
end
local function frame()
    local f={shown=false,enabled=false,checked=true,value=7,width=510,parent="native",hooks={}}
    function f:CreateTexture() return texture() end
    function f:HookScript(event,fn) self.hooks[event]=fn end
    function f:GetFontString() return self.Text end
    for _,k in ipairs({"SetScript","SetPoint","SetSize","SetParent","Show","Hide","SetShown","SetText","SetValue","SetMinMaxValues","SetChecked","SetEnabled","UpdateDisplay","RefreshRaidFrames","SaveLayoutChanges","SelectLayout"}) do f[k]=forbidden end
    f.nativeAction=function() return "native action" end
    f.OnClick=f.nativeAction
    f.Text=texture()
    return f
end
local function check() local f=frame(); f.Button=frame(); f.Label=texture(); return f end
local function slider()
    local f=frame(); f.Slider=frame()
    f.Slider.Left,f.Slider.Middle,f.Slider.Right,f.Slider.Thumb=texture(),texture(),texture(),texture()
    f.Back,f.Forward=frame(),frame(); f.Back.Icon,f.Forward.Icon=texture(),texture()
    f.LeftText,f.RightText,f.TopText,f.MinText,f.MaxText=texture(),texture(),texture(),texture(),texture()
    return f
end
local function bar() return {Back={Texture=texture()},Forward={Texture=texture()}} end
local function dialog()
    local f=frame(); f.Title,f.EditBoxLabel,f.NameEditBoxLabel=texture(),texture(),texture()
    f.Border,f.CloseButton,f.LayoutNameEditBox=frame(),frame(),frame()
    f.CharacterSpecificLayoutCheckButton=check()
    for _,k in ipairs({"AcceptButton","CancelButton","SaveAndProceedButton","ProceedButton"}) do f[k]=frame() end
    f.layoutInfo={id=2}; return f
end
local W={Theme={accR=.1,accG=.8,accB=.6,insetR=.04,insetG=.04,insetB=.04,insetA=.85,brdR=.2,brdG=.2,brdB=.2}}
function W.WindowCallback(key,fn) assert(key=="settings"); return function(...) if style~="off" then fn(...) end end end
function W.ResolveTheme() end
function W.Font(f,r,g,b) if f then f.font=true; if r then f.color={r,g,b} end end end
function W.AddBorder(f) f.border=true end
function W.Button(f) f.buttonSkin=true end
function W.StateButtonLabel() end
function W.Checkbox(f,opt) assert(opt.stockCheck); f.checkSkin=true end
function W.Dropdown(f) f.dropdownSkin=true; f.Text.color={1,1,1,1} end
function W.Shell(key,f) assert(key=="settings"); f.shell=true end
function W.Inset(f) f.insetSkin=true end
function W.CloseButton() end
function W.ScrollBar(f) f.Back.Texture.alpha=0; f.Forward.Texture.alpha=0 end
function W.RegisterWindow(entry) W.entry=entry end
function W.OnLooksChanged(fn) W.look=fn end
function hooksecurefunc(object,key,fn)
    local original=object[key]
    object[key]=function(...) original(...); fn(...) end
end
NS={WSkin=W}
C_EditMode=setmetatable({}, {__index=forbidden})
local m=dialog(); EditModeManagerFrame=m
m.LayoutLabel=texture(); m.LayoutDropdown=frame()
m.ShowGridCheckButton,m.EnableSnapCheckButton,m.EnableAdvancedOptionsCheckButton=check(),check(),check()
m.GridSpacingSlider={Slider=slider()}
m.SaveChangesButton,m.RevertAllChangesButton=frame(),frame()
m.Grid,m.MagnetismPreviewLinesContainer,m.Tutorial=frame(),frame(),frame()
m.Grid.texture=texture(); m.MagnetismPreviewLinesContainer.line=texture(); m.Tutorial.Icon=texture()
m.AccountSettings={settingsCheckButtons={SwingTimer=check(),TotemActionBar=check(),RaidFrames=check()}}
local a=m.AccountSettings
a.settingsCheckButtons.TotemActionBar.shown=false
a.SettingsContainer={BorderArt=frame(),ScrollBar=bar(),ScrollChild={AdvancedOptionsContainer={FramesTitle={Title=texture()},CombatTitle={Title=texture()},MiscTitle={Title=texture()}}}}
a.Expander={Label=texture(),Divider=texture()}
local s=dialog(); EditModeSystemSettingsDialog=s
s.Buttons={RevertChangesButton=frame(),Divider=texture()}
local dropdown=frame(); dropdown.Label=texture(); dropdown.Dropdown=frame()
local slide=frame(); slide.Label=texture(); slide.Slider=slider()
local checkbox=check(); local extra=frame(); extra.NewOptionsFrame={Icon=texture()}
s.pools={rows={EditModeSettingDropdownTemplate={dropdown},EditModeSettingSliderTemplate={slide},EditModeSettingCheckboxTemplate={checkbox},EditModeSystemSettingsDialogExtraButtonTemplate={extra}}}
function s.pools:EnumerateActiveByTemplate(template)
    local rows=self.rows[template]; local i=0
    return function() i=i+1; return rows[i] end
end
function s:UpdateDialog() self.nativeRefresh=(self.nativeRefresh or 0)+1 end
for _,name in ipairs({"EditModeLayoutDialog","EditModeImportLayoutDialog","EditModeImportLayoutLinkDialog","EditModeUnsavedChangesDialog"}) do _G[name]=dialog() end
EditModeImportLayoutDialog.ImportBox=frame()
EditModeImportLayoutDialog.ImportBox.EditBox=frame()
EditModeImportLayoutDialog.ImportBox.CharCount=texture()
EditModeImportLayoutDialog.ImportBox.ScrollBar=bar()
function verify()
    assert(W.entry.addons.Blizzard_EditMode)
    W.entry.apply(); assert(not m.shell,"style off mutated UI")
    style="modern"; W.look()
    assert(m.shell and m.Border.insetSkin and m.Title.font)
    assert(m.LayoutDropdown.dropdownSkin and m.LayoutDropdown.Text.font)
    assert(m.LayoutDropdown.Text.color[1]==.5,"native disabled dropdown color changed")
    for _,c in pairs(a.settingsCheckButtons) do
        assert(c.Label.font and c.Button.checkSkin)
        assert(c.Button.checked and not c.Button.enabled and not c.shown)
        assert(c.OnClick==c.nativeAction)
    end
    assert(m.GridSpacingSlider.Slider.Slider.value==7)
    assert(m.GridSpacingSlider.Slider.Slider.Thumb.alpha==.7)
    assert(m.GridSpacingSlider.Slider.Back.Icon.atlas=="native")
    assert(not m.Grid.shell and not m.MagnetismPreviewLinesContainer.shell)
    assert(m.Grid.texture.alpha==.7 and m.Tutorial.Icon.atlas=="native")
    assert(a.SettingsContainer.ScrollBar.Back.Texture.alpha==.7)
    assert(a.SettingsContainer.ScrollBar.Forward.Texture.alpha==.7)
    assert(dropdown.Dropdown.dropdownSkin and slide.Slider.TopText.font and checkbox.Button.checkSkin)
    assert(extra.buttonSkin and extra.NewOptionsFrame.Icon.atlas=="native")
    local late=frame(); late.Label=texture(); late.Dropdown=frame()
    s.pools.rows.EditModeSettingDropdownTemplate[2]=late
    s:UpdateDialog(); assert(s.nativeRefresh==1 and late.Dropdown.dropdownSkin)
    assert(late.OnClick==late.nativeAction and not late.enabled and late.value==7)
    style="off"
    local inactive=check(); s.pools.rows.EditModeSettingCheckboxTemplate[2]=inactive
    s:UpdateDialog(); assert(s.nativeRefresh==2 and not inactive.Button.checkSkin)
    style="modern"; W.look(); assert(inactive.Button.checkSkin)
    for _,f in ipairs({m,s,EditModeLayoutDialog,EditModeImportLayoutDialog,EditModeImportLayoutLinkDialog,EditModeUnsavedChangesDialog}) do
        assert(f.shell and not f.shown and f.width==510 and f.parent=="native")
        assert(f.OnClick==f.nativeAction and f.layoutInfo.id==2)
        assert(not f.AcceptButton.enabled and not f.CancelButton.enabled)
    end
    assert(EditModeImportLayoutDialog.ImportBox.EditBox.font)
    assert(EditModeImportLayoutDialog.ImportBox.ScrollBar.Back.Texture.alpha==.7)
end
''')
lua.execute("local fn=assert(loadstring(...)); fn('EllesmereUIBlizzardSkin',NS)", SOURCE.read_text(encoding="utf-8"))
lua.eval("verify")()
print("PASS: Edit Mode style gate, native handlers/state/layout/previews, pooled settings, dialog inputs, glyphs and slider/scroll values preserved")
