local A,e=EllesmereUIChatMeters,EllesmereUI
A:SetOption("enabled",true)
SELECTED=ChatFrame1
A:SetActive(true)
local left,right=A.left,A.right
local lr,rr=A.records[left],A.records[right]
local lp,rp=left.frame.parentChanges,right.frame.parentChanges
EditModeManagerFrame=CreateFrame("Frame",nil,UIParent)

-- Every combination of edit, unlock, settings and resize, for BOTH selected
-- views, including returning out of the combination without a reload.
for _,metersSelected in ipairs({true,false}) do
    A:SetActive(metersSelected)
    for mask=0,15 do
        EditModeManagerFrame:SetShown(mask%2==1)
        e._unlockActive=math.floor(mask/2)%2==1
        DM._optionsOpen=math.floor(mask/4)%2==1
        CHAT._chatSizingActive=math.floor(mask/8)%2==1
        PANEL:SetSize(450+mask*7,220+mask*4)
        left.frame:Show(); right.frame:Show() -- upstream preview visibility
        A:Tick()
        assert(A.ready and A.records[left]==lr and A.records[right]==rr)
        assert(left.frame:GetParent()==A.body and right.frame:GetParent()==A.body)
        assert(A.button:IsShown(), "Sidebar icon survives every UI-mode combination")
        assert(left.frame:IsVisible()==metersSelected and right.frame:IsVisible()==metersSelected,
            "Mode changes preserve the selected chat/meters view")
    end
end
assert(left.frame.parentChanges==lp and right.frame.parentChanges==rp,
    "No detach/re-attach during the 32 mode/view combinations")
EditModeManagerFrame:Hide(); e._unlockActive=false; DM._optionsOpen=false; CHAT._chatSizingActive=false
A:SetActive(true)

local width,height=left.frame:GetWidth(),left.frame:GetHeight()
left.frame:ClearAllPoints()
local _,relative=left.frame:GetPoint(1)
assert(relative==A.body, "Clearing standalone anchors cannot unanchor an embedded window")
left.frame:SetPoint("TOPLEFT",UIParent,"BOTTOMLEFT",1400,400)
local _,relative=left.frame:GetPoint(1)
assert(relative==A.body and left.frame:GetNumPoints()==1, "Immediately reject standalone repositioning")
left.frame:SetSize(700,500)
left.frame:SetWidth(900); left.frame:SetHeight(600); left.frame:SetScale(2)
left.frame:SetFrameStrata("HIGH"); left.frame:SetFrameLevel(200)
assert(left.frame:GetWidth()==width and left.frame:GetHeight()==height and left.frame:GetScale()==1)
assert(left.frame:GetFrameStrata()=="MEDIUM" and left.frame:GetFrameLevel()==125)
left.frame:SetParent(UIParent)
assert(left.frame:GetParent()==A.body, "Immediately correct a live window's external reparent")
A:ReleaseAll(); A:Detach(left,true)
assert(A.records[left]==lr and left.frame:GetParent()==A.body, "Central policy rejects accidental live release")

-- Temporarily hidden/missing Settings must not delete the Meters entry point.
CHAT_CONFIG.showSettings=false; CHAT_DATA.settingsBtn:Hide(); A:Tick()
assert(A.button:IsShown() and A.button:GetParent()==CHAT_DATA.sidebar)
local originalSettings=CHAT_DATA.settingsBtn
CHAT_DATA.settingsBtn=nil; A:Tick(); assert(A.button:IsShown())
CHAT_DATA.settingsBtn=originalSettings; CHAT_CONFIG.showSettings=true; originalSettings:Show(); A:Tick()

-- Temporarily unavailable host: keep ownership and restore the same snapshots.
local panel=CHAT_DATA.bg
CHAT_DATA.bg=nil; A:Tick()
assert(left.frame:GetParent()==A.body and A.records[left]==lr)
CHAT_DATA.bg=panel; A:Tick(); assert(A.button:IsShown() and A.records[left]==lr)
local savedChat=e._ModuleNS.EllesmereUIChat
e._ModuleNS.EllesmereUIChat=nil; A:Tick()
assert(left.frame:GetParent()==A.body and A.records[left]==lr)
e._ModuleNS.EllesmereUIChat=savedChat; A:Tick(); assert(A.ready and A.button:IsShown())
CHAT_CONFIG.enabled=false; A:Tick(); assert(left.frame:GetParent()==A.body)
CHAT_CONFIG.enabled=true; A:Tick(); assert(A.ready)

-- Mirror the actual unlock API, including the destructive unregister method
-- which this companion must never call. Saved anchor links remain untouched.
local writes=0
local links={EDM_Win1={target="EDM_Win2"}}
e._unlockRegisteredElements={}
e.UnregisterUnlockElement=function() error("Would delete saved anchor links") end
e.RegisterUnlockElements=function(self,elements)
    for _,element in ipairs(elements) do self._unlockRegisteredElements[element.key]=element end
end
local function NewElement(index)
    return {key="EDM_Win"..index,
        getFrame=function() return DM._windows[index].frame end,
        getSize=function() return 375,180 end,
        setWidth=function(_,v) writes=writes+1; DM._windows[index].frame:SetWidth(v) end,
        setHeight=function() writes=writes+1 end,
        savePosition=function() writes=writes+1 end,
        clearPosition=function() writes=writes+1 end,
        applyPosition=function() writes=writes+1 end,
    }
end
e:RegisterUnlockElements({NewElement(1),NewElement(2),NewElement(3)})
A:Tick()
local element=e._unlockRegisteredElements.EDM_Win1
assert(element.getFrame("EDM_Win1")==nil, "Embedded windows have no standalone mover")
element.setWidth("EDM_Win1",999); element.setHeight("EDM_Win1",777)
element.savePosition("EDM_Win1"); element.clearPosition("EDM_Win1"); element.applyPosition("EDM_Win1")
assert(writes==0 and links.EDM_Win1.target=="EDM_Win2", "Mover writes cannot alter saved standalone settings")
local standaloneIndex
for index, window in ipairs(DM._windows) do
    if window~=A.left and window~=A.right then standaloneIndex=index end
end
assert(standaloneIndex, "Fixture includes a standalone window")
local standaloneKey="EDM_Win"..standaloneIndex
assert(e._unlockRegisteredElements[standaloneKey].getFrame(standaloneKey)==DM._windows[standaloneIndex].frame,
    "Unembedded windows keep normal movers")
e:RegisterUnlockElements({NewElement(1)})
assert(e._unlockRegisteredElements.EDM_Win1.getFrame("EDM_Win1")==nil,
    "Re-registrations are guarded immediately")

-- A genuine destruction/rebuild retires old objects without resurrecting them.
left.frame:Hide(); left.frame:SetParent(nil)
assert(not left.frame:IsShown())
DM._windows={right}; A:Tick(); Flush()
assert(not A.records[left] and A.records[right]==rr and right.frame:GetParent()==A.body)
assert(A.button:IsShown() and A.ready, "Surviving meter and icon remain while the other window is absent")
right.frame:Hide(); right.frame:SetParent(nil); DM._windows={}; A:Tick(); Flush()
assert(A.ready and A.button:IsShown() and A.waitingText:IsShown(), "Empty rebuild retains an entry point")
DM._windows={NewWindow(0),NewWindow(2),NewWindow(5)}
e:RegisterUnlockElements({NewElement(1),NewElement(2),NewElement(3)})
assert(A.ready and A.left==DM._windows[1] and A.left.frame:GetParent()==A.body and not A.waitingText:IsShown(),
    "Profile rebuild registration adopts new windows immediately, without waiting for the ticker")
A:SetOption("enabled",false)
element=e._unlockRegisteredElements.EDM_Win1
assert(element.getFrame("EDM_Win1")==DM._windows[1].frame, "Explicit disable restores normal mover behavior")
element.savePosition("EDM_Win1"); assert(writes==1)
assert(DM._windows[1].frame:GetParent()==UIParent and DM._windows[1].frame:GetWidth()==375)
