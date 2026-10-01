# Grimlight Meters companion maintenance

Read [the repository guide](../AGENTS.md) and
[maintenance procedure](../docs/MAINTENANCE.md). The custom embedding companion
is original Grimlight work; EUI host modules remain separately owned and retain
their credits/licenses. Preserve the installed folder/save identity until a
reviewed data-preserving public upgrade is ready. Do not publish host source as
part of a standalone Grimlight companion.

Each player-facing companion fix/update needs an incremented vMAJOR.MINOR.PATCH
with aligned TOC/runtime/ZIP/changelog and a verified file on its dedicated
CurseForge page, in addition to the existing applicable GitHub workflow. The
owner gives standing authorization for eligible releases; no project ID is
recorded yet. Establish and verify its own project, never an upstream/host ID.
Read back uploads and complete publication after moderation and actual gates.
Record exact blockers and pending version/file; an unpublished file has not
delivered the update. Internal AGENTS-only edits need no runtime bump/release.

Ship neutral defaults and empty player state. No owner meter/chat layouts,
anchors, settings, characters, history, profiles, diagnostics, receipts or
credentials may ship. Verify an allowlisted clean stage, actual final ZIP and
fresh synthetic initialization without owner saves. Supported upgrades retain
existing players' settings; never deploy a public placeholder over private
seeds. The separate Auctions base Veruca v0.1 exception does not apply here.

Ordinary scoped Lua/XML edits use external backups, relevant checks and the
player's convenient /reload while WoW may stay running. Never send game input
or execute SavedVariables. Writing live saved data requires a closed client.
Preserve native frame ownership, optional-host failure behavior, secret-value
guards, UI reuse and independently versioned companion metadata. State offline
checks, loaded code and observed native acceptance separately.
