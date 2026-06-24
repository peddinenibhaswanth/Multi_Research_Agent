import {
  Activity,
  AlertCircle,
  BookOpenText,
  Check,
  ClipboardList,
  Copy,
  Download,
  ExternalLink,
  FileJson,
  FileText,
  History,
  Loader2,
  Play,
  RadioTower,
  RotateCcw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Square,
  Trash2,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type Source = {
  title: string;
  url: string;
  key_insight: string;
};

type ResearchReport = {
  title: string;
  topic: string;
  executive_summary: string;
  key_findings: string[];
  detailed_analysis: string;
  future_implications: string;
  sources: Source[];
};

type SavedReport = ResearchReport & {
  id: string;
  createdAt: string;
  durationMs: number;
  requestedSources: number;
};

type HealthState = "checking" | "online" | "offline";
type RunState = "idle" | "loading" | "success" | "error";
type ReportTab = "summary" | "findings" | "analysis" | "future" | "sources";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
const STORAGE_KEY = "research-agent:reports";

const loadingStages = [
  "Searching web results",
  "Scraping selected sources",
  "Indexing research notes",
  "Retrieving supporting evidence",
  "Writing structured report",
];

const reportTabs: Array<{ id: ReportTab; label: string }> = [
  { id: "summary", label: "Summary" },
  { id: "findings", label: "Findings" },
  { id: "analysis", label: "Analysis" },
  { id: "future", label: "Future" },
  { id: "sources", label: "Sources" },
];

function createId() {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatElapsed(ms: number) {
  const totalSeconds = Math.max(0, Math.round(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function normalizeError(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .join(" ");
  }

  return fallback;
}

function toMarkdown(report: SavedReport) {
  const findings = report.key_findings.map((finding) => `- ${finding}`).join("\n");
  const sources = report.sources
    .map((source, index) => `${index + 1}. [${source.title || source.url}](${source.url}) - ${source.key_insight}`)
    .join("\n");

  return `# ${report.title}

Topic: ${report.topic}
Generated: ${new Date(report.createdAt).toLocaleString()}
Sources requested: ${report.requestedSources}

## Executive Summary
${report.executive_summary}

## Key Findings
${findings}

## Detailed Analysis
${report.detailed_analysis}

## Future Implications
${report.future_implications}

## Sources
${sources}
`;
}

function downloadFile(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function App() {
  const [topic, setTopic] = useState("");
  const [maxSources, setMaxSources] = useState(5);
  const [reports, setReports] = useState<SavedReport[]>(() => {
    const rawReports = localStorage.getItem(STORAGE_KEY);
    if (!rawReports) {
      return [];
    }

    try {
      const parsedReports = JSON.parse(rawReports) as SavedReport[];
      return Array.isArray(parsedReports) ? parsedReports : [];
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      return [];
    }
  });
  const [activeReport, setActiveReport] = useState<SavedReport | null>(() => {
    const rawReports = localStorage.getItem(STORAGE_KEY);
    if (!rawReports) {
      return null;
    }

    try {
      const parsedReports = JSON.parse(rawReports) as SavedReport[];
      return Array.isArray(parsedReports) ? (parsedReports[0] ?? null) : null;
    } catch {
      return null;
    }
  });
  const [activeTab, setActiveTab] = useState<ReportTab>("summary");
  const [health, setHealth] = useState<HealthState>("checking");
  const [runState, setRunState] = useState<RunState>("idle");
  const [error, setError] = useState("");
  const [stageIndex, setStageIndex] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [copiedSources, setCopiedSources] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const runStartedAt = useRef(0);

  const trimmedTopic = topic.trim();
  const canSubmit = trimmedTopic.length > 0 && runState !== "loading";

  const reportMetrics = useMemo(() => {
    if (!activeReport) {
      return [
        { label: "Findings", value: "0" },
        { label: "Sources", value: "0" },
        { label: "Run time", value: "0:00" },
      ];
    }

    return [
      { label: "Findings", value: String(activeReport.key_findings.length) },
      { label: "Sources", value: String(activeReport.sources.length) },
      { label: "Run time", value: formatElapsed(activeReport.durationMs) },
    ];
  }, [activeReport]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reports.slice(0, 8)));
  }, [reports]);

  useEffect(() => {
    let mounted = true;

    async function checkHealth() {
      setHealth((current) => (current === "online" ? "online" : "checking"));
      try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        if (mounted) {
          setHealth(response.ok ? "online" : "offline");
        }
      } catch {
        if (mounted) {
          setHealth("offline");
        }
      }
    }

    checkHealth();
    const interval = window.setInterval(checkHealth, 30000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (runState !== "loading") {
      setElapsedMs(0);
      return;
    }

    const timer = window.setInterval(() => {
      const elapsed = Date.now() - runStartedAt.current;
      setElapsedMs(elapsed);
      setStageIndex(Math.min(loadingStages.length - 1, Math.floor(elapsed / 5000)));
    }, 500);

    return () => window.clearInterval(timer);
  }, [runState]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    runStartedAt.current = Date.now();
    setRunState("loading");
    setError("");
    setStageIndex(0);
    setCopiedSources(false);

    try {
      const response = await fetch(`${API_BASE_URL}/api/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: trimmedTopic,
          max_sources: maxSources,
        }),
        signal: controller.signal,
      });

      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(normalizeError(payload, `Request failed with status ${response.status}.`));
      }

      const completedReport: SavedReport = {
        ...(payload as ResearchReport),
        id: createId(),
        createdAt: new Date().toISOString(),
        durationMs: Date.now() - runStartedAt.current,
        requestedSources: maxSources,
      };

      setReports((current) => [completedReport, ...current.filter((report) => report.id !== completedReport.id)].slice(0, 8));
      setActiveReport(completedReport);
      setActiveTab("summary");
      setRunState("success");
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === "AbortError") {
        setError("Research run cancelled.");
      } else {
        setError(requestError instanceof Error ? requestError.message : "Something went wrong while generating the report.");
      }
      setRunState("error");
    } finally {
      abortRef.current = null;
    }
  }

  function cancelRun() {
    abortRef.current?.abort();
  }

  function selectReport(report: SavedReport) {
    setActiveReport(report);
    setActiveTab("summary");
    setError("");
    setRunState((current) => (current === "loading" ? current : "idle"));
  }

  function clearHistory() {
    setReports([]);
    setActiveReport(null);
    setActiveTab("summary");
  }

  function exportJson() {
    if (!activeReport) {
      return;
    }

    downloadFile(`${activeReport.topic.replace(/\W+/g, "-").toLowerCase()}-report.json`, JSON.stringify(activeReport, null, 2), "application/json");
  }

  function exportMarkdown() {
    if (!activeReport) {
      return;
    }

    downloadFile(`${activeReport.topic.replace(/\W+/g, "-").toLowerCase()}-report.md`, toMarkdown(activeReport), "text/markdown");
  }

  async function copySources() {
    if (!activeReport) {
      return;
    }

    const sourceText = activeReport.sources.map((source) => `${source.title || source.url}\n${source.url}`).join("\n\n");
    await navigator.clipboard.writeText(sourceText);
    setCopiedSources(true);
    window.setTimeout(() => setCopiedSources(false), 1800);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <Sparkles size={20} />
          </div>
          <div>
            <p className="eyebrow">Multi Research Agent</p>
            <h1>Research workspace</h1>
          </div>
        </div>

        <div className={`health-pill health-${health}`} title={`Backend: ${health}`}>
          {health === "online" ? <ShieldCheck size={16} /> : health === "checking" ? <Loader2 size={16} className="spin" /> : <AlertCircle size={16} />}
          <span>{health === "online" ? "API online" : health === "checking" ? "Checking API" : "API offline"}</span>
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="control-panel" aria-label="Research controls">
          <form className="research-form" onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="topic">
              <Search size={16} />
              Topic
            </label>
            <textarea
              id="topic"
              className="topic-input"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="AI regulation trends in healthcare"
              rows={5}
              disabled={runState === "loading"}
            />

            <div className="source-control">
              <label className="field-label" htmlFor="max-sources">
                <SlidersHorizontal size={16} />
                Sources
              </label>
              <div className="source-row">
                <input
                  id="max-sources"
                  type="range"
                  min="1"
                  max="10"
                  value={maxSources}
                  onChange={(event) => setMaxSources(Number(event.target.value))}
                  disabled={runState === "loading"}
                />
                <input
                  className="source-number"
                  type="number"
                  min="1"
                  max="10"
                  value={maxSources}
                  onChange={(event) => setMaxSources(Math.min(10, Math.max(1, Number(event.target.value))))}
                  disabled={runState === "loading"}
                  aria-label="Maximum sources"
                />
              </div>
            </div>

            <div className="button-row">
              <button className="primary-button" type="submit" disabled={!canSubmit}>
                {runState === "loading" ? <Loader2 size={18} className="spin" /> : <Play size={18} />}
                <span>{runState === "loading" ? "Running" : "Run research"}</span>
              </button>
              <button className="icon-button" type="button" onClick={cancelRun} disabled={runState !== "loading"} title="Cancel run" aria-label="Cancel run">
                <Square size={17} />
              </button>
            </div>
          </form>

          <div className="run-panel">
            <div className="section-heading">
              <Activity size={17} />
              <h2>Run status</h2>
            </div>
            {runState === "loading" ? (
              <div className="progress-stack">
                <div className="progress-header">
                  <span>{loadingStages[stageIndex]}</span>
                  <strong>{formatElapsed(elapsedMs)}</strong>
                </div>
                <div className="progress-track">
                  <span style={{ width: `${((stageIndex + 1) / loadingStages.length) * 100}%` }} />
                </div>
                <ol className="stage-list">
                  {loadingStages.map((stage, index) => (
                    <li key={stage} className={index <= stageIndex ? "stage-active" : ""}>
                      {index < stageIndex ? <Check size={14} /> : <RadioTower size={14} />}
                      <span>{stage}</span>
                    </li>
                  ))}
                </ol>
              </div>
            ) : (
              <div className="quiet-status">
                <ClipboardList size={18} />
                <span>{runState === "error" ? "Run needs attention" : activeReport ? "Report ready" : "Idle"}</span>
              </div>
            )}
            {error && (
              <div className="error-box" role="alert">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}
          </div>

          <div className="history-panel">
            <div className="section-heading split">
              <span>
                <History size={17} />
                <h2>History</h2>
              </span>
              <button className="ghost-icon-button" type="button" onClick={clearHistory} disabled={!reports.length} title="Clear history" aria-label="Clear history">
                <Trash2 size={16} />
              </button>
            </div>

            <div className="history-list">
              {reports.length ? (
                reports.map((report) => (
                  <button
                    className={`history-item ${activeReport?.id === report.id ? "history-item-active" : ""}`}
                    key={report.id}
                    type="button"
                    onClick={() => selectReport(report)}
                  >
                    <span>{report.topic}</span>
                    <small>{formatDate(report.createdAt)}</small>
                  </button>
                ))
              ) : (
                <div className="empty-history">No saved reports</div>
              )}
            </div>
          </div>
        </aside>

        <section className="report-panel" aria-label="Research report">
          <div className="report-toolbar">
            <div>
              <p className="eyebrow">Report</p>
              <h2>{activeReport?.title ?? "Ready for a research run"}</h2>
            </div>
            <div className="toolbar-actions">
              <button className="icon-button" type="button" onClick={exportMarkdown} disabled={!activeReport} title="Download Markdown" aria-label="Download Markdown">
                <FileText size={17} />
              </button>
              <button className="icon-button" type="button" onClick={exportJson} disabled={!activeReport} title="Download JSON" aria-label="Download JSON">
                <FileJson size={17} />
              </button>
              <button className="icon-button" type="button" onClick={copySources} disabled={!activeReport} title="Copy sources" aria-label="Copy sources">
                {copiedSources ? <Check size={17} /> : <Copy size={17} />}
              </button>
            </div>
          </div>

          <div className="metric-row">
            {reportMetrics.map((metric) => (
              <div className="metric" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </div>

          <div className="tabs" role="tablist" aria-label="Report sections">
            {reportTabs.map((tab) => (
              <button
                key={tab.id}
                className={activeTab === tab.id ? "tab-active" : ""}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                disabled={!activeReport}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <article className="report-content">
            {activeReport ? (
              <ReportSection report={activeReport} tab={activeTab} />
            ) : (
              <div className="empty-report">
                <BookOpenText size={34} />
                <h3>No report selected</h3>
                <p>Run a topic or select a saved report.</p>
              </div>
            )}
          </article>
        </section>
      </section>
    </main>
  );
}

function ReportSection({ report, tab }: { report: SavedReport; tab: ReportTab }) {
  if (tab === "summary") {
    return (
      <section className="text-section">
        <h3>Executive Summary</h3>
        <p>{report.executive_summary}</p>
      </section>
    );
  }

  if (tab === "findings") {
    return (
      <section className="finding-list">
        {report.key_findings.map((finding, index) => (
          <div className="finding-item" key={`${finding}-${index}`}>
            <span>{index + 1}</span>
            <p>{finding}</p>
          </div>
        ))}
      </section>
    );
  }

  if (tab === "analysis") {
    return (
      <section className="text-section">
        <h3>Detailed Analysis</h3>
        <p>{report.detailed_analysis}</p>
      </section>
    );
  }

  if (tab === "future") {
    return (
      <section className="text-section">
        <h3>Future Implications</h3>
        <p>{report.future_implications}</p>
      </section>
    );
  }

  return (
    <section className="source-list">
      {report.sources.map((source, index) => (
        <a className="source-item" href={source.url} target="_blank" rel="noreferrer" key={`${source.url}-${index}`}>
          <div>
            <span>Source {index + 1}</span>
            <h3>{source.title || source.url}</h3>
            <p>{source.key_insight}</p>
          </div>
          <ExternalLink size={18} />
        </a>
      ))}
    </section>
  );
}

export default App;
