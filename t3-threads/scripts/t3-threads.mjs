#!/usr/bin/env -S node --disable-warning=ExperimentalWarning
// Read T3 Code threads from the server's SQLite projection, opened read-only. Never writes.
//
//   t3-threads.mjs list [--project <name>] [--limit N] [--json]   newest threads first
//   t3-threads.mjs find <text> [--limit N] [--json]               title or message text contains <text>
//   t3-threads.mjs show <thread> [--last N]                       messages of one thread
//
// <thread> is a thread id, an id prefix of at least 6 characters, or a case-insensitive title
// fragment that matches exactly one thread; an ambiguous fragment lists the candidates.
// Env: T3_DB (default ~/.t3/userdata/state.sqlite).
// The schema is T3's internal projection (checked against 0.0.42); a missing column fails loudly.
// Exit codes: 0 ok, 1 error or no unique match, 2 usage.
import { homedir } from "node:os";
import { DatabaseSync } from "node:sqlite";

const DB = process.env.T3_DB ?? `${homedir()}/.t3/userdata/state.sqlite`;
const USAGE =
  "usage: t3-threads.mjs list [--project <name>] [--limit N] [--json] | find <text> [--limit N] [--json] | show <thread> [--last N]";
const SCHEMA = {
  projection_projects: ["project_id", "title", "workspace_root", "deleted_at"],
  projection_threads: [
    "thread_id", "project_id", "title", "updated_at", "deleted_at", "archived_at", "runtime_mode",
    "model_selection_json", "latest_turn_id", "pending_approval_count", "pending_user_input_count",
  ],
  projection_turns: ["turn_id", "state"],
  projection_thread_messages: ["thread_id", "role", "text", "created_at"],
};

const fail = (code, message) => {
  console.error(message);
  process.exit(code);
};

const [mode, ...rest] = process.argv.slice(2);
const flags = {};
const positional = [];
for (let i = 0; i < rest.length; i++) {
  if (rest[i] === "--json") flags.json = true;
  else if (["--project", "--limit", "--last"].includes(rest[i])) {
    if (rest[i + 1] === undefined) fail(2, USAGE);
    flags[rest[i].slice(2)] = rest[++i];
  } else positional.push(rest[i]);
}
if (!["list", "find", "show"].includes(mode) || (mode !== "list" && !positional.length)) fail(2, USAGE);
const limit = Number(flags.limit ?? 30);
const last = flags.last === undefined ? Infinity : Number(flags.last);
const positiveInt = (n) => Number.isSafeInteger(n) && n > 0;
if (!positiveInt(limit) || !(last === Infinity || positiveInt(last))) fail(2, USAGE);

let db;
try {
  db = new DatabaseSync(DB, { readOnly: true });
} catch (e) {
  fail(1, `cannot open T3 database ${DB}: ${e.message}`);
}
// SQLite's lower() folds ASCII only; titles and messages are often German.
db.function("ulower", { deterministic: true }, (s) => (s == null ? s : String(s).toLowerCase()));
for (const [table, columns] of Object.entries(SCHEMA)) {
  const have = new Set(db.prepare(`pragma table_info(${table})`).all().map((r) => r.name));
  const missing = columns.filter((c) => !have.has(c));
  if (missing.length) fail(1, `T3 schema changed: ${table} lacks ${missing.join(", ")} (${DB})`);
}

// One row per live thread with project, model and a derived status.
const THREADS = `
  select t.thread_id, t.title, t.updated_at, t.runtime_mode, t.archived_at, t.model_selection_json,
         p.title as project, t.pending_approval_count + t.pending_user_input_count as waiting,
         (select state from projection_turns where turn_id = t.latest_turn_id) as turn_state
  from projection_threads t left join projection_projects p using (project_id)
  where t.deleted_at is null`;

function describe(row) {
  let model = "?";
  try {
    const m = JSON.parse(row.model_selection_json);
    model = `${m.instanceId}/${m.model}`;
  } catch {}
  const status = row.waiting
    ? "waiting-for-input"
    : ["pending", "running"].includes(row.turn_state)
      ? "running"
      : row.archived_at
        ? "archived"
        : "idle";
  return {
    id: row.thread_id,
    project: row.project ?? "?",
    title: row.title,
    model,
    status,
    runtimeMode: row.runtime_mode,
    updatedAt: row.updated_at,
    ...(row.hits !== undefined && { messageHits: row.hits, titleMatch: Boolean(row.title_match) }),
  };
}

function print(rows) {
  if (flags.json) return console.log(JSON.stringify(rows, null, 2));
  for (const r of rows) {
    const hits = r.messageHits === undefined ? "" : `  [${r.titleMatch ? "title, " : ""}${r.messageHits} message hits]`;
    console.log(`${r.id}  ${r.updatedAt.slice(0, 16)}  ${r.status.padEnd(17)} ${r.project} · ${r.model}${hits}\n    ${r.title}`);
  }
}

function resolve(ref) {
  const exact = db.prepare(`${THREADS} and t.thread_id = ?`).get(ref);
  if (exact) return exact;
  const byPrefix = ref.length >= 6 ? db.prepare(`${THREADS} and substr(t.thread_id, 1, length(?)) = ?`).all(ref, ref) : [];
  const candidates = byPrefix.length
    ? byPrefix
    : db.prepare(`${THREADS} and instr(ulower(t.title), ulower(?)) > 0 order by t.updated_at desc`).all(ref);
  if (candidates.length === 1) return candidates[0];
  if (!candidates.length) fail(1, `no thread matches "${ref}"`);
  console.error(`"${ref}" matches ${candidates.length} threads; use an id:`);
  flags.json = false;
  print(candidates.map(describe));
  process.exit(1);
}

if (mode === "list") {
  const rows = flags.project
    ? db.prepare(`${THREADS} and ulower(p.title) = ulower(?) order by t.updated_at desc limit ?`).all(flags.project, limit)
    : db.prepare(`${THREADS} order by t.updated_at desc limit ?`).all(limit);
  print(rows.map(describe));
} else if (mode === "find") {
  const text = positional.join(" ");
  const rows = db
    .prepare(
      `select * from (
         select x.*, instr(ulower(x.title), ulower(?)) > 0 as title_match,
                (select count(*) from projection_thread_messages m
                 where m.thread_id = x.thread_id and instr(ulower(m.text), ulower(?)) > 0) as hits
         from (${THREADS}) x)
       where hits > 0 or title_match
       order by updated_at desc limit ?`,
    )
    .all(text, text, limit);
  print(rows.map(describe));
} else {
  const thread = describe(resolve(positional.join(" ")));
  const messages = db
    .prepare(
      `select role, created_at, text from projection_thread_messages
       where thread_id = ? order by created_at, rowid`,
    )
    .all(thread.id);
  const shown = messages.slice(Math.max(0, messages.length - last));
  console.log(
    `# ${thread.title}\n${thread.id} · ${thread.project} · ${thread.model} · ${thread.status} · ${thread.runtimeMode}` +
      `\n${messages.length} messages${shown.length < messages.length ? `, last ${shown.length} shown` : ""}`,
  );
  for (const m of shown) console.log(`\n## ${m.role} ${m.created_at}\n${m.text}`);
}
