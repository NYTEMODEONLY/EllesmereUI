-- Fresh-login fixture: no remembered frame objects survive a /reload.
local A=EllesmereUIChatMeters
local first,second,extra=NewWindow(RESTORE_LEFT),NewWindow(RESTORE_RIGHT),NewWindow(0)
-- Native meters are built over successive frames after login.
DM._windows={first}
Event("PLAYER_LOGIN")
assert(A.left==first and not A.right, "Adopt the first window regardless of its mode")
DM._windows={first,second,extra}; A:Tick(); A:SetActive(true)
assert(A.left==first and A.right==second, "Restore both pane windows without requiring Damage/Healing types")
assert(first.frame:GetParent()==A.body and second.frame:GetParent()==A.body)
assert(first.frame:IsVisible() and second.frame:IsVisible(), "Both panes must be visible after login")
assert(extra.frame:GetParent()==UIParent, "Do not steal a later Damage window to replace Threat")
assert(first.curDMType==RESTORE_LEFT and second.curDMType==RESTORE_RIGHT, "Never change persisted modes")
first.curDMType="THREAT"; second.curDMType=5; A:Tick()
assert(A.left==first and A.right==second, "Changing modes must preserve live ownership")
-- Profile rebuild loses objects just like reload, including two Threat windows.
first.frame:Hide(); first.frame:SetParent(nil)
second.frame:Hide(); second.frame:SetParent(nil)
DM._windows={}; A:Tick()
local rebuiltLeft,rebuiltRight=NewWindow("THREAT"),NewWindow("THREAT")
DM._windows={rebuiltLeft}; A:Tick()
DM._windows={rebuiltLeft,rebuiltRight}; A:Tick(); A:SetActive(true)
assert(A.left==rebuiltLeft and A.right==rebuiltRight)
assert(rebuiltLeft.frame:IsVisible() and rebuiltRight.frame:IsVisible())
assert(not A.records[first] and not A.records[second], "Retired frames must not reappear")
