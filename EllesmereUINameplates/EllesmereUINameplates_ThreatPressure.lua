-- Retired badge: official v9.3 owns nameplate threat text and its controls.
-- Retain this manifest entry as a one-time settings handoff, with no frames,
-- hooks, events, polling, preview, or slash command. Old keys remain recoverable.
if EUI_CLIENT_BLOCKED or not EUI_FOREVER then return end
local profiles = EllesmereUIDB and EllesmereUIDB.profiles
for _, profile in pairs(profiles or {}) do
    local p = type(profile) == "table" and profile.addons and profile.addons.EllesmereUINameplates
    if type(p) == "table" and not p.foreverOfficialThreatMigrated then
        -- Lite strips default-valued keys on logout. The former badge default
        -- was ON; an absent official choice inherits that existing visibility.
        -- Explicit official values (including false) and every layout/color stay.
        if p.threatPctEnabled == nil then
            p.threatPctEnabled = p.threatPressureEnabled ~= false
        end
        p.foreverOfficialThreatMigrated = true
    end
end
