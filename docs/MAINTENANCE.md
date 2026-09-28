# Publishing and release maintenance

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
evidence; private fixture absence is not a passed check. The baseline had 50
passing active scripts plus Lua 5.1 compilation on September 27, 2026.

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
