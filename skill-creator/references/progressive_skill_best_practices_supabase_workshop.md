# Skill Best Practices aus Supabase-Workshop

**Quelle:** „Skill Issue / Level Up Your Skills: How We Used AI to Make Agents Actually Good at Supabase“ — Pedro Rodrigues, Supabase

## Kurzfazit

Skills sind keine MCP-Alternative, sondern eine **progressive Context- und Workflow-Schicht** für Agenten.

Die beste Architektur ist meist:

```text
Skills / AGENTS.md = Wie soll der Agent arbeiten?
MCP / Tools      = Was kann der Agent ausführen?
CLI / Scripts    = Lokale, reproduzierbare Hilfsaktionen
```

Für token-effiziente Agenten ist das zentrale Prinzip:

> **Nicht alles vorab in den Kontext laden. Nur genug Beschreibung laden, damit der Agent entscheiden kann, wann er mehr braucht.**

---

## 1. Was ein Skill ist

Ein Skill ist typischerweise ein Ordner mit:

```text
skill-name/
  skill.md
  references/
  scripts/
```

### `skill.md`

Pflichtdatei. Enthält Frontmatter und die Hauptanweisungen.

```yaml
---
name: supabase-security
description: Use this skill when working with Supabase security, RLS policies, views, migrations, or exposed schemas.
---
```

Wichtig:

- `name` und `description` werden initial sichtbar gemacht.
- Der eigentliche Inhalt von `skill.md` wird erst geladen, wenn der Agent den Skill nutzt.
- Weitere Markdown-Dateien oder Scripts können referenziert werden.
- Referenzdateien können wiederum andere Referenzdateien verlinken.

Mentalmodell:

```text
skill.md      = Index / Einstiegspunkt / Routing-Hinweis
references/   = Detailkapitel
scripts/      = ausführbare Hilfslogik
```

---

## 2. Progressive Disclosure

Der wichtigste Vorteil von Skills ist **progressive Disclosure**.

Statt alle Regeln, Toolbeschreibungen, Workflows und Projektdetails dauerhaft in den Kontext zu laden, sieht der Agent initial nur eine kompakte Beschreibung.

Erst bei Bedarf lädt er:

- die vollständige Skill-Datei
- referenzierte Detaildateien
- Scripts oder Hilfsdateien

Das reduziert:

- Prompt-Bloat
- Tool-Schema-Bloat
- irrelevanten Kontext
- Kontextkontamination
- Kosten
- Fehlfokus des Agenten

---

## 3. Skill vs. MCP

Skills und MCP lösen unterschiedliche Probleme.

| Thema | Skills | MCP |
|---|---|---|
| Hauptzweck | Kontext, Regeln, Workflows, Guidelines | Tools, APIs, Integrationen |
| Frage | „Wie soll der Agent arbeiten?“ | „Was kann der Agent aufrufen?“ |
| Kontextkosten | Niedrig durch progressive Disclosure | Je nach Client potenziell hoch |
| Ausführung | Optional via lokale Scripts | Tool-Aufruf lokal oder remote |
| Authentifizierung | Bei Scripts lokal zu lösen | Besser im Tool/MCP gekapselt |
| Portabilität | Hoch, da Markdown + Dateien | Abhängig von Server/Client |
| Ideal für | Policies, Checklisten, Projektwissen | Remote APIs, DB-Zugriff, Actions |

### Praktische Regel

```text
MCP für Zugriff und Aktionen.
Skills für Instruktionen, Sicherheitsregeln und Tool-Nutzung.
```

Beispiel:

```text
Supabase MCP:
- Tabellen listen
- SQL ausführen
- Migration anwenden
- Advisor ausführen

Supabase Skill:
- RLS-Regeln beachten
- Views mit security_invoker erzeugen
- Migrationen statt Ad-hoc-Änderungen bevorzugen
- Advisor nach Schemaänderungen laufen lassen
- Security-Checks vor Abschluss durchführen
```

---

## 4. Scripts in Skills vs. MCP Tools

Skills können Scripts enthalten, z. B. Bash, Python, Node.

### Scripts eignen sich für

- lokale Checks
- Projekt-spezifische Linter
- Dateitransformationen
- deterministische Hilfslogik
- kleine Workflows

### MCP eignet sich besser für

- Remote Services
- Produktionssysteme
- APIs mit Authentifizierung
- Datenbanken
- externe SaaS-Integrationen
- standardisierte Tool-Aufrufe

### Trade-off

```text
Skill-Script = leichtgewichtig, lokal, aber umgebungsabhängig.
MCP-Tool     = robuster für Integrationen, aber potenziell mehr Setup und Kontextkosten.
```

---

## 5. Gute Skill-Beschreibungen

Die `description` entscheidet stark darüber, ob ein Skill automatisch geladen wird.

### Gute Beschreibung

```yaml
---
name: supabase-security
description: Use this skill when creating or modifying Supabase database schemas, RLS policies, views, migrations, exposed schemas, or security-sensitive SQL.
---
```

Eigenschaften:

- beginnt aktiv mit `Use this skill when ...`
- nennt konkrete Trigger
- nennt relevante Begriffe, nach denen der Agent matchen kann
- beschreibt Aufgabe und Kontext, nicht nur das Thema

### Schwache Beschreibung

```yaml
---
name: supabase-security
description: Supabase security guidelines.
---
```

Problem:

- zu generisch
- wenig Trigger-Begriffe
- keine klare Handlungsbedingung
- Agent könnte sie übersehen

### Empfehlung

Beschreibungen sollten enthalten:

- Produkt/Projektname
- konkrete Tasks
- relevante Fehlerklassen
- wichtige Technologien
- klare Aktivierungsbedingung

Beispiel für Codebase-Skill:

```yaml
---
name: codebase-investigation
description: Use this skill when investigating bugs, searching a codebase, tracing call flows, modifying existing code, or preparing a patch with tests.
---
```

---

## 6. Skill-Loading ist nicht garantiert

Es gibt typischerweise drei Wege, einen Skill zu laden:

1. **Implizit:** Agent entscheidet anhand der Description.
2. **Prompt-Hinweis:** User schreibt z. B. `use supabase-security`.
3. **Explizit:** Client/Agent-Harness bietet Slash-Command oder direkte Skill-Auswahl.

### Konsequenz

Für kritische Workflows sollte man sich nicht blind auf implizites Laden verlassen.

Best Practice:

```text
Kritische Skills explizit laden oder ihre Aktivierung evaluieren.
```

Beispiele für kritische Skills:

- Security
- Datenbankmigrationen
- Produktionsdeployments
- Zahlungen
- Compliance
- destructive actions
- große Refactorings

---

## 7. Supabase-Beispiel: RLS und Views

Im Workshop sollte der Agent eine View `department_stats` erzeugen.

Naiver Agent-Output:

```sql
create or replace view department_stats as
select ...
```

Problem:

In PostgreSQL können Views standardmäßig mit den Rechten des View-Owners laufen. Dadurch können Row-Level-Security-Policies (RLS) der darunterliegenden Tabellen umgangen werden.

Korrektes Muster ab PostgreSQL 15:

```sql
create or replace view department_stats
with (security_invoker = true) as
select ...
```

Dadurch werden die Berechtigungen des aufrufenden Users verwendet, und RLS greift wie erwartet.

### Skill-Regel daraus

```text
When creating views over RLS-protected tables in Supabase/Postgres 15+, use security_invoker = true unless there is a documented reason not to.
```

### Zusätzliche Supabase-Security-Checks

Ein Supabase/Postgres-Skill sollte prüfen:

- Ist RLS auf exposed/public Tabellen aktiv?
- Gibt es passende Policies für `anon`, `authenticated`, Service-Roles und Rollenmodelle?
- Umgehen Views, Functions oder Policies versehentlich RLS?
- Wird `security_invoker` bei Views verwendet?
- Sind Functions mit `security definer` wirklich nötig?
- Sind exposed Schemas bewusst freigegeben?
- Wird nach Schemaänderungen der Supabase Advisor ausgeführt?
- Gibt es Tests mit verschiedenen User-Rollen?

---

## 8. Skills als agentische Dokumentation

Skills sollten wie Dokumentation behandelt werden, aber mit stärkerem operativen Fokus.

Normale Dokumentation sagt oft:

```text
So funktioniert das System.
```

Ein Skill sollte sagen:

```text
Wenn du diese Aufgabe ausführst, gehe so vor, prüfe diese Risiken und nutze diese Tools in dieser Reihenfolge.
```

Gute Skill-Inhalte:

- kurze Checklisten
- konkrete Entscheidungsregeln
- Tool-Reihenfolgen
- bekannte Fallstricke
- Do/Don’t-Regeln
- Beispiele guter Outputs
- Verweise auf Detaildateien

Schlechte Skill-Inhalte:

- lange Fließtext-Dokumentation
- irrelevante Hintergrundgeschichte
- komplette API-Dumps
- riesige Schemata
- allgemeine Erklärungen ohne Handlungsanweisung
- unklare „be careful“-Hinweise ohne konkrete Checks

---

## 9. Skills testen: Eval-Zyklus

Skill-Entwicklung sollte eval-getrieben sein.

Zyklus:

```text
1. Metriken definieren
2. Skill schreiben
3. Test-Szenarien bauen
4. Agent mit und ohne Skill laufen lassen
5. Ergebnis graden
6. Skill anpassen
7. Regression erneut testen
```

### Was man testen sollte

Nicht nur finalen Text prüfen. Besser:

- Wurde der Skill geladen?
- Wurde das richtige Tool aufgerufen?
- Wurde die richtige Datei gelesen?
- Wurde eine gefährliche Aktion vermieden?
- Wurde eine Migration statt Direktänderung erzeugt?
- Enthält SQL die erwarteten Sicherheitsoptionen?
- Wurden Tests ausgeführt?
- Wurde ein bekannter Edge Case berücksichtigt?

---

## 10. Eval-Struktur

Ein einfacher Eval kann enthalten:

```json
{
  "name": "creates_rls_safe_department_stats_view",
  "prompt": "Create a department_stats view that shows employee count and average salary by department.",
  "expected": {
    "sql_contains": "security_invoker = true",
    "view_name": "department_stats"
  },
  "assertions": [
    "view_exists",
    "view_uses_security_invoker",
    "employee_cannot_see_other_departments",
    "manager_can_only_see_own_department",
    "hr_can_see_all_departments"
  ]
}
```

### Mit/ohne Skill vergleichen

Besonders nützlich:

```text
Condition A: ohne Skill
Condition B: mit Skill
```

Dann vergleichen:

- verbessert sich Tool-Nutzung?
- werden Sicherheitsregeln eingehalten?
- sinkt Fehlerquote?
- entstehen neue False Positives?
- wird der Agent zu eng geführt?

---

## 11. Vorsicht: Evals können selbst falsch sein

Ein wichtiger Live-Demo-Punkt: Der Eval prüfte offenbar die falsche Metadatenstelle und meldete ein falsches Ergebnis.

Lehre:

```text
Ein failing Eval beweist nicht automatisch, dass der Skill schlecht ist.
Ein passing Eval beweist nicht automatisch, dass der Skill korrekt ist.
```

Best Practices:

- Assertions möglichst deterministisch machen.
- Nicht nur LLM-as-judge verwenden.
- Kritische Eigenschaften direkt prüfen.
- Testumgebung jedes Mal resetten.
- Output-Artefakte speichern.
- SQL/Code/Diff direkt inspizieren.
- Eval selbst reviewen wie Produktionscode.

Gute deterministische Checks:

```text
- grep auf erzeugtes SQL
- Datenbank-Introspection
- Rollenbasierte Query-Tests
- Unit-/Integrationstests
- Exit Codes
- Linter
- Typecheck
```

LLM-as-judge nur für weichere Kriterien:

```text
- Antwortqualität
- Vollständigkeit
- Relevanz
- Erklärungsgüte
- Einhaltung eines Formats
```

---

## 12. Große Datenbank-Schemata progressiv laden

Für große Datenbanken sollte das Schema nicht komplett in einen Skill geschrieben werden.

Besser:

```text
MCP-Tool oder CLI für Schema-Introspection
+ Skill für die Nutzungsstrategie
```

Der Skill beschreibt z. B.:

```text
1. Lade zuerst nur relevante Schemas.
2. Suche Tabellen anhand Task-Begriffen.
3. Lade Spalten nur für Kandidatentabellen.
4. Lade Policies/Indexes/Constraints erst bei Bedarf.
5. Führe keine produktiven Queries ohne Limit aus.
6. Frage bei Ambiguität nach oder mache eine Read-only Exploration.
```

### Gute Architektur

```text
MCP/CLI:
- list_schemas
- list_tables(schema)
- describe_table(table)
- list_policies(table)
- explain_query(sql)
- run_readonly_query(sql, limit)

Skill:
- welche Reihenfolge?
- welche Sicherheitsregeln?
- welche Tabellen zuerst?
- wann abbrechen?
- welche Checks vor Schreiboperationen?
```

---

## 13. Produktionsregeln für Skills

Für lokale Experimente sind viele Skills akzeptabel, weil initial nur Beschreibungen geladen werden.

Für Produktion/CI gilt:

- nur benötigte Skills installieren
- Skills versionieren
- Skills mit Codeänderungen aktualisieren
- Skills in Review-Prozess einbeziehen
- Skills regelmäßig evaluieren
- ungenutzte Skills entfernen
- kritische Skills explizit laden
- Output-Regressionen speichern

### Skills als Repository-Artefakt

Skills können direkt im Repository liegen:

```text
.agent/skills/
  supabase-security/
    skill.md
  codebase-investigation/
    skill.md
  release-checklist/
    skill.md
```

Oder kompatibel mit dem jeweiligen Agent-Client verlinkt werden.

Wichtig ist nicht der Speicherort, sondern:

```text
Der Skill muss nah am Projekt liegen und mit dem Projekt gepflegt werden.
```

---

## 14. Best Practices für Skill-Inhalte

### Gute Struktur

```markdown
# Purpose
Wann dieser Skill gilt.

# Required workflow
Konkrete Schrittfolge.

# Safety checks
Was zwingend geprüft werden muss.

# Tool usage
Welche Tools in welcher Reihenfolge.

# Do not
Klare Verbote.

# References
Links auf Detaildateien.
```

### Beispiel: Codebase Investigation Skill

```markdown
# Purpose
Use this skill when investigating bugs, tracing code paths, modifying existing code, or preparing patches.

# Required workflow
1. Start with code search, not broad file reads.
2. Identify the smallest relevant entry points.
3. Read only files needed for the task.
4. Make the smallest safe change.
5. Run targeted tests.
6. Summarize diff, tests, and residual risk.

# Do not
- Do not rewrite unrelated code.
- Do not read huge files blindly.
- Do not claim tests passed unless they were run.
- Do not modify public APIs without checking call sites.
```

---

## 15. Anti-Patterns

### Skill als Datenspeicher missbrauchen

Schlecht:

```text
Ganzes DB-Schema, komplette API-Dokumentation oder riesige Code-Map in skill.md.
```

Besser:

```text
Skill enthält Such-/Ladestrategie und verweist auf Tools oder References.
```

### Zu viele globale Skills in Produktion

Lokal okay, Produktion riskant.

Problem:

- unklare Aktivierung
- unerwartete Interaktionen
- veraltete Regeln
- schwer reproduzierbares Verhalten

### Unklare Skill-Descriptions

Schlecht:

```yaml
description: Helpful project info.
```

Besser:

```yaml
description: Use this skill when modifying authentication, authorization, RLS policies, database views, or security-sensitive migrations in this project.
```

### Nur LLM-as-judge verwenden

Schlecht bei Security, SQL, Codequalität.

Besser:

```text
Deterministische Assertions zuerst.
LLM-as-judge nur ergänzend.
```

---

## 16. Ableitung für Pi / pi-coding-agent

Für Pi passt das sehr gut zur bestehenden Linie:

```text
Minimaler Systemprompt
+ AGENTS.md als normative Projektpolicy
+ Skills für wiederverwendbare Workflows
+ CLI/Bash für lokale Tools
+ MCP nur bei echtem Integrationsvorteil
```

### Empfohlene Rollenverteilung

| Ebene | Inhalt |
|---|---|
| Systemprompt | minimal, stabil, nicht projektüberladen |
| AGENTS.md | Projektregeln, Routing, Done-Kriterien, Sicherheitsgrenzen |
| Skills | spezifische Workflows: Debugging, DB, Release, Tests, Security |
| CLI | `rg`, `ast-grep`, Tests, Linter, Build, Scripts |
| MCP | Remote APIs, Auth, Datenbankzugriff, externe Systeme |

### Gute Pi-Skills

```text
codebase-investigation
- code_search / rg / ast-grep Reihenfolge
- Scout → Worker → Reviewer Ablauf
- Tests und Diff-Pflicht

postgres-supabase-security
- RLS
- security_invoker
- migration workflow
- advisor/checks

release-checklist
- changelog
- tests
- build
- rollback notes

agent-review
- Reviewer sieht Originaltask + Scout-Brief + Diff
- prüft Must-Fixes, Tests, Nebenwirkungen
```

---

## 17. Skill + Subagent-Strategie

Skills passen gut zu Subagents.

Beispiel:

```text
Scout Subagent:
- nutzt codebase-investigation Skill
- sucht relevante Dateien
- komprimiert Befunde

Worker Subagent:
- nutzt spezifischen Implementierungs-Skill
- macht Patch

Reviewer Subagent:
- nutzt review Skill
- sieht Task + Scout-Brief + Diff
- prüft Tests und Risiken
```

Vorteil:

- Skills geben jedem Subagent genau den passenden Workflow.
- Hauptkontext bleibt sauber.
- Reviewer bleibt unabhängiger.
- Weniger permanenter Tool-/Regel-Bloat.

---

## 18. Minimal-MCP-Variante

Für codebase search / bug fixing reicht meist:

```text
Kein MCP nötig:
- rg
- ast-grep
- git diff
- test runner
- typecheck
- project scripts
```

MCP lohnt sich nur, wenn mindestens eines gilt:

- Auth/Remote-System nötig
- API-Zugriff sonst umständlich
- Tool liefert strukturierte Ergebnisse besser als CLI
- Tool reduziert Kontext statt ihn zu erhöhen
- Tool ist in CI/Agent-Harness reproduzierbar

Beispiele, wo MCP sinnvoll sein kann:

```text
- Supabase remote project inspection
- GitHub Issues/PRs
- Jira/Linear
- Cloud deployment status
- production logs/metrics
```

Nicht sinnvoll als MCP:

```text
- bloßer Wrapper um rg
- riesige statische Tool-Schemas
- lokale Checks, die CLI sauber erledigt
- Knowledge-Graph-Spielerei ohne klaren Call-Chain-Mehrwert
```

---

## 19. Konkrete Skill-Templates

### Template: Sicherheitskritischer DB-Skill

```markdown
---
name: postgres-security
description: Use this skill when creating or modifying Postgres schemas, views, RLS policies, functions, migrations, or security-sensitive SQL.
---

# Purpose
Ensure database changes preserve authorization boundaries and do not bypass RLS.

# Required workflow
1. Inspect relevant tables, policies, views, and functions.
2. Identify whether affected tables are exposed to application users.
3. Prefer migrations over direct ad-hoc schema changes.
4. For views over RLS-protected tables on Postgres 15+, use `security_invoker = true` unless explicitly justified.
5. Check `security definer` functions for privilege escalation.
6. Test behavior with representative roles.
7. Run advisor/security checks if available.

# Do not
- Do not assume application-level filtering is sufficient.
- Do not create views over sensitive tables without checking RLS behavior.
- Do not claim security is correct without role-based verification.
```

### Template: Codebase Investigation Skill

```markdown
---
name: codebase-investigation
description: Use this skill when investigating bugs, searching unfamiliar code, tracing call flows, modifying existing code, or preparing a patch with tests.
---

# Required workflow
1. Start with targeted search: `rg`, `code_search`, or `ast-grep`.
2. Identify entry points and call sites before editing.
3. Read only relevant files.
4. Make the smallest safe change.
5. Run targeted tests or explain why unavailable.
6. Report changed files, test results, and residual risk.

# Do not
- Do not rewrite unrelated code.
- Do not read large files blindly.
- Do not skip call-site checks for public APIs.
- Do not say tests passed unless actually run.
```

---

## 20. Finaler Merksatz

```text
Skills sind agentische Runbooks mit progressiver Offenlegung.
MCP ist die Integrationsschicht.
CLI ist die robuste lokale Ausführungsschicht.
AGENTS.md ist die stabile Projektverfassung.
```

Für ein gutes Agent-Setup:

```text
So wenig dauerhaft sichtbarer Kontext wie möglich.
So viel gezielte, ladbare Anleitung wie nötig.
Tools nur dort, wo sie echten Zugriff oder echte Automatisierung liefern.
```

