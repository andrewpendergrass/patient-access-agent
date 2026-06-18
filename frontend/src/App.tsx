import { useState, useRef } from "react";
import {
  Activity,
  AlertCircle,
  ChevronRight,
  ClipboardList,
  SendHorizonal,
  Stethoscope,
} from "lucide-react";
import { AgentStep, AgentResult } from "./types";
import { streamRequest } from "./api";
import { AgentTrace } from "./components/AgentTrace";
import { ResponsePanel } from "./components/ResponsePanel";
import { AuditLog } from "./components/AuditLog";

const EXAMPLE_REQUESTS = [
  {
    label: "Emergency escalation",
    text: "I need to reschedule my cardiology appointment and I've been having chest tightness for the past hour.",
  },
  {
    label: "Provider lookup",
    text: "I need to find a Spanish-speaking pediatrician near Lee's Summit who takes Aetna.",
  },
  {
    label: "Appointment scheduling",
    text: "I'd like to reschedule my follow-up appointment. I originally had it for next Tuesday but need to move it.",
  },
  {
    label: "Insurance question",
    text: "Does your clinic accept Blue Cross Blue Shield? What's my expected copay for a specialist visit?",
  },
  {
    label: "Prescription refill",
    text: "I need to request a refill for my blood pressure medication. How do I do that and how long will it take?",
  },
];

type Tab = "agent" | "audit";


export default function App() {
  const [tab, setTab] = useState<Tab>("agent");
  const [request, setRequest] = useState("");
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const cancelRef = useRef<(() => void) | null>(null);

  const handleSubmit = () => {
    if (!request.trim() || isRunning) return;

    setSteps([]);
    setResult(null);
    setError("");
    setIsRunning(true);

    cancelRef.current = streamRequest(
      request,
      (step) => setSteps((prev) => [...prev, step]),
      (res) => {
        setResult(res);
        setIsRunning(false);
      },
      (msg) => {
        setError(msg);
        setIsRunning(false);
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
          <Stethoscope className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-slate-900 leading-tight">Patient Access Triage Agent</h1>
          <p className="text-xs text-slate-500">AI-powered healthcare request routing & workflow automation</p>
        </div>
        <div className="ml-auto flex gap-1">
          <button
            onClick={() => setTab("agent")}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              tab === "agent" ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Agent
          </button>
          <button
            onClick={() => setTab("audit")}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              tab === "audit" ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <ClipboardList className="w-3.5 h-3.5" />
            Audit Log
          </button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {tab === "audit" ? (
          <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
            <AuditLog />
          </div>
        ) : (
          <div className="flex-1 flex gap-0 overflow-hidden">
            {/* Left — input */}
            <div className="w-[420px] flex-shrink-0 border-r border-slate-200 bg-white flex flex-col">
              <div className="p-4 flex-1 flex flex-col gap-4 overflow-y-auto">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    Patient Request
                  </label>
                  <textarea
                    value={request}
                    onChange={(e) => setRequest(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter or paste patient request here…"
                    rows={5}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  />
                  <p className="text-xs text-slate-400 mt-1">⌘↵ or Ctrl+↵ to submit</p>
                </div>

                <button
                  onClick={handleSubmit}
                  disabled={isRunning || !request.trim()}
                  className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-semibold text-sm transition-colors"
                >
                  <SendHorizonal className="w-4 h-4" />
                  {isRunning ? "Processing…" : "Submit Request"}
                </button>

                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    Example Requests
                  </p>
                  <div className="space-y-1.5">
                    {EXAMPLE_REQUESTS.map((ex) => (
                      <button
                        key={ex.label}
                        onClick={() => setRequest(ex.text)}
                        disabled={isRunning}
                        className="w-full text-left px-3 py-2 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-xs text-slate-600 transition-colors flex items-start gap-2 group disabled:opacity-50"
                      >
                        <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-blue-400 flex-shrink-0 mt-0.5" />
                        <span>
                          <span className="font-semibold text-slate-700 block">{ex.label}</span>
                          {ex.text}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right — trace + result */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {(steps.length > 0 || isRunning) && (
                <AgentTrace steps={steps} isRunning={isRunning} />
              )}

              {result && (
                <div>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    Agent Output
                  </h3>
                  <ResponsePanel result={result} />
                </div>
              )}

              {steps.length === 0 && !isRunning && !result && (
                <div className="flex flex-col items-center justify-center h-full text-center text-slate-400 py-16">
                  <Stethoscope className="w-10 h-10 mb-3 opacity-30" />
                  <p className="text-sm font-medium">Select an example or type a patient request</p>
                  <p className="text-xs mt-1">The agent will classify, retrieve context, and draft a response</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
