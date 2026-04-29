# Frontmatter Conventions

Use compact YAML frontmatter on maintained Markdown files so file role and update triggers are visible when the file is opened.

## Required fields

```yaml
---
role: Short noun phrase describing the file's job
contains: Information that belongs in this file
not-contains: Information that should not be stored here
write-when: Concrete update trigger
---
```

## Field guidance

### `role`

Use one sentence fragment. Describe the file's authority, not its topic only.

Good:

- `Primary bootstrap document for follow-up agent sessions`
- `Active open work backlog`
- `Human/operator entry point`

Avoid:

- `Docs`
- `Misc notes`
- `Important file`

### `contains`

List the information categories that belong here. Keep it short enough to read at a glance.

### `not-contains`

Name common drift risks. This is where the frontmatter earns its keep.

Examples:

- `Diary-style history`
- `Active backlog`
- `Agent operating rules`
- `Detailed architecture decisions`
- `Secrets`

### `write-when`

State the update trigger. Prefer observable events over vague advice.

Good:

- `Setup, usage, operation, support, or project positioning changes`
- `Active work or priorities change`
- `A durable decision is made`

Avoid:

- `When needed`
- `Often`
- `Whenever`

## Rules of thumb

- Frontmatter is not a replacement for reading the file.
- Do not add frontmatter to generated files unless it will be preserved.
- Do not use frontmatter to store secrets, owners, credentials, or volatile status.
- If the frontmatter becomes long, the file role is probably unclear.
- Keep field names stable: `role`, `contains`, `not-contains`, `write-when`.
