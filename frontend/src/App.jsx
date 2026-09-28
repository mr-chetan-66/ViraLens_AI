import React, { useEffect, useState } from 'react';
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
  Settings, 
  Sparkles,
  Info,
  Check,
  Clock
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
  const [showConfig, setShowConfig] = useState(false);
  const [groqKey, setGroqKey] = useState('');
  const [tavilyKey, setTavilyKey] = useState('');
  const [serperKey, setSerperKey] = useState('');
  const [historyItems, setHistoryItems] = useState([]);

  const loadHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (!res.ok) return;
      const data = await res.json();
      setHistoryItems(data.items || []);
    } catch {
      /* history is optional */
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

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

    // Simulate progress stepper ticks
    const stepInterval = setInterval(() => {
      setCurrentStepIndex(prev => {
        if (prev < steps.length - 1) return prev + 1;
        return prev;
      });
    }, 1200);

    try {
      let response;
      if (activeTab === 'text') {
        response = await fetch('/api/check-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: claimText,
            groq_api_key: groqKey || undefined,
            tavily_api_key: tavilyKey || undefined,
            serper_api_key: serperKey || undefined
          })
        });
      } else {
        const formData = new FormData();
        formData.append('file', selectedFile);
        if (groqKey) formData.append('groq_api_key', groqKey);
        if (tavilyKey) formData.append('tavily_api_key', tavilyKey);
        if (serperKey) formData.append('serper_api_key', serperKey);

        response = await fetch('/api/check-image', {
          method: 'POST',
          body: formData
        });
      }

      const data = await response.json();
      clearInterval(stepInterval);
      setCurrentStepIndex(steps.length - 1);

      if (!response.ok || data.success === false) {
        setErrorMessage(data.error || data.detail || 'Failed to verify claim. Please check your network or API keys.');
      } else {
        setResults(data);
        loadHistory();
      }
    } catch (err) {
      clearInterval(stepInterval);
      setErrorMessage('Unable to reach backend server. Make sure the FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (index) => {
    setExpandedSources(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', padding: '2.5rem 1.25rem' }}>
      
      {/* Top Header */}
      <header style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
          <div style={{ 
            background: 'rgba(16, 185, 129, 0.15)', 
            border: '1px solid rgba(52, 211, 153, 0.3)',
            borderRadius: '12px',
            padding: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldCheck size={28} color="#10b981" />
          </div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.025em', color: '#f0fdf4' }}>
            ViraLens <span style={{ color: '#10b981' }}>AI</span>
          </h1>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', maxWidth: '520px', margin: '0 auto' }}>
          Straight-answer fact checking for text and screenshots. No debates. No chat. Real verified sources.
        </p>

        {/* Configuration Toggle */}
        <div style={{ marginTop: '0.85rem' }}>
          <button 
            onClick={() => setShowConfig(!showConfig)}
            style={{ 
              background: 'transparent', 
              border: 'none', 
              color: 'var(--text-dim)', 
              cursor: 'pointer',
              fontSize: '0.85rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <Settings size={14} /> {showConfig ? 'Hide API Keys' : 'Configure API Keys (Optional)'}
          </button>
        </div>

        {/* Configuration Drawer */}
        {showConfig && (
          <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1rem', textAlign: 'left', maxWidth: '540px', margin: '1rem auto 0 auto' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-light)', marginBottom: '0.75rem' }}>
              Optional Custom Keys (free tiers)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <input
                type="password"
                className="glass-input"
                style={{ padding: '0.55rem 0.85rem', fontSize: '0.85rem' }}
                placeholder="Groq API Key (gsk_...)"
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
              />
              <input
                type="password"
                className="glass-input"
                style={{ padding: '0.55rem 0.85rem', fontSize: '0.85rem' }}
                placeholder="Tavily Search API Key (tvly-...)"
                value={tavilyKey}
                onChange={(e) => setTavilyKey(e.target.value)}
              />
              <input
                type="password"
                className="glass-input"
                style={{ padding: '0.55rem 0.85rem', fontSize: '0.85rem' }}
                placeholder="Serper Search API Key (Optional)"
                value={serperKey}
                onChange={(e) => setSerperKey(e.target.value)}
              />
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
              If left blank, uses keys configured in <code>.env</code>. DuckDuckGo search is always on as a free fallback — no extra key.
            </p>
          </div>
        )}
      </header>

      {/* Main Glass Panel Card */}
      <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
        
        {/* Input Mode Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
          <button
            onClick={() => { setActiveTab('text'); setErrorMessage(''); }}
            style={{
              flex: 1,
              padding: '0.75rem',
              borderRadius: '10px',
              border: activeTab === 'text' ? '1px solid var(--accent-light)' : '1px solid transparent',
              background: activeTab === 'text' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.03)',
              color: activeTab === 'text' ? '#f0fdf4' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.95rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s'
            }}
          >
            <FileText size={18} /> Paste Text
          </button>
          <button
            onClick={() => { setActiveTab('image'); setErrorMessage(''); }}
            style={{
              flex: 1,
              padding: '0.75rem',
              borderRadius: '10px',
              border: activeTab === 'image' ? '1px solid var(--accent-light)' : '1px solid transparent',
              background: activeTab === 'image' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.03)',
              color: activeTab === 'image' ? '#f0fdf4' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.95rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s'
            }}
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
            onClick={() => document.getElementById('file-input').click()}
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
        <div style={{ marginTop: '1.25rem' }}>
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
        </div>
      </div>

      {/* Live Stepper View */}
      {loading && (
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--accent-light)', marginBottom: '1rem', fontWeight: 600 }}>
            Fact-Checking Progress
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {steps.map((step, idx) => {
              const isPast = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;
              return (
                <div 
                  key={step} 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.75rem',
                    color: isPast ? '#6ee7b7' : isCurrent ? '#f0fdf4' : 'var(--text-dim)',
                    fontWeight: isCurrent ? 600 : 400,
                    fontSize: '0.95rem'
                  }}
                >
                  <div style={{ width: '20px', display: 'flex', justifyContent: 'center' }}>
                    {isPast ? (
                      <Check size={16} color="#10b981" />
                    ) : isCurrent ? (
                      <div className="pulse-glow" style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399' }} />
                    ) : (
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'rgba(255,255,255,0.2)' }} />
                    )}
                  </div>
                  <span>{step}</span>
                  {isCurrent && <span style={{ fontSize: '0.8rem', color: 'var(--accent-light)' }}>(in progress...)</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Results View */}
      {results && (
        <div>
          {/* OCR preview if present */}
          {results.notice && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
              <p style={{ color: '#fde68a', fontSize: '0.95rem' }}>{results.notice}</p>
            </div>
          )}

          {results.authenticity_warning && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', border: '1px solid rgba(245, 158, 11, 0.35)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                Screenshot authenticity
              </div>
              <p style={{ color: '#fde68a', fontSize: '0.9rem' }}>{results.authenticity_warning}</p>
            </div>
          )}

          {results.ocr_extracted_text && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', background: 'rgba(10, 22, 16, 0.4)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
                OCR Extracted Text from Image
              </div>
              <p style={{ fontStyle: 'italic', fontSize: '0.9rem', color: '#d1fae5' }}>
                "{results.ocr_extracted_text}"
              </p>
            </div>
          )}

          {(!results.reports || results.reports.length === 0) && !results.notice && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                No factual claims were checked. Try pasting a specific statement with names, dates, or numbers.
              </p>
            </div>
          )}

          {/* Factual Claim Reports */}
          {results.reports && results.reports.map((report, idx) => {
            const isSupported = report.verdict === 'Supported';
            const isContradicted = report.verdict === 'Contradicted';
            const badgeClass = isSupported ? 'badge-supported' : isContradicted ? 'badge-contradicted' : 'badge-unclear';
            const barColor = isSupported ? '#10b981' : isContradicted ? '#f43f5e' : '#f59e0b';
            const isExpanded = expandedSources[idx];

            return (
              <div key={idx} className="glass-panel" style={{ padding: '1.75rem', marginBottom: '1.5rem' }}>
                
                {/* Claim Statement */}
                <div style={{ marginBottom: '1.25rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    CLAIM
                  </span>
                  <blockquote style={{ 
                    fontSize: '1.15rem', 
                    fontWeight: 600, 
                    color: '#f0fdf4', 
                    margin: '0.35rem 0 0 0',
                    lineHeight: '1.4' 
                  }}>
                    "{report.claim}"
                  </blockquote>
                  {report.search_engines && report.search_engines.length > 0 && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.45rem' }}>
                      Searched via: {report.search_engines.join(', ')}
                    </p>
                  )}
                </div>

                {/* Verdict & Confidence Row */}
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                  gap: '1.25rem',
                  padding: '1.25rem',
                  background: 'rgba(6, 14, 10, 0.5)',
                  borderRadius: '12px',
                  marginBottom: '1.25rem',
                  border: '1px solid rgba(52, 211, 153, 0.1)'
                }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                      VERDICT
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <span className={badgeClass}>
                        {isSupported && <CheckCircle2 size={16} />}
                        {isContradicted && <XCircle size={16} />}
                        {!isSupported && !isContradicted && <AlertTriangle size={16} />}
                        {report.verdict}
                      </span>
                      {report.verdict_sub_type && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--accent-light)', fontWeight: 500 }}>
                          {report.verdict_sub_type}
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                      <span>CONFIDENCE</span>
                      <span style={{ color: '#f0fdf4', fontSize: '0.9rem' }}>{report.confidence}%</span>
                    </div>
                    <div className="confidence-track">
                      <div 
                        className="confidence-fill" 
                        style={{ width: `${report.confidence}%`, backgroundColor: barColor }} 
                      />
                    </div>
                  </div>
                </div>

                {/* Source Breakdown */}
                {report.source_breakdown && (
                  <div style={{ 
                    padding: '0.85rem 1rem',
                    background: 'rgba(16, 185, 129, 0.05)',
                    borderRadius: '8px',
                    marginBottom: '1.25rem',
                    border: '1px solid rgba(52, 211, 153, 0.1)'
                  }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                      SOURCE CREDIBILITY BREAKDOWN
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
                        <span style={{ fontSize: '0.8rem', color: '#f0fdf4' }}>
                          Official: {report.source_breakdown.confirmed_official || 0}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399' }} />
                        <span style={{ fontSize: '0.8rem', color: '#f0fdf4' }}>
                          News: {report.source_breakdown.confirmed_news || 0}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }} />
                        <span style={{ fontSize: '0.8rem', color: '#f0fdf4' }}>
                          Rumor/Insider: {report.source_breakdown.rumor_insider || 0}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#64748b' }} />
                        <span style={{ fontSize: '0.8rem', color: '#f0fdf4' }}>
                          Unverified: {report.source_breakdown.unverified || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* What We Found */}
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-light)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
                    WHAT WE FOUND
                  </div>
                  <ul style={{ paddingLeft: '1.25rem', color: '#e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.95rem' }}>
                    {report.what_we_found.map((finding, fIdx) => (
                      <li key={fIdx}>{finding}</li>
                    ))}
                  </ul>
                </div>

                {/* In Simple Terms */}
                <div style={{ 
                  background: 'rgba(16, 185, 129, 0.08)', 
                  borderLeft: '4px solid var(--accent-primary)',
                  padding: '1rem',
                  borderRadius: '0 8px 8px 0',
                  marginBottom: '1.25rem'
                }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
                    IN SIMPLE TERMS
                  </div>
                  <p style={{ color: '#f0fdf4', fontSize: '0.95rem', fontWeight: 500 }}>
                    {report.in_simple_terms}
                  </p>
                </div>

                {/* Verified Citations Accordion */}
                <div>
                  <button
                    onClick={() => toggleSources(idx)}
                    style={{
                      width: '100%',
                      padding: '0.65rem 0.85rem',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(52, 211, 153, 0.15)',
                      borderRadius: '8px',
                      color: 'var(--text-muted)',
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.2s'
                    }}
                  >
                    <span>🔗 See Sources ({report.citations ? report.citations.length : 0} verified links)</span>
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>

                  {isExpanded && (
                    <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                      {report.citations && report.citations.length > 0 ? (
                        report.citations.map((cit, cIdx) => (
                          <div 
                            key={cIdx}
                            style={{
                              background: 'rgba(8, 16, 12, 0.6)',
                              border: '1px solid rgba(52, 211, 153, 0.12)',
                              padding: '0.75rem 1rem',
                              borderRadius: '8px',
                              fontSize: '0.85rem'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.35rem' }}>
                              <a 
                                href={cit.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                style={{ color: '#34d399', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                              >
                                {cit.title} <ExternalLink size={13} />
                              </a>
                              <div style={{ display: 'flex', gap: '0.35rem' }}>
                                <span style={{ 
                                  fontSize: '0.7rem', 
                                  padding: '0.15rem 0.45rem', 
                                  borderRadius: '4px', 
                                  background: cit.news_type === 'Confirmed Official' ? 'rgba(16, 185, 129, 0.15)' : 
                                            cit.news_type === 'Confirmed News' ? 'rgba(52, 211, 153, 0.1)' :
                                            cit.news_type === 'Rumor/Insider' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.06)',
                                  color: cit.news_type === 'Confirmed Official' ? '#10b981' : 
                                         cit.news_type === 'Confirmed News' ? '#34d399' :
                                         cit.news_type === 'Rumor/Insider' ? '#f59e0b' : 'var(--text-dim)',
                                  fontWeight: 500
                                }}>
                                  {cit.news_type || 'Source'}
                                </span>
                                <span style={{ 
                                  fontSize: '0.7rem', 
                                  padding: '0.15rem 0.45rem', 
                                  borderRadius: '4px', 
                                  background: 'rgba(255, 255, 255, 0.06)',
                                  color: 'var(--text-dim)' 
                                }}>
                                  {cit.tier_name}
                                </span>
                                {cit.stance && (
                                  <span style={{
                                    fontSize: '0.7rem',
                                    padding: '0.15rem 0.45rem',
                                    borderRadius: '4px',
                                    background: cit.stance === 'Supporting' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                                    color: cit.stance === 'Supporting' ? '#6ee7b7' : '#fda4af'
                                  }}>
                                    {cit.stance}
                                  </span>
                                )}
                              </div>
                            </div>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
                              {cit.finding}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '0.5rem' }}>
                          No specific direct citations available for this claim.
                        </p>
                      )}
                    </div>
                  )}
                </div>

              </div>
            );
          })}

          {/* Skipped Opinions Section */}
          {results.skipped_opinions && results.skipped_opinions.length > 0 && (
            <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1.5rem', background: 'rgba(10, 18, 14, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-dim)', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                <Info size={15} /> Skipped Statements ({results.skipped_opinions.length} Non-Factual / Opinions)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {results.skipped_opinions.map((op, oIdx) => (
                  <div key={oIdx} style={{ 
                    borderLeft: '3px solid #64748b', 
                    padding: '0.4rem 0.75rem', 
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '0 6px 6px 0',
                    fontSize: '0.85rem' 
                  }}>
                    <div style={{ color: '#cbd5e1' }}>"{op.text}"</div>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                      Skipped: {op.category} — {op.reason}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}

      {historyItems.length > 0 && (
        <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            <Clock size={15} /> Recent checks
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
            {historyItems.map((item) => (
              <button
                key={item.id}
                onClick={async () => {
                  try {
                    const res = await fetch(`/api/history/${item.id}`);
                    if (!res.ok) return;
                    const data = await res.json();
                    setResults(data);
                    setErrorMessage('');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  } catch {
                    setErrorMessage('Could not load that previous check.');
                  }
                }}
                style={{
                  textAlign: 'left',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(52, 211, 153, 0.12)',
                  borderRadius: '8px',
                  padding: '0.65rem 0.8rem',
                  color: '#e2e8f0',
                  cursor: 'pointer'
                }}
              >
                <div style={{ fontSize: '0.85rem' }}>{item.input_preview || 'Untitled check'}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                  {item.input_type} · {item.verdict || 'No verdict'} {item.confidence != null ? `· ${item.confidence}%` : ''}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{ textAlign: 'center', marginTop: '3rem', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
        ViraLens AI — Free-tier inference & search. No chatbot debates. Just verified verdicts.
      </footer>

    </div>
  );
}
