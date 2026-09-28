-- Extend only the already-registered Damage Meters page. This runtime override
-- is reapplied when the load-on-demand options addon registers the real page.
local A = EllesmereUIChatMeters
local MODULE, PAGE = "EllesmereUIDamageMeters", "Damage Meters"
local installed = setmetatable({}, { __mode = "k" })

local function Toggle(key, label, tooltip)
    return {
        type = "toggle", text = label,
        tooltip = tooltip .. " Settings are saved separately for this character.",
        getValue = function() return A.db and A.db[key] == true end,
        setValue = function(value) A:SetOption(key, value) end,
    }
end

function A:BuildIntegratedOptions(parent, y)
    local W = EllesmereUI.Widgets
    parent._showRowDivider = true
    local _, h = W:SectionHeader(parent, "CHAT METERS (CUSTOM)", y)
    y = y - h
    _, h = W:DualRow(parent, y,
        Toggle("enabled", "Embed Meters in Chat",
            "Place your first two meter windows side by side in chat. Each pane keeps its selected view, including Threat. Toggle with the sidebar Meters icon. Turn off to restore separate windows."),
        Toggle("returnOnExit", "Return to Chat on Exit",
            "Return to the previous chat view when leaving a dungeon or raid."))
    y = y - h
    _, h = W:DualRow(parent, y,
        Toggle("autoDungeon", "Auto Show in Dungeons",
            "Select Meters when entering a dungeon. You can still switch to chat manually."),
        Toggle("autoRaid", "Auto Show in Raids",
            "Select Meters when entering a raid. You can still switch to chat manually."))
    return y - h
end

function A:IntegrateOptions()
    local e = EllesmereUI
    local config = e and e._modules and e._modules[MODULE]
    if not config or type(config.buildPage) ~= "function" then return false end
    if installed[config] then return true end
    -- Ignore core placeholder pages before the real options module has loaded.
    local found
    for _, page in ipairs(config.pages or {}) do if page == PAGE then found = true; break end end
    if not found then return false end
    local original = config.buildPage
    config.buildPage = function(pageName, parent, yOffset, ...)
        local W = e.Widgets -- also supports the suite's search-only widget absorber
        if pageName == PAGE and W and W.SectionHeader and W.DualRow then
            yOffset = A:BuildIntegratedOptions(parent, yOffset or 0)
        end
        -- Upstream owns previews, other pages, and the final full scroll height.
        return original(pageName, parent, yOffset, ...)
    end
    installed[config] = true
    if e.InvalidateModulePageCache then e:InvalidateModulePageCache(MODULE) end
    if e.IsShown and e:IsShown() and e.GetActiveModule and e:GetActiveModule() == MODULE and e.RefreshPage then
        e:RefreshPage(true)
    end
    return true
end

local fallbackOpen = A.OpenOptions
function A:OpenOptions()
    local e = EllesmereUI
    if not (e and e.ShowModule and e.SelectPage and e.GetActiveModule) then return fallbackOpen(self) end
    if self.optionsOpenTicker then self.optionsOpenTicker:Cancel(); self.optionsOpenTicker = nil end
    -- ShowModule supplies the suite's normal combat-lockdown message.
    if InCombatLockdown and InCombatLockdown() then e:ShowModule(MODULE); return end
    self:IntegrateOptions()
    e:ShowModule(MODULE)
    local function FinishOpen()
        if e:GetActiveModule() ~= MODULE or (e.IsShown and not e:IsShown()) then return false end
        A:IntegrateOptions()
        e:SelectPage(PAGE)
        if e.ScrollToTop then e:ScrollToTop() end
        return true
    end
    if FinishOpen() then return end
    -- First-open work, including LOD registration, is deferred over several frames.
    local attempts = 0
    self.optionsOpenTicker = C_Timer.NewTicker(0.05, function(ticker)
        attempts = attempts + 1
        if FinishOpen() or attempts >= 100 then
            ticker:Cancel()
            A.optionsOpenTicker = nil
        end
    end)
end

local events = CreateFrame("Frame")
events:RegisterEvent("ADDON_LOADED")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(_, event, addon)
    if event == "PLAYER_LOGIN" or addon == "EllesmereUIOptions" then A:IntegrateOptions() end
end)
A:IntegrateOptions()
