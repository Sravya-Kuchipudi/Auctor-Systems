import React, { useState, useEffect, useMemo } from 'react';
import { useProject } from '../../context/ProjectContext';
import { FileCode, Copy, Check, Download, Eye } from 'lucide-react';
import { api } from '../../api/client';

const REQUIRED_FILES_SPEC = [
  { path: 'src/index.html', label: 'index.html', filename: 'index.html', category: 'source' },
  { path: 'src/style.css', label: 'style.css', filename: 'style.css', category: 'source' },
  { path: 'src/script.js', label: 'script.js', filename: 'script.js', category: 'source' },
  { path: 'README.md', label: 'README.md', filename: 'README.md', category: 'doc' },
  { path: 'docs/README.md', label: 'docs/README.md', filename: 'README.md', category: 'doc' },
  { path: 'docs/ARCHITECTURE.md', label: 'docs/ARCHITECTURE.md', filename: 'ARCHITECTURE.md', category: 'doc' },
  { path: 'deploy/vercel.json', label: 'deploy/vercel.json', filename: 'vercel.json', category: 'deploy' },
  { path: 'marketing/LAUNCH_COPY.md', label: 'marketing/LAUNCH_COPY.md', filename: 'LAUNCH_COPY.md', category: 'doc' },
];

export default function CodeInspector() {
  const { projectId, generatedFiles, codeCache, downloadFile, openDocViewer } = useProject();
  const [activeFile, setActiveFile] = useState('src/index.html');
  const [fileContent, setFileContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Compute canonical files list ensuring all 8 required tabs are available
  const filesList = useMemo(() => {
    const list = [...REQUIRED_FILES_SPEC];

    // If generatedFiles contains any extra custom files not in standard 8, append them
    if (generatedFiles && Array.isArray(generatedFiles)) {
      generatedFiles.forEach((gf) => {
        const p = gf.path || gf.filename;
        const exists = list.some((item) => item.path === p || (item.path.endsWith(p) && p.includes('/')));
        if (!exists && p) {
          list.push({
            path: p,
            label: p,
            filename: gf.filename || p.split('/').pop(),
            category: gf.category || 'other',
          });
        }
      });
    }

    return list;
  }, [generatedFiles]);

  useEffect(() => {
    if (!activeFile) return;

    const baseName = activeFile.split('/').pop();

    // Check codeCache first for instant zero-latency loading
    if (codeCache) {
      // 1. Direct path lookup e.g. codeCache['docs/README.md'] or codeCache['README.md']
      if (codeCache[activeFile] !== undefined && codeCache[activeFile] !== '') {
        setFileContent(codeCache[activeFile]);
        setLoading(false);
        return;
      }
      // 2. Exact match if activeFile was just basename
      if (codeCache[baseName] !== undefined && codeCache[baseName] !== '') {
        // If activeFile is 'docs/README.md' and codeCache has 'docs/README.md', step 1 handled it.
        // If activeFile is 'README.md' and codeCache has 'README.md', step 1 handled it.
        // If activeFile is 'docs/ARCHITECTURE.md' and codeCache only has 'ARCHITECTURE.md':
        setFileContent(codeCache[baseName]);
        setLoading(false);
        return;
      }
    }

    if (!projectId) {
      setFileContent('// Select a file above or generate a site to view source code.');
      return;
    }

    let isMounted = true;
    setLoading(true);

    api.getFileContent(projectId, activeFile)
      .then((content) => {
        if (isMounted) {
          setFileContent(content);
          setLoading(false);
        }
      })
      .catch((err) => {
        // Fallback fetch by basename
        api.getFileContent(projectId, baseName)
          .then((content) => {
            if (isMounted) {
              setFileContent(content);
              setLoading(false);
            }
          })
          .catch(() => {
            if (isMounted) {
              setFileContent(`// Unable to load ${activeFile}: ${err.message}`);
              setLoading(false);
            }
          });
      });

    return () => {
      isMounted = false;
    };
  }, [projectId, activeFile, codeCache]);

  const handleCopy = () => {
    if (!fileContent) return;
    navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!fileContent && !codeCache) return;
    downloadFile(activeFile, fileContent);
  };

  const isMarkdown = activeFile.endsWith('.md');
  const baseFilename = activeFile.split('/').pop();

  return (
    <div className="code-inspector-wrap">
      {/* File Tabs Bar (Midnight Navy Secondary #273049) */}
      <div className="code-tabs-bar">
        <div className="file-tabs-scroll">
          {filesList.map((file) => {
            const isSelected = activeFile === file.path;
            return (
              <button
                key={file.path}
                type="button"
                className={`code-tab-btn ${isSelected ? 'active' : ''}`}
                onClick={() => setActiveFile(file.path)}
                title={file.path}
              >
                <FileCode size={13} className="tab-icon" />
                <span>{file.label}</span>
              </button>
            );
          })}
        </div>

        <div className="code-tab-actions">
          {/* Formatted Doc Viewer shortcut for Markdown files */}
          {isMarkdown && (
            <button
              type="button"
              className="code-action-btn view-doc-btn"
              onClick={() => openDocViewer(baseFilename)}
              title="Open in Documentation Viewer"
            >
              <Eye size={13} />
              <span>Doc View</span>
            </button>
          )}

          <button
            type="button"
            className="code-action-btn download-btn"
            onClick={handleDownload}
            disabled={!fileContent || loading}
            title={`Download ${baseFilename}`}
          >
            <Download size={13} />
            <span>Download</span>
          </button>

          <button
            type="button"
            className="code-action-btn"
            onClick={handleCopy}
            disabled={!fileContent || loading}
            title="Copy file contents"
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Code Viewer (Midnight Navy Background #20243A) */}
      <div className="code-viewer-area">
        {loading ? (
          <div className="code-loading font-mono">Reading {activeFile}...</div>
        ) : (
          <pre className="code-pre font-mono">
            <code>{fileContent || '// Generated file content will appear here.'}</code>
          </pre>
        )}
      </div>

      <style>{`
        .code-inspector-wrap {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--navy); /* #20243A */
          color: var(--text-on-dark); /* #F5F4F5 */
        }

        .code-tabs-bar {
          height: 38px;
          background: var(--navy-surface); /* #273049 */
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 10px;
          user-select: none;
          gap: 8px;
        }

        .file-tabs-scroll {
          display: flex;
          gap: 4px;
          overflow-x: auto;
          scrollbar-width: thin;
        }

        .code-tab-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: transparent;
          color: #989BB0;
          border: none;
          border-radius: 4px 4px 0 0;
          font-family: var(--font-mono);
          font-size: 11px;
          white-space: nowrap;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .code-tab-btn:hover {
          color: var(--pearl);
          background: rgba(255, 255, 255, 0.06);
        }

        .code-tab-btn.active {
          background: var(--navy);
          color: #FFFFFF;
          border-bottom: 2px solid var(--rose);
        }

        .code-tab-btn.active .tab-icon {
          color: var(--rose);
        }

        .code-tab-actions {
          display: flex;
          align-items: center;
          gap: 6px;
          flex-shrink: 0;
        }

        .code-action-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 9px;
          border-radius: var(--radius-sm);
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.12);
          color: var(--pearl);
          font-size: 11px;
          font-family: var(--font-sans);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .code-action-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.15);
          border-color: var(--rose);
        }

        .code-action-btn.view-doc-btn {
          background: rgba(84, 27, 59, 0.6);
          border-color: var(--rose);
          color: #FFFFFF;
        }

        .code-action-btn.view-doc-btn:hover:not(:disabled) {
          background: var(--burgundy);
        }

        .code-action-btn.download-btn {
          background: rgba(199, 154, 74, 0.15);
          border-color: var(--muted-gold); /* #C79A4A */
          color: var(--muted-gold);
        }

        .code-action-btn.download-btn:hover:not(:disabled) {
          background: var(--muted-gold);
          color: #20243A;
        }

        .code-viewer-area {
          flex: 1;
          overflow: auto;
          padding: 16px 20px;
          background: var(--navy);
        }

        .code-loading {
          color: #797E98;
          font-size: 12px;
        }

        .code-pre {
          font-size: 12px;
          line-height: 1.65;
          tab-size: 2;
          color: #E2E4F0;
        }

        .code-pre code {
          font-family: var(--font-mono);
        }
      `}</style>
    </div>
  );
}
