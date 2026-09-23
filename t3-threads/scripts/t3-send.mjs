#!/usr/bin/env -S node --disable-warning=ExperimentalWarning
// Send a user message into any T3 Code thread (Claude, Codex, ...) and wait for the reply.
//
//   t3-send.mjs send <threadId> <text>                      message into an existing thread
//   t3-send.mjs new <projectId> <instanceId> <model> <text>  new thread, first message
//
// Writes go through the T3 server's WebSocket RPC (orchestration.dispatchCommand);
// the reply is read from the server's SQLite projection, opened read-only.
// Env: T3_TOKEN_FILE (required; bearer token from `t3 auth session issue --token-only`),
//      T3_URL (default http://127.0.0.1:3773; plain http only on loopback), T3_DB,
//      T3_TIMEOUT_S (default 300), T3_ALLOW_FULL_ACCESS=1 to message a full-access thread.
// The busy check before sending is not atomic: a turn the user starts in the same instant can
// still overlap with ours. Use it on threads nobody is typing into.
// Exit codes: 0 ok, 1 error, 2 usage, 3 turn blocked on approval/input, 4 timeout, 5 turn failed or ended without a reply.
import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { DatabaseSync } from "node:sqlite";

const BASE = new URL(process.env.T3_URL ?? "http://127.0.0.1:3773");
const DB = process.env.T3_DB ?? `${homedir()}/.t3/userdata/state.sqlite`;
const TIMEOUT_MS = Number(process.env.T3_TIMEOUT_S ?? 300) * 1000;
const RPC_TIMEOUT_MS = 30_000;
// Turn states: pending, running, interrupted, completed, error (ProjectionTurns.ts).
const ACTIVE_TURN_STATES = ["pending", "running"];
const USAGE =
  "usage: t3-send.mjs send <threadId> <text> | new <projectId> <instanceId> <model> <text>";

const fail = (code, message) => {
  console.error(message);
  process.exit(code);
};

const [mode, ...args] = process.argv.slice(2);
if (!["send", "new"].includes(mode) || args.length < (mode === "new" ? 4 : 2)) fail(2, USAGE);
if (!process.env.T3_TOKEN_FILE) fail(2, "T3_TOKEN_FILE is required");
const loopback = ["127.0.0.1", "localhost", "[::1]"].includes(BASE.hostname);
if (BASE.protocol !== "https:" && !loopback) fail(2, "refusing to send a bearer token over plain http to a non-loopback host");
const token = readFileSync(process.env.T3_TOKEN_FILE, "utf8").trim();

async function openSocket() {
  const res = await fetch(new URL("/api/auth/websocket-ticket", BASE), {
    method: "POST",
    headers: { authorization: `Bearer ${token}` },
    signal: AbortSignal.timeout(RPC_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error(`ticket: HTTP ${res.status} ${await res.text()}`);
  const { ticket } = await res.json();
  const url = new URL("/ws", BASE);
  url.protocol = BASE.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("wsTicket", ticket);
  url.searchParams.set("clientSurface", "harness-comm");
  const ws = new WebSocket(url);
  await new Promise((ok, reject) => {
    ws.onopen = ok;
    ws.onerror = () => reject(new Error("websocket connect failed"));
  });
  return ws;
}

// Effect RPC over JSON: one Request, answered by an Exit with the same id.
// A Defect, a closed socket or silence past RPC_TIMEOUT_MS rejects instead of hanging.
let nextId = 0;
function call(ws, tag, payload) {
  const id = String(++nextId);
  return new Promise((ok, reject) => {
    const timer = setTimeout(() => reject(new Error(`${tag}: no answer in ${RPC_TIMEOUT_MS} ms`)), RPC_TIMEOUT_MS);
    const settle = (fn, value) => {
      clearTimeout(timer);
      fn(value);
    };
    ws.onclose = () => settle(reject, new Error(`${tag}: websocket closed`));
    ws.onmessage = (ev) => {
      for (const msg of [JSON.parse(ev.data)].flat()) {
        if (msg._tag === "Ping") ws.send(JSON.stringify({ _tag: "Pong" }));
        else if (msg._tag === "Defect" || msg._tag === "ClientProtocolError")
          settle(reject, new Error(`${tag}: ${JSON.stringify(msg)}`));
        else if (msg._tag === "Exit" && msg.requestId === id) {
          if (msg.exit._tag === "Success") settle(ok, msg.exit.value);
          else settle(reject, new Error(`${tag}: ${JSON.stringify(msg.exit.cause)}`));
        }
      }
    };
    ws.send(JSON.stringify({ _tag: "Request", id, tag, payload, headers: [] }));
  });
}

const dispatch = (ws, command) =>
  call(ws, "orchestration.dispatchCommand", {
    commandId: randomUUID(),
    createdAt: new Date().toISOString(),
    ...command,
  });

const db = new DatabaseSync(DB, { readOnly: true });
const threadRow = db.prepare(
  `select runtime_mode, interaction_mode, latest_turn_id, pending_approval_count, pending_user_input_count
   from projection_threads where thread_id = ? and deleted_at is null`,
);
// The turn T3 starts for our message records the message id as pending_message_id.
const turnRow = db.prepare("select turn_id, state from projection_turns where pending_message_id = ?");
const repliesOf = db.prepare(
  `select text from projection_thread_messages
   where turn_id = ? and role = 'assistant' order by created_at`,
);

async function waitForReply(threadId, messageId) {
  const deadline = Date.now() + TIMEOUT_MS;
  while (Date.now() < deadline) {
    const turn = turnRow.get(messageId);
    const thread = threadRow.get(threadId);
    const texts = () => (turn ? repliesOf.all(turn.turn_id).map((r) => r.text) : []);
    if (turn && !ACTIVE_TURN_STATES.includes(turn.state)) {
      const replies = texts();
      if (turn.state !== "completed") return { code: 5, status: turn.state, texts: replies };
      return replies.length ? { code: 0, status: "ok", texts: replies } : { code: 5, status: "completed without reply", texts: replies };
    }
    if (turn && (thread?.pending_approval_count || thread?.pending_user_input_count)) {
      return { code: 3, status: "blocked on approval or user input", texts: texts() };
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  const turn = turnRow.get(messageId);
  return { code: 4, status: "timeout", texts: turn ? repliesOf.all(turn.turn_id).map((r) => r.text) : [] };
}

let threadId;
let text;
let turnModes = { runtimeMode: "approval-required", interactionMode: "default" };
const ws = await openSocket();
if (mode === "new") {
  const [projectId, instanceId, model, ...rest] = args;
  text = rest.join(" ");
  threadId = randomUUID();
  await dispatch(ws, {
    type: "thread.create",
    threadId,
    projectId,
    title: text.slice(0, 60),
    modelSelection: { instanceId, model },
    ...turnModes,
    branch: null,
    worktreePath: null,
  });
} else {
  [threadId] = args;
  text = args.slice(1).join(" ");
  const row = threadRow.get(threadId);
  if (!row) fail(1, `unknown thread ${threadId}`);
  if (row.runtime_mode === "full-access" && process.env.T3_ALLOW_FULL_ACCESS !== "1")
    fail(1, `thread ${threadId} runs in full-access mode; set T3_ALLOW_FULL_ACCESS=1 to message it anyway`);
  const latest = row.latest_turn_id && db.prepare("select state from projection_turns where turn_id = ?").get(row.latest_turn_id);
  if (ACTIVE_TURN_STATES.includes(latest?.state)) fail(1, `thread ${threadId} is busy with a running turn`);
  turnModes = { runtimeMode: row.runtime_mode, interactionMode: row.interaction_mode };
}

const messageId = randomUUID();
const started = Date.now();
await dispatch(ws, {
  type: "thread.turn.start",
  threadId,
  message: { messageId, role: "user", text, attachments: [] },
  ...turnModes,
});
ws.onclose = null;
ws.close();
const reply = await waitForReply(threadId, messageId);
console.log(
  JSON.stringify(
    { threadId, status: reply.status, seconds: (Date.now() - started) / 1000, reply: reply.texts.join("\n\n") },
    null,
    2,
  ),
);
// exitCode instead of exit(): a pending write of a long reply to a pipe must not be cut off.
process.exitCode = reply.code;
