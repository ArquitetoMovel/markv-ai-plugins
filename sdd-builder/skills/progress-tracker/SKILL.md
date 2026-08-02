---
name: progress-tracker
description: >
  Canonical schema and single-writer protocol for `.sdd-builder/prd_map_progress.json`,
  the feature roadmap that tracks every PRD feature through `todo`, `in-progress` and
  `done`. Use when creating, reading or updating the roadmap file, when several agents
  may touch it in the same run, or when reporting overall project progress.
---

# progress-tracker

## Objective

Define one canonical artifact for feature progress across the whole SDD journey and one
protocol for writing to it safely. Every other skill in `sdd-builder-plugin` reads this
file; only the writers named below may modify it.

The file lives at `.sdd-builder/prd_map_progress.json`, next to the PRD.

---

## File schema

```json
{
  "project": "My Project",
  "version": "1.0",
  "lang": "en",
  "prdPath": ".sdd-builder/PRD.md",
  "updatedAt": "2026-08-01T20:28:00Z",
  "features": [
    {
      "id": "F01",
      "name": "Authentication System",
      "status": "done",
      "wave": 1,
      "priority": 1,
      "specPath": ".sdd-builder/F01-authentication-system/",
      "updatedAt": "2026-08-01T20:28:00Z",
      "note": ""
    }
  ],
  "decisions": [
    {
      "id": "D01",
      "title": "Session storage",
      "decision": "Server-side sessions in Postgres instead of JWT"
    }
  ],
  "notes": ""
}
```

### Field rules

| Field | Rules |
|---|---|
| `project` | Product title from the PRD H1. |
| `version` | Schema version of this file. Always `"1.0"` for now. |
| `lang` | Language the PRD was written in, as a BCP-47-ish tag: `en`, `pt-BR`, etc. `spec-builder` reads this to decide the language of `spec.md`, `plan.md` and `tests.md`. |
| `prdPath` | Repo-relative path to the PRD that this roadmap belongs to. |
| `updatedAt` | UTC ISO-8601 with `Z`, e.g. `2026-08-01T20:28:00Z`. Refreshed on every write. |
| `features[].id` | Must match the PRD feature IDs exactly (`F01`, `F02`, ...). Unique. |
| `features[].name` | Feature name from PRD Section 6, without the ID prefix. |
| `features[].status` | Exactly one of `todo`, `in-progress`, `done`. No other literal is valid. |
| `features[].wave` | Integer wave number from PRD Section 8 Execution Waves. Omit when the PRD has no waves. |
| `features[].priority` | Integer 1-3 from the PRD dependency table. |
| `features[].specPath` | Folder holding `spec.md` / `plan.md` / `tests.md`. Empty string until `spec-builder` runs. |
| `features[].updatedAt` | UTC ISO-8601 of the last status change for this feature. |
| `features[].note` | Short free text: why a feature is blocked, what was detected as already implemented, abort reason. Empty string when there is nothing to say. |
| `decisions[]` | Cross-cutting decisions worth remembering across features. `id` is `D01`, `D02`, ... |
| `notes` | Free text at project level. Used by `prd-builder` to record missing repo documentation warnings. |

`features` order follows the PRD dependency table (topological order), not status.

---

## Status semantics

| Status | Meaning | Who sets it |
|---|---|---|
| `todo` | Declared in the PRD, not implemented. | `prd-builder` at creation |
| `in-progress` | Implementation started and not finished, or finished with unresolved failures. | `feature-builder` |
| `done` | Implemented and verified: the feature's final verification passed. | `feature-builder` |

Extra rules:

- On an **existing project**, `prd-builder` marks a feature `done` when the capability is
  already present in the codebase. Record the evidence in `note`, e.g.
  `"detected in src/auth/session.ts"`.
- `spec-builder` never changes `status`. It only fills `specPath`.
- A `feature-builder` run that ends in `completed with regressions`, `incomplete` or
  `aborted` leaves the feature `in-progress` and writes the reason to `note`.

---

## Single-writer rule

Concurrency is handled by restricting who writes, not by hoping writes interleave well.

**Allowed writers**

| Writer | Allowed mutations |
|---|---|
| `prd-builder` | Create the file; write `project`, `version`, `lang`, `prdPath`, the full `features` array, `notes`. |
| `spec-builder` | Update `specPath` of the features it generated. In Batch Mode, only the **orchestrator** writes, once, after all sub-agents return. Sub-agents never write. |
| `feature-builder` | Update `status`, `note` and `updatedAt` of the single feature it is implementing, and append to `decisions`. |

**Forbidden writers**

- Technology specialist sub-agents (`sdd-dotnet-specialist` and siblings) never open this
  file for writing. They report back to `feature-builder`, which performs the write.
- Any sub-agent dispatched in parallel. Parallel fan-out must always converge on a single
  writer before touching the roadmap.

---

## Write protocol

Never write the file from memory. Always run the full cycle:

1. **Acquire the lock.** `mkdir` is atomic on POSIX, so it is the lock primitive:

   ```bash
   mkdir .sdd-builder/prd_map_progress.lock 2>/dev/null \
     && echo "acquired" \
     || echo "busy"
   ```

   On `acquired`, write an owner stamp so a stale lock can be diagnosed:

   ```bash
   printf '%s %s %s\n' "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "<agent-name>" \
     > .sdd-builder/prd_map_progress.lock/owner
   ```

   On `busy`, wait 2 seconds and retry, up to 5 attempts. If still busy, read
   `.sdd-builder/prd_map_progress.lock/owner`: when the stamp is older than 10 minutes the
   lock is stale, so report it to the user and ask before removing it. Never remove a
   fresh lock.

2. **Re-read** `.sdd-builder/prd_map_progress.json` from disk. Discard any copy loaded
   earlier in the run: another agent may have changed it.

3. **Mutate only your own scope.** Touch just the fields listed for your writer role above,
   and just the feature entries you own. Leave every other entry byte-identical.

4. **Refresh timestamps.** Set the top-level `updatedAt` and, for each feature you changed,
   its own `updatedAt`.

5. **Write atomically.** Write to a temporary file in the same directory, then rename:

   ```bash
   mv .sdd-builder/prd_map_progress.json.tmp .sdd-builder/prd_map_progress.json
   ```

   `mv` within the same filesystem is atomic, so a reader never sees a half-written file.

6. **Release the lock**, including on failure:

   ```bash
   rm -rf .sdd-builder/prd_map_progress.lock
   ```

7. **Verify.** Re-read the file and confirm it parses as JSON and contains the change you
   made. If parsing fails, restore the pre-write content and report the failure instead of
   leaving a corrupt roadmap behind.

Keep the locked window as short as possible: do all analysis before step 1. The lock covers
read-modify-write only, never implementation work.

---

## Validation

Run before any write is considered complete:

- [ ] The file parses as valid JSON.
- [ ] `features[].id` values are unique and each one exists in the PRD dependency table.
- [ ] Every feature in the PRD dependency table appears exactly once in `features`.
- [ ] Every `status` is one of `todo`, `in-progress`, `done`.
- [ ] `updatedAt` fields are UTC ISO-8601 ending in `Z`.
- [ ] `lang` is present and matches the language the PRD was actually written in.
- [ ] No lock directory left behind at `.sdd-builder/prd_map_progress.lock`.

---

## Reading the roadmap

Consumers should read, never guess:

- `spec-builder` reads `lang` to pick the output language, and `status` to skip features
  that are already `done`.
- `feature-builder` reads `specPath` to locate `spec.md` / `plan.md`, and `status` to skip
  work that is already `done`.
- The orchestrator agent reads the whole file to answer "where is this project?" without
  re-scanning the codebase.

Progress summary format when reporting to the user:

```text
Roadmap: 12 features — 5 done, 2 in-progress, 5 todo
Next up (wave 3): F06 Video Player, F07 Transcription Search
```

---

## Edge cases

**File does not exist and the caller is not `prd-builder`:** stop and tell the user to run
the PRD step first. Do not synthesize a roadmap from the codebase.

**PRD has features that are missing from the roadmap** (PRD edited by hand after
generation): report the drift, then add the missing features with status `todo`. Never
delete entries that disappeared from the PRD — set `note` to `"no longer in PRD"` and leave
the status untouched so the history is preserved.

**Feature IDs renumbered in the PRD:** do not attempt an automatic remap. Report the
mismatch and ask the user whether to rebuild the roadmap from the current PRD.

**Lock directory exists but has no `owner` file:** treat it as fresh for one retry cycle,
then as stale, and confirm with the user before removing.

**Read-only filesystem or write failure:** report the exact path and the OS error. Do not
continue the SDD flow pretending the roadmap advanced.
