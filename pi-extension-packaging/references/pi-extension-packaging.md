# Pi Extensions — Mini Best Practice

Stand: geprüft gegen Pi-Dokumentation und Referenzpaket `badlogic/pi-package-test`.

## 1. Begriffe

**Extension**
Eine Pi Extension ist ein TypeScript-Modul, das Pi erweitert, z. B. durch Tools, Commands, Shortcuts, Flags, Events oder UI-Elemente.

**Skill**
Ein Skill ist kein Extension-Code, sondern eine on-demand geladene Capability-Beschreibung mit Workflow-/Setup-/Referenzmaterial.

**Pi Package**
Ein Pi Package kann Extensions, Skills, Prompt Templates und Themes bündeln und über npm, git oder lokale Pfade geteilt/installiert werden.

**„Multi-Extension-Paket“**
Kein offizieller Pi-Begriff. Gemeint ist ein Pi Package, das mehrere Extensions enthält. Der offizielle Begriff bleibt: **Pi Package**.

## 2. Wie Pi Extensions findet

Pi auto-discovered Extensions an diesen Orten:

```text
~/.pi/agent/extensions/*.ts
~/.pi/agent/extensions/*/index.ts
.pi/extensions/*.ts
.pi/extensions/*/index.ts
```

Zusätzlich können lokale Extension-Dateien oder -Ordner in `settings.json` unter `extensions` eingetragen werden.

Für Packages gibt es zwei Wege:

```json
{
  "pi": {
    "extensions": ["./src/index.ts"]
  }
}
```

oder konventionelle Ordner wie:

```text
extensions/
skills/
prompts/
themes/
```

Ohne `pi`-Manifest kann Pi bei Packages Ressourcen aus diesen Standardordnern auto-discoveren.

## 3. Loader-Fakten

Eine Extension exportiert default eine Factory-Funktion:

```ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // register tools, commands, shortcuts, flags, events, UI hooks
}
```

TypeScript funktioniert ohne vorheriges Kompilieren, weil Pi Extensions via `jiti` lädt.

NPM-Abhängigkeiten funktionieren, wenn eine `package.json` neben der Extension oder in einem Parent-Verzeichnis liegt und `npm install` ausgeführt wurde.

Für verteilte Packages gehören Runtime-Abhängigkeiten in `dependencies`, nicht nur in `devDependencies`, weil Package-Installationen produktionsnah laufen können.

## 4. Empfohlene Struktur für eine einzelne Extension

Für eine eigenständige Extension ist diese Struktur am klarsten:

```text
pi-my-extension/
├── package.json
├── README.md
├── CHANGELOG.md          # optional
├── LICENSE               # optional, aber üblich
├── src/
│   ├── index.ts          # einziger Pi-Entrypoint
│   ├── tools/
│   ├── config/
│   ├── types.ts
│   └── utils/
└── test/                 # optional
```

Minimaler `package.json`-Kern:

```json
{
  "name": "pi-my-extension",
  "version": "0.1.0",
  "type": "module",
  "pi": {
    "extensions": ["./src/index.ts"]
  },
  "dependencies": {},
  "devDependencies": {
    "@mariozechner/pi-coding-agent": "*",
    "typescript": "^5"
  }
}
```

Empfehlung:

```text
Eine Extension → package.json → pi.extensions → ./src/index.ts
```

Das ist explizit, leicht zu prüfen und vermeidet Verwechslung zwischen Repo-Struktur und Package-Konvention.

## 5. Empfohlene Struktur für ein Pi Package mit mehreren Ressourcen

Wenn ein Repo bewusst mehrere Pi-Ressourcen enthält, ist die dokumentierte Package-Konvention sinnvoll:

```text
pi-my-package/
├── package.json
├── extensions/
│   ├── subagent.ts
│   ├── planner.ts
│   └── reviewer.ts
├── skills/
│   └── subagent/
│       └── SKILL.md
├── prompts/
└── themes/
```

Dazu entweder kein `pi`-Manifest, wenn nur Standardordner verwendet werden, oder explizit:

```json
{
  "pi": {
    "extensions": ["extensions"],
    "skills": ["skills"],
    "prompts": ["prompts"],
    "themes": ["themes"]
  }
}
```

Glob-Patterns und Excludes sind möglich:

```json
{
  "pi": {
    "extensions": [
      "extensions",
      "!**/legacy.ts"
    ]
  }
}
```

## 6. Entscheidung: `src/` oder `extensions/`?

| Situation                                          | Empfehlung                                                     |
| -------------------------------------------------- | -------------------------------------------------------------- |
| Eine einzelne Extension                            | `src/index.ts` + explizites `pi.extensions`                    |
| Mehrere getrennte Extension-Dateien                | `extensions/`                                                  |
| Package mit Extensions + Skills + Prompts + Themes | Standardordner `extensions/`, `skills/`, `prompts/`, `themes/` |
| Lokale schnelle Einzeldatei                        | `~/.pi/agent/extensions/name.ts`                               |
| Projektlokale Extension                            | `.pi/extensions/name.ts` oder `.pi/extensions/name/index.ts`   |

Wichtig: `extensions/` ist nicht falsch. Es ist dokumentierte Package-Konvention. Für eine einzelne Extension ist `src/index.ts` aber meist klarer.

## 7. Anwendung auf typische Repos

### `pi-context7-cli`

Sieht nach einzelner Extension aus.

```text
pi-context7-cli/
├── package.json
└── src/index.ts
```

`package.json`:

```json
{
  "pi": {
    "extensions": ["./src/index.ts"]
  }
}
```

### `pi-memory`

Ebenfalls sinnvoll als einzelne Extension mit zusätzlicher Doku/Test-Struktur.

```text
pi-memory/
├── package.json
├── src/index.ts
├── test/
├── docs/
└── AGENTS.md
```

`AGENTS.md` ist eine repo-interne Agent-Datei, aber keine Pi-Ressource, solange sie nicht über `pi.skills`, `pi.prompts` usw. eingebunden wird. Dauerhafte Projekt-/Handoff-Notizen gehören in Pi in die pi-memory Tools statt in ein committetes `MEMORY.md`.

### `pi-subagents`

Zwei valide Optionen:

**Option A — eine Extension:**

```text
pi-subagents/
├── package.json
└── src/index.ts
```

```json
{
  "pi": {
    "extensions": ["./src/index.ts"]
  }
}
```

Das ist die beste Struktur, wenn `subagents` als eine Extension geladen wird und intern mehrere Rollen/Tools verwaltet.

**Option B — Pi Package mit mehreren Extensions/Skills:**

```text
pi-subagents/
├── package.json
├── extensions/
│   ├── subagent.ts
│   ├── planner.ts
│   └── reviewer.ts
└── skills/
    └── subagent/
        └── SKILL.md
```

```json
{
  "pi": {
    "extensions": ["extensions"],
    "skills": ["skills"]
  }
}
```

Das ist sinnvoll, wenn wirklich mehrere getrennte Pi-Ressourcen gebündelt werden sollen.

## 8. Prüf-Commands

```bash
cat package.json | jq '.pi'
find . -maxdepth 3 -type f | sort
```

Für konkrete Loader-Prüfung:

```bash
cat ~/.pi/agent/settings.json | jq '.extensions, .packages'
```

Für Package-Struktur:

```bash
find extensions skills prompts themes -maxdepth 3 -type f 2>/dev/null | sort
```

## 9. Praktische Regeln

1. Pro Repo zuerst entscheiden: **einzelne Extension** oder **Pi Package mit mehreren Ressourcen**.
2. Einzelne Extension: `src/index.ts` bevorzugen.
3. Mehrere Ressourcen: Standardordner `extensions/`, `skills/`, `prompts/`, `themes/` verwenden.
4. Bei nicht-konventionellen Pfaden immer `package.json → pi` explizit setzen.
5. Runtime-Abhängigkeiten in `dependencies` eintragen.
6. Secrets nicht in `package.json`, `README.md`, `AGENTS.md` oder committed `.env` speichern.
7. README kurz halten: Zweck, Installation, benötigte Settings, Commands/Tools, Sicherheitsrisiken.
8. Bei Subagents: Reviewer muss Task + Scout-Brief + Diff sehen; sonst prüft er nur Worker-Behauptungen statt Intention gegen Umsetzung.

## 10. Beleggrundlage

Geprüfte Quellen:

- Pi Docs — Extensions: `https://pi.dev/docs/latest/extensions`
- Pi Docs — Packages: `https://pi.dev/docs/latest/packages`
- Pi Docs — Settings: `https://pi.dev/docs/latest/settings`
- Pi Docs — Usage / Design Principles: `https://pi.dev/docs/latest/usage`
- Pi examples — Extension examples: `https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/examples/extensions/README.md`
- Pi reference package: `https://github.com/badlogic/pi-package-test`

Hinweis: Die Bezeichnung „Multi-Extension-Paket“ ist keine offizielle Pi-Terminologie. Sie beschreibt nur ein Pi Package, das mehrere Extensions enthält.
