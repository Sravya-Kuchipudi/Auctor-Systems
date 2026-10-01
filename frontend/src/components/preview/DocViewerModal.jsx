import React, { useState, useEffect, useMemo } from 'react';
import { useProject } from '../../context/ProjectContext';
import { FileText, Download, X, Copy, Check, BookOpen } from 'lucide-react';
import { api } from '../../api/client';

/**
 * Minimalist, robust Markdown-to-HTML parser for formatted display
 * Preserves headings, lists, code blocks, blockquotes, tables, bold, and monospace text.
 */
function renderMarkdown(mdText) {
  if (!mdText) return '<p class="empty-doc-hint">// No documentation content available.</p>';

  const lines = mdText.split(/\r?\n/);
  const htmlParts = [];
  let inCodeBlock = false;
  let codeBlockBuffer = [];
  let inUl = false;
  let inOl = false;

  const closeLists = () => {
    if (inUl) {
      htmlParts.push('</ul>');
      inUl = false;
    }
    if (inOl) {
      htmlParts.push('</ol>');
      inOl = false;
    }
  };

  const formatInline = (text) => {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="doc-link">$1</a>');
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Code block toggle
    if (trimmed.startsWith('```')) {
      closeLists();
      if (inCodeBlock) {
        // Closing code block
        const codeContent = codeBlockBuffer
          .join('\n')
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');
        htmlParts.push(`<pre class="doc-code-block"><code>${codeContent}</code></pre>`);
        codeBlockBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
        codeBlockBuffer = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockBuffer.push(rawLine);
      continue;
    }

    // Empty line
    if (!trimmed) {
      closeLists();
      continue;
    }

    // Headings
    if (trimmed.startsWith('# ')) {
      closeLists();
      htmlParts.push(`<h1 class="doc-h1 font-serif">${formatInline(trimmed.slice(2))}</h1>`);
      continue;
    }
    if (trimmed.startsWith('## ')) {
      closeLists();
      htmlParts.push(`<h2 class="doc-h2 font-serif">${formatInline(trimmed.slice(3))}</h2>`);
      continue;
    }
    if (trimmed.startsWith('### ')) {
      closeLists();
      htmlParts.push(`<h3 class="doc-h3 font-serif">${formatInline(trimmed.slice(4))}</h3>`);
      continue;
    }
    if (trimmed.startsWith('#### ')) {
      closeLists();
      htmlParts.push(`<h4 class="doc-h4 font-serif">${formatInline(trimmed.slice(5))}</h4>`);
      continue;
    }

    // Blockquote
    if (trimmed.startsWith('>')) {
      closeLists();
      const quoteText = trimmed.replace(/^>\s*/, '');
      htmlParts.push(`<blockquote class="doc-blockquote">${formatInline(quoteText)}</blockquote>`);
      continue;
    }

    // Unordered List
    if (/^[-*]\s+/.test(trimmed)) {
      if (inOl) {
        htmlParts.push('</ol>');
        inOl = false;
      }
      if (!inUl) {
        htmlParts.push('<ul class="doc-ul">');
        inUl = true;
      }
      const itemText = trimmed.replace(/^[-*]\s+/, '');
      htmlParts.push(`<li>${formatInline(itemText)}</li>`);
      continue;
    }

    // Ordered List
    if (/^\d+\.\s+/.test(trimmed)) {
      if (inUl) {
        htmlParts.push('</ul>');
        inUl = false;
      }
      if (!inOl) {
        htmlParts.push('<ol class="doc-ol">');
        inOl = true;
      }
      const itemText = trimmed.replace(/^\d+\.\s+/, '');
      htmlParts.push(`<li>${formatInline(itemText)}</li>`);
      continue;
    }

    // Horizontal Rule
    if (/^[-*_]{3,}$/.test(trimmed)) {
      closeLists();
      htmlParts.push('<hr class="doc-divider" />');
      continue;
    }

    // Normal paragraph
    closeLists();
    htmlParts.push(`<p class="doc-p">${formatInline(trimmed)}</p>`);
  }

  closeLists();

  if (inCodeBlock && codeBlockBuffer.length > 0) {
    const codeContent = codeBlockBuffer.join('\n').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    htmlParts.push(`<pre class="doc-code-block"><code>${codeContent}</code></pre>`);
  }

  return htmlParts.join('\n');
}

export default function DocViewerModal() {
  const {
    isDocViewerOpen,
    docViewerDoc,
    openDocViewer,
    closeDocViewer,
    codeCache,
    projectId,
    downloadFile,
  } = useProject();

  const [activeDoc, setActiveDoc] = useState(docViewerDoc || 'README.md');
  const [viewMode, setViewMode] = useState('formatted'); // formatted | raw
  const [copied, setCopied] = useState(false);
  const [fetchedContent, setFetchedContent] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (docViewerDoc) {
      setActiveDoc(docViewerDoc);
    }
  }, [docViewerDoc]);

  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isDocViewerOpen) {
        closeDocViewer();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDocViewerOpen, closeDocViewer]);

  // Fetch or retrieve markdown content
  useEffect(() => {
    if (!isDocViewerOpen) return;

    const baseName = activeDoc.split('/').pop();
    const candidatePaths = [
      activeDoc,
      baseName,
      `docs/${baseName}`,
      baseName === 'README.md' ? 'README.md' : null,
    ].filter(Boolean);

    let contentFromCache = null;
    if (codeCache) {
      for (const p of candidatePaths) {
        if (codeCache[p]) {
          contentFromCache = codeCache[p];
          break;
        }
      }
    }

    if (contentFromCache) {
      setFetchedContent(contentFromCache);
      setLoading(false);
      return;
    }

    if (projectId && projectId !== 'kairos-academic-studio') {
      setLoading(true);
      const fetchPath = activeDoc.includes('/') ? activeDoc : `docs/${activeDoc}`;
      api.getFileContent(projectId, fetchPath)
        .then((text) => {
          setFetchedContent(text);
          setLoading(false);
        })
        .catch(() => {
          // Fallback to basename
          api.getFileContent(projectId, baseName)
            .then((text) => {
              setFetchedContent(text);
              setLoading(false);
            })
            .catch((err) => {
              setFetchedContent(`// Documentation content unavailable: ${err.message}`);
              setLoading(false);
            });
        });
    } else {
      setFetchedContent('// No documentation generated yet. Run a workflow to view generated docs.');
      setLoading(false);
    }
  }, [isDocViewerOpen, activeDoc, codeCache, projectId]);

  const parsedHtml = useMemo(() => {
    return renderMarkdown(fetchedContent);
  }, [fetchedContent]);

  if (!isDocViewerOpen) return null;

  const handleCopy = () => {
    if (!fetchedContent) return;
    navigator.clipboard.writeText(fetchedContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    downloadFile(activeDoc, fetchedContent);
  };

  return (
    <div className="doc-modal-overlay" onClick={closeDocViewer} role="dialog" aria-modal="true" aria-label="Documentation Viewer">
      <div className="doc-modal-window" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="doc-modal-header">
          <div className="doc-header-left">
            <div className="doc-brand-icon">
              <BookOpen size={16} />
            </div>
            <div className="doc-title-group">
              <h2 className="doc-modal-title font-serif">Auctor Documentation Viewer</h2>
              <span className="doc-modal-sub font-mono">Preserved Markdown • Real Output</span>
            </div>
          </div>

          {/* Doc Switcher Tabs */}
          <div className="doc-switcher-tabs">
            <button
              type="button"
              className={`doc-tab-btn ${activeDoc === 'README.md' ? 'active' : ''}`}
              onClick={() => setActiveDoc('README.md')}
            >
              <FileText size={13} />
              <span>README.md</span>
            </button>
            <button
              type="button"
              className={`doc-tab-btn ${activeDoc === 'ARCHITECTURE.md' ? 'active' : ''}`}
              onClick={() => setActiveDoc('ARCHITECTURE.md')}
            >
              <FileText size={13} />
              <span>ARCHITECTURE.md</span>
            </button>
          </div>

          {/* Actions */}
          <div className="doc-header-actions">
            <div className="view-mode-pill">
              <button
                type="button"
                className={`mode-pill-btn ${viewMode === 'formatted' ? 'active' : ''}`}
                onClick={() => setViewMode('formatted')}
              >
                Formatted
              </button>
              <button
                type="button"
                className={`mode-pill-btn ${viewMode === 'raw' ? 'active' : ''}`}
                onClick={() => setViewMode('raw')}
              >
                Raw
              </button>
            </div>

            <button
              type="button"
              className="doc-tool-btn"
              onClick={handleCopy}
              disabled={!fetchedContent || loading}
              title="Copy markdown content"
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              type="button"
              className="doc-tool-btn download-highlight"
              onClick={handleDownload}
              disabled={!fetchedContent || loading}
              title={`Download ${activeDoc}`}
            >
              <Download size={13} />
              <span>Download</span>
            </button>

            <button
              type="button"
              className="doc-close-btn"
              onClick={closeDocViewer}
              title="Close Documentation Viewer (Esc)"
              aria-label="Close Documentation Viewer"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="doc-modal-body">
          {loading ? (
            <div className="doc-loading font-mono">Loading {activeDoc}...</div>
          ) : viewMode === 'raw' ? (
            <pre className="doc-raw-pre font-mono">
              <code>{fetchedContent}</code>
            </pre>
          ) : (
            <div
              className="doc-formatted-container"
              dangerouslySetInnerHTML={{ __html: parsedHtml }}
            />
          )}
        </div>
      </div>

      <style>{`
        .doc-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: rgba(32, 36, 58, 0.75);
          backdrop-filter: blur(6px);
          z-index: 9999;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          animation: docFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes docFadeIn {
          from { opacity: 0; transform: scale(0.98); }
          to { opacity: 1; transform: scale(1); }
        }

        .doc-modal-window {
          background: #FFFFFF;
          border: 1px solid rgba(58, 16, 40, 0.15);
          border-radius: 8px;
          width: 920px;
          max-width: 95vw;
          height: 84vh;
          display: flex;
          flex-direction: column;
          box-shadow: 0 20px 48px rgba(32, 36, 58, 0.28), 0 4px 12px rgba(58, 16, 40, 0.12);
          overflow: hidden;
        }

        .doc-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 18px;
          background: var(--navy); /* #20243A */
          color: #FFFFFF;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          gap: 12px;
          flex-wrap: wrap;
        }

        .doc-header-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .doc-brand-icon {
          width: 28px;
          height: 28px;
          border-radius: 6px;
          background: var(--burgundy); /* #541B3B */
          color: var(--muted-gold); /* #C79A4A */
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .doc-title-group {
          display: flex;
          flex-direction: column;
        }

        .doc-modal-title {
          font-size: 14px;
          font-weight: 600;
          letter-spacing: 0.02em;
          margin: 0;
          color: #FFFFFF;
        }

        .doc-modal-sub {
          font-size: 10px;
          color: #A3A7BD;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }

        .doc-switcher-tabs {
          display: flex;
          gap: 4px;
          background: var(--navy-surface); /* #273049 */
          padding: 3px;
          border-radius: 6px;
        }

        .doc-tab-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 12px;
          font-family: var(--font-mono);
          font-size: 11px;
          font-weight: 500;
          color: #A3A7BD;
          background: transparent;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .doc-tab-btn:hover {
          color: #FFFFFF;
          background: rgba(255, 255, 255, 0.06);
        }

        .doc-tab-btn.active {
          background: var(--deep-wine); /* #3A1028 */
          color: #FFFFFF;
          box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
        }

        .doc-header-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .view-mode-pill {
          display: flex;
          background: var(--navy-surface);
          padding: 2px;
          border-radius: 4px;
        }

        .mode-pill-btn {
          padding: 3px 8px;
          font-size: 11px;
          font-family: var(--font-mono);
          border: none;
          background: transparent;
          color: #A3A7BD;
          border-radius: 3px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .mode-pill-btn.active {
          background: rgba(255, 255, 255, 0.15);
          color: #FFFFFF;
        }

        .doc-tool-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 5px 10px;
          font-size: 11px;
          font-weight: 500;
          font-family: var(--font-mono);
          color: #FFFFFF;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.14);
          border-radius: 4px;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .doc-tool-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.16);
          border-color: rgba(255, 255, 255, 0.3);
        }

        .doc-tool-btn.download-highlight {
          background: var(--muted-gold); /* #C79A4A */
          color: #20243A;
          border-color: var(--muted-gold);
          font-weight: 600;
        }

        .doc-tool-btn.download-highlight:hover:not(:disabled) {
          background: #D3A758;
          color: #1A1D2F;
        }

        .doc-close-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          border-radius: 4px;
          background: transparent;
          border: none;
          color: #A3A7BD;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .doc-close-btn:hover {
          color: #FFFFFF;
          background: rgba(255, 255, 255, 0.12);
        }

        .doc-modal-body {
          flex: 1;
          overflow-y: auto;
          padding: 32px 40px;
          background: var(--pearl); /* #F5F4F5 */
          color: var(--text-primary); /* #29232B */
        }

        .doc-loading {
          text-align: center;
          padding: 40px;
          color: var(--cool-gray);
          font-size: 13px;
        }

        .doc-raw-pre {
          background: var(--navy);
          color: #F5F4F5;
          padding: 20px;
          border-radius: 6px;
          font-size: 12px;
          line-height: 1.6;
          overflow-x: auto;
          margin: 0;
          white-space: pre-wrap;
          word-break: break-word;
        }

        /* Formatted Typography */
        .doc-formatted-container {
          max-width: 820px;
          margin: 0 auto;
          background: #FFFFFF;
          padding: 36px 44px;
          border-radius: 6px;
          border: 1px solid rgba(58, 16, 40, 0.08);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
          font-family: var(--font-sans);
          line-height: 1.7;
          color: var(--text-primary);
        }

        .doc-h1 {
          font-size: 24px;
          font-weight: 700;
          color: var(--deep-wine); /* #3A1028 */
          margin: 0 0 16px 0;
          padding-bottom: 10px;
          border-bottom: 2px solid var(--burgundy); /* #541B3B */
        }

        .doc-h2 {
          font-size: 18px;
          font-weight: 600;
          color: var(--burgundy); /* #541B3B */
          margin: 28px 0 12px 0;
          padding-bottom: 6px;
          border-bottom: 1px solid rgba(58, 16, 40, 0.12);
        }

        .doc-h3 {
          font-size: 15px;
          font-weight: 600;
          color: var(--navy); /* #20243A */
          margin: 20px 0 8px 0;
        }

        .doc-h4 {
          font-size: 13px;
          font-weight: 600;
          color: var(--deep-wine);
          margin: 16px 0 6px 0;
        }

        .doc-p {
          font-size: 14px;
          margin: 0 0 14px 0;
          color: #38343D;
        }

        .doc-blockquote {
          margin: 16px 0;
          padding: 10px 18px;
          background: rgba(84, 27, 59, 0.05);
          border-left: 4px solid var(--burgundy);
          border-radius: 0 4px 4px 0;
          color: var(--deep-wine);
          font-style: italic;
          font-size: 13.5px;
        }

        .doc-ul, .doc-ol {
          margin: 0 0 16px 0;
          padding-left: 24px;
          font-size: 13.5px;
          color: #38343D;
        }

        .doc-ul li, .doc-ol li {
          margin-bottom: 6px;
        }

        .doc-code-block {
          background: var(--navy); /* #20243A */
          color: #F5F4F5;
          padding: 14px 18px;
          border-radius: 6px;
          font-family: var(--font-mono);
          font-size: 12px;
          line-height: 1.5;
          overflow-x: auto;
          margin: 16px 0;
          border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .inline-code {
          background: rgba(32, 36, 58, 0.08);
          color: var(--deep-wine);
          padding: 2px 5px;
          border-radius: 3px;
          font-family: var(--font-mono);
          font-size: 12px;
          font-weight: 500;
        }

        .doc-divider {
          border: none;
          border-top: 1px solid rgba(58, 16, 40, 0.12);
          margin: 24px 0;
        }

        .doc-link {
          color: var(--burgundy);
          text-decoration: underline;
        }

        .doc-link:hover {
          color: var(--deep-wine);
        }

        .empty-doc-hint {
          color: var(--cool-gray);
          font-style: italic;
          text-align: center;
          padding: 30px;
        }

        @media (max-width: 640px) {
          .doc-modal-body {
            padding: 16px;
          }
          .doc-formatted-container {
            padding: 20px;
          }
          .doc-modal-header {
            padding: 10px;
          }
        }
      `}</style>
    </div>
  );
}
