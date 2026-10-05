## October 4: GitHub distribution and the Depot UI page

The owner's latest direction keeps https://github.com/NYTEMODEONLY/EllesmereUI
as the canonical custom project. The proposed separate CurseForge edition is
shelved; do not migrate source or publish a custom CurseForge project.

The community introduction is https://grimlightdepot.com/ui . Website My UI
links and Discord UI announcement buttons go there. That page credits Ellesmere /
EllesmereGaming and links both the original UI and the canonical custom GitHub.
The README's https://grimlightdepot.com/ui/download link resolves GitHub's
designated latest stable release to its versioned full-suite ZIP. Never replace
it with GitHub's generated source archive or a personal installation export.

Preserve the existing update, review, privacy, rights and live acceptance gates.
The prior rights review did not record a new redistribution grant; this direction
does not change upstream licenses. This website/docs task links existing releases
and does not publish new upstream code/assets. Do not delete release history.
Read docs/COMMUNITY_RELEASES.md in the canonical GitHub checkout for the complete
cross-project publication checklist. Installed settings and private seeds stay local.

# Publishing and release maintenance

October 1 owner clarification: EUI's GitHub workflow and upstream credits stay
unchanged. The separately owned Grimlight ChatMeters companion also needs a
versioned release on its own CurseForge project for each player-facing update,
once eligible. This is standing authorization; record moderation/publication
blockers rather than treating a local push as completed delivery. No verified
companion CurseForge ID is recorded yet; never use an upstream/host project.
Internal maintenance/AGENTS-only edits require no runtime bump or duplicate
release. See [the current public guide](../AGENTS.md).

Downloads must be neutral fresh installations, without owner profile seeds,
settings/layouts, histories, diagnostics, generated receipts or credentials.
Keep the documented no-op profile replacement and inspect staged/final bytes;
verify clean startup without owner saves. Preserve existing players' data in
supported upgrades. The Auctions base-profile exception applies to that separate
addon only and provides no exception for EUI or Meters.

Every completed change goes to this repository. Major updates also get GitHub
Releases. Use a normal forward commit; never reset this fork to upstream or move
published tags. Existing proposal branches are independent and stay preserved.

## Owner installation to public source

1. Complete the installed workspace's diagnostics-first check and relevant
   backup, edit, verification and external Capture procedure. Resolve the current
   matching official/custom pair from the private manager's current.json.
2. Fetch/review this checkout and synchronize from that reviewed suite capture:
   `python tools/sync_public.py --source PATH_TO_CAPTURE` (Python 3.12+).
3. Review the complete diff and public-source-manifest.json. Core files map to
   the repository root; sibling modules keep their directories. Export uses an
   allowlist of runtime/media/license files and regression source, not private
   reports, saved data, historical maintenance notes or client fixtures. An account
   folder in a quest-tracker provenance comment is redacted; executable code is
   otherwise unchanged except for the no-op private-profile replacement.
4. Curate README/CHANGELOG/agent documentation. The installed private agent guide
   is not copied wholesale; its public policies and behavior belong here.
5. Build with `python tools/package_release.py --output EXTERNAL_OUTPUT_DIR`.
   This checks export hashes, the profile placeholder, TOC/XML references and ZIP
   contents. Runtime files are packaged into sibling addon folders, including
   libraries, ChatMeters and ForeverEssentials. Tests/tools are source-only.
6. Stage explicit reviewed changes, inspect staged content, commit and push to
   main (use the required PR flow if protections change). Check the remote SHA.
   Save publication evidence in the private maintenance receipt.

## Release rules

An upstream version integration, significant custom feature or substantial
behavior/compatibility change is major. Use `vUPSTREAM-forever.X.Y.Z` tags matching
the custom package version. Increment the custom version before subsequent
releases; never overwrite an existing tag or asset. Routine commits do not need
a release unless requested. Documentation alone does not change the addon version.

Create notes with upstream base, custom changes/options, installation steps,
validation, known limits and pending live acceptance. Push the annotated tag for
the verified commit, then publish using GitHub CLI:

```text
git tag -a vVERSION -m "Custom EllesmereUI VERSION"
git push origin vVERSION
gh release create vVERSION PATH_TO_ZIP PATH_TO_SHA256SUMS --verify-tag --repo NYTEMODEONLY/EllesmereUI --title "EllesmereUI Forever VERSION" --notes-file PATH_TO_NOTES
```

Verify release/tag commit and downloaded asset checksum. The inherited workflow
that uploaded to upstream CurseForge/Wago project IDs has been removed. This
workflow publishes only to the owner's GitHub. Do not restore those uploads.

## Tests and evidence

The owner maintains a full private staged regression runner using Python, lupa
Lua 5.1 and preserved native source fixtures. Use its error_reporter.py verify
wrapper when working on that installation. Keep assertions and resolved issue
evidence; private fixture absence is not a passed check. The v9.3.4 integration has
52 passing active scripts plus Lua 5.1 compilation on October 1, 2026.

Review the [v9.3.4 integration audit](UPSTREAM_9.3.4.md) before the next update.
The official framework and ResourceBars options were split into separate files;
local popup fixes now belong in EllesmereUI_Popups.lua. Merge from the current
matching official/custom pair, never a fixed historical baseline. Preserve
ChatMeters' independent v0.4.0 version. The new official Threat bridge must stand
down while the custom provider exists. Missing-buff modules must also stand down
for the native group renderer. Include verify-flight-timer.py and
verify-9.3.4-features.py; fixture changes must preserve behavior assertions.

Regression sources are included for review, but their expected layout is an
AddOns-shaped stage (core files under EllesmereUI/ alongside sibling modules).
Some need native fixtures; the original verify.py also tests the owner's private
profile import and cannot pass against the public no-op replacement. Do not
publish the private seed or weaken that regression. Public packaging checks are
separate from the full private suite. The two external-ForeverThreat harnesses
remain historical, not active dependencies or current tests.

The public seed placeholder makes no API calls and writes no saved state. Existing
user settings stay authoritative; a new installation uses normal suite defaults.
Public code/assets are the custom implementation, not the owner's exported layout.

No offline test establishes game rendering, combat security, taint freedom, taxi
timing or actual saved-data persistence. Preserve those as live acceptance items.


## v9.3.6 maintenance

Read UPSTREAM_9.3.6.md for the current integration. There are 55 active checks.
Options/runtime splits relocate unit prediction refresh to EUI_UnitFrames_Reload
and missing-buff defaults to RaidFrames_Options/VisualIndicators_Options.lua.
All official group parts, including Preview, stand down in native fallback mode.
The shared Essentials Feature kit loads before Travel/Loot. Keep bounded flight
takeoff/recovery and explicit false behavior. Grimlight Meters v0.4.1 uses public
RegisterPlugin/OpenPlugin; never mutate the current host's core module registry.
The old-host fallback remains covered by the companion test suite. New official
skins do not silently take ownership of custom native windows or bar artwork.

The 9.3.6-forever.0.6.1 bag tooltip patch keeps native container item buttons
one frame level above their wrappers in grid, list, detached reagent and upstream
bank factories. Preserve this relative layer when creating pooled buttons; the
native template fixes a low absolute level. Run verify-bag-tooltips.py with the
preserved native fixtures. Normal bag tooltips were player-confirmed after reload;
comparison/combat behavior still requires native acceptance.

## October 5 minimap tray maintenance

The popup click hook excludes its own ungroupBg background so it stays below
the addon icon. Keep this ownership distinction when changing tray child levels.
verify-minimap-tray.py reproduces the old bug; all 56 active scripts and Lua 5.1
compilation pass. Native click/appearance acceptance after reload remains pending.
This routine source fix does not replace the published 0.6.1 release asset.


### Bag Disenchant input

Keep the secure overlay parented and anchored only to UIParent so bag layout
stays unprotected. Explicitly enable mouse input and consume clicks. Set the
visual anchor's hover-only mouse policy after installing scripts. The secure
target is top-level, raises on show and recovers on anchor hover when bag raising
changes hit order. Never raise in combat or continuously during idle updates.
Preserve native secure OnClick, release-only casting and combat hiding.
verify-bag-disenchant.py exercises the native dispatcher, script-enabled input,
raising/reopening, hover recovery, scaling and combat lifecycle. All 56 checks
pass. Authorized live checks on build 1.60.1.70205 verified targeting after bag
raising and reopening, and Escape cancellation. Automation did not select or destroy an item;
actual item disenchant and combat remain untested. Do not publish temporary probes.
