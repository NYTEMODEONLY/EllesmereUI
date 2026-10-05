# Custom UI maintenance and community releases

Owner direction, October 4, 2026: keep this existing GitHub project. The separate
CurseForge edition proposal is shelved. The community entrance is
https://grimlightdepot.com/ui, with prominent original EllesmereUI credit.

## One update path

1. Read the official [patch notes](https://ellesmereui.com/patch-notes) and
   [complete-suite releases](https://github.com/EllesmereGaming/EllesmereUI/releases).
   Identify and pin the new upstream tag and package hash. The current custom tag
   includes its actual integrated upstream version; never call an unmerged release current.
2. On MESHWORK, follow the installed `UPDATE_WORKFLOW.md` and external
   `EllesmereUI-Forever-Updates/README.md`. Resolve `current.json` each time,
   import diagnostics, back up the suite, and capture local custom changes before
   any replacement. Stage a three-way merge from the matching official/custom pair.
3. Review features, file moves, ownership overlaps and migrations; retain custom
   functionality and all player settings. Run the existing full regressions,
   Lua 5.1 compile and active TOC/XML checks. Record exact verified hashes and rollback.
   A clean text merge is insufficient; never automatically overwrite the installation.
4. Capture verified custom source, export with `tools/sync_public.py`, and review
   the diff and privacy manifest. Public packages use the exact no-op private-profile
   placeholder. No WTF, SavedVariables, personal layouts, history, diagnostics,
   native fixtures, credentials or recovery files may be published. Retain credits
   and applicable licenses; the existing redistribution-rights gate still applies.
5. Commit and push reviewed public changes to this repository; verify the remote SHA.
   For an eligible upstream integration or major custom change, build the complete
   suite using `tools/package_release.py`. Publish an immutable
   `vUPSTREAM-forever.X.Y.Z` tag with `EllesmereUI-VERSION.zip`, `SHA256SUMS.txt`,
   and notes describing the upstream base, custom changes, checks and pending live acceptance.
   Upload both assets before marking the stable release **Latest**. Do not move old tags.
6. Verify GitHub's `/releases/latest` points to that exact tag and both assets are
   publicly downloadable with the expected hash. The repository's Releases sidebar
   should show that tag. Documentation/website-only changes do not need a new suite version.
7. Check https://grimlightdepot.com/ui-release.json reports the intended custom
   version and upstream base. Check https://grimlightdepot.com/ui/download returns
   a redirect to the versioned ZIP, then verify the downloaded bytes against SHA256SUMS.
   Metadata is cached for at most two minutes. The README's stable link needs no
   per-release edit. GitHub failures/incomplete assets show an explicit fallback;
   the site must not silently substitute a source archive or claim a stale version latest.
8. The existing Gibson Grimlight Tools service checks custom GitHub releases every
   two minutes, validates the full package and announces it in `#ellesmere-ui`.
   Verify the exact saved receipt, version and both buttons. The primary button is
   **Explore UI & downloads** → https://grimlightdepot.com/ui; the secondary link
   opens that release's notes. Preserve `state/eui.sqlite3`; never reset or replay
   history. Website/presentation changes edit the existing saved receipt in place.

## Ownership and recovery

- Canonical suite checkout: `C:/Users/Lobo/Documents/GitHub/EllesmereUI`.
- Private update manager: `C:/Users/Lobo/Documents/EllesmereUI-Forever-Updates`.
- Website/automation Git history: `C:/Users/Lobo/Documents/GitHub/grimlightdepot`.
- Editable bot source: `C:/Users/Lobo/Documents/MESHWORK/grimlight-automations`.
- Website route and dynamic latest links: `site/ui-release.mjs` in grimlightdepot.
- Bot operations: `grimlight-tools/eui-monitor.md` in the automation source.

Keep the website and bot source mirrored between their documented PC paths and
the grimlightdepot repository. Back up state before service upgrades, retain
encrypted credentials and verify boot-enabled services plus the common monitor audit.
Preserve the previous Cloudflare version for site rollback. Game runtime updates
still require the player's own reload and acceptance; publishing is not live testing.

The original UI is by [Ellesmere / EllesmereGaming](https://ellesmereui.com/).
Link the [official CurseForge project](https://www.curseforge.com/wow/addons/ellesmereui)
and upstream source prominently. Custom support belongs to this fork. No new
license or official endorsement is implied by maintaining this workflow.
