-- Independent adapter for EllesmereUI 9.1.8 / Retail 12.1.
-- Never write upstream databases or Blizzard's secure chat/dock state.
local A = { records = {}, hooked = setmetatable({}, { __mode = "k" }), hiddenVisuals = {},
    panelHooks = setmetatable({}, { __mode = "k" }),
    unlockHooks = setmetatable({}, { __mode = "k" }) }
_G.EllesmereUIChatMeters = A
local defaults = { enabled = true, autoDungeon = true, autoRaid = true, returnOnExit = true }
local unpack = unpack or table.unpack
local function Plain(v) return not (issecretvalue and issecretvalue(v)) end
local function Number(v) return Plain(v) and type(v) == "number" end
local function VisibleMouseOver(frame)
    if not frame then return false end
    local shown = frame:IsShown()
    if not Plain(shown) then return nil end
    if not shown then return false end
    -- Use the region API directly; the global MouseIsOver helper fails on 12.1.
    local over = frame:IsMouseOver()
    if Plain(over) then return over end -- secret geometry cannot drive a branch
end
local function FocusWithin(focus, frame)
    -- Walk only the click recipient's ancestry. A popup covering a
    -- chat tab is not a tab click, even if the tab's rectangle is under it.
    while Plain(focus) and focus do
        if focus == frame then return true end
        focus = focus:GetParent()
    end
    return false
end
local function Print(s) print("|cff0cd29fMeters Tab:|r " .. s) end
local function Selected()
    return GENERAL_CHAT_DOCK and FCFDock_GetSelectedWindow and FCFDock_GetSelectedWindow(GENERAL_CHAT_DOCK)
end
local function Modules()
    local e = EllesmereUI
    local ns = e and e._ModuleNS
    return e, ns and ns.EllesmereUIChat, ns and ns.EllesmereUIDamageMeters
end
local function Points(f)
    local points = {}
    for i = 1, f:GetNumPoints() do points[i] = { f:GetPoint(i) } end
    return points
end
local function SetPoints(f, points)
    f:ClearAllPoints()
    for _, p in ipairs(points) do f:SetPoint(unpack(p)) end
end
local function Anchor(f, point, relative, relativePoint, x, y)
    local p, r, rp, px, py = f:GetPoint(1)
    if f:GetNumPoints() == 1 and p == point and r == relative and rp == relativePoint and px == x and py == y then return end
    f:ClearAllPoints()
    f:SetPoint(point, relative, relativePoint, x, y)
end
local function SaveFrame(f)
    return { parent = f:GetParent(), points = Points(f), width = f:GetWidth(), height = f:GetHeight(),
        scale = f:GetScale(), strata = f:GetFrameStrata(), level = f:GetFrameLevel(),
        shown = f:IsShown(), alpha = f:GetAlpha(), clamped = f:IsClampedToScreen() }
end
local function RestoreFrame(f, s)
    f:SetParent(s.parent)
    f:SetScale(s.scale)
    f:SetFrameStrata(s.strata)
    f:SetFrameLevel(s.level)
    f:SetClampedToScreen(s.clamped)
    f:SetSize(s.width, s.height)
    SetPoints(f, s.points)
    f:SetAlpha(s.alpha)
    f:SetShown(s.shown)
end

function A:BuildUI()
    local root = CreateFrame("Frame", "EllesmereUIChatMetersRoot", UIParent)
    root:SetFrameStrata("MEDIUM")
    root:SetFrameLevel(120)
    root:SetSize(1, 1)
    self.root = root
    local body = CreateFrame("Frame", nil, root)
    body:SetFrameLevel(121)
    body:EnableMouse(true) -- block the invisible native chat hyperlinks below the meters
    body:EnableMouseWheel(true)
    body:SetScript("OnMouseWheel", function() end)
    body:Hide()
    self.body = body
    self.waitingText = body:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    self.waitingText:SetPoint("CENTER")
    self.waitingText:SetText("Waiting for EllesmereUI meter windows...")
    self.waitingText:Hide()
    self.parking = CreateFrame("Frame", nil, root)
    self.parking:Hide()
    local button = CreateFrame("Button", "EllesmereUIChatMetersButton", root)
    button:SetSize(22, 22)
    button:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    button.lines = {}
    -- Three outlined bars, matching the sidebar's thin monochrome icons.
    for i, height in ipairs({ 7, 15, 11 }) do
        local x = 3 + (i - 1) * 6
        for _, edge in ipairs({ {x, 3, 4, 1}, {x, 3 + height - 1, 4, 1},
            {x, 3, 1, height}, {x + 3, 3, 1, height} }) do
            local line = button:CreateTexture(nil, "ARTWORK")
            line:SetPoint("BOTTOMLEFT", button, "BOTTOMLEFT", edge[1], edge[2])
            line:SetSize(edge[3], edge[4])
            line.box = edge
            button.lines[#button.lines + 1] = line
        end
    end
    -- Stock styles use the chat module's own plate, glyph and press renderer.
    button._icon = button:CreateTexture(nil, "ARTWORK")
    button._icon:Hide()
    button:SetScript("OnClick", function(_, mouseButton)
        if mouseButton == "RightButton" then A:OpenOptions() else A:SetActive(not A.active) end
    end)
    button:SetScript("OnEnter", function()
        A.iconHovered = true
        A:PaintIcon()
        if A.chat and A.chat.ECHAT.ResetIdleTimer then A.chat.ECHAT.ResetIdleTimer() end
        GameTooltip:SetOwner(button, "ANCHOR_RIGHT")
        GameTooltip:SetText("Meters")
        GameTooltip:AddLine("Left-click: meters / previous chat\nRight-click: meter settings", 1, 1, 1)
        GameTooltip:Show()
    end)
    button:SetScript("OnLeave", function() A.iconHovered = false; A:PaintIcon(); GameTooltip:Hide() end)
    button:SetScript("OnHide", function()
        if A.iconHovered then GameTooltip:Hide() end
        A.iconHovered = false
        if button._fvPlate and button._fvPlate.lift then
            EllesmereUI.ForeverBorderShown(button._fvPlate.lift, false)
        end
        A:PaintIcon()
    end)
    self.button = button
    self:PaintIcon()
end

function A:PaintIcon()
    if not self.button then return end
    local kit = self.button._metersKit
    if kit then
        -- Keep the stock glyph opaque; selected Forever uses its gold, and
        -- Blizzard/Classic keep their native highlight while selected.
        local chat = self.button._metersChat
        local tint = self.active and chat.FV and kit == chat.SB_KITS.forever and chat.FV.gold or kit.tint
        self.button._icon:SetVertexColor(tint and tint[1] or 1, tint and tint[2] or 0.82, tint and tint[3] or 0, 1)
        if self.active then self.button:LockHighlight() else self.button:UnlockHighlight() end
        return
    end
    local c = self.chat and self.chat.ECHAT.DB() or {}
    local r, g, b = c.iconR or 1, c.iconG or 1, c.iconB or 1
    if (self.active or c.iconUseAccent) and EllesmereUI.GetAccentColor then
        r, g, b = EllesmereUI.GetAccentColor()
    end
    for _, line in ipairs(self.button.lines) do
        line:SetColorTexture(r, g, b, (self.active or self.iconHovered) and 0.9 or 0.4)
    end
end

function A:StyleSidebarButton()
    local chat, button = self.chat.ECHAT, self.button
    local kit = chat.SB_KIT
    if not (kit and kit.copy and chat.SB_Entry and chat.SB_Dress) then return nil end
    if not button._metersKit then
        -- Inherit the generic plate from the active kit, not the Settings
        -- gear (which is a different shape on Blizzard and Classic).
        kit.meters = chat.SB_Entry(kit.copy, { glyph = {{
            file = "Interface\\AddOns\\EllesmereUIChatMeters\\Media\\meters.tga",
            w = 18, h = 18, gold = true,
        }} })
        chat.SB_Dress(button, "meters")
        button._metersKit, button._metersChat = kit, chat
        for _, line in ipairs(button.lines) do line:Hide() end
    end
    local s, e = chat.DB().sidebarIconScale or 1, button._sbEntry
    if button._metersScale ~= s then
        button._metersScale = s
        button:SetSize(e.w * s, e.h * s)
        button._sbPadT, button._sbPadB = (e.padT or 0) * s, (e.padB or 0) * s
        button._icon:SetSize(button._sbGW * s, button._sbGH * s)
        if button._sbInset then
            button._sbInset:ClearAllPoints()
            button._sbInset:SetPoint("TOPLEFT", button, "TOPLEFT", 5 * s, -6 * s)
            button._sbInset:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", -6 * s, 6 * s)
        end
    end
    if e.plate then chat.FV_Plate(button, true) end
    return kit
end

function A:RestoreSidebar()
    if self.sidebarSettings and self.sidebarPoints then
        local _, relative = self.sidebarSettings:GetPoint(1)
        if relative == self.button then SetPoints(self.sidebarSettings, self.sidebarPoints) end
    end
    self.sidebarSettings, self.sidebarPoints = nil, nil
    if self.button then self.button:Hide() end
end

function A:LayoutSidebar(data)
    local settings, sidebar = data.settingsBtn, data.sidebar
    local c = self.chat.ECHAT.DB()
    if not sidebar then return end -- retain the previous sidebar during rebuild
    local useSettings = settings and settings:IsShown() and c.showSettings ~= false
    if not useSettings then
        self:RestoreSidebar()
    elseif self.sidebarSettings ~= settings then
        self:RestoreSidebar()
    end
    self.button:SetParent(sidebar)
    self.button:SetScale(settings and settings:GetScale() or 1)
    local width, height = settings and settings:GetWidth() or 22, settings and settings:GetHeight() or 22
    self.button:SetFrameLevel((settings and settings:GetFrameLevel() or sidebar:GetFrameLevel()) + 1)
    local kit = self:StyleSidebarButton()
    if not kit then
        self.button:SetSize(width, height)
        for _, line in ipairs(self.button.lines) do
            local box = line.box
            line:ClearAllPoints()
            line:SetPoint("BOTTOMLEFT", self.button, "BOTTOMLEFT", box[1] * width / 22, box[2] * height / 22)
            line:SetSize(box[3] * width / 22, box[4] * height / 22)
        end
    end
    local gap = kit and (c.stockIconSpacing or kit.gap) or (c.sidebarIconSpacing or 10)
    if useSettings then
        local _, relative = settings:GetPoint(1)
        if relative ~= self.button then self.sidebarPoints = Points(settings) end
        self.sidebarSettings = settings
        SetPoints(self.button, self.sidebarPoints)
        if kit and #self.sidebarPoints == 1 then
            local p = self.sidebarPoints[1]
            Anchor(self.button, p[1], p[2], p[3], p[4], p[5] + (self.button._sbPadT or 0) - (settings._sbPadT or 0))
        end
        Anchor(settings, "TOP", self.button, "BOTTOM", 0, -(gap - (self.button._sbPadB or 0) - (settings._sbPadT or 0)))
    else
        -- Settings can be hidden independently; Meters still needs an entry point.
        local refs = { showFriends="friendsBtn", showGuild="guildBtn", showDurability="durabilityBtn",
            showCopy="copyBtn", showPortals="portalBtn", showVoice="voiceBtn" }
        local tails = { showFriends="friendsCount", showGuild="guildCount", showDurability="durabilityPct" }
        local last
        for _, key in ipairs(data._iconChainOrder or {"showFriends","showGuild","showDurability","showCopy","showPortals","showVoice"}) do
            local btn = refs[key] and data[refs[key]]
            if btn and btn:IsShown() then
                local tail = tails[key] and data[tails[key]]
                last = tail and tail:IsShown() and not btn._sbTailInside and tail or btn
            end
        end
        if last then Anchor(self.button, "TOP", last, "BOTTOM", 0, -(gap - (last._sbPadB or 0) - (self.button._sbPadT or 0)))
        else Anchor(self.button, "TOP", sidebar, "TOP", 0, kit and 0 or -gap) end
    end
    local faded = c.sidebarVisibility == "mouseover" and sidebar:GetAlpha() == 0
    self.button:SetShown(self.root:IsShown() and c.sidebarVisibility ~= "never"
        and not faded
        and not self.chat._chatPassthrough and (not settings or settings:IsShown() or c.showSettings == false
            or (c.sidebarVisibility or "always") == "always"))
end

function A:SyncChatVisuals(hide)
    -- Suppress only display layers; chat continues receiving messages underneath.
    -- Combat Log uses the same alpha-only containers managed by Ellesmere's engine.
    local wanted = {}
    local selected = Selected()
    if hide and selected then
        local win = self.chat and self.chat._chatWins and self.chat._chatWins[selected]
        if win then
            if win.smf then wanted[win.smf] = true end
            if win.track then wanted[win.track] = true end
        end
        if selected == ChatFrame2 then
            if selected.FontStringContainer then wanted[selected.FontStringContainer] = "log" end
            if selected.ScrollBar and selected.ScrollBar.Track then wanted[selected.ScrollBar.Track] = "log" end
            if CombatLogQuickButtonFrame_Custom then wanted[CombatLogQuickButtonFrame_Custom] = true end
        end
    end
    for visual, saved in pairs(self.hiddenVisuals) do
        if not wanted[visual] then
            -- A native selection change may already have hidden Combat Log.
            visual:SetAlpha(saved.kind == "log" and selected ~= ChatFrame2 and 0 or saved.alpha)
            self.hiddenVisuals[visual] = nil
        end
    end
    for visual, kind in pairs(wanted) do
        if not self.hiddenVisuals[visual] then
            self.hiddenVisuals[visual] = { alpha = visual:GetAlpha(), kind = kind }
        end
        visual:SetAlpha(0)
    end
end

function A:SetActive(on)
    if on and (not self.db.enabled or not self.ready) then
        Print(self.problem or "Waiting for the chat panel and both meter windows.")
        return
    end
    self.active = on == true
    self.db.metersSelected = self.active
    self.pendingRestore = nil
    self.selectedAtOpen = self.active and Selected() or nil
    if self.body then self.body:SetShown(self.active and self.ready and self.root:IsShown()) end
    self:PaintIcon()
    self:SyncChatVisuals(self.active and self.ready and self.root:IsShown())
    if self.active then
        if self.chat and self.chat.ECHAT and self.chat.ECHAT.ResetIdleTimer then self.chat.ECHAT.ResetIdleTimer() end
        for w in pairs(self.records) do w.frame:Show(); w.Refresh() end
    end
end

-- Only the chosen two windows are adopted. Other meter windows stay independent.
function A:ChooseWindows(dm)
    local live = {}
    for _, w in ipairs(dm._windows or {}) do live[w] = true end
    local left = live[self.left] and self.left or nil
    local right = live[self.right] and self.right or nil
    -- Window order survives reload through the native meter profile. A pane's
    -- selected metric is content, not its identity; retain live owners and
    -- adopt the first unclaimed windows when login/profile rebuild replaces them.
    for _, w in ipairs(dm._windows or {}) do
        if w ~= left and w ~= right then
            if not left then left = w
            elseif not right then right = w end
        end
    end
    return left, right
end

-- One geometry owner, independent of edit/settings mode. Reassert immediately
-- after upstream writes, before any standalone anchor can reach the renderer.
function A:EnforceWindow(w)
    local r = self.records[w]
    if not r or not r.target or r.enforcing then return end
    local f, t = w.frame, r.target
    if f:GetParent() == nil then return end -- upstream has retired this frame
    r.enforcing = true
    local ok, err = pcall(function()
        if f:GetParent() ~= self.body then f:SetParent(self.body) end
        if f:GetScale() ~= 1 then f:SetScale(1) end
        if f:GetFrameStrata() ~= "MEDIUM" then f:SetFrameStrata("MEDIUM") end
        if f:GetFrameLevel() ~= 125 then f:SetFrameLevel(125) end
        Anchor(f, "TOPLEFT", self.body, "TOPLEFT", t.x, -1)
        if f:GetWidth() ~= t.width or f:GetHeight() ~= t.height then f:SetSize(t.width, t.height) end
    end)
    r.enforcing = false
    if not ok then self:HandleError(err) end
end

function A:EmbeddedKey(key)
    local index = type(key) == "string" and tonumber(key:match("^EDM_Win(%d+)$"))
    local _, _, dm = Modules()
    local w = index and dm and dm._windows and dm._windows[index]
    return w and self.records[w]
end

function A:GuardUnlockElements()
    local e = EllesmereUI
    if not e or not e._unlockRegisteredElements then return end
    -- UnregisterUnlockElement deletes saved anchor links: never call it here.
    -- Keep registrations, but hide embedded windows from standalone movers and
    -- ignore mover writes. Wrappers delegate normally once embedding is disabled.
    for key, element in pairs(e._unlockRegisteredElements) do
        if key:match("^EDM_Win%d+$") and not self.unlockHooks[element] then
            self.unlockHooks[element] = true
            for _, name in ipairs({ "getFrame", "getSize", "setWidth", "setHeight",
                "savePosition", "savePos", "clearPosition", "clearPos", "applyPosition", "applyPos" }) do
                local original, field, elementKey = element[name], name, key
                if type(original) == "function" then
                    element[name] = function(k, ...)
                        local record = A:EmbeddedKey(k or elementKey)
                        if record then
                            if field == "getSize" then return record.frame.width, record.frame.height end
                            return nil
                        end
                        return original(k, ...)
                    end
                end
            end
            e._unlockRegistrationDirty = true
        end
    end
    if e.RegisterUnlockElements and not self.unlockRegistrationHooked then
        self.unlockRegistrationHooked = true
        hooksecurefunc(e, "RegisterUnlockElements", function(_, elements)
            A:GuardUnlockElements()
            -- A profile rebuild/add-window registers after constructing its new
            -- frames. Adopt them in the same call stack, before the next render.
            for _, element in ipairs(elements or {}) do
                if element.key and element.key:match("^EDM_Win%d+$") then
                    A:SafeTick()
                    break
                end
            end
        end)
    end
end

function A:Attach(w)
    if not w then return end
    if self.records[w] then return end
    local f = w.frame
    local r = { frame = SaveFrame(f), locked = w.windowLocked, controls = {} }
    self.records[w] = r
    if EllesmereUI then EllesmereUI._unlockRegistrationDirty = true end
    -- Keep every native header button and its own scripts/layout. Prevent only
    -- dragging/resizing the embedded window; the header's right-click menu stays.
    for _, control in ipairs({ w.resizeGrip, w.lockBtn }) do
        r.controls[control] = SaveFrame(control)
        control:SetParent(self.parking)
    end
    r.headerMouseDown = w.header:GetScript("OnMouseDown")
    w.header:SetScript("OnMouseDown", nil)
    r.backgrounds = {}
    for _, texture in pairs({ body = f._bg, header = w.header._hdrBg }) do
        r.backgrounds[texture] = texture:GetAlpha()
        texture:SetAlpha(0)
    end
    f:SetParent(self.body)
    f:SetClampedToScreen(false)
    f:SetScale(1)
    f:SetFrameStrata("MEDIUM")
    f:SetFrameLevel(125)
    f:SetAlpha(1)
    f:Show()
    if not self.hooked[w] then
        self.hooked[w] = true
        for _, method in ipairs({ "ClearAllPoints", "SetPoint", "SetSize", "SetWidth", "SetHeight",
            "SetScale", "SetFrameStrata", "SetFrameLevel" }) do
            hooksecurefunc(f, method, function() A:EnforceWindow(w) end)
        end
        hooksecurefunc(f, "SetParent", function(_, parent)
            if parent == nil then
                if A.records[w] then f:Hide() end
            else
                A:EnforceWindow(w)
            end
        end)
        -- Keep UpdateVisibility's identity intact: upstream registers and
        -- unregisters that exact callback during profile rebuilds. Observe only
        -- this Ellesmere-owned frame, never a Blizzard chat frame. Defer until a
        -- destroy/rebuild has removed the window from the active array.
        f:HookScript("OnHide", function()
            if not A.records[w] or f:IsShown() then return end
            C_Timer.After(0, function()
                if not A.records[w] or f:GetParent() ~= A.body then return end
                local _, _, dm = Modules()
                for _, live in ipairs(dm and dm._windows or {}) do
                    if live == w then f:SetAlpha(1); f:Show(); break end
                end
            end)
        end)

    end
end

function A:Detach(w, alive)
    local r = self.records[w]
    if not r then return end
    -- Only explicit companion disable releases a LIVE window.
    if alive and self.db and self.db.enabled then return end
    self.records[w] = nil -- make installed hooks dormant before restoring
    if EllesmereUI then EllesmereUI._unlockRegistrationDirty = true end
    -- Restore the outer frame first: its level/parent changes can shift all
    -- descendants. Restore the saved header control levels only afterwards.
    if alive then
        RestoreFrame(w.frame, r.frame)
    else
        w.frame:Hide()
        w.frame:SetParent(nil)
    end
    for f, saved in pairs(r.controls) do RestoreFrame(f, saved) end
    w.windowLocked = r.locked
    w.header:SetScript("OnMouseDown", r.headerMouseDown)
    for texture, alpha in pairs(r.backgrounds) do texture:SetAlpha(alpha) end
    if alive then
        if w.ApplyPosition then w.ApplyPosition() end
        w.FitTitle()
        w.UpdateVisibility()
        w.Refresh()
    end
end

function A:ReleaseAll()
    if self.db and self.db.enabled then return end
    self:SyncChatVisuals(false)
    self:RestoreSidebar()
    if not next(self.records) then
        self.ready = false
        if self.body then self.body:Hide() end
        return
    end
    local _, _, dm = Modules()
    local alive = {}
    for _, w in ipairs(dm and dm._windows or {}) do alive[w] = true end
    local list = {}
    for w in pairs(self.records) do list[#list + 1] = w end
    for _, w in ipairs(list) do self:Detach(w, alive[w]) end
    self.ready = false
    if self.body then self.body:Hide() end
end

-- Geometry is read only from Ellesmere-owned display panels.
function A:Layout(panel, data, chat, geometryOnly)
    local c = chat.ECHAT.DB()
    local width, height = panel:GetWidth(), panel:GetHeight()
    if not Number(width) or not Number(height) or width <= 8 or height <= 4 then
        -- Keep the last valid embedded rectangle through an unresolved layout
        -- pass. Never expose the standalone windows during an ongoing resize.
        return self.ready == true, "Waiting for the chat panel's dimensions."
    end
    local selected = Selected()
    local sd = selected and EllesmereUI._chatCFD(selected) or data
    local input = sd and sd._smfTopExtra or 0
    local ins = data._bgIns or { b = -6 }
    local bottom = c.inputOnTop and 2 or math.max(2, -(ins.b or -6) - 8)
    local top = 2 + input
    local contentHeight = height - bottom - top
    if contentHeight <= 2 then return self.ready == true, "Waiting for the chat content area." end
    Anchor(self.body, "TOPLEFT", panel, "TOPLEFT", 1, -top)
    if self.body:GetWidth() ~= width - 2 or self.body:GetHeight() ~= contentHeight then
        self.body:SetSize(width - 2, contentHeight)
    end
    local meterWidth = (width - 8) / 2
    for i = 1, 2 do
        local w
        if i == 1 then w = self.left else w = self.right end
        if w and self.records[w] then
            local f, r = w.frame, self.records[w]
            local changed = f:GetWidth() ~= meterWidth or f:GetHeight() ~= contentHeight - 2
            r.target = { x = (i - 1) * (meterWidth + 4) + 1, width = meterWidth, height = contentHeight - 2 }
            self:EnforceWindow(w)
            if changed then w.FitTitle(); self.layoutDirty = true end
            for texture in pairs(r.backgrounds) do texture:SetAlpha(0) end
        end
    end
    if not geometryOnly and self.layoutDirty then
        self.layoutDirty = nil
        if self.left then self.left.Refresh() end
        if self.right then self.right.Refresh() end
    end
    self.waitingText:SetShown(not self.left and not self.right)

    return true
end

function A:FollowPanel(panel, data, chat)
    self.followedPanel, self.followedData, self.followedChat = panel, data, chat
    if self.panelHooks[panel] then return end
    self.panelHooks[panel] = true
    -- Hook only Ellesmere's standalone display panel, never ChatFrame1 or the
    -- secure dock. This fires along with its normal per-frame resize follower.
    panel:HookScript("OnSizeChanged", function(changedPanel)
        if A.failed or not A.ready or A.followedPanel ~= changedPanel then return end
        for w in pairs(A.records) do
            if w.frame:GetParent() ~= A.body then return end
        end
        local ok, err = pcall(A.Layout, A, changedPanel, A.followedData, A.followedChat, true)
        if not ok then A:HandleError(err) end
    end)
end

-- A missing/rebuilding host may temporarily hide its contents, but must never
-- turn adopted frames back into standalone windows or discard their snapshots.
function A:Hold(reason, hide)
    self.problem = reason
    if hide then
        self:SyncChatVisuals(false)
        if self.body then self.body:Hide() end
        if self.root then self.root:Hide() end
        if self.button then self.button:Hide() end
    end
end

function A:PruneRetired(dm)
    local live, retired = {}, {}
    for _, w in ipairs(dm._windows or {}) do live[w] = true end
    for w in pairs(self.records) do if not live[w] then retired[#retired + 1] = w end end
    for _, w in ipairs(retired) do self:Detach(w, false) end
end

function A:Tick()
    if not self.db then return end
    if not self.db.enabled then
        self:ReleaseAll()
        if self.root then self.root:Hide() end
        return
    end
    local e, chat, dm = Modules()
    self.chat = chat
    if dm and dm._windows then self:PruneRetired(dm) end
    local usable = not EUI_CLIENT_BLOCKED and e and chat and chat.ECHAT
        and chat.ECHAT.DB and dm and dm._windows and e._chatCFD
    if not usable or chat.ECHAT.DB().enabled == false then
        self:Hold("Waiting for EllesmereUI Chat and Damage Meters.", true)
        return
    end
    local data = ChatFrame1 and e._chatCFD(ChatFrame1)
    local panel = data and data.bg
    if not panel then self:Hold("Waiting for the chat display panel.", true); return end
    local left, right = self:ChooseWindows(dm)
    for _, w in pairs({ left = left, right = right }) do
        if not (w.frame and w.header and w.titleText and w.segmentBtn and w.Refresh and w.FitTitle and w.UpdateVisibility)
            or (w.frame.IsProtected and w.frame:IsProtected()) then
            self.ready = false
            self:Hold("The meter interface changed; embedding is paused. /eumeters off restores standalone windows.", true)
            return
        end
    end
    if not self.root then self:BuildUI() end
    -- No settings, edit, unlock, combat, zone, or resize condition releases
    -- live windows. Container visibility and embedding are separate decisions.
    self.left, self.right = left, right
    self:Attach(left)
    self:Attach(right)
    self:GuardUnlockElements()
    self:FollowPanel(panel, data, chat)
    local ok, reason = self:Layout(panel, data, chat)
    if not ok then self:Hold(reason, true); return end
    self.ready = true
    self.problem = (not left or not right) and "Waiting for the remaining meter window; existing meters stay embedded." or nil
    self.root:SetShown(not chat._chatStackHidden and not chat._chatPassthrough)
    if self.active and Selected() ~= self.selectedAtOpen then self:SetActive(false) end
    self.body:SetShown(self.active == true)
    self:SyncChatVisuals(self.active and self.root:IsShown())
    self:LayoutSidebar(data)
    self:PaintIcon()
    if self.active and chat.ECHAT.ResetIdleTimer then chat.ECHAT.ResetIdleTimer() end
    if self.pendingRestore ~= nil then
        local selected = self.pendingRestore
        self.pendingRestore, self.pendingAuto = nil, nil
        self:SetActive(selected)
    elseif self.pendingAuto then self.pendingAuto = nil; self:SetActive(true) end
end

function A:CheckZone()
    local inside, kind = IsInInstance()
    local _, _, _, _, _, _, _, instanceID = GetInstanceInfo()
    local key = inside and (kind .. ":" .. tostring(instanceID)) or "world"
    if key == self.zoneKey then return end -- manual chat choice persists until the next zone
    local wasInstance = self.wasInstance
    self.zoneKey, self.wasInstance = key, inside and (kind == "party" or kind == "raid")
    self.pendingAuto = nil
    if self.db.enabled and inside and ((kind == "party" and self.db.autoDungeon) or (kind == "raid" and self.db.autoRaid)) then
        self.pendingAuto = true
    elseif wasInstance and not self.wasInstance and self.db.returnOnExit then
        self:SetActive(false)
    end
end

function A:SetOption(key, value)
    self.db[key] = value == true
    if key == "enabled" and not value then self.active = false; self.pendingAuto = nil; self:ReleaseAll() end
    if key == "autoDungeon" or key == "autoRaid" or (key == "enabled" and value) then
        self.zoneKey = nil
        self:CheckZone()
    end
    if key == "enabled" and value then self.failed = nil end
    self:SafeTick()
end

function A:SafeTick()
    if self.failed or self.ticking then return end
    self.ticking = true
    local ok, err = pcall(self.Tick, self)
    self.ticking = false
    if ok then return end
    self:HandleError(err)
end

function A:HandleError(err)
    self.failed, self.ready, self.pendingAuto = true, false, nil
    self:SyncChatVisuals(false)
    if self.body then self.body:Hide() end
    -- Preserve the sidebar and ownership records so the user can inspect the
    -- problem or explicitly disable embedding; never release on an error.
    self.problem = "Compatibility error: " .. tostring(err)
    Print(self.problem .. " Embedding is paused. /eumeters off restores standalone windows.")
end

function A:BuildOptions()
    local panel = CreateFrame("Frame", "EllesmereUIChatMetersOptions", UIParent)
    panel:Hide()
    local title = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", 16, -16)
    title:SetText("EllesmereUI - Meters Tab (Custom)")
    local desc = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    desc:SetPoint("TOPLEFT", 16, -48)
    desc:SetJustifyH("LEFT")
    desc:SetText("Your first two meter windows, side by side in chat. Choose any view in either pane.\nSettings apply to this character. Also available in EllesmereUI > Damage Meters.")
    local rows = {
        { "enabled", "Embed the first two meter windows" },
        { "autoDungeon", "Automatically show Meters when entering a dungeon" },
        { "autoRaid", "Automatically show Meters when entering a raid" },
        { "returnOnExit", "Return to chat when leaving a dungeon or raid" },
    }
    panel.checks = {}
    for i, row in ipairs(rows) do
        local key = row[1]
        local cb = CreateFrame("CheckButton", nil, panel, "InterfaceOptionsCheckButtonTemplate")
        cb:SetPoint("TOPLEFT", 16, -94 - (i - 1) * 36)
        cb.Text:SetText(row[2])
        cb:SetScript("OnClick", function(b) A:SetOption(key, b:GetChecked()) end)
        panel.checks[key] = cb
    end
    local note = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    note:SetPoint("TOPLEFT", 20, -254)
    note:SetJustifyH("LEFT")
    note:SetText("Click any chat tab to return to chat, or click Meters again.\nAll meter header controls retain their normal actions.\nUse EllesmereUI's Damage Meters settings for appearance and data options.\nDisable embedding to restore the separate windows.\nThe Meters icon sits above Settings in the chat sidebar.")
    panel:SetScript("OnShow", function()
        for key, cb in pairs(panel.checks) do cb:SetChecked(A.db[key]) end
    end)
    self.options = panel
    if Settings and Settings.RegisterCanvasLayoutCategory then
        local category = Settings.RegisterCanvasLayoutCategory(panel, "EllesmereUI Meters Tab")
        Settings.RegisterAddOnCategory(category)
        self.category = category
    end
end

function A:OpenOptions()
    if self.category and Settings.OpenToCategory then Settings.OpenToCategory(self.category:GetID()) end
end

function A:Initialize()
    if self.db then return end
    EllesmereUIChatMetersDB = EllesmereUIChatMetersDB or {}
    self.db = EllesmereUIChatMetersDB
    for key, value in pairs(defaults) do if self.db[key] == nil then self.db[key] = value end end
    -- Restore only once the host and its windows are ready. A saved manual
    -- selection takes precedence over instance auto-open on this login.
    self.pendingRestore = self.db.metersSelected
    self:BuildOptions()
    self:CheckZone()
    self:SafeTick()
    self.ticker = C_Timer.NewTicker(0.2, function() A:SafeTick() end)
    if not self.db.welcomed then
        Print("Installed. Click the sidebar Meters icon; right-click for options. /eumeters help")
        self.db.welcomed = true
    end
end

SLASH_ELLESMEREUICHATMETERS1 = "/eumeters"
SlashCmdList.ELLESMEREUICHATMETERS = function(message)
    local cmd = (message or ""):lower():match("^%s*(%S*)")
    if cmd == "" or cmd == "config" then A:OpenOptions()
    elseif cmd == "show" then A:SetActive(true)
    elseif cmd == "hide" then A:SetActive(false)
    elseif cmd == "on" then A:SetOption("enabled", true)
    elseif cmd == "off" then A:SetOption("enabled", false)
    elseif cmd == "status" then
        Print(A.problem or (A.ready and "Ready. " .. (A.active and "Meters selected." or "Chat selected.")) or "Waiting for initialization.")
    else Print("/eumeters: options | show | hide | on | off | status. Click any chat tab to leave Meters.") end
end

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:RegisterEvent("PLAYER_ENTERING_WORLD")
events:RegisterEvent("ZONE_CHANGED_NEW_AREA")
events:RegisterEvent("GLOBAL_MOUSE_DOWN")
events:SetScript("OnEvent", function(_, event, button)
    if event == "PLAYER_LOGIN" then
        C_Timer.After(0, function() A:Initialize() end)
    elseif event == "PLAYER_ENTERING_WORLD" or event == "ZONE_CHANGED_NEW_AREA" then
        if A.db then A:CheckZone() end
    elseif event == "GLOBAL_MOUSE_DOWN" and A.active and button == "LeftButton" then
        -- Observe the hardware click; do not hook or select a native tab. This
        -- also handles clicking the already-selected chat tab under the overlay.
        if VisibleMouseOver(A.button) ~= false then return end
        local foci = GetMouseFoci()
        if not Plain(foci) or type(foci) ~= "table" then return end
        -- EllesmereUI's ghost strip receives mouse motion above the real tabs
        -- but explicitly propagates clicks. It can be first in GetMouseFoci.
        -- Skip only this known click-through layer, never arbitrary popups.
        local strip = A.chat and A.chat._chatTabStrip
        local focus
        for _, candidate in ipairs(foci) do
            if not Plain(candidate) then return end
            if candidate ~= strip then focus = candidate; break end
        end
        if not Plain(focus) or not focus then return end
        local dock = GENERAL_CHAT_DOCK
        for _, cf in ipairs(dock and dock.DOCKED_CHAT_FRAMES or {}) do
            local name = cf:GetName()
            local tab = name and _G[name .. "Tab"]
            if VisibleMouseOver(tab) == true and FocusWithin(focus, tab) then
                C_Timer.After(0, function() A:SetActive(false) end)
                break
            end
        end
    end
end)
