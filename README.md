# EllesmereUI Forever — NYTEMODEONLY's custom edition

A maintained custom version of [EllesmereUI](https://github.com/EllesmereGaming/EllesmereUI)
for **WoW Forever**, with chat-embedded meters, integrated threat, expanded native
window support, safer bag operations and Forever-specific fixes.

**Current custom baseline: 9.3.6-forever.0.6.0**, based on the official complete-suite
[**v9.3.6** release](https://github.com/EllesmereGaming/EllesmereUI/releases/tag/v9.3.6). This is an independently maintained fork, not an official
EllesmereUI release. The target is Forever's interface **16001** (16000–19999
client family); this custom distribution is not validated for Retail or other
Classic clients.

[Download releases](https://github.com/NYTEMODEONLY/EllesmereUI/releases) ·
[Custom changelog](CHANGELOG.md) · [Maintenance](docs/MAINTENANCE.md)

## What differs from official EllesmereUI?

This edition keeps the official framework and supported features, then adds the
custom behavior below. Settings, styles and native actions are preserved. It does
not replace every official feature with a second custom implementation.

### Chat and damage meters

- **Meters inside chat:** a Meters sidebar button switches the chat area between
  chat and the first two saved meter windows, regardless of their selected metric.
  Damage, healing, Threat and other supported modes use the real meter frames.
- **Persistent selection and automation:** the selected Chat/Meters view is saved
  per character. Optional instance-entry selection and return-to-chat on exit are
  available through **Grimlight Meters → Chat Embedding** or `/eumeters`. Earlier hosts
  retain the Damage Meters page integration.
- **Grimlight Meters artwork:** the addon-list icon and existing sidebar slot use
  AI-generated fantasy artwork with ascending crystal meter columns. The host
  still owns sidebar tint, sizing and behavior; native visual acceptance is pending.
- **Normal meter controls:** headers, menus, scrolling, reports and breakdowns
  remain available. Chat resizing immediately resizes the embedded panes;
  settings, Edit Mode and EUI Unlock Mode preserve embedding. Explicitly disabling
  embedding restores standalone placement without resetting window choices.
- **Chat reports:** an added Report control previews a readable snapshot and sends
  only after an explicit Send Report action. Lines respect the 255-byte UTF-8 chat
  limit, group sends are paced, and protected totals cannot be exported.
- **Instance reset prompt:** one Yes/No choice per visit, including PvP/scenarios.
  Yes resets meter sessions; No preserves them. Combat deferral and reload tracking
  prevent repeated prompts. Metric selections and layouts stay intact.
- **Spell history extensions:** retained alongside the existing meter sessions and
  native row pools.

### Threat, integrated into existing UI

- **Threat is a normal Damage Meters mode**, including embedded panes and bookmarks.
  It uses the same rows, fonts, styles, headers and pinned-self presentation.
- In Threat mode, open the **segment menu** for **Target/Focus**, friendly-unit
  enemy selection, **Show Pets**, **Pull %/Tank %**, percentage/raw text, optional
  pull reference row, warning threshold/sound/skip-tank controls and a bounded
  **10-second preview**. Pull reference and warnings are opt-in.
- Bars retain native 0–100 pull progress. Readable values permit holder-first
  sorting; protected values keep safe native rendering and stable order. Threat
  is live data, not fabricated historical sessions. Polling stops when inactive.
- **Official nameplate threat text** is the sole nameplate renderer. This fork adds
  **Below Health Bar** to its position selector, with cast-bar clearance and the
  existing font, color and X/Y controls.
- The former custom threat-pressure badges and `/euithreat` are retired. The
  official standalone threat window stands down while the embedded provider is
  available; it remains a fallback when Damage Meters is disabled. No separate
  ForeverThreat addon is needed.

### Forever buff reminders

- Paladin **Tank Mode / Righteous Fury**, preferred aura, personal/group blessing,
  optional out-of-combat group coverage, food, flask/elixir and main-hand temporary
  enchant reminders extend the official reminder display.
- Named active-effect selectors and existing Camp/custom spell preferences remain
  available. Built-in spell families and custom entries are deduplicated without
  deleting saved choices. Automatic seal reminders have been removed.
- **Show in Cities / Inns** is optional and defaults off. Other global/section
  location exclusions and settings-panel suppression continue to apply.
- Unavailable aura information is **unknown**, never assumed missing. Diagnostic
  unknown-status icons default off; opting in shows dim, silent indicators without
  misleading stock-zero badges or cast actions. Actual buff actions require a
  player click out of combat.

### Bags, bank and native windows

| Area | Custom behavior |
| --- | --- |
| Bags | Serialized, confirmed inventory transactions; locked-slot reservations; sort/randomize cleanup and timeouts; categories and Sort to Bottom; stack splitting and disenchant actions; profession-bag transfers using real family masks, matching stacks first and metadata/binding checks. Native MultiBag behavior remains. |
| Bank | Forever-native equipment/page tabs, search, bag purchase, locks, money and account controls, with a separate bank skin setting. |
| Character / Inspect | Custom six-tab shell, collapsible panes, stats styling, item levels inside the icon's upper-right corner, green enchant details/tooltips and gems. Official item-stat/weapon-DPS labels use a separate lane; duplicate shell/enchant painters are suppressed. |
| Legacy | Native rewards, challenges and tree integrated with the custom native window presentation. |
| Spellbook / talents / professions | Ranked spellbook, talent-window fixes, profession overview/cards, First Aid, crafting and pooled recipe details. |
| Other windows | Forever adapters for Collections, Group Finder, social, Edit Mode, auction and native window geometry/tooltips. |
| Quest tracker | Native anchors plus local layout, options and taint fixes; yields to Questie's enabled tracker and restores existing EUI preferences when it is disabled. |
| Data Bars / minimap | Real Forever endpoints for Legacy, Spellbook, Talents and Professions, preserving disabled choices and native capability explanations. |

Native window skins retain their **EUI / Modern / Off** choices where supported.
Native menu and bag bars retain native artwork and interaction states; official
Action Bars visibility controls still apply. The previous custom tile/bar repaint
is intentionally removed.

### Flight timer, groups and unit frames

- **Flight timer:** the official v9.3.4 route track includes multi-stop labels,
  route preview and optional early landing. It retains a local takeoff-detection fix for delayed
  taxi state or missing control events. It checks briefly after a taxi click,
  avoids idle polling and duplicate starts, and cleans up on disable. Enabling or
  reloading mid-flight shows elapsed time since detection without inventing a
  destination or ETA. Route learning, normal-arrival calibration, early-landing
  exclusion and Frequent Flier adjustment remain.
- **Party/raid:** the owner's installation uses the full official renderer with
  party/raid options, previews, aura managers, click casting and party targets/pets.
  New official level text and missing-buff indicators are available and default
  off to preserve the previous appearance. Existing explicit choices remain.
  The optional native fallback remains available. EUI Unlock Mode owns official
  positions; Blizzard Edit Mode owns native-fallback positions.
- **Heal/shield prediction:** official player/target/focus prediction owns supported
  units, including OFF. A local native extension covers pet/target-of-target and
  other unsupported units without duplicate overlays.
- **Actions/resources:** native action/paging/security, HUD/layout and combat/Edit
  Mode fixes are preserved. Current builds use official countdown styling; old
  build-specific adapters stay inactive. Missing spell IDs, readable zero Holy
  Power maximum and protected resource values have local compatibility handling.

### Appearance and supported official features

Custom controls follow their host's **EUI, Blizzard, Classic or Forever** style.
Chat sidebar plates, Report/Threat header icons, report dialogs, fonts, hover,
pressed and selected states use the host renderer. Chat style, meter style,
options-panel theme, accent and native-window skin choices remain independent.

Official v9.3–9.3.4 features such as controller support, optional Forever artwork /
PapaPixels controls, party targets/pets, reminder growth direction, mana spark,
resource-bar swing timers and compatible fixes remain integrated. These are
official features, not claims of new work by this fork. The owner's Forever
options theme and cyan accent are preserved locally, not imposed on downloaders.

The latest integration also brings official shared combat deferral, resource mana
prediction/regen, ranked HoverCast and group fixes, nameplate text slots and meter
visibility optimizations. See the [upstream integration audit](docs/UPSTREAM_9.3.4.md)
for feature ownership and preservation decisions.

### Compatibility and diagnostics

Forever bootstrap/API adapters, native actions, normal SavedVariables lifecycle,
profile preservation and secret-value protections remain in place. Unsupported
Mythic+ tools, keystones, seasonal dungeon teleports, Great Vault, crest calculator,
Skyriding HUD and Retail-only rating/difficulty controls stay unavailable; the
Mythic Timer manifest is disabled. Native features are not removed just because
their names also appear in Retail.

`/euiforever` provides diagnostics. Error-bearing reports are retained through
normal reload/logout checkpoints in the existing database, with five reports
capped at 32 KiB each. The original error handler remains active. Diagnostics stay
local; nothing is automatically uploaded. A crash can lose unsaved reports.

## Install or update

1. Download the **EllesmereUI-9.3.4-forever.0.5.0.zip** release asset (or the matching
   asset from a later release). GitHub's automatic source archives are developer
   checkouts, not ready-to-copy AddOns packages.
2. Back up your current suite and settings. For a complete package replacement,
   close WoW, then extract the ZIP's sibling `EllesmereUI*` folders into the
   Forever client's `Interface/AddOns` directory. Do not nest them under one
   additional directory. Use the supplied disabled Mythic manifest; an old active
   Mythic Timer manifest must not remain from a different package.
3. Enable the desired modules. Chat embedding requires **EllesmereUI**,
   **EllesmereUIChat**, **EllesmereUIDamageMeters** and **EllesmereUIChatMeters**.
   Do not install standalone Raid Frames or Forever Essentials over the complete
   suite: they duplicate shared implementations.
4. Keep your own saved settings. **No WTF files or personal profile export are
   included.** The private profile seed is replaced only in the public build with
   a no-op file; new users get normal suite defaults. Never use that placeholder
   to overwrite the owner's private installed seed.

Routine source fixes can be loaded with a player-initiated `/reload`; documentation
and source publishing need no reload. Complete package updates need a consistent
replacement because load-on-demand modules could otherwise load mixed versions.

**CurseForge updates can overwrite this custom code.** The owner's installation
uses a separate private capture/three-way-merge workflow; a plain upstream update
does not preserve this fork. Follow [maintenance guidance](docs/MAINTENANCE.md)
and use this repository's releases for the published custom build.

## Handy controls

| Control | Purpose |
| --- | --- |
| `/eumeters` | Open Chat Meters settings. |
| `/eumeters show` / `hide` | Switch to meters or chat. |
| `/eumeters on` / `off` | Enable embedding or explicitly restore standalone windows. |
| `/eumeters status` | Show embedding readiness. |
| Meter type menu → Threat | Select integrated threat; use its segment menu for Threat options. |
| `/euigroups official` / `native` | Select the group renderer; follow the command's reload guidance. |
| `/euiforever` | Local diagnostic tools. |

## Verification and release policy

The installed update passed **52 active regression scripts and Lua 5.1
compilation** on October 1, 2026. Public packaging additionally checks hashes,
load references and private-profile exclusion. Some source tests require the
owner's private profile or separately preserved native fixtures; see maintenance
notes rather than treating missing dependencies as passed tests.

Offline checks do not certify live rendering, secure combat, absence of taint,
taxi behavior or client persistence. Recent changes still have live acceptance
pending the player's reload and testing.

Every future custom change is committed and pushed here. Major upstream or
custom updates also receive a tagged GitHub Release with an installable ZIP,
checksum, changes and validation notes. Private settings, diagnostics and backups
remain outside the repository.

## Credits and license

EllesmereUI and its official features/artwork are by **Ellesmere / EllesmereGaming**
and the upstream contributors. This repository maintains NYTEMODEONLY's custom
Forever modifications. Upstream's [license](license.txt) and third-party library
licenses are retained; this fork does not relicense those materials.
