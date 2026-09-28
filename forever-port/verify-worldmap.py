"""Exercise the real WorldMap skin with Forever-native preservation fixtures.

Uses Lua 5.1 via lupa. Mocks validate state and callback behavior, not live
rendering, collection data, or WoW's secure execution rules.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT.parent / "EllesmereUIBlizzardSkin" / "EllesmereUIBlizzardSkin_WindowPacks.lua"
source = PACK.read_text(encoding="utf-8")
start = source.index("local function Skin_WorldMap()")
end = source.index("--  Micro Menu & Bags.", start)
section = source[start:end]
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true
local timers={}
local function forbidden() error("skin changed native action, visibility, value, or layout") end
local function texture(text, r,g,b)
    local t={text=text or "native",color={r or .3,g or .6,b or .2},alpha=.65,shown=false,atlas="native"}
    function t:SetAlpha(a) self.alpha=a end
    function t:GetAlpha() return self.alpha end
    function t:SetTextColor(...) self.color={...} end
    function t:SetAllPoints(target) self.allPoints=target end
    function t:SetColorTexture(...) self.fill={...} end
    t.SetText=forbidden; t.Show=forbidden; t.Hide=forbidden
    return t
end
local function frame()
    local f={shown=true,enabled=false,checked=true,width=333,value=7,hooks={},scripts={OnClick=function() end}}
    function f:IsShown() return self.shown end
    function f:IsVisible() return self.shown end
    function f:GetParent() return self.parent end
    function f:HookScript(event,fn) self.hooks[event]=fn end
    for _,key in ipairs({"SetPoint","ClearAllPoints","SetWidth","SetHeight","SetSize","Show","Hide","SetShown","SetValue","SetChecked","SetEnabled","SetScript","SetAttribute","SetText"}) do f[key]=forbidden end
    return f
end
local function pool(...)
    local p={rows={...}}
    function p:EnumerateActive() local i=0; return function() i=i+1; return self.rows[i] end end
    return p
end
local function row()
    local r=frame(); r.Text=texture("[15+] Elite quest",1,.3,.1); r.TagText=texture("(Elite)",1,.3,.1)
    r.Dash=texture("-",.5,.5,.5); r.StorylineTexture=texture(); r.Checkbox=frame(); return r
end
local function bar() return {Back={Texture=texture()},Forward={Texture=texture()},value=27} end
local function control()
    local c=frame(); c.Icon=texture(); c.Text=texture(); c.ResetButton=frame(); return c
end
FFD={}
function GetFFD(f) if not FFD[f] then FFD[f]={} end; return FFD[f] end
Theme={bgR=.08,bgG=.08,bgB=.08,bgA=.95}
function SolidTex() return texture() end
WSkin={}
function WSkin.Shell(_,f) f.shell=true end
function WSkin.RemovePortrait() end
function WSkin.FadeRegions() end
function WSkin.Register() end
function WSkin.AddBorder(f) f.border=true end
function WSkin.Font(fs) if fs then fs.font=true end end
function WSkin.White(fs) fs:SetTextColor(1,1,1) end
function WSkin.EditBox(f) f.inputSkin=true end
function WSkin.Button(f) f.buttonSkin=true end
function WSkin.ScrollBar(f) f.skin=true; f.Back.Texture:SetAlpha(0); f.Forward.Texture:SetAlpha(0) end
function WSkin.RegisterWindow(entry) WSkin.entry=entry end
function WSkin.HookShow(f,fn) f.hooks.OnShow=fn end
function WSkin.Debounce(fn) return fn end
function WSkin.Restrip() end
function SkinMapSideTab(f) assert(not EUI_FOREVER,"Forever hidden side tab was styled"); if f then f.sideSkin=true end end
function hooksecurefunc(name,fn)
    local original=_G[name]; _G[name]=function(...) original(...); fn(...) end
end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
local function flush() local batch=timers; timers={}; for _,fn in ipairs(batch) do fn() end end
WorldMapFrame=frame(); local map=WorldMapFrame
map.WorldMapTrackingOptionsButton=control()
QuestMapFrame=frame(); local qm=QuestMapFrame
qm.DetailsFrame=frame(); qm.DetailsFrame.parent=qm
qm.QuestsTab, qm.EventsTab, qm.MapLegendTab=frame(),frame(),frame()
qm.QuestsTab.shown=false; qm.EventsTab.shown=false; qm.MapLegendTab.shown=false
function qm:HookScript(event,fn) assert(not EUI_FOREVER,"Forever installed Retail QuestMapFrame layout hook"); self.hooks[event]=fn end
QuestScrollFrame=frame(); local qs=QuestScrollFrame
qs.SearchBox=frame(); qs.ScrollBar=bar(); qs.SettingsDropdown=control()
qs.titleFramePool=pool(row()); qs.objectiveFramePool=pool(row())
QuestLogCount=frame(); QuestLogCount.Left,QuestLogCount.Middle,QuestLogCount.Right=texture(),texture(),texture()
QuestLogQuestCount=texture("|cffff000026 / 25",1,0,0)
QuestMapDetailsScrollFrame={ScrollBar=bar()}
QuestInfoObjectivesFrame={Objectives={texture("Finished (Complete)",.2,.8,.1),texture("Unfinished",.9,.9,.9)}}
QuestInfoDescriptionText=texture(); QuestInfoObjectivesText=texture(); QuestInfoGroupSize=texture()
function QuestLogQuests_Update() qs.nativeUpdates=(qs.nativeUpdates or 0)+1 end
function QuestInfo_Display(_,parent)
    parent.nativeDisplays=(parent.nativeDisplays or 0)+1
    QuestInfoObjectivesFrame.Objectives[1]:SetTextColor(.1,.7,.2)
end
QUEST_OBJECTIVE_COMPLETED_FONT_COLOR={GetRGB=function() return .2,.8,.1 end}
QUEST_OBJECTIVE_COMPLETED_FONT_COLOR_DARK_BACKGROUND={GetRGB=function() return .1,.7,.2 end}
function GetMaterialTextColors(material)
    if material=="Default" then return {.1,.1,.1}, {1,.82,0} end
    assert(material=="Stone"); return {.9,.9,.9}, {1,.82,0}
end
function issecretvalue(value) return type(value)=="table" and value.secret end
for _,objective in ipairs(QuestInfoObjectivesFrame.Objectives) do
    function objective:GetTextColor() return unpack(self.color) end
end
QuestInfoObjectivesFrame.Objectives[2].color={.1,.1,.1}
function verify()
    WSkin.entry.apply()
    assert(WSkin.entry.key=="worldmap" and map.shell)
    assert(qs.ScrollBar.Back.Texture.alpha==.65 and qs.ScrollBar.Forward.Texture.alpha==.65)
    assert(QuestMapDetailsScrollFrame.ScrollBar.Back.Texture.alpha==.65 and QuestMapDetailsScrollFrame.ScrollBar.Forward.Texture.alpha==.65)
    assert(qs.ScrollBar.value==27 and QuestMapDetailsScrollFrame.ScrollBar.value==27)
    assert(QuestLogCount.border and QuestLogCount.width==333 and QuestLogCount.shown)
    assert(QuestLogQuestCount.font and QuestLogQuestCount.text=="|cffff000026 / 25" and QuestLogQuestCount.color[1]==1 and QuestLogQuestCount.color[2]==0)
    for _,c in ipairs({qs.SettingsDropdown,map.WorldMapTrackingOptionsButton}) do
        assert(c.border and c.Icon.atlas=="native" and c.Icon.alpha==.65)
        assert(c.checked and not c.enabled and c.scripts.OnClick and c.ResetButton.scripts.OnClick)
    end
    for _,p in ipairs({qs.titleFramePool,qs.objectiveFramePool}) do
        local r=p.rows[1]
        assert(r.Text.font and r.TagText.font and r.Dash.font)
        assert(r.Text.text=="[15+] Elite quest" and r.Text.color[1]==1 and r.Text.color[2]==.3)
        assert(r.TagText.text=="(Elite)" and r.TagText.color[2]==.3 and r.Checkbox.checked)
        assert(r.StorylineTexture.atlas=="native" and not r.StorylineTexture.shown)
    end
    local complete=QuestInfoObjectivesFrame.Objectives[1]
    assert(complete.font and complete.color[1]==.1 and complete.color[2]==.7)
    assert(QuestInfoObjectivesFrame.Objectives[2].color[1]==.9)
    QuestInfo_Display("template",qm.DetailsFrame)
    assert(complete.color[1]==.1 and complete.color[2]==.7 and qm.DetailsFrame.nativeDisplays==1)
    complete:SetTextColor(.3,.9,.4); flush()
    assert(complete.color[1]==.3 and complete.color[2]==.9,"delayed skin overwrote native objective status color")
    local body=QuestInfoObjectivesFrame.Objectives[2]
    -- Simulate native reuse of one objective for complete and then incomplete
    -- text. No cached status may survive the native color update.
    body:SetTextColor(.2,.8,.1); WSkin.entry.apply()
    assert(body.color[1]==.1 and body.color[2]==.7,"completed status didn't use native dark-background color")
    WSkin.entry.apply(); assert(body.color[1]==.1 and body.color[2]==.7,"completed recolor wasn't idempotent")
    body:SetTextColor(.1,.1,.1); WSkin.entry.apply()
    assert(body.color[1]==.9 and body.color[2]==.9,"recycled unfinished objective retained completion color")
    WSkin.entry.apply(); assert(body.color[1]==.9,"light body recolor wasn't idempotent")
    body:SetTextColor(1,.25,0); WSkin.entry.apply()
    assert(body.color[1]==1 and body.color[2]==.25,"unknown warning color was changed")
    local secret={secret=true}; body.color={secret,secret,secret}; WSkin.entry.apply()
    assert(body.color[1]==secret,"secret objective color was compared or overwritten")
    body:SetTextColor(.9,.9,.9)
    local late=row(); late.Text.color={.5,.5,.5}; qs.titleFramePool.rows[2]=late
    QuestLogQuests_Update(); assert(qs.nativeUpdates==1 and late.Text.font and late.Text.color[1]==.5)
    assert(not qm.hooks.OnShow and (not FFD[qm] or not FFD[qm].sideSeatHook))
    for _,tab in ipairs({qm.QuestsTab,qm.EventsTab,qm.MapLegendTab}) do assert(not tab.shown and not tab.sideSkin and tab.width==333) end
    WSkin.entry.apply(); assert(QuestLogCount.width==333 and QuestLogQuestCount.text=="|cffff000026 / 25")
    -- The non-Forever branch retains its pre-existing white objective styling.
    EUI_FOREVER=false; WSkin.entry.apply(); assert(complete.color[1]==1 and complete.color[2]==1)
end
''')
lua.execute(section)
lua.eval("verify")()
print("PASS: map objective/difficulty/cap semantics, native controls, arrows, pooled row fonts and Forever hidden-tab layout isolation")
