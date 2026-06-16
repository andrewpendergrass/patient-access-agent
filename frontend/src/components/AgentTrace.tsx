import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Loader2,
  Search,
  Shield,
  Stethoscope,
  Zap,
} from "lucide-react";
import { AgentStep } from "../types";

const NODE_ICONS: Record<string, React.ReactNode> = {
  triage: <Stethoscope className="w-4 h-4" />,
  emergency: <AlertTriangle className="w-4 h-4" />,
  provider_lookup: <Search className="w-4 h-4" />,
  appointment: <Clock className="w-4 h-4" />,
  insurance: <Shield className="w-4 h-4" />,
  synthesize: <Zap className="w-4 h-4" />,
  log: <FileText className="w-4 h-4" />,
};

function StepCard({ step, index }: { step: AgentStep; index: number }) {
  const isEmergency = step.status === "emergency";
  const icon = NODE_ICONS[step.node] ?? <CheckCircle className="w-4 h-4" />;

  return (
    <div
      className={`flex gap-3 p-3 rounded-lg border text-sm transition-all ${
        isEmergency
          ? "border-red-300 bg-red-50"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex flex-col items-center gap-1">
        <div
          className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
            isEmergency ? "bg-red-100 text-red-600" : "bg-blue-100 text-blue-600"
          }`}
        >
          {icon}
        </div>
        {/* connector line — invisible on last item */}
        <div className="w-px flex-1 bg-slate-200 min-h-[8px]" />
      </div>
      <div className="flex-1 min-w-0 pb-1">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">#{index + 1}</span>
          <span className={`font-semibold ${isEmergency ? "text-red-700" : "text-slate-800"}`}>
            {step.label}
          </span>
        </div>
        <p className="text-slate-600 mt-0.5 leading-snug">{step.detail}</p>
      </div>
    </div>
  );
}

export function AgentTrace({
  steps,
  isRunning,
}: {
  steps: AgentStep[];
  isRunning: boolean;
}) {
  if (steps.length === 0 && !isRunning) return null;

  return (
    <div className="space-y-1">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
        Agent Reasoning Trace
      </h3>
      <div className="space-y-1">
        {steps.map((step, i) => (
          <StepCard key={i} step={step} index={i} />
        ))}
        {isRunning && (
          <div className="flex items-center gap-3 p-3 rounded-lg border border-blue-200 bg-blue-50 text-sm">
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
            <span className="text-blue-700 font-medium">Processing…</span>
          </div>
        )}
      </div>
    </div>
  );
}
