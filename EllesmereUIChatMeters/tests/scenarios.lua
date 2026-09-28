local A=EllesmereUIChatMeters
local damage,healing,third=unpack(DM._windows)
local cachedVisibility=damage.UpdateVisibility
Event("PLAYER_LOGIN")
assert(A.ready and not A.active)
assert(damage.frame:GetParent()==A.body and not damage.frame:IsVisible())
assert(third.frame:GetParent()==UIParent and third.frame:IsVisible())
assert(not EllesmereUIChatMetersTab, "No Meters tab created")
assert(A.button:GetParent()==CHAT_DATA.sidebar and A.button:IsShown())
local _,anchor=CHAT_DATA.settingsBtn:GetPoint(1)
assert(anchor==A.button, "Meters icon inserted above Settings")
A:SetActive(true)
assert(damage.frame:IsVisible() and healing.frame:IsVisible())
assert(A.body:GetWidth()==518 and damage.frame:GetWidth()==256)
assert(not damage.windowLocked and not damage.lockBtn:IsVisible())
assert(not damage.header:GetScript("OnMouseDown") and damage.header:GetScript("OnMouseUp"))
for _,button in ipairs(damage.hdrBtns) do assert(button:IsVisible(), "Retain every header control") end
assert(damage.titleText:GetAlpha()==1 and damage.timerText:GetAlpha()==1)
assert(damage.frame._bg:GetAlpha()==0 and damage.header._hdrBg:GetAlpha()==0)
assert(CHAT._chatWins[ChatFrame1].smf:GetAlpha()==0, "Hide chat text under transparent meter area")
assert(PANEL:GetAlpha()==1, "Leave existing chat background unchanged")
local left,right=A:ChooseWindows(DM)
damage.curDMType=5
local editedLeft,editedRight=A:ChooseWindows(DM)
assert(editedLeft==left and editedRight==right, "Editing a meter type keeps it embedded")
damage.curDMType=0
assert(SAVED.width==375 and SAVED.position.x==1000)
damage.hideRule=true; damage.UpdateVisibility()
Flush()
assert(damage.frame:IsVisible(), "Tab controls embedded visibility")
assert(damage.UpdateVisibility==cachedVisibility, "Preserve upstream registered callback identity")
cachedVisibility(); Flush()
assert(damage.frame:IsVisible(), "Cached upstream visibility callback cannot permanently hide embedded meter")
ChatFrame1Tab.mouseOver=true
MOUSE_FOCI={ChatFrame1Tab}
Event("GLOBAL_MOUSE_DOWN","RightButton")
assert(A.active, "Right-clicking a tab leaves meters selected")
A.button.mouseOver=true
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Sidebar click is left to its own OnClick handler")
A.button.mouseOver=SECRET
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Unknown sidebar hit test cannot hide meters")
A.button.mouseOver=false
ChatFrame1Tab.mouseOver=SECRET
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Secret tab hit test cannot drive a selection change")
ChatFrame1Tab.mouseOver=true; ChatFrame1Tab.shown=SECRET
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Secret tab visibility cannot drive a selection change")
ChatFrame1Tab.shown=false
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Hidden tab does not capture a click")
ChatFrame1Tab.shown=true
-- A popup can cover the tab's rectangle without clicking the tab underneath.
local segmentMenu=CreateFrame("Frame",nil,UIParent)
local segmentRow=CreateFrame("Button",nil,segmentMenu)
local segmentLabel=segmentRow:CreateFontString()
for _, segment in ipairs({"Overall", "Current", "Overall", "Current", "Previous Boss"}) do
    segmentMenu:Show()
    MOUSE_FOCI={segmentLabel,ChatFrame1Tab}
    segmentRow:SetScript("OnClick",function()
        damage.selectedSegment=segment
        segmentMenu:Hide()
    end)
    Event("GLOBAL_MOUSE_DOWN","LeftButton")
    segmentRow:GetScript("OnClick")(segmentRow)
    Flush(); A:Tick()
    assert(A.active and damage.frame:IsVisible() and healing.frame:IsVisible(), "Segment selection must keep meters visible")
    assert(damage.selectedSegment==segment and SELECTED==ChatFrame1, "Segment changes without changing the native tab")
end
for _, name in ipairs({"Mode", "Settings", "Report"}) do
    local popup=CreateFrame("Frame",nil,UIParent)
    local row=CreateFrame("Button",nil,popup)
    MOUSE_FOCI={row,ChatFrame1Tab}
    Event("GLOBAL_MOUSE_DOWN","LeftButton")
    assert(A.active, name.." popup must not click the tab underneath")
end
MOUSE_FOCI={}
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Missing mouse focus must not infer a tab click from geometry")
MOUSE_FOCI={SECRET,ChatFrame1Tab}
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Restricted mouse focus must not hide meters")
MOUSE_FOCI=SECRET
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(A.active, "Restricted focus list must not hide meters")
MOUSE_FOCI={ChatFrame1Tab}
Event("GLOBAL_MOUSE_DOWN","LeftButton")
ChatFrame1Tab.mouseOver=false
assert(not A.active and not damage.frame:IsVisible(), "Click same native tab returns chat")
assert(CHAT._chatWins[ChatFrame1].smf:GetAlpha()==1, "Restore chat renderer")
A:SetActive(true)
local tabLabel=CreateFrame("FontString",nil,ChatFrame1Tab)
ChatFrame1Tab.mouseOver=true; MOUSE_FOCI={tabLabel}
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(not A.active, "Clicking a tab's own child still returns to chat")
ChatFrame1Tab.mouseOver=false; MOUSE_FOCI={}
-- The installed tab skin overlays the native tabs with a motion-enabled,
-- click-through strip. General may already be selected behind the meters.
CHAT._chatTabStrip=CreateFrame("Frame",nil,UIParent)
A:SetActive(true)
ChatFrame1Tab.mouseOver=true; MOUSE_FOCI={CHAT._chatTabStrip,ChatFrame1Tab}
Event("GLOBAL_MOUSE_DOWN","LeftButton")
assert(not A.active and not damage.frame:IsVisible() and not healing.frame:IsVisible(),
    "General click through decorative strip hides both meters")
assert(SELECTED==ChatFrame1 and CHAT._chatWins[ChatFrame1].smf:GetAlpha()==1,
    "Already-selected General restores chat without writing native selection")
A:SetActive(true)
ChatFrame1Tab.mouseOver=false; ChatFrame2Tab.mouseOver=true
MOUSE_FOCI={CHAT._chatTabStrip,ChatFrame2Tab}
Event("GLOBAL_MOUSE_DOWN","LeftButton")
SELECTED=ChatFrame2; A:Tick() -- native tab's own click chooses the destination
assert(not A.active and not damage.frame:IsVisible(), "Different tab restores its chat through the strip")
SELECTED=ChatFrame1; ChatFrame2Tab.mouseOver=false; ChatFrame1Tab.mouseOver=true
A:SetActive(true)
local coveringMenu=CreateFrame("Button",nil,UIParent)
for _, foci in ipairs({{coveringMenu,CHAT._chatTabStrip,ChatFrame1Tab},
    {CHAT._chatTabStrip,coveringMenu,ChatFrame1Tab}, {CHAT._chatTabStrip,SECRET,ChatFrame1Tab},
    {CHAT._chatTabStrip}}) do
    MOUSE_FOCI=foci; Event("GLOBAL_MOUSE_DOWN","LeftButton")
    assert(A.active, "Strip cannot make an overlapping popup, restricted focus, or empty area a tab click")
end
MOUSE_FOCI={CHAT._chatTabStrip,ChatFrame1Tab}
Event("GLOBAL_MOUSE_DOWN","RightButton")
assert(A.active, "Tab context-menu click does not toggle meters")
ChatFrame1Tab.mouseOver=false; MOUSE_FOCI={}; CHAT._chatTabStrip=nil
A:SetActive(true); SELECTED=ChatFrame2; A:Tick()
assert(not A.active, "Native selection change returns chat")
ZONE_KIND,ZONE_ID="party",1; A:CheckZone(); A:Tick()
assert(A.active, "Dungeon auto select")
A:SetActive(false); A:CheckZone(); A:Tick()
assert(not A.active, "Manual chat choice survives repeated zone events")
ZONE_KIND,ZONE_ID="raid",2; A:CheckZone(); A:Tick()
assert(A.active, "Raid auto select")
ZONE_KIND,ZONE_ID="none",0; A:CheckZone(); A:Tick()
assert(not A.active, "Return on exit")
A:SetOption("autoDungeon",false)
ZONE_KIND,ZONE_ID="party",3; A:CheckZone(); A:Tick()
assert(not A.active, "Dungeon auto can be disabled")
A:SetActive(true); A:SetOption("returnOnExit",false)
ZONE_KIND="none"; A:CheckZone(); A:Tick()
assert(A.active, "Keep meters after exit option")
A:SetOption("enabled",false)
assert(damage.frame:GetParent()==UIParent and damage.frame:GetWidth()==375 and damage.frame:GetHeight()==180)
assert(not damage.windowLocked and damage.titleText:GetAlpha()==1)
assert(damage.frame._bg:GetAlpha()==1 and damage.header._hdrBg:GetAlpha()==1)
assert(damage.header:GetScript("OnMouseDown"), "Restore native drag script")
local _,restoredAnchor=CHAT_DATA.settingsBtn:GetPoint(1)
assert(restoredAnchor==CHAT_DATA.portalBtn and not A.button:IsShown(), "Restore sidebar layout")
assert(damage.segmentBtn:GetParent()==damage.header and damage.hdrBtns[1]:IsVisible()==damage.frame:IsVisible())
assert(not damage.frame:IsShown(), "Original meter hide rule restored")
damage.hideRule=false; A:SetOption("enabled",true)
EllesmereUI._unlockActive=true; A:Tick()
assert(A.ready and damage.frame:GetParent()==A.body and A.button:IsShown(), "Unlock mode keeps embedding and icon")
EllesmereUI._unlockActive=false; A:Tick(); assert(A.ready)
PANEL:SetSize(620,300); A:Tick()
assert(damage.frame:GetWidth()==306, "Chat resize updates both windows")
ChatFrame2Tab.right=SECRET; A:Tick()
assert(A.button:IsShown(), "Sidebar placement does not read native tab geometry")
CHAT_DATA.settingsBtn:ClearAllPoints()
CHAT_DATA.settingsBtn:SetPoint("TOP",CHAT_DATA.portalBtn,"BOTTOM",0,-14)
A:Tick()
local _,reflowAnchor=CHAT_DATA.settingsBtn:GetPoint(1)
assert(reflowAnchor==A.button and A.sidebarPoints[1][5]==-14, "Adopt upstream sidebar reflow")
ChatFrame2Tab.right=360
local oldDamage,oldHealing=damage,healing
oldDamage.frame:Hide(); oldDamage.frame:SetParent(nil)
oldHealing.frame:Hide(); oldHealing.frame:SetParent(nil)
damage,healing=NewWindow(0),NewWindow(2)
DM._windows={damage,healing,third}; A:Tick()
Flush()
assert(A.ready and damage.frame:GetParent()==A.body)
assert(not oldDamage.frame:IsShown() and oldDamage.frame:GetParent()==nil, "Retired frames never resurrect")
A:SetActive(true)
CHAT._chatStackHidden=true; A:Tick(); assert(not damage.frame:IsVisible())
CHAT._chatStackHidden=false; A:Tick(); assert(damage.frame:IsVisible())
DM._windows={damage,third}; A:Tick()
assert(A.ready and damage.frame:GetParent()==A.body and A.button:IsShown(), "Missing healing window retains damage and icon")
DM._windows={damage,healing,third}; A:Tick(); assert(A.ready)
assert(A.right==third, "Returning windows must not steal an already adopted pane")
healing=A.right -- the remaining geometry checks apply to the current right pane
PANEL:SetSize(250,200); A:Tick()
assert(A.ready and damage.frame:GetParent()==A.body and damage.frame:GetWidth()==121,
    "Narrow chat keeps meters embedded")
PANEL:SetSize(520,280); A:Tick(); assert(A.ready)
CHAT_CONFIG.inputOnTop=true; CHAT_DATA._smfTopExtra=30; A:Tick()
assert(A.body:GetHeight()==246, "Top input stays available")
CHAT_CONFIG.inputOnTop=false; CHAT_DATA._smfTopExtra=0
A:OpenOptions(); assert(OPENED_CATEGORY==123)
damage.frame.protected=true; A:Tick(); assert(not A.ready, "Unknown protected windows are not adopted")
damage.frame.protected=false; A:Tick(); assert(A.ready)
local before=#FRAMES
for i=1,5 do
    EllesmereUI._unlockActive=true; A:Tick()
    EllesmereUI._unlockActive=false; A:Tick()
end
assert(#FRAMES==before, "Repeated edit mode must not allocate more controls")
local normalTick=A.Tick
A.Tick=function() error("simulated future incompatibility") end
A:SafeTick()
assert(A.failed and damage.frame:GetParent()==A.body and A.root:IsShown() and A.button:IsShown(), "Runtime error retains ownership and sidebar")
A.Tick=normalTick
A:SetOption("enabled",true)
assert(not A.failed and A.ready, "Explicit enable can retry after compatibility error")
A:SetOption("enabled",false)
assert(SAVED.width==375 and SAVED.height==180 and SAVED.position.x==1000, "Upstream settings untouched")

A:SetOption("enabled",true)
SELECTED=ChatFrame2
ChatFrame2.FontStringContainer:SetAlpha(1)
ChatFrame2.ScrollBar.Track:SetAlpha(1)
A:SetActive(true)
assert(ChatFrame2.FontStringContainer:GetAlpha()==0 and CombatLogQuickButtonFrame_Custom:GetAlpha()==0)
A:SetActive(false)
assert(ChatFrame2.FontStringContainer:GetAlpha()==1 and CombatLogQuickButtonFrame_Custom:GetAlpha()==1)
A:SetActive(true); SELECTED=ChatFrame1; A:Tick()
assert(ChatFrame2.FontStringContainer:GetAlpha()==0 and CombatLogQuickButtonFrame_Custom:GetAlpha()==1,
    "Combat Log restoration respects changed native selection without leaving quick buttons dimmed")
A:SetActive(true)
local damageRecord,healingRecord=A.records[damage],A.records[healing]
local damageParents,healingParents=damage.frame.parentChanges,healing.frame.parentChanges
local damageRefreshes,healingRefreshes=damage.refreshes,healing.refreshes
CHAT._chatSizingActive=true
A:Tick()
assert(A.ready and A.active and damage.frame:IsVisible(), "Grabbing chat grip never releases meters")
for _,size in ipairs({{640,320},{410,210},{240,150},{720,380}}) do
    PANEL:SetSize(size[1],size[2])
    assert(damage.frame:GetWidth()==(size[1]-8)/2 and healing.frame:GetWidth()==(size[1]-8)/2,
        "Both meters resize immediately before the periodic ticker")
    assert(damage.frame:GetHeight()==size[2]-30, "Meter height tracks chat content")
    assert(damage.frame:IsVisible() and healing.frame:IsVisible(), "Meters stay visible during every resize sample")
end
assert(damage.refreshes==damageRefreshes and healing.refreshes==healingRefreshes,
    "Per-frame geometry does not fetch combat data")
A:Tick()
assert(damage.refreshes==damageRefreshes+1 and healing.refreshes==healingRefreshes+1,
    "Coalesce meter refreshes at the normal ticker rate")
local lastWidth=damage.frame:GetWidth()
PANEL:SetSize(0,0); A:Tick()
assert(A.ready and damage.frame:IsVisible() and damage.frame:GetWidth()==lastWidth,
    "Transient invalid geometry retains last valid embedded layout")
PANEL:SetSize(520,280)
CHAT._chatSizingActive=nil
A:Tick()
assert(A.records[damage]==damageRecord and A.records[healing]==healingRecord,
    "Release of chat grip retains the same embedding records")
assert(damage.frame.parentChanges==damageParents and healing.frame.parentChanges==healingParents,
    "No temporary standalone reparenting during resize")
A:SetActive(false)
CHAT._chatSizingActive=true; PANEL:SetSize(600,300); A:Tick()
assert(not damage.frame:IsVisible() and not healing.frame:IsVisible(),
    "Resizing while chat is selected does not reveal meters")
CHAT._chatSizingActive=nil
A:SetOption("enabled",false)
