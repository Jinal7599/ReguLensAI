import { useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowRight, Bell, Check, ChevronDown,
  ChevronRight, CircleAlert, Clock3, FileCheck2, FileSearch, FileText,
  FileUp, Filter, Globe2, LayoutDashboard, RefreshCw, Search, Settings,
  ShieldCheck, Sparkles, type LucideIcon,
} from "lucide-react";
import { api } from "./api";
import type { ChangeItem, DocumentAnalysis, Overview, Publication, Source } from "./types";
import DocumentIntake from "./DocumentIntake";

type Page = "Overview" | "Document Intake" | "Regulatory Feed" | "Change Analysis" | "Settings";
const navItems: { label: Page; icon: LucideIcon }[] = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Document Intake", icon: FileUp },
  { label: "Regulatory Feed", icon: FileSearch },
  { label: "Change Analysis", icon: Activity },
  { label: "Settings", icon: Settings },
];
const statusTone: Record<string, string> = {
  "Awaiting review": "amber", Processed: "green", New: "blue",
  "Relationship unresolved": "rose", Configured: "green",
  "Needs configuration": "amber",
};

function StatusPill({ value }: { value: string }) {
  return <span className={"pill " + (statusTone[value] ?? "neutral")}><i />{value}</span>;
}

function MetricCard({ label, value, note, icon: Icon, tone = "blue" }: {
  label: string; value: string | number; note: string; icon: LucideIcon; tone?: string;
}) {
  return <article className="metric-card">
    <div className="metric-top"><span>{label}</span><span className={"metric-icon " + tone}><Icon size={18} /></span></div>
    <div className="metric-value">{value}</div><div className="metric-note">{note}</div>
  </article>;
}

function PageHeader({ title, description, onRefresh, refreshing }: {
  title: string; description: string; onRefresh: () => void; refreshing: boolean;
}) {
  return <div className="page-heading">
    <div><div className="eyebrow">REGULATORY INTELLIGENCE</div><h1>{title}</h1><p>{description}</p></div>
    <button className="button secondary" onClick={onRefresh} disabled={refreshing}>
      <RefreshCw size={15} className={refreshing ? "spin" : ""} /> Refresh data
    </button>
  </div>;
}

export default function App() {
  const [page, setPage] = useState<Page>("Overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [changes, setChanges] = useState<ChangeItem[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("All regions");
  const [status, setStatus] = useState("All statuses");
  const [selectedChange, setSelectedChange] = useState("CHG-001");
  const [completed, setCompleted] = useState<string[]>([]);
  const [latestAnalysis, setLatestAnalysis] = useState<DocumentAnalysis | null>(null);

  async function loadData(isRefresh = false) {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const results = await Promise.all([
        api.overview(), api.publications(), api.changes(), api.sources(),
      ]);
      setOverview(results[0]);
      setPublications(results[1].items);
      setChanges(results[2].items);
      setSources(results[3].items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to connect to the API.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { void loadData(); }, []);

  const filteredPublications = useMemo(() => publications.filter((item) => {
    const searchable = [item.id, item.title, item.authority, item.country, item.area].join(" ").toLowerCase();
    return (!query || searchable.includes(query.toLowerCase()))
      && (country === "All regions" || item.country === country)
      && (status === "All statuses" || item.status === status);
  }), [publications, query, country, status]);

  const activeChange = changes.find((item) => item.id === selectedChange) ?? changes[0];
  const descriptions: Record<Page, string> = {
    Overview: "A clear view of regulatory developments and review priorities across your regions.",
    "Document Intake": "Upload a regulatory publication and extract obligations with traceable source evidence.",
    "Regulatory Feed": "Discover, search and review regulatory publications from configured authorities.",
    "Change Analysis": "Understand what changed, why it matters and which actions may be required.",
    Settings: "Manage regulatory source coverage and workspace configuration.",
  };

  function handleDocumentAnalyzed(result: DocumentAnalysis, fromRepository = false) {
    setLatestAnalysis(result);
    if (fromRepository || result.persistence?.duplicate) return;
    setPublications((current) => [result.publication, ...current.filter((item) => item.id !== result.publication.id)]);
    setOverview((current) => {
      if (!current) return current;
      const existing = current.coverage.find((item) => item.country === result.publication.country);
      const coverage = existing
        ? current.coverage.map((item) => item.country === result.publication.country
          ? { ...item, count: item.count + 1 } : item)
        : [...current.coverage, { country: result.publication.country, count: 1 }];
      return {
        ...current,
        total_publications: current.total_publications + 1,
        new_or_unreviewed: current.new_or_unreviewed + 1,
        awaiting_review: current.awaiting_review + 1,
        regions_represented: coverage.length,
        coverage,
        recent_publications: [result.publication, ...current.recent_publications.filter((item) => item.id !== result.publication.id)].slice(0, 5),
      };
    });
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={21} /></div>
        <div><strong>ReguLens<span>AI</span></strong><small>REGULATORY INTELLIGENCE</small></div>
      </div>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="nav-list" aria-label="Main navigation">
        {navItems.map(({ label, icon: Icon }) => <button key={label}
          className={"nav-item " + (page === label ? "active" : "")} onClick={() => setPage(label)}>
          <Icon size={18} /><span>{label}</span>{page === label && <ChevronRight size={15} className="nav-chevron" />}
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="coverage-card">
          <div className="coverage-card-title"><Globe2 size={15} /> Regional coverage</div>
          <strong>{sources.length || 4} source groups</strong>
          <div className="coverage-dots"><i /><i /><i /><i /></div>
          <small>India · UAE · KSA · Africa</small>
        </div>
        <div className="user-row"><div className="avatar">RL</div>
          <div><strong>Compliance workspace</strong><small>Demo environment</small></div><ChevronDown size={15} />
        </div>
      </div>
    </aside>

    <main className="main-area">
      <header className="topbar">
        <div className="breadcrumb">Workspace <ChevronRight size={13} /> <strong>{page}</strong></div>
        <div className="topbar-actions"><span className="environment"><i /> DEMO + PERSISTED UPLOADS</span>
          <button className="icon-button" aria-label="Notifications"><Bell size={18} /></button>
        </div>
      </header>
      <div className="content">
        {error && <div className="error-banner"><CircleAlert size={17} /><div>
          <strong>Could not load live workspace data</strong>
          <span>{error}. Start the FastAPI server and check the API URL.</span>
        </div><button onClick={() => void loadData(true)}><RefreshCw size={15} /> Retry</button></div>}

        {loading ? <div className="loading-panel"><div className="loader" />
          <span>Connecting to regulatory intelligence services…</span></div> : <>
          <PageHeader title={page} description={descriptions[page]}
            onRefresh={() => void loadData(true)} refreshing={refreshing} />

          {page === "Overview" && overview && <>
            <section className="metric-grid">
              <MetricCard label="Total publications" value={overview.total_publications} note="In the searchable repository" icon={FileText} />
              <MetricCard label="New or unreviewed" value={overview.new_or_unreviewed} note="Require attention or triage" icon={Activity} tone="amber" />
              <MetricCard label="Awaiting review" value={overview.awaiting_review} note="Pending human assessment" icon={Clock3} tone="purple" />
              <MetricCard label="Regions represented" value={overview.regions_represented} note="Across the demo source set" icon={Globe2} tone="green" />
            </section>
            <section className="dashboard-grid">
              <article className="panel publications-panel">
                <div className="panel-heading"><div><h2>Recent developments</h2><p>Latest items in your regulatory feed</p></div>
                  <button className="text-button" onClick={() => setPage("Regulatory Feed")}>View all <ArrowRight size={14} /></button>
                </div>
                <div className="table-wrap"><table><thead><tr><th>PUBLICATION</th><th>REGION</th><th>PUBLISHED</th><th>STATUS</th></tr></thead>
                  <tbody>{overview.recent_publications.map((item) => <tr key={item.id}>
                    <td><strong>{item.title}</strong><small>{item.authority}</small></td><td>{item.country}</td>
                    <td>{item.published}</td><td><StatusPill value={item.status} /></td>
                  </tr>)}</tbody></table></div>
              </article>
              <article className="panel coverage-panel">
                <div className="panel-heading"><div><h2>Regional coverage</h2><p>Publications by jurisdiction</p></div><Globe2 size={18} className="muted-icon" /></div>
                <div className="coverage-list">{overview.coverage.map((item) => {
                  const max = Math.max(...overview.coverage.map((x) => x.count), 1);
                  return <div className="coverage-item" key={item.country}>
                    <div><span>{item.country}</span><strong>{item.count}</strong></div>
                    <div className="bar-track"><i style={{ width: ((item.count / max) * 100) + "%" }} /></div>
                  </div>;
                })}</div>
                <div className="coverage-footnote"><span className="dot-blue" /> Synthetic publications in demo dataset</div>
              </article>
            </section>
            <div className="notice"><Sparkles size={17} /><span><strong>Built for review, not blind automation.</strong>
              Regulatory interpretations and suggested actions should be verified by qualified compliance reviewers.</span></div>
          </>}

          {page === "Document Intake" && <DocumentIntake analysis={latestAnalysis} onAnalyzed={handleDocumentAnalyzed} />}

          {page === "Regulatory Feed" && <section className="panel feed-panel">
            <div className="filter-row">
              <label className="search-box"><Search size={17} /><input value={query}
                onChange={(event) => setQuery(event.target.value)} placeholder="Search title, authority, reference…" /></label>
              <label className="select-wrap"><Filter size={15} /><select value={country} onChange={(event) => setCountry(event.target.value)}>
                <option>All regions</option>{[...new Set(publications.map((item) => item.country))].map((item) => <option key={item}>{item}</option>)}
              </select></label>
              <label className="select-wrap"><select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option>All statuses</option>{[...new Set(publications.map((item) => item.status))].map((item) => <option key={item}>{item}</option>)}
              </select></label>
            </div>
            <div className="result-count">{filteredPublications.length} publications found</div>
            <div className="table-wrap"><table><thead><tr><th>PUBLICATION</th><th>REFERENCE</th><th>REGION</th><th>BUSINESS AREA</th><th>EFFECTIVE DATE</th><th>STATUS</th></tr></thead>
              <tbody>{filteredPublications.map((item) => <tr key={item.id}>
                <td><strong>{item.title}</strong><small>{item.authority}</small></td><td>{item.id}</td><td>{item.country}</td>
                <td>{item.area}</td><td>{item.effective}</td><td><StatusPill value={item.status} /></td>
              </tr>)}</tbody></table></div>
            {filteredPublications.length === 0 && <div className="empty-state"><FileSearch size={25} />
              <strong>No publications match your filters</strong><span>Try changing the search term or filters.</span></div>}
          </section>}

          {page === "Change Analysis" && activeChange && <div className="analysis-layout">
            <section className="panel change-list"><div className="panel-heading"><div><h2>Detected changes</h2><p>{changes.length} items to review</p></div></div>
              {changes.map((item) => <button key={item.id} className={"change-option " + (selectedChange === item.id ? "selected" : "")}
                onClick={() => setSelectedChange(item.id)}><span className={"priority-dot " + item.priority.toLowerCase()} />
                <span><strong>{item.publication}</strong><small>{item.country} · {item.classification}</small></span><ChevronRight size={16} /></button>)}
            </section>
            <section className="panel analysis-detail">
              <div className="panel-heading"><div><div className="eyebrow">CHANGE ASSESSMENT · {activeChange.id}</div>
                <h2>{activeChange.publication}</h2><p>{activeChange.country} · {activeChange.classification}</p></div>
                <StatusPill value={activeChange.priority} /></div>
              <div className="clause-grid">
                <article className="clause-card previous"><span>PREVIOUS POSITION</span><p>{activeChange.previous}</p></article>
                <article className="clause-card updated"><span>UPDATED POSITION</span><p>{activeChange.updated}</p></article>
              </div>
              <div className="detail-section"><h3><Sparkles size={16} /> Potential business impact</h3><p>{activeChange.impact}</p></div>
              <div className="detail-section"><h3><FileCheck2 size={16} /> Suggested review actions</h3><div className="action-list">
                {activeChange.actions.map((action) => {
                  const key = activeChange.id + ":" + action;
                  const checked = completed.includes(key);
                  return <button className={"action-item " + (checked ? "done" : "")} key={action}
                    onClick={() => setCompleted((current) => checked ? current.filter((value) => value !== key) : [...current, key])}>
                    <span className="check-box">{checked && <Check size={13} />}</span>{action}</button>;
                })}
              </div></div>
              <div className="source-note"><ShieldCheck size={15} /><span>Evidence: {activeChange.source}</span></div>
            </section>
          </div>}

          {page === "Settings" && <section className="panel settings-panel">
            <div className="panel-heading"><div><h2>Regulatory source coverage</h2><p>Configure the authorities monitored by your workspace.</p></div>
              <span className="pill neutral">4 regions</span></div>
            {sources.map((source) => <div className="source-row" key={source.country}>
              <div className="source-icon"><Globe2 size={18} /></div>
              <div className="source-info"><strong>{source.authority}</strong><small>{source.country} · {source.region}</small></div>
              <StatusPill value={source.status} /><button className="icon-button" aria-label={"Configure " + source.country} disabled><Settings size={16} /></button>
            </div>)}
            <div className="settings-note"><CircleAlert size={16} /><span>Connector URLs and monitoring schedules will be configured in the source-monitoring iteration.</span></div>
            <div className="settings-footer"><div><strong>Workspace preferences</strong><small>Monitoring schedule · Notifications · API configuration</small></div>
              <button className="button secondary" disabled>Coming in next iteration</button></div>
          </section>}
        </>}
        <footer className="footer"><span>© 2026 ReguLens AI</span><span><i /> Demo workspace · Synthetic samples + session uploads</span></footer>
      </div>
    </main>
  </div>;
}
