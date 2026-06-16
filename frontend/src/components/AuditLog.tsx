import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";
import { fetchCases } from "../api";
import { Case } from "../types";

const RISK_DOT: Record<string, string> = {
  low: "bg-green-500",
  medium: "bg-yellow-500",
  high: "bg-orange-500",
  emergency: "bg-red-500",
};

function CaseRow({ c }: { c: Case }) {
  const [expanded, setExpanded] = useState(false);
  const dot = RISK_DOT[c.risk_level] ?? "bg-slate-400";
  const date = new Date(c.created_at + "Z").toLocaleString();

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-slate-50 text-left transition-colors"
      >
        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dot}`} />
        <span className="font-mono text-xs text-slate-400 flex-shrink-0">{c.id}</span>
        <span className="flex-1 text-sm text-slate-700 truncate">{c.request}</span>
        <span className="text-xs text-slate-400 flex-shrink-0">{date}</span>
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 space-y-3 text-sm">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="text-xs text-slate-400 font-medium block">Intent</span>
              <span className="text-slate-700 capitalize">{c.intent.replace("_", " ")}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 font-medium block">Risk</span>
              <span className={`font-semibold capitalize ${c.risk_level === "emergency" ? "text-red-600" : c.risk_level === "high" ? "text-orange-600" : "text-green-600"}`}>
                {c.risk_level}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 font-medium block">Escalated</span>
              <span className={c.case_summary?.escalated ? "text-red-600 font-semibold" : "text-green-600"}>
                {c.case_summary?.escalated ? "Yes" : "No"}
              </span>
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-medium block mb-1">Response</span>
            <p className="text-slate-600 leading-relaxed whitespace-pre-wrap">{c.response}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-medium block mb-1">Reasoning Steps</span>
            <div className="space-y-1">
              {c.steps.map((step, i) => (
                <div key={i} className="flex gap-2 text-xs">
                  <span className="text-slate-400 font-mono w-5 flex-shrink-0">#{i + 1}</span>
                  <span className="font-medium text-slate-600 w-40 flex-shrink-0">{step.label}</span>
                  <span className="text-slate-500">{step.detail}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function AuditLog() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setCases(await fetchCases());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">
          {cases.length} case{cases.length !== 1 ? "s" : ""} logged
        </h2>
        <button
          onClick={load}
          className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {loading && (
        <div className="text-sm text-slate-500 text-center py-8">Loading audit log…</div>
      )}
      {error && (
        <div className="text-sm text-red-600 text-center py-4">{error}</div>
      )}
      {!loading && !error && cases.length === 0 && (
        <div className="text-sm text-slate-400 text-center py-8">
          No cases yet — submit a patient request to get started.
        </div>
      )}
      {cases.map((c) => (
        <CaseRow key={c.id} c={c} />
      ))}
    </div>
  );
}
