/** @jsxImportSource @opentui/solid */
import { For, Show, createSignal, onCleanup } from "solid-js"
import type { TuiPlugin, TuiPluginApi, TuiPluginModule } from "@opencode-ai/plugin/tui"
import type fs from "node:fs"
import type path from "node:path"

const id = "local-todos-sidebar"

type SidebarData = {
  active: string[]
  plan: string[]
  build: string[]
  error?: string
}

function getFs() {
  return require("node:fs") as typeof fs
}

function getPath() {
  return require("node:path") as typeof path
}

function projectRoot(api: TuiPluginApi) {
  return api.state.path.worktree || api.state.path.directory || process.cwd()
}

function opencodeFile(root: string, file: string) {
  const pathApi = getPath()
  const base = pathApi.resolve(root, ".opencode")
  const wanted = pathApi.resolve(base, file)
  if (!(wanted === base || wanted.startsWith(base + pathApi.sep))) {
    throw new Error("invalid .opencode path")
  }
  return wanted
}

function readFileSafe(root: string, file: string) {
  const fsApi = getFs()
  const wanted = opencodeFile(root, file)
  try {
    return fsApi.readFileSync(wanted, "utf8")
  } catch {
    return ""
  }
}

function normalizeLine(line: string) {
  return line.replace(/^\s*[-*]\s*/, "").replace(/^\[.\]\s*/, "").trim()
}

function cleanItems(lines: string[]) {
  return lines
    .map((line) => normalizeLine(line))
    .map((line) => line.replace(/^None\.$/, "").trim())
    .filter((line) => line && line !== "-- leer --")
}

function extractMarkdownSection(content: string, heading: string) {
  const lines = content.split(/\r?\n/)
  const marker = `## ${heading}`
  const start = lines.findIndex((line) => line.trim() === marker)
  if (start < 0) return []
  const out: string[] = []
  for (let i = start + 1; i < lines.length; i += 1) {
    const line = lines[i] || ""
    if (line.startsWith("## ")) break
    if (/^\s*[-*]\s+/.test(line)) out.push(line)
  }
  return cleanItems(out)
}

function parseQueue(content: string) {
  const lines = content.split(/\r?\n/)
  return cleanItems(lines.filter((line) => /^\s*[-*]\s+/.test(line)))
}

function loadSidebarData(root: string): SidebarData {
  try {
    const planState = readFileSafe(root, "plan_state.md")
    const todoPlan = readFileSafe(root, "todo_plan.md")
    const todoBuild = readFileSafe(root, "todo_build.md")
    return {
      active: extractMarkdownSection(planState, "Current Work"),
      plan: parseQueue(todoPlan),
      build: parseQueue(todoBuild),
    }
  } catch (error) {
    return {
      active: [],
      plan: [],
      build: [],
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

function Section(props: { api: TuiPluginApi; title: string; items: string[] }) {
  return (
    <box flexDirection="column" gap={0}>
      <text fg={props.api.theme.current.text}>
        <b>{props.title}</b>
      </text>
      <Show
        when={props.items.length > 0}
        fallback={<text fg={props.api.theme.current.textMuted}>- -- leer --</text>}
      >
        <For each={props.items.slice(0, 8)}>
          {(item) => <text fg={props.api.theme.current.textMuted}>- {item}</text>}
        </For>
      </Show>
    </box>
  )
}

function SidebarContentView(props: { api: TuiPluginApi }) {
  const [data, setData] = createSignal<SidebarData>(loadSidebarData(projectRoot(props.api)))

  const refresh = () => {
    setData(loadSidebarData(projectRoot(props.api)))
  }

  const interval = setInterval(refresh, 1500)
  const unsubscribers = [
    props.api.event.on("session.updated", refresh),
    props.api.event.on("message.updated", refresh),
    props.api.event.on("todo.updated", refresh),
  ]

  onCleanup(() => {
    clearInterval(interval)
    for (const unsubscribe of unsubscribers) unsubscribe()
  })

  return (
    <box flexDirection="column" gap={1}>
      <text fg={props.api.theme.current.text}>
        <b>OpenCode ToDos</b>
      </text>
      <Show when={!data().error} fallback={<text fg={props.api.theme.current.error}>Fehler: {data().error}</text>}>
        <Section api={props.api} title="Aktiv" items={data().active} />
        <Section api={props.api} title="Plan Queue" items={data().plan} />
        <Section api={props.api} title="Build Queue" items={data().build} />
      </Show>
    </box>
  )
}

const tui: TuiPlugin = async (api) => {
  api.slots.register({
    order: 40,
    slots: {
      sidebar_content() {
        return <SidebarContentView api={api} />
      },
    },
  })
}

const plugin: TuiPluginModule & { id: string } = {
  id,
  tui,
}

export default plugin
