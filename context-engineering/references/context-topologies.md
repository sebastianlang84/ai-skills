# Context topologies

How the knowledge about a machine's applications and repositories reaches an agent. There is no
best topology; choose one per environment, record the choice and its reason in one place, and
revisit it when the environment changes. Read `harness-loading.md` first: every topology depends
on what each harness actually loads.

## Topologies

| Topology | Shape | Fits when | Costs and failure modes |
| --- | --- | --- | --- |
| Monolithic global file | Everything about all apps in the global instruction file | One or two apps, one harness | Loaded in every session; Codex cuts silently at 32 KiB; app detail drifts and contradicts the repos |
| Routing map in the global file | One line per app (path, responsibility) in the global file; detail in each repo | Few, stable apps; sessions often start outside the repos | Every session pays for every line; grows linearly; the map duplicates ownership that lives elsewhere |
| Skill per app | One skill per app: the description says what the app is and when it applies, the body holds paths, interfaces and runbooks | Many apps, several harnesses, apps used from outside their repo | Depends on the skill listing (cut on overflow, per harness); a vague description triggers wrong or not at all; each skill needs a distinct job |
| Index in a knowledge base | A pointer in the global file to an index (e.g. a Brain page) that lists the apps | Large or fast-changing landscape | Weakest guarantee: the agent must follow the pointer; the index goes stale without an owner |
| Repo-local only | Each repo's own instruction file; nothing global | Sessions always start inside the relevant repo | Cross-repo tasks and sessions started elsewhere see nothing |
| Injected by hook | A session-start hook writes the relevant facts into the context | Facts that depend on the runtime (host, client, checkout) or a rule that was broken despite prose | Harness-specific; must be built and tested per harness; adds a failure point |

Hybrids are normal: for example skill per app for routing, repo-local files for development rules,
an index for the full map, and a hook only for runtime facts. Keep one canonical home per fact
across all of them.

## Choosing

Decide from the environment, not from preference:

1. **Where sessions start.** Inside repos favours repo-local files; from the home directory or a
   coordinating session needs global routing (map, skills or index).
2. **Harnesses in use.** Check for each one what it loads globally and how it lists skills; a
   topology that one harness does not load is not a topology for that machine.
3. **Number and stability of apps.** A few stable apps fit a map; many or changing apps fit skills
   or an index.
4. **Cross-app work.** Frequent tasks that span apps need every app's responsibility visible at
   once (map or skill descriptions), not only after a lookup.
5. **Guarantee needed.** What must always be known goes into always-loaded context or a hook; what
   is needed on demand goes into skills, references or an index.

## Verifying the choice

In a fresh session of each harness, started where real sessions start, first inspect which
routing instructions and skill descriptions were actually supplied, checking for truncation. Then
allow the reads and tools the chosen topology requires and ask which app owns a sample task,
including one near-miss between two apps. Verify that the agent reaches the canonical ownership
source and answers correctly. Repeat after adding apps or skills.
