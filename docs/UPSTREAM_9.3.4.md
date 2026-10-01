# Official v9.3.4 integration

Custom release: **9.3.4-forever.0.5.0**, October 1, 2026. Based on the
[official complete-suite v9.3.4](https://github.com/EllesmereGaming/EllesmereUI/releases/tag/v9.3.4),
commit `de88c8670d7ccc308ff96eeda0265f7f468aaaf4`, incorporating v9.3.1–9.3.4.
[Author's patch notes](https://ellesmereui.com/patch-notes).
Official ZIP SHA-256: `6b50805f411f5c73e4be3cad6bd075b199552d857bbf5b15a6839e431b7a1ab7`.

Use official shipped features where they cover the desired behavior. Preserve
custom extensions, preferences and necessary Forever compatibility fixes. A
clean text merge alone does not establish feature or saved-setting compatibility.

| Area | Integration and owner |
| --- | --- |
| Flight | New official multi-stop route track, labels, preview and optional early landing. Retain secure taxi post-hook, bounded takeoff checks, duplicate/disable cleanup, unknown-route handling and elapsed-only mid-flight recovery. Saved routes, speed calibration and positions survive. Timer/early exit remain opt-in. |
| Chat meters | Custom companion continues embedding the first two actual saved meter windows. View persistence, resizing, host styles, menus, artwork and explicit disable behavior remain. Upstream has no equivalent chat embedding. |
| Threat | Custom embedded DamageMeters THREAT retains focus/pet/text/pull/warning/preview controls and native protected-value fills. New official lowercase bridge stands down before allocation. Official nameplate threat stays the sole nameplate owner. Standalone Essentials is the disabled-DamageMeters fallback. |
| Framework | Official core split and shared combat queues load normally. Custom confirmation fixes move into Popups. ResourceBars options use official split builders/shared environment. |
| Groups | Official ranked HoverCast, roster, aura/name/level and missing-buff improvements integrate. New level/missing-buff visuals default off; explicit settings remain authoritative. All official modules stand down in native fallback mode. |
| Resources / nameplates | Official prediction/regen/totem and text-slot/cast/unit fixes integrate with existing native/protected-value compatibility and sole renderer ownership. |
| Meters | Official hidden-window no-fetch/no-paint and show catch-up integrate without replacing the custom provider, reporting or reset workflow. |
| Native windows / bags | Preserve custom six-tab character shell, green enchants, official stat lane, native bank and confirmed bag operations. Retain Group Finder/Housing skin cards, checkbox/comment fixes and native social behavior. |
| Reminders | Official glow API integrates with the custom Forever collector, unknown/disabled handling, optional towns and explicit player actions. Retired seal reminders stay retired. |
| Native endpoints / logging | Preserve Legacy/Spellbook/Talents/Professions and saved false choices. New dungeon logging honors legacy settings when unset; an explicit new false wins. |
| Unavailable systems | Mythic manifest stays disabled; unsupported vault/crests/keystones/seasonal teleports/Skyriding remain excluded without deleting saved preferences. |
| Distribution | Grimlight Meters Tab stays v0.4.0. Upstream attribution/licenses and custom license boundaries remain. Public seed is a no-op; settings, private layouts, diagnostics, backups and native fixtures are excluded. |

All 52 active regressions and Lua 5.1 compilation pass on the private installed
suite. Coverage includes real route/takeoff/early-landing behavior, embedded
meter/report/Threat paths, combat queue ordering/replacement/error handling and
missing-buff pool/opt-in cleanup. Disposable updater/restore checks pass.
Public packaging independently checks exported bytes, manifest references,
profile exclusion and ZIP integrity. Some regressions require private native
fixtures or the installed personal seed; those dependencies are not distributed.

Live acceptance is pending for startup/reload, settings persistence, embedded
Chat/Meters views and reports/Threat, party/raid combat and Unlock Mode, bags/bank,
native window geometry, reminders and flight routes/normal landing/early landing/
mid-flight reload. Offline checks do not certify rendering, taint freedom or secure
combat behavior. The private maintenance receipt records installed source hashes,
full backups, matching merge baselines and rollback instructions.
