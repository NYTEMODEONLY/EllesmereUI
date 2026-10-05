# Official v9.3.6 integration — October 4, 2026

Custom candidate: **9.3.6-forever.0.6.0**, incorporating v9.3.5 and v9.3.6.
Official complete suite: https://github.com/EllesmereGaming/EllesmereUI/releases/tag/v9.3.6
Published 2026-10-04 23:36:17 UTC. ZIP SHA-256:
e72d5ebf40e7a0f89a198bfe3b7b5e95745f1f9bad4c7c774bccf9143666aa80.
Author notes: https://ellesmereui.com/patch-notes . The release asset checksum pins the pristine source used for this integration.

| Area | Reviewed integration and preservation decision |
| --- | --- |
| Core/options splits | Integrate official plugin registry, CVar ownership/uninstall, scale slider, style/color controls and split options/runtime files. Keep first client gate, normal persistence, private seed and unloaded automatic layout. Compact confirmation and outside-world-input behavior combine with new overflow/handle support. Uninstall remains an explicit player action. |
| Meters companion | Grimlight Meters Tab v0.4.1 registers its controls under Grimlight Meters > Chat Embedding using the public plugin API. /eumeters and right-click open that page; old hosts retain the old integrated page. No writes to protected core pages on current hosts. Embedding, selected view, windows, per-character saves, artwork, host styles, auto-instance behavior and standalone restoration remain unchanged. |
| Bags | Integrate official list view, sortable/resizable columns, window resizing, empty-space drop, merchant stack visibility and special-bag sections. Preserve custom confirmed transaction executor, matching profession stacks, family/lock/link/binding guards, stack split, disenchant and native MultiBag. New windows-over-bags preference is available but defaults off to preserve layering. |
| Bank | Native Forever bank controls and custom skin remain exclusive. The upstream reconstructed bank/list renderer stays inactive on Forever, retaining native pages, equipment, purchases and account controls; bag List View remains available. |
| Actions/XP | Integrate official XP overhaul/texts/styles, modifier/target paging switch, equipped quality-color control and fixes. Prior native XP/layout choices remain authoritative. Equipped border starts off in custom defaults; existing choices remain. Old-build adapters stay inert. |
| Nameplates | Integrate debuff/combo colors, new core text/position/filter controls, shield placements, borders and official Threat Gap option. Official threat text remains sole owner with custom Below Health Bar placement; retired badges stay retired. Prior Important buff filter remains the custom default; Show All is selectable. |
| Groups/units/resources | Integrate v9.3.6 HoverCast/Dynamic Rez hotfix, clear-target/combat-rez items, Cmd modifiers, portraits/borders/absorb placements, resource absorb/spender/cast controls and fixes. Keep official renderer and exclusive native fallback, missing-buff visuals opt-in, native/protected-value guards and prediction OFF semantics. Relocate prediction refresh into EUI_UnitFrames_Reload.lua and missing-buff defaults into VisualIndicators_Options.lua. Existing enabled threat continues on target and focus; the new focus toggle remains available. |
| Flight/Loot | Integrate shared Feature kit and opt-in Loot Feed. Preserve flight enable/early-exit opt-ins, bounded takeoff checks, elapsed-only recovery, routes/perks/calibration, early-landing exclusion and saved geometry. |
| Native windows | Integrate new chat-bubble owner, health-strip controls, gamepad stand-down and compatible sheet/stat/window fixes. Custom Character/Inspect, GroupFinder and Legacy remain exclusive where equivalent official painters were introduced; native bag/micro-bar art remains owner-selected. Duplicate stock painters are retained as upstream source but not loaded. Legacy initial-load nil reward cards now defer card styling until native setup completes without replacing handlers. |
| DataBars/minimap/chat/QoL | Integrate native icons, drag reorder, class reagents/ammo, First Aid/text options, coordinates, chat fading/copy fixes and opt-in Self Combat Text. Preserve saved Legacy/professions keys and native endpoints (including supported Housing), glyphs and explicit false; no duplicate new-key controls. |
| Unavailable systems | Keep Mythic loader disabled; no vault, crests, seasonal teleports, Skyriding or unsupported Retail tools activated. Dormant choices and excluded blocks remain. |
| Appearance and defaults | Host Chat/Meters themes and options artwork/accent stay independent. New optional displays stay opt-in. Existing profile values win; no saved-data writes or resets are performed by maintenance. |
| Distribution | Upstream credit/license retained. Public GitHub package uses the reviewed no-op profile placeholder and excludes personal saves/history, diagnostics, backups and fixtures. Companion first-release native/provenance/CurseForge gates remain outstanding; do not call it a completed CurseForge release. |


Validation: 54 active scripts, Lua 5.1 compilation and manifest references;
disposable updater/deployment/rollback tests and public ZIP roundtrip checks.
Native startup, settings/plugin page, embedding, bags, groups/click casting,
combat/Unlock, native windows, flight and persistence remain pending acceptance.
