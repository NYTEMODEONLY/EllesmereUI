-- Personal compatibility choices; no automatic profile/layout migration.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
SLASH_EUIFOREVERGROUPS1 = "/euigroups"
SlashCmdList.EUIFOREVERGROUPS = function(message)
    local mode = (message or ""):lower():match("^%s*(.-)%s*$")
    if mode ~= "native" and mode ~= "official" then
        local chosen = EllesmereUIDB and EllesmereUIDB.foreverGroupRenderer or "native"
        print("EllesmereUI group frames: " .. chosen .. ". /euigroups native or /euigroups official; then /reload.")
        return
    end
    if InCombatLockdown() then
        print("EllesmereUI: change group renderer outside combat.")
        return
    end
    EllesmereUIDB = EllesmereUIDB or {}
    EllesmereUIDB.foreverGroupRenderer = mode
    print("EllesmereUI: " .. mode .. " group frames selected for next /reload. Existing settings and native layout are retained.")
end
