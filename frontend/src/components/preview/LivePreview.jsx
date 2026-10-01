import React, { useState, useEffect, useMemo } from 'react';
import { useProject } from '../../context/ProjectContext';
import {
  Monitor,
  Tablet,
  Smartphone,
  RefreshCw,
  ExternalLink,
  Code2,
  Eye,
  Sparkles,
  Layers,
  Maximize2,
  X,
} from 'lucide-react';
import CodeInspector from './CodeInspector';

export default function LivePreview() {
  const {
    projectId,
    isGenerating,
    currentAgentName,
    generatedFiles,
    codeCache,
    previewDevice,
    setPreviewDevice,
    previewRefreshKey,
    refreshPreview,
    activeTab,
    setActiveTab,
  } = useProject();

  const [isExpanded, setIsExpanded] = useState(false);

  const previewUrl = projectId ? `/api/project/${projectId}/preview` : null;
  const hasFiles = generatedFiles && generatedFiles.length > 0;

  const renderedHtml = useMemo(() => {
    if (codeCache && codeCache['index.html']) {
      let html = codeCache['index.html'];
      if (codeCache['style.css']) {
        html = html.replace('</head>', `<style>${codeCache['style.css']}</style></head>`);
      }
      if (codeCache['script.js']) {
        html = html.replace('</body>', `<script>${codeCache['script.js']}</script></body>`);
      }
      return html;
    }
    return null;
  }, [codeCache]);

  const canDisplayPreview = Boolean(hasFiles || renderedHtml || previewUrl);

  const handleToggleExpand = () => {
    if (!isExpanded) {
      setActiveTab('preview');
      setIsExpanded(true);
    } else {
      setIsExpanded(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isExpanded) {
        setIsExpanded(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isExpanded]);

  const handleOpenExternal = () => {
    if (renderedHtml) {
      const blob = new Blob([renderedHtml], { type: 'text/html;charset=utf-8' });
      const blobUrl = URL.createObjectURL(blob);
      window.open(blobUrl, '_blank');
    } else if (previewUrl) {
      window.open(previewUrl, '_blank');
    }
  };

  return (
    <section className={`live-preview-section ${isExpanded ? 'expanded' : ''}`}>
      {/* Canvas Top Control Bar */}
      <div className="preview-control-bar">
        {/* Left: View Mode Toggle OR Expanded View Header */}
        {isExpanded ? (
          <div className="expanded-title-group">
            <span className="expanded-title-dot" />
            <span className="expanded-title-text font-serif">Live Preview</span>
            <span className="expanded-tag">Expanded View</span>
          </div>
        ) : (
          <div className="view-mode-toggle">
            <button
              type="button"
              className={`mode-btn ${activeTab === 'preview' ? 'active' : ''}`}
              onClick={() => setActiveTab('preview')}
            >
              <Eye size={13} />
              <span>Live Preview</span>
            </button>
            <button
              type="button"
              className={`mode-btn ${activeTab === 'code' ? 'active' : ''}`}
              onClick={() => setActiveTab('code')}
            >
              <Code2 size={13} />
              <span>Source Code</span>
              {hasFiles && <span className="files-count-badge">{generatedFiles.length}</span>}
            </button>
          </div>
        )}

        {/* Center: Device Viewport Switcher (Active during preview or expanded mode) */}
        {(isExpanded || activeTab === 'preview') && (
          <div className="device-switcher-pill">
            <button
              type="button"
              className={`device-btn ${previewDevice === 'desktop' ? 'active' : ''}`}
              onClick={() => setPreviewDevice('desktop')}
              title="Desktop Viewport (100%)"
            >
              <Monitor size={13} />
              <span>Desktop</span>
            </button>
            <button
              type="button"
              className={`device-btn ${previewDevice === 'tablet' ? 'active' : ''}`}
              onClick={() => setPreviewDevice('tablet')}
              title="Tablet Viewport (768px)"
            >
              <Tablet size={13} />
              <span>Tablet</span>
            </button>
            <button
              type="button"
              className={`device-btn ${previewDevice === 'mobile' ? 'active' : ''}`}
              onClick={() => setPreviewDevice('mobile')}
              title="Mobile Viewport (375px)"
            >
              <Smartphone size={13} />
              <span>Mobile</span>
            </button>
          </div>
        )}

        {/* Right: Actions (Refresh, External Window, Expand / Exit Fullscreen) */}
        <div className="preview-actions-group">
          {canDisplayPreview && (
            <>
              <button
                type="button"
                className="icon-action-btn"
                onClick={refreshPreview}
                title="Reload preview"
              >
                <RefreshCw size={13} />
              </button>
              <button
                type="button"
                className="icon-action-btn"
                onClick={handleOpenExternal}
                title="Open live site in new tab"
              >
                <ExternalLink size={13} />
              </button>
              <button
                type="button"
                className={`icon-action-btn ${isExpanded ? 'close-expand-btn' : 'expand-btn'}`}
                onClick={handleToggleExpand}
                title={isExpanded ? 'Close expanded view (Esc)' : 'Expand preview to full screen'}
                aria-label={isExpanded ? 'Close expanded view' : 'Expand preview'}
              >
                {isExpanded ? <X size={15} /> : <Maximize2 size={13} />}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Canvas Stage (Clean Pearl Background, Crisp White Canvas) */}
      <div className="preview-stage-container">
        {activeTab === 'code' && !isExpanded ? (
          <CodeInspector />
        ) : canDisplayPreview ? (
          <div className={`viewport-frame-wrapper device-${previewDevice} ${isExpanded ? 'in-expanded-stage' : ''}`}>
            <div className="frame-header-mock">
              <span className="frame-dot dot-red" />
              <span className="frame-dot dot-yellow" />
              <span className="frame-dot dot-green" />
              <div className="frame-address-bar font-mono">
                auctor://preview/{projectId?.slice(0, 8) || 'live'}/index.html
              </div>
              {isExpanded && (
                <span className="frame-expanded-badge font-mono">EXPANDED</span>
              )}
            </div>
            <iframe
              key={previewRefreshKey}
              src={!renderedHtml ? previewUrl : undefined}
              srcDoc={renderedHtml || undefined}
              title="Generated Website Live Preview"
              className="preview-iframe"
              sandbox="allow-scripts allow-same-origin"
            />
          </div>
        ) : isGenerating ? (
          <div className="preview-generating-state">
            <div className="generating-card">
              <div className="blueprint-grid-anim">
                <Sparkles className="sparkle-float" size={28} />
              </div>
              <h3 className="generating-heading font-serif">Assembling Website</h3>
              <p className="generating-sub">
                The <strong className="agent-highlight">{currentAgentName || 'Auctor'} Agent</strong> is actively constructing your website files and responsive styles.
              </p>
              <div className="generation-progress-bar">
                <div className="progress-fill" />
              </div>
            </div>
          </div>
        ) : (
          <div className="preview-empty-state">
            <div className="empty-state-card">
              <div className="empty-symbol-wrap">
                <Layers size={32} className="empty-symbol" />
              </div>
              <h3 className="empty-title font-serif">Your Website Canvas</h3>
              <p className="empty-desc">
                Describe your website concept in the Director's Console to begin. The 8 specialized agents will plan, write, design, test, and render your website right here.
              </p>
              <div className="empty-features-row">
                <span className="feature-pill">Real HTML/CSS/JS</span>
                <span className="feature-pill">Responsive Breakpoints</span>
                <span className="feature-pill">WCAG Audited</span>
                <span className="feature-pill">Vercel & ZIP Ready</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .live-preview-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          height: 100%;
          min-width: 0;
          background: var(--pearl);
          position: relative;
          transition: all var(--transition-normal);
        }

        /* Expanded Mode Overlay: Take over viewport without unmounting iframe */
        .live-preview-section.expanded {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          width: 100vw;
          height: 100vh;
          z-index: 9999;
          background: var(--pearl);
          animation: fadeIn 0.18s ease-out;
        }

        .preview-control-bar {
          height: 44px;
          padding: 0 16px;
          background: var(--white);
          border-bottom: 1px solid var(--border-light);
          display: flex;
          align-items: center;
          justify-content: space-between;
          user-select: none;
          z-index: 10;
        }

        .live-preview-section.expanded .preview-control-bar {
          height: 50px;
          padding: 0 20px;
          box-shadow: 0 2px 10px rgba(32, 36, 58, 0.05);
        }

        .expanded-title-group {
          display: flex;
          align-items: center;
          gap: 9px;
        }

        .expanded-title-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--burgundy);
          box-shadow: 0 0 0 3px var(--burgundy-light);
        }

        .expanded-title-text {
          font-size: 16px;
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: -0.01em;
        }

        .expanded-tag {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          padding: 2px 8px;
          border-radius: var(--radius-pill);
          background: var(--burgundy-light);
          color: var(--burgundy);
          border: 1px solid var(--rose);
        }

        .view-mode-toggle {
          display: flex;
          background: var(--pearl);
          border-radius: var(--radius-sm);
          padding: 2px;
          gap: 2px;
        }

        .mode-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 12px;
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-size: 12px;
          font-weight: 600;
          border-radius: 4px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .mode-btn:hover {
          color: var(--text-primary);
        }

        .mode-btn.active {
          background: var(--white);
          color: var(--burgundy);
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        }

        .files-count-badge {
          background: var(--burgundy-light);
          color: var(--burgundy);
          font-size: 10px;
          font-weight: 700;
          padding: 1px 5px;
          border-radius: 9999px;
        }

        .device-switcher-pill {
          display: flex;
          align-items: center;
          background: var(--pearl);
          border-radius: var(--radius-pill);
          padding: 2px;
          gap: 2px;
        }

        .device-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 4px 10px;
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-size: 11px;
          font-weight: 600;
          border-radius: var(--radius-pill);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .device-btn:hover {
          color: var(--burgundy);
          background: rgba(182, 138, 154, 0.12);
        }

        .device-btn.active {
          background: var(--burgundy);
          color: var(--white);
          box-shadow: 0 1px 3px rgba(84, 27, 59, 0.25);
        }

        .preview-actions-group {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .icon-action-btn {
          width: 28px;
          height: 28px;
          border-radius: var(--radius-sm);
          background: transparent;
          border: 1px solid var(--border-light);
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .icon-action-btn:hover {
          background: var(--white);
          color: var(--burgundy);
          border-color: var(--rose);
        }

        .close-expand-btn {
          background: var(--burgundy) !important;
          color: var(--white) !important;
          border-color: var(--burgundy) !important;
          width: 30px;
          height: 30px;
        }

        .close-expand-btn:hover {
          background: var(--burgundy-dark) !important;
          transform: scale(1.05);
        }

        .preview-stage-container {
          flex: 1;
          overflow: auto;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 16px;
          background: var(--pearl);
        }

        .live-preview-section.expanded .preview-stage-container {
          padding: 16px 24px;
        }

        .viewport-frame-wrapper {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--white);
          border-radius: var(--radius-md);
          overflow: hidden;
          box-shadow: 0 10px 32px rgba(32, 36, 58, 0.08), 0 2px 6px rgba(32, 36, 58, 0.04);
          border: 1px solid var(--border-light);
          transition: width var(--transition-normal);
        }

        .viewport-frame-wrapper.in-expanded-stage {
          box-shadow: 0 20px 50px rgba(32, 36, 58, 0.16), 0 4px 12px rgba(32, 36, 58, 0.08);
        }

        .viewport-frame-wrapper.device-desktop {
          width: 100%;
        }

        .viewport-frame-wrapper.device-tablet {
          width: 768px;
          max-width: 100%;
        }

        .viewport-frame-wrapper.device-mobile {
          width: 375px;
          max-width: 100%;
        }

        .viewport-frame-wrapper.in-expanded-stage.device-desktop {
          width: 100%;
          max-width: 100%;
        }

        .frame-header-mock {
          height: 32px;
          background: var(--pearl);
          border-bottom: 1px solid var(--border-light);
          display: flex;
          align-items: center;
          padding: 0 12px;
          gap: 6px;
          user-select: none;
        }

        .frame-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .frame-dot.dot-red { background: #E58B88; }
        .frame-dot.dot-yellow { background: #E5BE7A; }
        .frame-dot.dot-green { background: #8EBA96; }

        .frame-address-bar {
          margin-left: 10px;
          flex: 1;
          background: var(--white);
          border: 1px solid var(--border-light);
          border-radius: 4px;
          padding: 2px 10px;
          font-size: 11px;
          color: var(--text-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .frame-expanded-badge {
          font-size: 9px;
          font-weight: 700;
          color: var(--burgundy);
          background: var(--burgundy-light);
          padding: 2px 6px;
          border-radius: 3px;
          letter-spacing: 0.05em;
        }

        .preview-iframe {
          width: 100%;
          flex: 1;
          border: none;
          background: var(--white);
        }

        .preview-empty-state, .preview-generating-state {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 16px;
        }

        .empty-state-card, .generating-card {
          max-width: 460px;
          padding: 24px 28px;
          background: var(--white);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-xl);
          text-align: center;
          box-shadow: var(--shadow-md);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 10px;
        }

        .empty-symbol-wrap {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: var(--pearl);
          border: 1px solid var(--border-light);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--burgundy);
          margin-bottom: 2px;
        }

        .empty-title, .generating-heading {
          font-size: 18px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .empty-desc, .generating-sub {
          font-size: 12px;
          color: var(--text-secondary);
          line-height: 1.45;
          max-width: 380px;
        }

        .agent-highlight {
          color: var(--burgundy);
        }

        .empty-features-row {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          justify-content: center;
          margin-top: 4px;
        }

        .feature-pill {
          font-size: 10.5px;
          font-weight: 600;
          padding: 3px 9px;
          background: var(--pearl);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-pill);
          color: var(--text-secondary);
        }

        .blueprint-grid-anim {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: var(--burgundy-light);
          border: 1px solid var(--rose);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--burgundy);
          animation: pulse-burgundy 2s infinite ease-in-out;
        }

        .generation-progress-bar {
          width: 100%;
          height: 5px;
          background: var(--pearl-dark);
          border-radius: 9999px;
          overflow: hidden;
          margin-top: 12px;
        }

        .progress-fill {
          height: 100%;
          width: 40%;
          background: linear-gradient(90deg, var(--burgundy), var(--rose));
          border-radius: 9999px;
          animation: sweep-burgundy 1.6s infinite ease-in-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </section>
  );
}
