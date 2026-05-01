# OSBuilder Friendly-Error Dictionary

This directory holds the data file that `scripts/friendly_error.py` uses to
translate raw subprocess output and exception strings into plain-English
`FriendlyMessage` objects. The translator is the boundary between OSBuilder's
internal error handling and the user-facing terminal output.

## Location and Format

- **File path:** `references/friendly-errors/dictionary.yaml`
- **Format:** YAML block sequence (one record per error pattern).
- **First record:** the `format_version` metadata record. It is required
  before any error entries; `friendly_error.load_dictionary` raises
  `SystemExit` if it is missing or set to anything other than `"1.0"`.
- **Parser:** the file is parsed by `friendly_error._parse_yaml_subset`, a
  hand-rolled YAML subset parser. It supports inline scalars, `~` for null,
  comments (`#`), and a single layer of nested block sequences (used only by
  `format_version.schema_fields`). Multi-line block scalars (`|`, `>`) are
  not implemented — extend the parser and add tests if you need them.
- **No third-party YAML dependency** is introduced. The parser stays self-
  contained inside `friendly_error.py`.

## Field Schema

Every error entry must have exactly these nine fields:

| Field                 | Type             | Description                                                                          | Example                                |
| --------------------- | ---------------- | ------------------------------------------------------------------------------------ | -------------------------------------- |
| `id`                  | string (slug)    | Unique slug; lowercase + hyphens. Used as the entry's stable identifier.             | `port-in-use`                          |
| `match_pattern`       | string           | Substring or regex matched against the raw error text (case-insensitive).            | `EADDRINUSE`                           |
| `category`            | string (enum)    | One of: `preflight`, `gh-auth`, `registry`, `runtime`, `docker`, `filesystem`, `network`, `git`, `scaffold`. | `runtime`                              |
| `title`               | string           | Plain-English title (no jargon, no errno codes).                                     | `The port is already taken`            |
| `what_broke`          | string           | One sentence explaining what failed, in user-facing language.                        | `Another process is already listening...` |
| `what_to_do`          | string           | Plain-English instruction for the user.                                              | `Stop the other thing using port 3000.` |
| `copy_paste_command`  | string or `~`    | Exact shell command for the user to run, or `~` (null) when there is no single fix. | `lsof -i :3000`                        |
| `phase_seen`          | string           | Free-form phase tag: which OSBuilder phase(s) saw this error.                        | `preflight`, `2-3`                     |
| `expansion_note`      | string           | Provenance: where the entry came from (PITFALLS.md, dogfood, ecosystem standard).    | `PITFALLS.md P15`                      |

A tenth optional field, `pattern_type: regex`, switches `match_pattern` from
substring matching to `re.search`. Omit it for substring entries.

A schema_fields list is also stored on the `format_version` metadata record
as a self-describing reference. It mirrors the nine fields above.

## How to Test a New Entry

1. Add the entry to `dictionary.yaml`. Keep the **ORDER MATTERS** rule in
   mind: more specific patterns must come *before* generic ones (e.g.
   `slopsquat-blocked` before `npm-404`, `pnpm-not-found` before
   `npm-not-found`).
2. Run the test suite:
   ```
   python3 -m pytest scripts/tests/test_friendly_error.py -x --tb=short -q
   ```
3. No code changes are needed. `load_dictionary` re-reads the file on each
   process start; `translate` walks `_DICTIONARY` in file order.
4. If your entry uses regex, set `pattern_type: regex`. If your entry uses
   ctx interpolation (`{tool}`, `{project_dir}`), the wiring site must
   pass that ctx key — the `_safe_format` path falls back to the original
   template on KeyError, so missing keys never raise at runtime.

## Inclusion Criteria

Add an entry only when at least one of the following is true:

- The error has been seen in a real dogfood build at least twice.
- The error definitively blocks user progress on a typical first build
  (e.g. preflight install failures, missing CLI tools, registry 404s).
- The error has a security implication that users need to understand
  (slopsquatting, path traversal, secret leakage).

Each entry must:

- Provide a concrete `copy_paste_command` if a single command can fix the
  problem; otherwise set it to `~`.
- Avoid jargon in `title` and `what_to_do`. Forbidden tokens: errno codes
  in the title, framework module names, raw exception class names.
- Match no more than one ecosystem-standard failure mode (one entry per
  failure family — split into multiple entries only if the user-facing
  remediation differs).

## Format Version

The `format_version` field on the first record is currently `"1.0"`.
`friendly_error.load_dictionary` rejects any other value with `SystemExit`
and a clear message. Increment the version (and update the test pin in
`test_dictionary_format_version_checked`) when:

- A required field is added or removed.
- The semantics of an existing field change.
- The pattern-matching algorithm changes (regex flags, anchors, etc.).

Mechanical edits — adding a new entry, fixing typos in existing entries,
reordering — do **not** require a format-version bump.
