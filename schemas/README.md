# Pair state schemas

These JSON Schemas define the persistent protocol used under `.pair/`.

Current schema version: **1**

Canonical state files:

- `.pair/config.yaml` -> `config.schema.json`
- `.pair/manifest.yaml` -> `manifest.schema.json`
- `.pair/progress.yaml` -> `progress.schema.json`
- `.pair/pitfalls.yaml` -> `pitfalls.schema.json`
- `.pair/operations/*.yaml` -> `takeover-operation.schema.json`

New state must use `schema_version: 1`.

Early Pair Programming Skill builds used `version: 1` in YAML templates. A reader may accept
that legacy key when recovering an existing feature, but any subsequent write should
canonicalize it to `schema_version: 1`. Never rewrite unrelated state merely to migrate the
key.

Schemas are intentionally stricter at the top level and extensible inside evidence/result
objects so repositories can preserve project-specific validation details.
