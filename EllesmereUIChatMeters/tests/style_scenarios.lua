-- Runs with the real upstream sidebar kits and Forever plate renderer.
local A, chat = EllesmereUIChatMeters, CHAT.ECHAT
local stock = STYLE ~= "eui"
chat.SB_Latch()
local kit = chat.SB_KIT
if stock then
    CHAT_DATA.settingsBtn._icon = CHAT_DATA.settingsBtn:CreateTexture()
    chat.SB_Dress(CHAT_DATA.settingsBtn, "settings")
    chat.SB_ApplyScale(CHAT_DATA, 1, true)
end
Event("PLAYER_LOGIN")
assert(A.ready and not A.failed, A.problem)
local button = A.button
assert(button._metersKit == kit)
if stock then
    assert(button._sbEntry.n == kit.copy.n and button._sbEntry.plate == kit.copy.plate)
    assert(button._icon:IsShown() and not button.lines[1]:IsShown())
    assert(button._icon.texture:find("meters.tga", 1, true))
    assert(button:GetWidth() == kit.copy.w, "generic plate width, not the Settings gear")
    if STYLE == "forever" then
        assert(button._fvPlate.host:IsShown(), "Forever bronze plate")
        assert(button._icon.color[1] == chat.FV.tan[1], "Forever tan glyph")
    end
else
    assert(button.lines[1]:IsShown() and not button._icon:IsShown())
end
-- Hover, click, hide and release must not accumulate decoration or stuck presses.
button:GetScript("OnEnter")(button)
if STYLE == "forever" then assert(button._fvPlate.lift:IsShown()) end
button:GetScript("OnLeave")(button)
button:GetScript("OnClick")(button, "LeftButton")
assert(A.active)
if stock then assert(button.highlightLocked) end
button:GetScript("OnClick")(button, "LeftButton")
assert(not A.active)
if stock then
    assert(not button.highlightLocked)
    button:GetScript("OnMouseDown")(button, "LeftButton")
    assert(button._sbPushed and button._icon:GetAlpha() == 0.75)
end
button:Hide()
assert(not A.iconHovered and not button._sbPushed)
if STYLE == "forever" then assert(not button._fvPlate.lift:IsShown(), "hidden hover cleans up") end
A:Tick()
local count = #FRAMES
for i=1,30 do A:Tick() end
assert(#FRAMES==count, "no repeated plate creation")
-- Scale and spacing use the actual kit, including transparent art pads.
for _, scale in ipairs({0.75, 1, 1.5, 2}) do
    CHAT_CONFIG.sidebarIconScale=scale
    CHAT_CONFIG.stockIconSpacing=13
    if stock then chat.SB_ApplyScale(CHAT_DATA, scale, true) end
    A:Tick()
    if stock then
        assert(button:GetWidth()==kit.copy.w*scale)
        assert(button._icon:GetWidth()==18*scale)
        local _,_,_,_,y=CHAT_DATA.settingsBtn:GetPoint(1)
        assert(y==-(13-button._sbPadB-CHAT_DATA.settingsBtn._sbPadT))
    end
end
CHAT_CONFIG.showSettings=false; CHAT_DATA.settingsBtn:Hide(); A:Tick()
assert(button:IsShown(), "hidden Settings does not remove Meters")
CHAT_CONFIG.sidebarVisibility="mouseover"; CHAT_DATA.sidebar:SetAlpha(0); A:Tick()
assert(not button:IsShown(), "faded sidebar has no invisible custom hit target")
CHAT_DATA.sidebar:SetAlpha(1); A:Tick(); assert(button:IsShown())
CHAT_CONFIG.sidebarVisibility="never"; A:Tick(); assert(not button:IsShown())
CHAT_CONFIG.sidebarVisibility="always"; A:Tick(); assert(button:IsShown())
local opened=0; A.OpenOptions=function() opened=opened+1 end
button:GetScript("OnClick")(button,"RightButton"); assert(opened==1 and not A.active)
A:SetOption("enabled",false); assert(not button:IsShown())
A:SetOption("enabled",true); assert(A.ready and button:IsShown())
print("PASS: real chat kit "..STYLE..", hover/press/selection, scale, spacing, hide and restore")
