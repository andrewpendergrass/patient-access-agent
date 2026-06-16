import { AgentStep, AgentResult, Case } from "./types";

const BASE = "/api";

export async function fetchCases(): Promise<Case[]> {
  const res = await fetch(`${BASE}/cases`);
  if (!res.ok) throw new Error("Failed to fetch cases");
  const data = await res.json();
  return data.cases;
}

export function streamRequest(
  request: string,
  onStep: (step: AgentStep) => void,
  onResult: (result: AgentResult) => void,
  onError: (msg: string) => void
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        onError(`Server error: ${text}`);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const msg = JSON.parse(raw);
              if (msg.type === "step") onStep(msg.data as AgentStep);
              else if (msg.type === "result") onResult(msg.data as AgentResult);
            } catch {
              // ignore parse errors on partial lines
            }
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== "AbortError") {
        onError(e.message);
      }
    }
  })();

  return () => controller.abort();
}
