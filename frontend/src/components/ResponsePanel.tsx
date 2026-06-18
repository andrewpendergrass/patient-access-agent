import { AlertCircle, CheckCircle, ClipboardList, Database, Tag } from "lucide-react";
import { AgentResult } from "../types";

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  emergency: "bg-red-100 text-red-700 border-red-200",
};

const INTENT_LABELS: Record<string, string> = {
  appointment: "Appointment",
  provider_lookup: "Provider Lookup",
  insurance: "Insurance",
  prescription: "Prescription",
  general: "General Inquiry",
};

export function ResponsePanel({ result }: { result: AgentResult }) {
  const { response, case_summary, case_id, risk_level, intent, retrieved_data } = result;
  const riskClass = RISK_COLORS[risk_level] ?? RISK_COLORS.low;

  return (
    <div className="space-y-4">
      {/* Badges */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${riskClass}`}>
          {risk_level === "emergency" ? <AlertCircle className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
          {risk_level.toUpperCase()} RISK
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border bg-blue-50 text-blue-700 border-blue-200">
          {INTENT_LABELS[intent] ?? intent}
        </span>
        <span className="ml-auto text-xs text-slate-400 font-mono">{case_id}</span>
      </div>

      {/* Draft Response */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Drafted Patient Response
        </h3>
        <p className="text-slate-800 text-sm leading-relaxed whitespace-pre-wrap">{response}</p>
      </div>

      {/* Case Summary */}
      {case_summary && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
          <h3 className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <ClipboardList className="w-3.5 h-3.5" />
            Case Summary
          </h3>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div>
              <dt className="text-xs text-slate-400 font-medium">Chief Request</dt>
              <dd className="text-slate-700 mt-0.5">{case_summary.chief_request}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-400 font-medium">Action Taken</dt>
              <dd className="text-slate-700 mt-0.5">{case_summary.action_taken}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-400 font-medium">Resolution</dt>
              <dd className="text-slate-700 mt-0.5">{case_summary.resolution}</dd>
            </div>
            <div className="flex gap-4">
              <div>
                <dt className="text-xs text-slate-400 font-medium">Follow-up</dt>
                <dd className={`mt-0.5 font-semibold ${case_summary.follow_up_required ? "text-orange-600" : "text-green-600"}`}>
                  {case_summary.follow_up_required ? "Required" : "None"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-slate-400 font-medium">Escalated</dt>
                <dd className={`mt-0.5 font-semibold ${case_summary.escalated ? "text-red-600" : "text-green-600"}`}>
                  {case_summary.escalated ? "Yes" : "No"}
                </dd>
              </div>
            </div>
          </dl>
          {case_summary.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1 border-t border-slate-100">
              {case_summary.tags.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600">
                  <Tag className="w-2.5 h-2.5" />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Retrieved Data */}
      {retrieved_data && Object.keys(retrieved_data).length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
          <h3 className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <Database className="w-3.5 h-3.5" />
            Retrieved Data
          </h3>
          <pre className="text-xs text-slate-700 bg-slate-50 rounded-lg p-3 overflow-auto max-h-64 leading-relaxed">
            {JSON.stringify(retrieved_data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
