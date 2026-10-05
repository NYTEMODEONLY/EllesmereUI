# Custom release history

## Unreleased maintenance — October 5, 2026

Repair bag Disenchant mouse ownership: explicitly enable the independent secure
click target and stop click propagation; leave the visual anchor hover-only.
Native spell dispatch, combat hiding, bag movement and saved settings are
preserved. Expanded regressions exercise native release-click dispatch with both
key-down settings, layers, scales and lifecycle. All 56 active checks pass;
player reload, targeting cursor and actual item disenchant remain unverified.

Fix addon icons disappearing after a click in the minimap tray's box mode.
The popup-raising hook now leaves its own opaque background below the button's
icon, while still raising addon popup children and respecting protected frames
in combat. Settings, placement and addon click actions stay unchanged.
A Lua 5.1 regression reproduces the old failure and checks repeated clicks,
popup nesting, hidden backgrounds and protected children. Native acceptance
after the player's reload remains pending. This is source maintenance after
9.3.6-forever.0.6.1; the published release ZIP is unchanged.

## 9.3.6-forever.0.6.1 — October 4, 2026

Fix missing bag item tooltips after the 9.3.6 integration. Blizzard's container
button template assigns an absolute frame level that can sit below the raised
bag window. New background hover handling then intercepts item mouseovers.
Grid, list, detached reagent and upstream bank slot factories now put each item
button one level above its parent, keeping native tooltip and item actions.
Saved settings, bag positions, inventory data and tooltip preferences are unchanged.

55 active regressions pass. A new test reproduces the old layer ordering and
executes all four production factories with native tooltip methods, checking
real slot changes, parent/window raises, native scripts and existing combat
creation guards. The player confirmed normal bag item tooltips work after reload.
Native comparison/combat behavior remains unverified. Upstream base stays v9.3.6;
the previous custom features and privacy omissions remain in place.


## 9.3.6-forever.0.6.0 — October 4, 2026

Integrate the official complete-suite v9.3.6 release, including v9.3.5 and the
v9.3.6 HoverCast / Dynamic Rez hotfix.

- Add the official XP overhaul, bag List View and resizing, debuff colors,
  optional Loot Feed/Self Combat Text, moved chat-bubble controls, DataBars icons
  and ordering, resource/absorb/portrait controls, plus compatible fixes.
- Update Grimlight Meters Tab to v0.4.1. Its four embedding controls use the
  supported plugin API under Grimlight Meters > Chat Embedding. Preserve older
  host support, saved views, per-character settings and actual embedded windows.
- Preserve confirmed bag transactions, native bank/sheet/LFG/Legacy owners,
  native bar artwork, embedded Threat/reports and unsupported-system exclusions.
  Upstream reconstructed bank List View stays inactive on Forever's native bank.
- Keep existing visual defaults: Important nameplate buffs, target-and-focus
  threat when enabled, bags above other windows and no equipped-item border.
  New controls stay available; explicit saved choices remain authoritative.
- Relocate custom prediction/missing-buff hooks across upstream file splits.
  Retain flight takeoff/recovery fixes and Questie tracker priority.
- Fix Legacy skin startup when the native reward-card list is not created yet.

54 active regression scripts, Lua 5.1 compilation, manifest references and
disposable updater/rollback checks pass. Public ZIP/profile omission checks are
separate from the private suite. Native rendering, combat/taint, real flights and
persistence still require player acceptance. The independently owned companion's
first CurseForge release remains gated on native/provenance/project requirements.
See [the integration audit](docs/UPSTREAM_9.3.6.md).


## October 2, 2026 maintenance — included in 9.3.6-forever.0.6.0

- Give Questie's enabled tracker priority over the EUI quest tracker. Suppress
  native tracker presentation, click sinks and EUI chrome while Questie owns
  tracking, including hover and native re-show paths. Retain EUI settings and
  anchors for fallback when Questie's tracker is disabled. Observe Questie
  readiness, profile changes and tracker toggles without additional polling.
- All 53 active regression scripts and suite Lua 5.1 compilation pass, including
  the new priority test and existing native tracker anchoring test. Player-run
  reload, native rendering, hover and combat/taint acceptance remain pending.
- Routine fix; upstream and custom baseline version declarations stay unchanged.

## 9.3.4-forever.0.5.0 — October 1, 2026

Integrate official complete-suite v9.3.4, including changes from v9.3.1–9.3.4.
Upstream base: `de88c8670d7ccc308ff96eeda0265f7f468aaaf4`.

- Use the official multi-stop flight route, preview and optional early landing;
  retain bounded Forever takeoff detection and elapsed-only mid-flight recovery.
- Preserve ChatMeters embedding and the custom Threat metric, reports, controls,
  selections and native protected-value rendering. The new official Threat bridge
  stands down while the custom provider owns the metric.
- Integrate the official core/options file splits, shared combat queue, meter
  visibility performance, resource prediction/regen, ranked HoverCast, group and
  nameplate fixes. Move local popup fixes to the new official popup module.
- Make new group level/missing-buff visuals opt-in; preserve native group fallback
  exclusivity, existing appearance, skins, positions, profiles and saved choices.
- Retain native Group Finder/Housing skin controls, native endpoints, bag/bank
  protections, reminders and official supported-unit prediction ownership.
- Preserve dungeon logging preferences across the upstream option rename.
- Keep Grimlight Meters Tab independently versioned `v0.4.0` and retain credits,
  artwork and license boundaries. Public builds omit personal profiles/settings.

The installed suite passes all 52 active regression scripts and Lua 5.1
compilation; disposable updater/rollback checks pass. Public ZIP hashes, manifest
references and private-profile exclusion are checked separately. In-game startup,
flight routes, embedded meters, group combat, native windows and persistence remain
pending player acceptance. See [the integration audit](docs/UPSTREAM_9.3.4.md).

## Grimlight companion release format - October 1, 2026

The custom Grimlight Meters Tab companion now declares `v0.4.0`, following the
owner's `vMAJOR.MINOR.PATCH` release format. This is a metadata-only change;
behavior and saved data declarations are unchanged. EUI host modules retain
their existing versions and attribution. The private capture and public source
manifest preserve the exact companion bytes.

## Source preservation and Meters artwork - October 1, 2026

Preserve the companion’s already-installed Grimlight identity and owner credit;
the earlier public source still used its retail custom-companion label.
The Meters companion now uses the selected AI-generated illustrated icon for
the addon list and its existing sidebar slot. Versions, runtime behavior and
saved declarations are unchanged; native rendering awaits player acceptance.

Preserve previously installed Forever checkbox and comment-box fixes that were
missing from this public source: one inset box on oversized native checkboxes,
no second box on already themed profession controls, and one owned frame for
the Group Finder comment outline. Existing regression sources accompany them.
The full private verification passes 51 active scripts and Lua 5.1 compilation.
Private profiles, diagnostics and native fixtures remain excluded. This source
update does not clear any standalone Grimlight CurseForge release.

## Meters companion license - October 1, 2026

Added the owner's All Rights Reserved notice for original Grimlight contributions
to the Meters companion, with free downloads and readable source. This does not
relicense upstream code/assets or clear a standalone CurseForge release.
Runtime and existing third-party rights are unchanged.

## Maintenance - September 27, 2026

Retired the owner-machine Zero delegation workflow. Agents perform requested
work directly; addon runtime and user settings are unchanged.

## 9.3-forever.0.4.0 — September 27, 2026

First published baseline of the maintained custom installation, based on official
complete-suite v9.3. Earlier upstream history remains in Git.

- Publish the current custom suite, including ChatMeters and ForeverEssentials.
- Preserve chat embedding, readable reports, once-per-visit reset prompts and
  native integrated Threat, including focus/pets/text/pull/warning/preview options.
- Retain official nameplate threat as the sole painter, with Below Health Bar
  placement and cast clearance. Retire the prior badge and duplicate threat UI.
- Include Forever buff reminders, optional town/inn visibility, silent opt-in
  unknown-state diagnostics, deduplication and removal of automatic seal reminders.
- Preserve bag transactions, native bank/window adapters, character/inspect
  details, official stat/DPS lane, group renderer and prediction ownership.
- Include taxi detection, action/layout/resource/native endpoint fixes and host
  style integration. Retain native menu/bag artwork and official visibility.
- Add public documentation, privacy-aware source export and installable packaging.
  Every future change must be pushed; major updates must receive GitHub Releases.

The installed baseline passed 50 active regression scripts and Lua 5.1 compilation.
Live acceptance remains pending for recent changes. This publication changes no
installed runtime files or live settings. Public releases omit the private profile
seed and saved data; see README for the complete feature and options guide.
