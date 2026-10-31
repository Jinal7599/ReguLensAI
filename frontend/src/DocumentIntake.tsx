import { useRef, useState, type DragEvent } from "react";
import {
  AlertCircle, CheckCircle2, CloudUpload, FileText, LoaderCircle,
  ShieldCheck, Sparkles, Upload, XCircle,
} from "lucide-react";
import { api } from "./api";
import type { DocumentAnalysis } from "./types";

interface DocumentIntakeProps {
  analysis: DocumentAnalysis | null;
  onAnalyzed: (result: DocumentAnalysis) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function DocumentIntake({ analysis, onAnalyzed }: DocumentIntakeProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  function selectFile(candidate?: File) {
    setError("");
    if (!candidate) return;
    const extension = candidate.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(extension ?? "")) {
      setFile(null);
      setError("Choose a PDF, DOCX or TXT document.");
      return;
    }
    if (candidate.size > 10 * 1024 * 1024) {
      setFile(null);
      setError("The maximum file size is 10 MB.");
      return;
    }
    setFile(candidate);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files[0]);
  }

  async function handleAnalyze() {
    if (!file || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.analyzeDocument(file);
      onAnalyzed(result);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Document analysis failed.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="intake-layout">
    <section className="panel intake-panel">
      <div className="panel-heading">
        <div><h2>Upload a regulatory publication</h2>
          <p>Start with a circular, guideline, directive or consultation paper.</p></div>
        <span className="intake-step">STEP 01</span>
      </div>
      <div className={"dropzone " + (dragging ? "dragging" : "")}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}>
        <input ref={inputRef} type="file" accept=".pdf,.docx,.txt"
          onChange={(event) => selectFile(event.target.files?.[0])} />
        <div className="dropzone-icon"><CloudUpload size={25} /></div>
        <strong>Drag and drop your document here</strong>
        <span>or browse from your device</span>
        <button className="button secondary" type="button" onClick={() => inputRef.current?.click()}>
          <Upload size={14} /> Browse files
        </button>
        <small>PDF, DOCX or TXT · Maximum 10 MB · Text-readable documents only</small>
      </div>
      {file && <div className="selected-file">
        <FileText size={18} />
        <div><strong>{file.name}</strong><small>{formatBytes(file.size)}</small></div>
        <button className="icon-button" aria-label="Remove selected file" onClick={() => {
          setFile(null); if (inputRef.current) inputRef.current.value = "";
        }}><XCircle size={16} /></button>
      </div>}
      {error && <div className="intake-error"><AlertCircle size={16} /><span>{error}</span></div>}
      <div className="intake-actions">
        <div><ShieldCheck size={15} /><span>Processed by the backend. The original file is not saved.</span></div>
        <button className="button primary" onClick={() => void handleAnalyze()} disabled={!file || busy}>
          {busy ? <><LoaderCircle size={15} className="spin" /> Analyzing…</> : <><Sparkles size={15} /> Analyze document</>}
        </button>
      </div>
    </section>

    <section className="panel intake-process">
      <div className="panel-heading"><div><h2>What happens next?</h2><p>Document-to-evidence workflow</p></div></div>
      <div className="process-step"><span>1</span><div><strong>Text extraction</strong><small>Read PDF pages, Word paragraphs and text lines.</small></div></div>
      <div className="process-step"><span>2</span><div><strong>Metadata identification</strong><small>Identify regulator, jurisdiction, dates and reference number.</small></div></div>
      <div className="process-step"><span>3</span><div><strong>Obligation extraction</strong><small>Find requirements, applicability, deadlines and source evidence.</small></div></div>
      <div className="process-step"><span>4</span><div><strong>Human review</strong><small>Verify the extracted facts before treating them as compliance actions.</small></div></div>
      <div className="process-note">Gemini structured extraction is enabled when <code>GEMINI_API_KEY</code> is set on the API service. Otherwise, the system uses a clearly labelled rule-based fallback.</div>
    </section>

    {analysis && <section className="panel analysis-result">
      <div className="analysis-result-header">
        <div><div className="eyebrow">LATEST UPLOAD · {analysis.publication.id}</div>
          <h2>{analysis.publication.title}</h2><p>{analysis.document.filename} · {formatBytes(analysis.document.size_bytes)} · {analysis.document.source_sections} source sections</p></div>
        <span className={"pill " + (analysis.extraction.method.startsWith("Gemini") ? "green" : "amber")}><i />{analysis.extraction.method}</span>
      </div>
      <div className="result-summary"><Sparkles size={16} /><p>{analysis.extraction.summary}</p></div>
      <div className="metadata-grid">
        <div><small>AUTHORITY</small><strong>{analysis.publication.authority}</strong></div>
        <div><small>JURISDICTION</small><strong>{analysis.publication.country}</strong></div>
        <div><small>PUBLICATION DATE</small><strong>{analysis.publication.published}</strong></div>
        <div><small>EFFECTIVE DATE</small><strong>{analysis.publication.effective}</strong></div>
        <div><small>REFERENCE NUMBER</small><strong>{analysis.extraction.metadata.reference_number}</strong></div>
        <div><small>BUSINESS AREA</small><strong>{analysis.publication.area}</strong></div>
      </div>
      <div className="obligation-heading"><div><h3>Extracted obligations</h3><p>{analysis.extraction.obligation_count} candidate clauses · publication status: awaiting review</p></div>
        <span className="pill neutral">{analysis.document.text_characters.toLocaleString()} characters read</span></div>
      {analysis.extraction.obligations.length > 0 ? <div className="obligation-list">
        {analysis.extraction.obligations.map((item, index) => <article className="obligation-card" key={index}>
          <div className="obligation-top"><span>OBLIGATION {String(index + 1).padStart(2, "0")}</span>
            <span className="pill neutral">{item.classification}</span></div>
          <p className="obligation-text">{item.requirement}</p>
          <div className="obligation-tags">{item.applies_to.map((tag) => <span key={tag}>{tag}</span>)}
            {item.deadline !== "Not identified" && <span>Deadline: {item.deadline}</span>}</div>
          <blockquote className="evidence-quote">“{item.source_excerpt}”</blockquote>
          <div className="evidence-footer"><span><FileText size={13} /> {item.source_reference}</span>
            <span className={item.evidence_verified ? "evidence-verified" : "evidence-unverified"}>
              {item.evidence_verified ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
              {item.evidence_verified ? "Evidence matched" : "Evidence needs verification"}
            </span></div>
        </article>)}
      </div> : <div className="empty-obligations"><FileText size={20} /><strong>No candidate obligations identified</strong>
        <span>Review the document manually. The parser may not identify tables, scanned text or unusual legal phrasing.</span></div>}
      <div className="extraction-note"><AlertCircle size={15} /><span>{analysis.extraction.note}</span></div>
      <div className="retention-note"><ShieldCheck size={15} /><span>Prototype privacy behaviour: the uploaded file is processed in memory and is not stored on the API. This result is held in this browser session only and will be cleared on refresh.</span></div>
    </section>}
  </div>;
}
