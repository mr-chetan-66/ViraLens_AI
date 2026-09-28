import React, { useRef, useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Sparkles,
  Check,
  Square,
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('text'); // 'text' | 'image'
  const [claimText, setClaimText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [results, setResults] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [expandedSources, setExpandedSources] = useState({});
  const activeCheckRef = useRef(null);

  const formatSourceDate = (value) => {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const steps = [
    "Reading claim",
    "Extracting factual statements",
    "Searching trusted sources",
    "Checking evidence",
    "Verifying citations",
    "Preparing report"
  ];

  const videoExtensions = ['.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv', '.wmv'];

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Video check
    const isVideo = videoExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (isVideo) {
      setErrorMessage("Video isn't supported — please paste the claim as text or a screenshot.");
      setSelectedFile(null);
      return;
    }

    setErrorMessage('');
    setSelectedFile(file);
  };

  const handleCheck = async () => {
    setErrorMessage('');
    setResults(null);

    if (activeTab === 'text' && !claimText.trim()) {
      setErrorMessage('Please enter a claim to verify.');
      return;
    }
    if (activeTab === 'image' && !selectedFile) {
      setErrorMessage('Please upload a screenshot or photo to verify.');
      return;
    }

    setLoading(true);
    setCurrentStepIndex(0);
    const requestId = crypto.randomUUID();
    const controller = new AbortController();

    const stepInterval = setInterval(() => {
      setCurrentStepIndex(prev => {
        if (prev < steps.length - 1) return prev + 1;
        return prev;
      });
    }, 450);
    const activeCheck = { requestId, controller, stepInterval };
    activeCheckRef.current = activeCheck;

    try {
      let response;
      if (activeTab === 'text') {
        response = await fetch('/api/check-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: claimText,
            request_id: requestId
          }),
          signal: controller.signal
        });
      } else {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('request_id', requestId);

        response = await fetch('/api/check-image', {
          method: 'POST',
          body: formData,
          signal: controller.signal
        });
      }

      const data = await response.json();
      clearInterval(stepInterval);
      setCurrentStepIndex(steps.length - 1);

      if (!response.ok || data.success === false) {
        setErrorMessage(data.error || data.detail || 'Failed to verify claim. Please check your connection and try again.');
      } else {
        setResults(data);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setErrorMessage('Unable to reach backend server. Make sure the FastAPI server is running on port 8000.');
      }
    } finally {
      clearInterval(stepInterval);
      if (activeCheckRef.current === activeCheck) {
        activeCheckRef.current = null;
        setLoading(false);
      }
    }
  };

  const stopCheck = () => {
    const activeCheck = activeCheckRef.current;
    if (!activeCheck) return;

    fetch(`/api/check/cancel/${activeCheck.requestId}`, {
      method: 'POST',
      keepalive: true
    }).catch(() => {});
    clearInterval(activeCheck.stepInterval);
    activeCheck.controller.abort();
    activeCheckRef.current = null;
    setLoading(false);
    setErrorMessage('Check stopped. You can edit the input and try again.');
  };

  const toggleSources = (index) => {
    setExpandedSources(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-icon">
            <Search size={26} color="#10b981" strokeWidth={2} />
          </div>
          <div>
            <h1 className="brand-title">
              ViraLens <span>AI</span>
            </h1>
            <p className="brand-subtitle">
              Straight-answer fact checking for claims, screenshots, and forwarded content.
            </p>
          </div>
        </div>

      </header>

      <div className="studio-grid">
        <div className="glass-panel input-panel">
        
        {/* Input Mode Tabs */}
        <div className="mode-toggle-group">
          <button
            type="button"
            className={`mode-toggle ${activeTab === 'text' ? 'active' : ''}`}
            disabled={loading}
            onClick={() => { setActiveTab('text'); setErrorMessage(''); }}
          >
            <FileText size={18} /> Paste Text
          </button>
          <button
            type="button"
            className={`mode-toggle ${activeTab === 'image' ? 'active' : ''}`}
            disabled={loading}
            onClick={() => { setActiveTab('image'); setErrorMessage(''); }}
          >
            <UploadCloud size={18} /> Upload Photo / Screenshot
          </button>
        </div>

        {/* Tab 1: Text Input */}
        {activeTab === 'text' && (
          <div>
            <textarea
              className="glass-input"
              rows={4}
              placeholder="Paste any claim, viral post, forwarded message, or news sentence here..."
              value={claimText}
              onChange={(e) => setClaimText(e.target.value)}
              disabled={loading}
              style={{ resize: 'vertical' }}
            />
          </div>
        )}

        {/* Tab 2: Image / Screenshot Upload */}
        {activeTab === 'image' && (
          <div 
            style={{
              border: '2px dashed rgba(52, 211, 153, 0.25)',
              borderRadius: '12px',
              padding: '2rem 1.5rem',
              textAlign: 'center',
              background: 'rgba(8, 16, 12, 0.4)',
              cursor: 'pointer'
            }}
            onClick={() => !loading && document.getElementById('file-input').click()}
          >
            <input
              id="file-input"
              type="file"
              accept="image/*,video/*"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              disabled={loading}
            />
            <UploadCloud size={36} color="#10b981" style={{ margin: '0 auto 0.75rem auto' }} />
            {selectedFile ? (
              <div>
                <p style={{ color: '#6ee7b7', fontWeight: 600 }}>{selectedFile.name}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {(selectedFile.size / 1024).toFixed(1)} KB — Click to change photo
                </p>
              </div>
            ) : (
              <div>
                <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
                  Click to upload screenshot, infographic or meme
                </p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                  PNG, JPG, JPEG, WEBP supported (OCR text auto-extracted)
                </p>
              </div>
            )}
          </div>
        )}

        {/* Error notification */}
        {errorMessage && (
          <div style={{
            marginTop: '1rem',
            padding: '0.85rem 1rem',
            borderRadius: '10px',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fda4af',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertTriangle size={18} /> {errorMessage}
          </div>
        )}

        {/* Action Button */}
        <div className="check-action-row" style={{ marginTop: '1.25rem' }}>
          <button
            className="glass-btn"
            style={{ width: '100%', height: '50px' }}
            onClick={handleCheck}
            disabled={loading}
          >
            {loading ? (
              <>
                <Sparkles size={18} className="pulse-glow" /> Checking with Trusted Sources...
              </>
            ) : (
              <>
                <Search size={18} /> CHECK IT
              </>
            )}
          </button>
          {loading && (
            <button type="button" className="stop-btn" onClick={stopCheck} title="Stop current fact check">
              <Square size={14} fill="currentColor" /> Stop
            </button>
          )}
        </div>
      </div>

        <div className="output-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Fact-check report</span>
              <h2>Live output</h2>
            </div>
            <div className="header-actions">
              <div className="output-badge">{loading ? 'Processing' : results ? 'Ready' : 'Idle'}</div>
            </div>
          </div>

          {!results && !loading && (
            <div className="empty-state">
              <div className="empty-state-icon"><ShieldCheck size={30} color="#10b981" /></div>
              <h3>Check a claim</h3>
              <p>Paste a statement or upload a screenshot, then review the verdict, sources, and confidence score here.</p>
            </div>
          )}

          {loading && (
            <div className="loading-panel">
              <div className="loading-shell">
                <div className="loading-mark" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
                <div className="loading-copy">
                  <span className="loading-tag">Processing</span>
                  <h3 key={currentStepIndex} aria-live="polite">{steps[currentStepIndex]}</h3>
                  <p>Validating sources, checking evidence, and preparing a trusted verdict.</p>
                </div>
              </div>

              <div className="progress-track" aria-label={`Current stage: ${steps[currentStepIndex]}`}>
                {steps.map((step, idx) => (
                  <div
                    key={step}
                    className={`progress-pill ${idx < currentStepIndex ? 'done' : ''} ${idx === currentStepIndex ? 'active' : ''}`}
                    aria-label={step}
                    aria-current={idx === currentStepIndex ? 'step' : undefined}
                  >
                    {idx < currentStepIndex ? <Check size={14} /> : <span>{idx + 1}</span>}
                  </div>
                ))}
              </div>
              <div className="loading-sweep" aria-hidden="true"><span /></div>
            </div>
          )}

          {results && (
            <div className="results-panel">
              {results.notice && (
                <div className="glass-panel notice-box">
                  <p>{results.notice}</p>
                </div>
              )}

              {results.authenticity_warning && (
                <div className="glass-panel notice-box warning-box">
                  <div className="notice-label">Screenshot authenticity</div>
                  <p>{results.authenticity_warning}</p>
                </div>
              )}

              {results.ocr_extracted_text && (
                <div className="glass-panel notice-box info-box">
                  <div className="notice-label">OCR extracted text</div>
                  <p>"{results.ocr_extracted_text}"</p>
                </div>
              )}

              {(!results.reports || results.reports.length === 0) && !results.notice && (
                <div className="glass-panel notice-box">
                  <p>No factual claims were found to verify in this input.</p>
                </div>
              )}

              {results.reports && results.reports.map((report, idx) => {
                const isSupported = report.verdict === 'Supported';
                const isContradicted = report.verdict === 'Contradicted';
                const badgeClass = isSupported ? 'badge-supported' : isContradicted ? 'badge-contradicted' : 'badge-unclear';
                const isExpanded = expandedSources[idx];
                const confidence = Number(report.confidence ?? 0);
                const confidenceLevel = confidence >= 80 ? 'high' : confidence >= 50 ? 'moderate' : 'low';

                return (
                  <div key={idx} className="glass-panel report-card">
                    <div className="report-head">
                      <span className="report-label">Claim</span>
                      <blockquote>"{report.claim}"</blockquote>
                      {report.search_engines && report.search_engines.length > 0 && (
                        <p className="source-line">Searched via: {report.search_engines.join(', ')}</p>
                      )}
                    </div>

                    <div className="verdict-grid">
                      <div>
                        <div className="report-label">Verdict</div>
                        <div className="verdict-stack">
                          <span className={badgeClass}>
                            {isSupported && <CheckCircle2 size={16} />}
                            {isContradicted && <XCircle size={16} />}
                            {!isSupported && !isContradicted && <AlertTriangle size={16} />}
                            {report.verdict}
                          </span>
                          {report.verdict_sub_type && (
                            <span className="sub-type">{report.verdict_sub_type}</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="confidence-header">
                          <span>Confidence level</span>
                          <span className={`confidence-level ${confidenceLevel}`}>
                            {confidenceLevel.charAt(0).toUpperCase() + confidenceLevel.slice(1)}
                          </span>
                        </div>
                        <div className={`confidence-meter ${confidenceLevel}`} aria-label={`Confidence ${confidenceLevel}`}>
                          <span />
                          <span />
                          <span />
                        </div>
                      </div>
                    </div>

                    {report.source_breakdown && (
                      <div className="source-breakdown">
                        <div className="report-label">Source credibility</div>
                        <div className="source-breakdown-items">
                          <div className="breakdown-pill"><span className="dot official" /> Official: {report.source_breakdown.confirmed_official || 0}</div>
                          <div className="breakdown-pill"><span className="dot news" /> News: {report.source_breakdown.confirmed_news || 0}</div>
                          <div className="breakdown-pill"><span className="dot rumor" /> Rumor: {report.source_breakdown.rumor_insider || 0}</div>
                          <div className="breakdown-pill"><span className="dot unverified" /> Unverified: {report.source_breakdown.unverified || 0}</div>
                        </div>
                      </div>
                    )}

                    <div className="report-section">
                      <div className="report-label">What we found</div>
                      <ul className="finding-list">
                        {report.what_we_found.map((finding, fIdx) => (
                          <li key={fIdx}>{finding}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="plain-summary">
                      <div className="report-label">In simple terms</div>
                      <p>{report.in_simple_terms}</p>
                    </div>

                    <div className="citations-box">
                      <button type="button" className="citation-toggle" onClick={() => toggleSources(idx)}>
                        <span>🔗 See sources ({report.citations ? report.citations.length : 0} verified links)</span>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>

                      {isExpanded && (
                        <div className="citation-list">
                          {report.citations && report.citations.length > 0 ? (
                            report.citations.map((cit, cIdx) => (
                              <div key={cIdx} className="citation-item">
                                <div className="citation-topline">
                                  <a href={cit.url} target="_blank" rel="noopener noreferrer">
                                    {cit.title} <ExternalLink size={13} />
                                  </a>
                                  <div className="citation-badges">
                                    {cit.published_at && <span className="mini-badge date">{formatSourceDate(cit.published_at)}</span>}
                                    <span className="mini-badge type" style={{ background: cit.news_type === 'Confirmed Official' ? 'rgba(16, 185, 129, 0.15)' : cit.news_type === 'Confirmed News' ? 'rgba(52, 211, 153, 0.1)' : cit.news_type === 'Rumor/Insider' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.06)', color: cit.news_type === 'Confirmed Official' ? '#10b981' : cit.news_type === 'Confirmed News' ? '#34d399' : cit.news_type === 'Rumor/Insider' ? '#f59e0b' : 'var(--text-dim)' }}>
                                      {cit.news_type || 'Source'}
                                    </span>
                                    <span className="mini-badge tier">{cit.tier_name}</span>
                                    {cit.stance && (
                                      <span className="mini-badge stance" style={{ background: cit.stance === 'Supporting' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)', color: cit.stance === 'Supporting' ? '#6ee7b7' : '#fda4af' }}>
                                        {cit.stance}
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <p>{cit.finding}</p>
                              </div>
                            ))
                          ) : (
                            <p className="empty-citations">No specific direct citations available for this claim.</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

            </div>
          )}

        </div>
      </div>

      <footer className="app-footer">
        ViraLens AI — Verified verdicts, source-backed answers, and fast fact checks.
      </footer>
    </div>
  );
}
