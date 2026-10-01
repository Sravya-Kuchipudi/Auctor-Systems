import React, { useState, useRef, useEffect } from 'react';
import { useProject } from '../../context/ProjectContext';
import {
  Download,
  Rocket,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  FolderArchive,
  ChevronDown,
  Check,
  Trash2,
  Plus,
} from 'lucide-react';

export default function Header() {
  const {
    backendStatus,
    projectId,
    projectsList,
    selectProject,
    deleteProject,
    projectState,
    revisionCount,
    isGenerating,
    currentAgentName,
    generatedFiles,
    resetWorkspace,
    deployCurrentProject,
  } = useProject();

  const [isProjectMenuOpen, setIsProjectMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsProjectMenuOpen(false);
      }
    }
    if (isProjectMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isProjectMenuOpen]);

  const currentProjectName =
    projectState?.name ||
    projectState?.project_name ||
    projectsList?.find((p) => p.id === projectId)?.name ||
    (projectId ? 'Active Website' : 'Select Project');

  const handleDownloadZip = () => {
    if (!projectId) return;
    window.location.href = `/api/project/${projectId}/export`;
  };

  const handleDeploy = async () => {
    try {
      const result = await deployCurrentProject();
      if (result?.status === 'DEPLOYED') {
        window.open(result.deployed_url, '_blank');
      } else {
        alert(result?.message || 'Deployment configured, but credentials are not set.');
      }
    } catch (err) {
      alert(`Deployment: ${err.message}`);
    }
  };

  const hasGeneratedFiles = generatedFiles && generatedFiles.length > 0;

  return (
    <header className="auctor-header">
      {/* Brand & Monogram */}
      <div className="header-brand-group">
        <div className="brand-monogram">
          <span className="monogram-letter">A</span>
          <span className="monogram-dot" />
        </div>
        <div className="brand-title-wrap">
          <h1 className="brand-name">AUCTOR SYSTEMS</h1>
          <span className="brand-tagline">AI Website Generation Studio</span>
        </div>

        {/* Brand Divider */}
        <div className="header-brand-divider" />

        {/* Project Selector (Phase 4A) */}
        <div className="project-selector-wrapper" ref={menuRef}>
          <button
            type="button"
            className={`project-selector-btn ${isProjectMenuOpen ? 'open' : ''}`}
            onClick={() => setIsProjectMenuOpen(!isProjectMenuOpen)}
            title="Switch or manage saved projects"
          >
            <FolderArchive size={13} className="selector-folder-icon" />
            <span className="selector-label">{currentProjectName}</span>
            <ChevronDown size={12} className={`selector-chevron ${isProjectMenuOpen ? 'chevron-up' : ''}`} />
          </button>

          {isProjectMenuOpen && (
            <div className="project-selector-dropdown">
              <div className="dropdown-header">
                <span className="dropdown-title">Saved Projects</span>
                <span className="dropdown-count">{projectsList?.length || 0}</span>
              </div>

              <div className="dropdown-project-list">
                {(!projectsList || projectsList.length === 0) ? (
                  <div className="dropdown-empty">No saved projects yet</div>
                ) : (
                  projectsList.map((p) => {
                    const isActive = p.id === projectId;
                    const isCompleted = p.status === 'completed' || p.status === 'generated';
                    const isGen = p.status === 'generating' || p.status === 'running';
                    return (
                      <div
                        key={p.id}
                        className={`dropdown-project-item ${isActive ? 'active' : ''}`}
                        onClick={() => {
                          selectProject(p.id);
                          setIsProjectMenuOpen(false);
                        }}
                      >
                        <div className="item-info">
                          <div className="item-name-row">
                            <span className="item-name">{p.name || 'Auctor Project'}</span>
                            {isActive && <Check size={12} className="active-check" />}
                          </div>
                          <div className="item-meta-row">
                            <span
                              className={`item-status-dot ${
                                isCompleted ? 'dot-completed' : isGen ? 'dot-generating' : 'dot-idle'
                              }`}
                            />
                            <span className="item-status-text">{p.status || 'idle'}</span>
                            {p.file_count > 0 && <span className="item-files-text">· {p.file_count} files</span>}
                          </div>
                        </div>
                        <button
                          type="button"
                          className="item-delete-btn"
                          title="Delete project"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm(`Delete project "${p.name || p.id}"? This cannot be undone.`)) {
                              deleteProject(p.id);
                            }
                          }}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="dropdown-footer">
                <button
                  type="button"
                  className="dropdown-new-btn"
                  onClick={() => {
                    resetWorkspace();
                    setIsProjectMenuOpen(false);
                  }}
                >
                  <Plus size={13} />
                  <span>New Project</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Center Status Indicators */}
      <div className="header-status-group">
        {/* Engine Status Badge */}
        <div className="status-badge engine-badge">
          <span className={`status-dot ${backendStatus.healthy ? 'dot-active' : 'dot-inactive'}`} />
          <span className="badge-text">
            {backendStatus.loading
              ? 'Connecting engine...'
              : backendStatus.healthy
              ? `Engine: ${backendStatus.model || 'Gemini'}`
              : 'Engine Offline'}
          </span>
        </div>

        {/* Workflow State Badge */}
        {isGenerating && (
          <div className="status-badge workflow-badge generating">
            <Sparkles className="badge-icon icon-pulse" size={13} />
            <span>Active: {currentAgentName || 'Orchestrating'} Agent</span>
          </div>
        )}

        {!isGenerating && hasGeneratedFiles && (
          <div className="status-badge workflow-badge ready">
            <CheckCircle2 className="badge-icon" size={13} />
            <span>Website Generated & Tested</span>
          </div>
        )}

        {hasGeneratedFiles && (
          <div className="status-badge rev-badge" title="Project Revision Number">
            <span className="badge-text font-mono">Rev {revisionCount ?? 0}</span>
          </div>
        )}
      </div>

      {/* Right Actions */}
      <div className="header-actions">
        {projectId && (
          <button
            type="button"
            className="action-btn outline-btn"
            onClick={resetWorkspace}
            title="Start a new website"
          >
            <RefreshCw size={13} />
            <span>New Site</span>
          </button>
        )}

        <button
          type="button"
          className="action-btn outline-btn"
          onClick={handleDownloadZip}
          disabled={!hasGeneratedFiles}
          title="Download production ZIP package"
        >
          <Download size={13} />
          <span>Export ZIP</span>
        </button>

        <button
          type="button"
          className="action-btn primary-deploy-btn"
          onClick={handleDeploy}
          disabled={!hasGeneratedFiles || isGenerating}
          title="Deploy static site to hosting"
        >
          <Rocket size={13} />
          <span>Deploy</span>
        </button>
      </div>

      <style>{`
        .auctor-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          height: 60px;
          padding: 0 24px;
          background: var(--wine);
          color: var(--pearl);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          box-shadow: 0 2px 12px rgba(39, 11, 27, 0.4);
          user-select: none;
          z-index: 50;
        }

        .header-brand-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .brand-monogram {
          width: 34px;
          height: 34px;
          border-radius: var(--radius-sm);
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(199, 154, 74, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        .monogram-letter {
          font-family: var(--font-serif);
          font-size: 18px;
          font-weight: 700;
          color: var(--gold);
          letter-spacing: 0.5px;
          line-height: 1;
        }

        .monogram-dot {
          position: absolute;
          top: 5px;
          right: 5px;
          width: 4px;
          height: 4px;
          border-radius: 50%;
          background: var(--gold);
        }

        .brand-title-wrap {
          display: flex;
          flex-direction: column;
        }

        .brand-name {
          font-family: var(--font-serif);
          font-size: 16px;
          font-weight: 700;
          letter-spacing: 1.6px;
          color: var(--white);
          line-height: 1.1;
        }

        .brand-tagline {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          color: var(--rose);
          font-weight: 500;
        }

        .header-brand-divider {
          width: 1px;
          height: 24px;
          background: rgba(255, 255, 255, 0.12);
          margin: 0 4px;
        }

        .project-selector-wrapper {
          position: relative;
        }

        .project-selector-btn {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 5px 11px;
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.14);
          border-radius: var(--radius-sm);
          color: var(--pearl);
          font-family: var(--font-sans);
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: all var(--transition-fast);
          max-width: 210px;
        }

        .project-selector-btn:hover {
          background: rgba(84, 27, 59, 0.6);
          border-color: rgba(182, 138, 154, 0.4);
          color: var(--white);
        }

        .project-selector-btn.open {
          background: var(--burgundy);
          border-color: var(--rose);
        }

        .selector-folder-icon {
          color: var(--rose);
          flex-shrink: 0;
        }

        .selector-label {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 140px;
        }

        .selector-chevron {
          color: var(--rose);
          transition: transform 0.2s ease;
          flex-shrink: 0;
        }

        .selector-chevron.chevron-up {
          transform: rotate(180deg);
        }

        .project-selector-dropdown {
          position: absolute;
          top: calc(100% + 8px);
          left: 0;
          width: 260px;
          background: #20243A;
          border: 1px solid rgba(182, 138, 154, 0.25);
          border-radius: var(--radius-sm);
          box-shadow: 0 10px 28px rgba(0, 0, 0, 0.5);
          z-index: 100;
          overflow: hidden;
          animation: fadeIn 0.15s ease-out;
        }

        .dropdown-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 12px;
          background: rgba(58, 16, 40, 0.8);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .dropdown-title {
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--rose);
        }

        .dropdown-count {
          font-size: 10px;
          font-weight: 700;
          padding: 1px 6px;
          border-radius: var(--radius-pill);
          background: var(--burgundy);
          color: var(--white);
        }

        .dropdown-project-list {
          max-height: 220px;
          overflow-y: auto;
          padding: 4px;
        }

        .dropdown-empty {
          padding: 16px 12px;
          text-align: center;
          font-size: 12px;
          color: var(--gray);
        }

        .dropdown-project-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 7px 9px;
          border-radius: var(--radius-sm);
          cursor: pointer;
          transition: background 0.15s ease;
          gap: 8px;
        }

        .dropdown-project-item:hover {
          background: rgba(84, 27, 59, 0.45);
        }

        .dropdown-project-item.active {
          background: rgba(84, 27, 59, 0.8);
          border: 1px solid rgba(182, 138, 154, 0.3);
        }

        .item-info {
          flex: 1;
          min-width: 0;
        }

        .item-name-row {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .item-name {
          font-size: 12px;
          font-weight: 600;
          color: var(--pearl);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .active-check {
          color: var(--sage);
          flex-shrink: 0;
        }

        .item-meta-row {
          display: flex;
          align-items: center;
          gap: 5px;
          margin-top: 2px;
          font-size: 10px;
          color: var(--gray);
        }

        .item-status-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
        }

        .dot-completed {
          background: var(--sage);
        }

        .dot-generating {
          background: var(--gold);
        }

        .dot-idle {
          background: var(--gray);
        }

        .item-status-text {
          text-transform: capitalize;
        }

        .item-files-text {
          font-size: 10px;
          color: var(--gray);
        }

        .item-delete-btn {
          background: transparent;
          border: none;
          color: var(--gray);
          cursor: pointer;
          padding: 4px;
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: color 0.15s ease, background 0.15s ease;
        }

        .item-delete-btn:hover {
          color: var(--error);
          background: rgba(184, 92, 92, 0.15);
        }

        .dropdown-footer {
          padding: 6px 8px;
          background: rgba(32, 36, 58, 0.95);
          border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .dropdown-new-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 6px 10px;
          background: rgba(255, 255, 255, 0.06);
          border: 1px dashed rgba(182, 138, 154, 0.35);
          border-radius: var(--radius-sm);
          color: var(--pearl);
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .dropdown-new-btn:hover {
          background: var(--burgundy);
          border-color: var(--rose);
          color: var(--white);
        }

        .header-status-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 5px 12px;
          border-radius: var(--radius-pill);
          font-size: 12px;
          font-weight: 500;
          letter-spacing: 0.2px;
        }

        .engine-badge {
          background: rgba(84, 27, 59, 0.45);
          border: 1px solid rgba(182, 138, 154, 0.25);
          color: var(--pearl);
        }

        .status-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
        }

        .dot-active {
          background: var(--sage);
          box-shadow: 0 0 6px var(--sage);
        }

        .dot-inactive {
          background: var(--error);
        }

        .workflow-badge.generating {
          background: rgba(182, 138, 154, 0.2);
          border: 1px solid rgba(182, 138, 154, 0.45);
          color: #E8D4DC;
        }

        .workflow-badge.ready {
          background: rgba(113, 130, 118, 0.25);
          border: 1px solid rgba(113, 130, 118, 0.55);
          color: #D3DDD5;
        }

        .rev-badge {
          background: rgba(199, 154, 74, 0.2);
          border: 1px solid rgba(199, 154, 74, 0.45);
          color: #E6CCA0;
          font-family: var(--font-mono, monospace);
          font-weight: 600;
          font-size: 11px;
        }

        .icon-pulse {
          animation: pulse-rose 2s infinite ease-in-out;
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .action-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 7px 14px;
          border-radius: var(--radius-sm);
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition-fast);
          font-family: var(--font-sans);
          border: none;
        }

        .action-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          pointer-events: none;
        }

        .outline-btn {
          background: rgba(255, 255, 255, 0.07);
          color: var(--pearl);
          border: 1px solid rgba(255, 255, 255, 0.16);
        }

        .outline-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.13);
          border-color: rgba(255, 255, 255, 0.3);
        }

        .primary-deploy-btn {
          background: var(--burgundy);
          color: var(--white);
          border: 1px solid rgba(182, 138, 154, 0.3);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }

        .primary-deploy-btn:hover:not(:disabled) {
          background: var(--burgundy-hover);
          border-color: var(--rose);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(84, 27, 59, 0.4);
        }

        @media (max-width: 900px) {
          .auctor-header {
            padding: 0 16px;
            height: 54px;
          }

          .brand-tagline {
            display: none;
          }

          .engine-badge,
          .workflow-badge {
            display: none;
          }

          .header-status-group {
            display: flex;
            align-items: center;
          }
        }

        @media (max-width: 480px) {
          .auctor-header {
            padding: 0 12px;
          }

          .brand-name {
            font-size: 14px;
            letter-spacing: 1px;
          }

          .brand-monogram {
            width: 28px;
            height: 28px;
          }

          .monogram-letter {
            font-size: 15px;
          }

          .action-btn {
            padding: 5px 10px;
            font-size: 11px;
          }

          .action-btn span {
            display: inline;
          }
        }
      `}</style>
    </header>
  );
}
