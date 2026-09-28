# Custom EllesmereUI Forever repository

Owner instruction (September 27, 2026): every custom change/update must be
committed and pushed to https://github.com/NYTEMODEONLY/EllesmereUI. Major updates
also require an immutable version tag and GitHub Release with notes, an installable
ZIP and SHA-256. This is standing authorization for reviewed nonprivate changes.
Verify the remote commit and release assets before claiming completion. If blocked,
preserve the work and state exactly what remains unpublished.

Read README.md and docs/MAINTENANCE.md first. This checkout uses the upstream
layout: core at root, sibling modules in EllesmereUI* directories. The live game
installation and private customization manager are separate. On the owner's
machine, read the installed EllesmereUI/AGENTS.md and ERROR_REPORTER.md, import
saved diagnostics before checking the external ledger, and follow shared
AddonOverseer guidance before investigating or editing installed files.

Preserve existing Git history and other branches. Fetch/review before synchronizing.
Do not force-push or overwrite concurrent work. Ordinary fixes/docs/tests/options
need commits too. Integrated upstream releases, significant custom features and
substantial behavior/compatibility changes need releases. Keep README and changelog
accurate about custom versus official ownership and pending live acceptance.

Never commit the owner's private profile snapshot, SavedVariables/WTF, chat history,
diagnostics, backups, native fixtures or credentials. The public profile file must
remain the exact no-op placeholder from tools/sync_public.py. Never deploy it over
the owner's private seed. Do not copy private maintenance directories wholesale.

Use tools/sync_public.py to export a reviewed current capture and
tools/package_release.py to verify/build a release. Review all staged changes and
hashes. The inherited CurseForge/Wago release workflow has been removed; publish
only to this GitHub repository. Preserve upstream license and attribution.

For installed source edits, back up outside AddOns, skip reparse points, preserve
settings/profiles/anchors, run existing applicable regressions, retain rollback and
Capture through the private manager. Ordinary Lua/XML edits allow WoW to keep
running; let the player initiate /reload. Documentation requires no reload. Never
send game input, execute SavedVariables or write live saved data. Offline checks,
installed bytes, loaded code and observed live behavior are distinct evidence.

Maintain one owner per UI surface: official nameplate threat text (including the
custom Below Health Bar option), embedded DamageMeters Threat, official group
renderer with optional native fallback, official supported-unit prediction and
local pet/ToT fallback. Retired badges, seals and competing painters stay retired.
Preserve unknown/protected-value handling, theme choices and native actions.
