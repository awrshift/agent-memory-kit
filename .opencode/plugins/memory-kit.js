// Memory Kit — OpenCode plugin shim.
//
// OpenCode has no session-start hook; injection rides `experimental.chat.system.transform`
// instead, which fires on EVERY model call. That is deliberately stronger than a one-shot
// injection: the memory lives in the system prompt, not the transcript, so compaction cannot
// drop it. Files are re-read on each call — always current, no session tracking needed.
// The PreCompact BLOCK has no OpenCode analog; `experimental.session.compacting` appends a
// save-state instruction to the compaction prompt, and the standing injection covers the rest.

import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const kitRoot = path.resolve(pluginDir, "../../plugins/memory-kit")
const skillsDir = path.join(kitRoot, "skills")
const identityFile = path.join(kitRoot, "context", "identity.md")

// Same three caps as hooks/session-start.py — line count alone lies.
const LINE_CAP = 180
const BYTE_CAP = 32768
const MAXLINE_CAP = 3000
const MEMORY_INJECT_CAP = 40000
const HANDOFF_INJECT_CAP = 6000

const readSafe = (p) => {
  try {
    return fs.readFileSync(p, "utf8")
  } catch {
    return ""
  }
}

const capBreaches = (content) => {
  const lines = content.split("\n")
  const bytes = Buffer.byteLength(content, "utf8")
  const maxLine = lines.reduce((m, l) => Math.max(m, l.length), 0)
  const reasons = []
  if (lines.length > LINE_CAP) reasons.push(`lines = ${lines.length} (cap ${LINE_CAP})`)
  if (bytes > BYTE_CAP) reasons.push(`size = ${(bytes / 1024).toFixed(1)} KB (cap ${BYTE_CAP / 1024} KB)`)
  if (maxLine > MAXLINE_CAP) reasons.push(`longest line = ${maxLine} chars (cap ${MAXLINE_CAP})`)
  return reasons
}

const newestHandoff = (dir) => {
  let files
  try {
    files = fs.readdirSync(dir).filter((f) => f.endsWith(".md") && f !== "HANDOFF-TEMPLATE.md")
  } catch {
    return null
  }
  if (!files.length) return null
  const stamped = files.map((f) => ({ f, m: fs.statSync(path.join(dir, f)).mtimeMs }))
  stamped.sort((a, b) => b.m - a.m)
  return path.join(dir, stamped[0].f)
}

export const MemoryKitPlugin = async ({ directory }) => {
  const memFile = path.join(directory, ".claude", "memory", "MEMORY.md")
  const handoffsDir = path.join(directory, "context", "handoffs")
  const adopted = () => fs.existsSync(memFile) || fs.existsSync(handoffsDir)

  const buildInjection = () => {
    if (!adopted())
      return (
        "## Memory Kit — not set up in this repository\n" +
        "The memory-kit plugin is loaded but this repo has no .claude/memory/MEMORY.md. " +
        "Nothing was created automatically. Run the setup skill to scaffold the memory layers " +
        "(it asks before writing), or ignore this line."
      )
    const parts = []
    const identity = readSafe(identityFile)
    if (identity) parts.push(identity)
    const memory = readSafe(memFile)
    if (memory) {
      const breaches = capBreaches(memory)
      if (breaches.length)
        parts.push(
          `## ⚠ MEMORY DISCIPLINE TRIGGER\nMEMORY.md tripped ${breaches.length} of 3 caps:\n` +
            breaches.map((r) => `  - ${r}`).join("\n") +
            "\nRun the memory-audit skill BEFORE other work.",
        )
      let body = memory
      if (body.length > MEMORY_INJECT_CAP)
        body = body.slice(0, MEMORY_INJECT_CAP) + "\n…(TRUNCATED — over the injection cap; audit and prune)"
      parts.push("## MEMORY.md (hot cache — durable patterns + current state)\n\n" + body)
    }
    const hand = newestHandoff(handoffsDir)
    if (hand) {
      let body = readSafe(hand)
      if (body.length > HANDOFF_INJECT_CAP)
        body = body.slice(0, HANDOFF_INJECT_CAP) + "\n…(truncated — read the full file on demand)"
      parts.push(`## Latest handoff — ${path.basename(hand)}\n\n` + body)
    }
    const index = readSafe(path.join(directory, "knowledge", "index.md"))
    if (index) parts.push("## Knowledge Base Index\n\n" + index)
    return parts.join("\n\n---\n\n")
  }

  return {
    config: async (config) => {
      config.skills = config.skills || {}
      config.skills.paths = config.skills.paths || []
      if (!config.skills.paths.includes(skillsDir)) config.skills.paths.push(skillsDir)
    },

    "experimental.chat.system.transform": async (_input, output) => {
      const injection = buildInjection()
      if (injection) output.system.push(injection)
    },

    "experimental.session.compacting": async (_input, output) => {
      output.context.push(
        "Memory Kit: before summarizing, preserve verbatim any observation from this session " +
          "worth keeping that is NOT yet a dated line in .claude/memory/MEMORY.md — the agent " +
          "must write those lines to MEMORY.md right after compaction. The hot cache itself is " +
          "re-injected via the system prompt and needs no summary space.",
      )
    },
  }
}

export default MemoryKitPlugin
