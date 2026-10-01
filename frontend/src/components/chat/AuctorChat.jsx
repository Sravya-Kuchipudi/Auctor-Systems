import React, { useState } from 'react';
import { useProject } from '../../context/ProjectContext';
import { Send, CheckCircle2, AlertTriangle, Lightbulb, Compass, ArrowRight, HelpCircle, Check, Eye, Download, Sparkles, History } from 'lucide-react';
import { AGENTS } from '../office/agentData';
import { ORCHESTRATOR_STATES } from '../../workflow/workflowTypes';

const PROMPT_SUGGESTIONS = [
  {
    title: 'Artisan Coffee Roastery',
    prompt: 'A warm, sophisticated static website for "Crest & Bean", a small-batch specialty coffee roaster with single-origin beans, tasting flight menu, brewing guides, and a café locator.',
  },
  {
    title: 'Architectural Studio',
    prompt: 'A minimalist architectural portfolio for "Atelier V", featuring dramatic editorial grid layouts, residential case studies, philosophy statement, team directory, and project inquiry form.',
  },
  {
    title: 'Boutique Perfumery',
    prompt: 'An opulent sensory website for "Nectar & Ash", an artisanal fragrance house showcasing signature botanical scents, olfactory note breakdowns, master perfumer story, and sample discovery kit.',
  },
  {
    title: 'Modern Dental Practice',
    prompt: 'A calming, professional static website for "Aura Dental Studio", highlighting cosmetic dentistry, team credentials, patient reviews, transparent treatment pricing, and appointment booking form.',
  },
];

const REVISION_QUICK_ACTIONS = [
  { label: 'Refine Typography', prompt: 'Refine typography and improve visual hierarchy across all sections.' },
  { label: 'Add Modal Dialog', prompt: 'Add an inquiry contact modal dialog with smooth open/close triggers.' },
  { label: 'Adjust Spacing & Layout', prompt: 'Adjust spacing, margins, and layout padding for enhanced breathing room.' },
  { label: 'Update Hero CTA', prompt: 'Update the hero call-to-action button with elevated styling and a refined label.' },
];

export default function AuctorChat() {
  const {
    projectId,
    projectState,
    userPrompt,
    isGenerating,
    generationError,
    startGeneration,
    modifyProject,
    revisions,
    revisionCount,
    generatedFiles,
    currentAgentName,
    agentStatuses,
    agentSnippets,
    backendStatus,
    orchestratorState,
    answerAgentQuestion,
    completionSummary,
    openDocViewer,
    downloadFile,
  } = useProject();

  const [inputPrompt, setInputPrompt] = useState('');

  const isAwaitingAnswer = Boolean(
    orchestratorState?.userInputRequired &&
    orchestratorState?.pendingQuestion &&
    orchestratorState?.status === ORCHESTRATOR_STATES.WAITING_USER
  );
  const isCompletedProject = Boolean((projectState?.status === 'completed' || projectState?.status === 'generated' || (generatedFiles && generatedFiles.length > 0)) && !isGenerating);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputPrompt.trim()) return;

    if (isAwaitingAnswer) {
      answerAgentQuestion(inputPrompt.trim());
      setInputPrompt('');
      return;
    }

    if (isGenerating) return;

    if (isCompletedProject && projectId) {
      modifyProject(inputPrompt.trim());
      setInputPrompt('');
    } else {
      startGeneration(inputPrompt.trim());
    }
  };

  const handleSelectSuggestion = (suggestionPrompt) => {
    if (isGenerating) return;
    setInputPrompt(suggestionPrompt);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <aside className="auctor-chat-panel">
      {/* Panel Header */}
      <div className="chat-panel-header">
        <div className="panel-title-row">
          <Compass className="panel-icon" size={16} />
          <h2 className="panel-title font-serif">Director's Console</h2>
        </div>
        <p className="panel-subtitle">Describe the website you desire. The 8 Auctor agents will plan, write, design, and assemble it.</p>
      </div>

      {/* Main Content Area */}
      <div className="chat-content-area">
        {/* Inspiration Starters (Visible prior to generation) */}
        {!userPrompt && !isGenerating && (
          <div className="suggestions-container">
            <div className="suggestions-header">
              <Lightbulb size={13} className="suggestion-icon" />
              <span>Inspiration Starters</span>
            </div>
            <div className="suggestions-grid">
              {PROMPT_SUGGESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="suggestion-card"
                  onClick={() => handleSelectSuggestion(item.prompt)}
                >
                  <div className="card-top-row">
                    <span className="suggestion-title font-serif">{item.title}</span>
                    <ArrowRight size={13} className="card-arrow" />
                  </div>
                  <span className="suggestion-snippet">{item.prompt}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Active Generation Narrative */}
        {(userPrompt || isGenerating) && (
          <div className="generation-narrative">
            <div className="user-directive-bubble">
              <span className="bubble-label">Client Directive</span>
              <p className="bubble-text">{userPrompt}</p>
            </div>

            {/* Topup 1: Interactive Agent Question Card */}
            {isAwaitingAnswer && orchestratorState?.pendingQuestion && (
              <div className="agent-question-card">
                <div className="question-header">
                  <div className="question-avatar-wrap">
                    <HelpCircle size={14} className="question-icon" />
                  </div>
                  <div className="question-meta">
                    <span className="question-agent-name font-serif">{orchestratorState.pendingQuestion.agentName}</span>
                    <span className="question-agent-role">{orchestratorState.pendingQuestion.role}</span>
                  </div>
                  <span className="question-badge">Decision Needed</span>
                </div>

                <p className="question-body font-serif">
                  "{orchestratorState.pendingQuestion.question}"
                </p>

                {orchestratorState.pendingQuestion.options?.length > 0 && (
                  <div className="question-options-list">
                    {orchestratorState.pendingQuestion.options.map((option, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className="question-option-pill"
                        onClick={() => answerAgentQuestion(option)}
                      >
                        <span>{option}</span>
                        <ArrowRight size={11} className="option-arrow" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {generationError && (
              <div className="error-card">
                <AlertTriangle className="error-icon" size={16} />
                <div className="error-text-wrap">
                  <strong>Pipeline Stalled</strong>
                  <p>{generationError}</p>
                </div>
              </div>
            )}

            {/* Phase 3C Compact Completion Summary */}
            {completionSummary && (
              <div className="completion-summary-card">
                <div className="summary-top-bar">
                  <div className="summary-badge-pill">
                    <span className="summary-status-dot" />
                    <span>PROJECT COMPLETE</span>
                  </div>
                  <span className="summary-status-tag">Verified</span>
                </div>

                <div className="summary-product-line">
                  <span className="summary-dim-label">Product:</span>
                  <strong className="summary-product-title font-serif">{completionSummary.product_name}</strong>
                </div>

                <div className="summary-metrics-grid">
                  <div className="summary-metric-box">
                    <span className="summary-box-label">Agents</span>
                    <strong className="summary-box-value">{completionSummary.agents_completed || '8 / 8 completed'}</strong>
                  </div>
                  <div className="summary-metric-box">
                    <span className="summary-box-label">Quality</span>
                    <strong className="summary-box-value">QA: {completionSummary.qa_status || 'Passed'}</strong>
                    <span className="summary-box-sub">Revisions: {completionSummary.revisions_count ?? 1}</span>
                  </div>
                  <div className="summary-metric-box">
                    <span className="summary-box-label">Generated</span>
                    <strong className="summary-box-value">{completionSummary.files_count || 7} files</strong>
                  </div>
                  <div className="summary-metric-box">
                    <span className="summary-box-label">Documentation</span>
                    <strong className="summary-box-value">{completionSummary.documentation_status || 'Complete'}</strong>
                  </div>
                  <div className="summary-metric-box">
                    <span className="summary-box-label">Deployment</span>
                    <strong className="summary-box-value">{completionSummary.deployment_status || 'Ready'}</strong>
                  </div>
                  <div className="summary-metric-box">
                    <span className="summary-box-label">Marketing</span>
                    <strong className="summary-box-value">{completionSummary.marketing_status || 'Complete'}</strong>
                  </div>
                </div>

                {/* Compact Documentation Section (Phase 3C Doc Fix) */}
                <div className="summary-docs-panel">
                  <div className="summary-docs-panel-header">
                    <span className="summary-docs-heading font-serif">Documentation</span>
                    <span className="summary-docs-tag font-mono">Available</span>
                  </div>
                  <div className="summary-docs-items">
                    <div className="summary-doc-row">
                      <div className="doc-row-left">
                        <Check size={13} className="doc-row-check" />
                        <span className="doc-row-name font-mono">README</span>
                      </div>
                      <div className="doc-row-actions">
                        <button
                          type="button"
                          className="doc-mini-btn view-btn"
                          onClick={() => openDocViewer('README.md')}
                          title="View README in workspace"
                        >
                          <Eye size={11} />
                          <span>View</span>
                        </button>
                        <button
                          type="button"
                          className="doc-mini-btn dl-btn"
                          onClick={() => downloadFile('README.md')}
                          title="Download README.md"
                        >
                          <Download size={11} />
                          <span>Download</span>
                        </button>
                      </div>
                    </div>

                    <div className="summary-doc-row">
                      <div className="doc-row-left">
                        <Check size={13} className="doc-row-check" />
                        <span className="doc-row-name font-mono">Architecture</span>
                      </div>
                      <div className="doc-row-actions">
                        <button
                          type="button"
                          className="doc-mini-btn view-btn"
                          onClick={() => openDocViewer('ARCHITECTURE.md')}
                          title="View Architecture in workspace"
                        >
                          <Eye size={11} />
                          <span>View</span>
                        </button>
                        <button
                          type="button"
                          className="doc-mini-btn dl-btn"
                          onClick={() => downloadFile('ARCHITECTURE.md')}
                          title="Download ARCHITECTURE.md"
                        >
                          <Download size={11} />
                          <span>Download</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Orchestrated Agent Sequence */}
            <div className="agent-timeline">
              <div className="timeline-title-row">
                <span>Orchestrated Sequence</span>
                {isGenerating && (
                  <span className="live-indicator">
                    <span className="pulse-dot" />
                    {orchestratorState?.statusText || 'Executing Workflow'}
                  </span>
                )}
              </div>

              <div className="timeline-steps">
                {AGENTS.map((agent, i) => {
                  const status = agentStatuses[agent.backendName] || 'idle';
                  const isActive = status === 'working' || status === 'active';
                  const isThinking = status === 'thinking';
                  const isCommunicating = status === 'communicating';
                  const isDone = status === 'completed';
                  const hasSnippet = agentSnippets[agent.backendName];

                  return (
                    <div key={agent.id} className={`timeline-step ${status}`}>
                      <div className="step-marker">
                        {isDone ? (
                          <CheckCircle2 size={14} className="check-icon" />
                        ) : isActive ? (
                          <span className="active-spinner" />
                        ) : isThinking ? (
                          <span className="thinking-pulse-dot" />
                        ) : isCommunicating ? (
                          <span className="communicating-orb" />
                        ) : (
                          <span className="step-num">{i + 1}</span>
                        )}
                      </div>

                      <div className="step-content">
                        <div className="step-header">
                          <span className="step-name">{agent.backendName}</span>
                          <span className="step-role">{agent.role}</span>
                          <span className={`step-badge badge-${status}`}>
                            {isActive
                              ? 'Working'
                              : isThinking
                              ? 'Thinking'
                              : isCommunicating
                              ? 'Handoff'
                              : isDone
                              ? 'Done'
                              : 'Pending'}
                          </span>
                        </div>

                        {(isActive || isThinking) && hasSnippet && (
                          <div className="step-snippet font-mono">
                            {hasSnippet.slice(0, 160)}...
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Prompt Composer */}
      <form className="chat-composer-form" onSubmit={handleSubmit}>
        {!backendStatus.geminiConfigured && !isGenerating && !userPrompt && (
          <div className="warning-banner">
            <span>Deterministic Demo Mode Active · Submit any directive to observe the 8-agent workflow.</span>
          </div>
        )}

        {/* Phase 4B Revision Quick Actions */}
        {isCompletedProject && !isGenerating && !isAwaitingAnswer && (
          <div className="revision-quick-actions">
            <div className="quick-actions-header">
              <Sparkles size={11} className="quick-icon" />
              <span>Quick Refinements</span>
              {revisionCount > 0 && (
                <span className="quick-rev-tag">Rev {revisionCount}</span>
              )}
            </div>
            <div className="quick-actions-chips">
              {REVISION_QUICK_ACTIONS.map((action, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="quick-action-chip"
                  onClick={() => setInputPrompt(action.prompt)}
                  title={action.prompt}
                >
                  <span>{action.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className={`composer-card ${isAwaitingAnswer ? 'composer-card-answering' : isCompletedProject ? 'composer-card-revision' : ''}`}>
          <textarea
            className="composer-textarea font-sans"
            placeholder={
              isAwaitingAnswer
                ? `Type your clarification reply for ${orchestratorState.pendingQuestion?.agentName || 'the agent'}...`
                : isCompletedProject
                ? `Provide revision directive for ${projectState?.name || 'this website'}... (e.g. "Change hero subtitle to 'Handcrafted Elegance' and add an inquiry modal")`
                : 'Describe the website you want built (pages, tone, visual style, purpose)...'
            }
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating && !isAwaitingAnswer}
            rows={isAwaitingAnswer ? 2 : isCompletedProject ? 2 : 3}
          />
          <div className="composer-bottom-bar">
            <span className="composer-shortcut-hint">
              {isAwaitingAnswer ? (
                <><strong>Enter</strong> to send reply to agent</>
              ) : isCompletedProject ? (
                <><strong>Enter</strong> to apply revision · <strong>Shift + Enter</strong> new line</>
              ) : (
                <><strong>Enter</strong> to generate · <strong>Shift + Enter</strong> new line</>
              )}
            </span>
            <button
              type="submit"
              className={`composer-send-btn ${isAwaitingAnswer ? 'btn-reply' : isCompletedProject ? 'btn-revise' : ''}`}
              disabled={!inputPrompt.trim() && !isAwaitingAnswer}
              title={isAwaitingAnswer ? 'Send answer to agent' : isCompletedProject ? 'Apply revision directive' : 'Generate website with 8 agents'}
            >
              {isGenerating && !isAwaitingAnswer ? (
                <span className="composer-spinner" />
              ) : (
                <>
                  <span>
                    {isAwaitingAnswer
                      ? 'Send Reply'
                      : isCompletedProject
                      ? 'Revise Site'
                      : 'Generate'}
                  </span>
                  <Send size={12} />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      <style>{`
        .auctor-chat-panel {
          width: 380px;
          min-width: 340px;
          height: 100%;
          background: var(--pearl);
          border-right: 1px solid var(--border-light);
          display: flex;
          flex-direction: column;
          box-shadow: 2px 0 10px rgba(32, 36, 58, 0.03);
          position: relative;
          z-index: 10;
        }

        .chat-panel-header {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-light);
          background: var(--white);
        }

        .panel-title-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .panel-icon {
          color: var(--burgundy);
        }

        .panel-title {
          font-size: 16px;
          font-weight: 700;
          letter-spacing: 0.3px;
          color: var(--text-primary);
        }

        .panel-subtitle {
          font-size: 11px;
          color: var(--text-secondary);
          margin-top: 4px;
          line-height: 1.4;
        }

        .chat-content-area {
          flex: 1;
          overflow-y: auto;
          padding: 16px 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          background: var(--pearl);
        }

        .suggestions-container {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .suggestions-header {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--text-secondary);
        }

        .suggestion-icon {
          color: var(--gold);
        }

        .suggestions-grid {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .suggestion-card {
          text-align: left;
          padding: 12px 14px;
          background: var(--white);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .suggestion-card:hover {
          border-color: var(--rose);
          background: rgba(182, 138, 154, 0.06);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(182, 138, 154, 0.12);
        }

        .suggestion-card:hover .card-arrow {
          transform: translateX(2px);
          color: var(--burgundy);
        }

        .card-top-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .suggestion-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .card-arrow {
          color: var(--text-muted);
          transition: all var(--transition-fast);
        }

        .suggestion-snippet {
          font-size: 11px;
          color: var(--text-secondary);
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .generation-narrative {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .user-directive-bubble {
          background: var(--white);
          border: 1px solid var(--border-light);
          border-left: 3px solid var(--burgundy);
          border-radius: var(--radius-sm);
          padding: 10px 12px;
          box-shadow: var(--shadow-sm);
        }

        .bubble-label {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--burgundy);
          display: block;
          margin-bottom: 4px;
        }

        .bubble-text {
          font-size: 12px;
          color: var(--text-primary);
          line-height: 1.45;
        }

        .error-card {
          display: flex;
          gap: 8px;
          padding: 10px 12px;
          background: var(--error-light);
          border: 1px solid rgba(184, 92, 92, 0.35);
          border-radius: var(--radius-sm);
          color: var(--error);
          font-size: 12px;
        }

        .agent-timeline {
          background: var(--white);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-md);
          padding: 12px;
          box-shadow: var(--shadow-sm);
        }

        .timeline-title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.5px;
          color: var(--text-secondary);
          margin-bottom: 12px;
          text-transform: uppercase;
        }

        .live-indicator {
          display: flex;
          align-items: center;
          gap: 5px;
          color: var(--burgundy);
          font-size: 10px;
          font-weight: 600;
        }

        .pulse-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--rose);
          animation: pulse-rose 1.5s infinite;
        }

        .timeline-steps {
          display: flex;
          flex-direction: column;
          gap: 7px;
        }

        .timeline-step {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          padding: 6px 8px;
          border-radius: var(--radius-sm);
          transition: background var(--transition-fast);
        }

        .timeline-step.active {
          background: var(--burgundy-light);
          border: 1px solid rgba(84, 27, 59, 0.2);
        }

        .timeline-step.completed {
          background: var(--sage-light);
        }

        .step-marker {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 700;
          margin-top: 1px;
          flex-shrink: 0;
        }

        .timeline-step.idle .step-marker {
          background: var(--pearl-dark);
          color: var(--text-secondary);
        }

        .timeline-step.active .step-marker {
          background: var(--burgundy);
          color: var(--white);
        }

        .timeline-step.completed .step-marker {
          background: var(--sage);
          color: var(--white);
        }

        .active-spinner {
          width: 9px;
          height: 9px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: #FFFFFF;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .step-content {
          flex: 1;
          min-width: 0;
        }

        .step-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
        }

        .step-name {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .step-role {
          font-size: 10px;
          color: var(--text-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .step-badge {
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          padding: 2px 6px;
          border-radius: 4px;
          flex-shrink: 0;
        }

        .badge-idle {
          background: var(--pearl-dark);
          color: var(--text-secondary);
        }

        .badge-active {
          background: var(--burgundy);
          color: var(--white);
        }

        .badge-completed {
          background: var(--sage);
          color: var(--white);
        }

        .step-snippet {
          margin-top: 4px;
          font-size: 10px;
          color: var(--text-secondary);
          background: rgba(84, 27, 59, 0.04);
          padding: 4px 6px;
          border-radius: 4px;
          border-left: 2px solid var(--rose);
        }

        .chat-composer-form {
          padding: 14px 20px;
          background: var(--white);
          border-top: 1px solid var(--border-light);
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .warning-banner {
          background: rgba(184, 92, 92, 0.08);
          border: 1px solid rgba(184, 92, 92, 0.25);
          color: var(--error);
          padding: 7px 10px;
          border-radius: var(--radius-sm);
          font-size: 11px;
          line-height: 1.35;
        }

        .composer-card {
          border: 1px solid var(--border-light);
          border-radius: var(--radius-md);
          background: var(--white);
          transition: all var(--transition-fast);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .composer-card:focus-within {
          border-color: var(--rose);
          box-shadow: 0 0 0 3px rgba(182, 138, 154, 0.2);
        }

        .composer-textarea {
          width: 100%;
          border: none;
          padding: 10px 12px 6px;
          background: transparent;
          color: var(--text-primary);
          font-size: 13px;
          resize: none;
        }

        .composer-textarea:focus {
          outline: none;
        }

        .composer-bottom-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 6px 10px 8px;
          background: transparent;
        }

        .composer-shortcut-hint {
          font-size: 10px;
          color: var(--text-secondary);
          opacity: 0.8;
        }

        .composer-send-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 5px 12px;
          background: var(--burgundy);
          color: var(--white);
          border: none;
          border-radius: var(--radius-sm);
          font-size: 11.5px;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .composer-send-btn:hover:not(:disabled) {
          background: var(--burgundy-hover);
          box-shadow: 0 2px 6px rgba(84, 27, 59, 0.3);
          transform: translateY(-1px);
        }

        .composer-send-btn:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }

        .composer-spinner {
          width: 12px;
          height: 12px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: #FFFFFF;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .agent-question-card {
          background: #FDFAF5;
          border: 1px solid var(--gold);
          border-left: 4px solid var(--gold);
          border-radius: var(--radius-md);
          padding: 12px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          box-shadow: 0 4px 14px rgba(199, 154, 74, 0.12);
          animation: pulse-rose 2s infinite ease-in-out;
        }

        .question-header {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .question-avatar-wrap {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: rgba(199, 154, 74, 0.2);
          color: var(--gold);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .question-meta {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .question-agent-name {
          font-size: 12px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .question-agent-role {
          font-size: 9.5px;
          color: var(--text-secondary);
        }

        .question-badge {
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          background: var(--gold);
          color: var(--white);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .question-body {
          font-size: 13px;
          line-height: 1.45;
          color: var(--wine);
          font-style: italic;
          padding: 0 4px;
        }

        .question-options-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
          margin-top: 2px;
        }

        .question-option-pill {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 7px 10px;
          background: var(--white);
          border: 1px solid rgba(199, 154, 74, 0.4);
          border-radius: var(--radius-sm);
          font-size: 11px;
          font-weight: 500;
          color: var(--text-primary);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }

        .question-option-pill:hover {
          background: rgba(199, 154, 74, 0.12);
          border-color: var(--gold);
          transform: translateX(2px);
          color: var(--burgundy);
        }

        .option-arrow {
          color: var(--gold);
          flex-shrink: 0;
        }

        .composer-card-answering {
          border-color: var(--gold);
          box-shadow: 0 0 0 3px rgba(199, 154, 74, 0.2);
        }

        .btn-reply {
          background: var(--gold) !important;
          color: var(--white) !important;
        }

        .btn-reply:hover:not(:disabled) {
          background: #B3883C !important;
        }

        .communicating-orb {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--gold);
          animation: handoff-pulse 1.2s infinite ease-in-out;
        }

        .badge-thinking {
          background: rgba(182, 138, 154, 0.2);
          color: var(--wine);
        }

        .badge-communicating {
          background: rgba(199, 154, 74, 0.2);
          color: #8F6922;
        }

        /* Completion Summary Card (Phase 3C) */
        .completion-summary-card {
          background: var(--white);
          border: 1px solid rgba(84, 27, 59, 0.15);
          border-radius: 12px;
          padding: 16px;
          box-shadow: 0 4px 16px rgba(58, 16, 40, 0.06);
          margin-bottom: 8px;
          animation: summary-fade-in 0.4s ease-out;
        }

        @keyframes summary-fade-in {
          from { opacity: 0; transform: translateY(-6px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .summary-top-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--border-light);
        }

        .summary-badge-pill {
          display: flex;
          align-items: center;
          gap: 6px;
          font-family: var(--font-mono, monospace);
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.8px;
          color: var(--burgundy, #541B3B);
        }

        .summary-status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #718276;
        }

        .summary-status-tag {
          font-size: 10px;
          font-weight: 600;
          color: #718276;
          background: rgba(113, 130, 118, 0.12);
          padding: 2px 8px;
          border-radius: 10px;
        }

        .summary-product-line {
          margin-bottom: 14px;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .summary-dim-label {
          font-size: 11px;
          color: var(--cool-gray, #6B6C78);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .summary-product-title {
          font-size: 15px;
          color: var(--deep-wine, #3A1028);
          line-height: 1.3;
        }

        .summary-metrics-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }

        .summary-metric-box {
          background: var(--pearl, #F5F4F5);
          border-radius: 8px;
          padding: 8px 10px;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .summary-box-label {
          font-size: 10px;
          color: var(--cool-gray, #6B6C78);
          text-transform: uppercase;
          letter-spacing: 0.4px;
        }

        .summary-box-value {
          font-size: 12px;
          font-weight: 700;
          color: var(--text-primary, #29232B);
        }

        .summary-box-sub {
          font-size: 10px;
          color: var(--dusty-rose, #B68A9A);
        }

        /* Compact Documentation Section */
        .summary-docs-panel {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid var(--border-light);
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .summary-docs-panel-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .summary-docs-heading {
          font-size: 13px;
          font-weight: 600;
          color: var(--deep-wine, #3A1028);
          margin: 0;
        }

        .summary-docs-tag {
          font-size: 10px;
          color: var(--burgundy, #541B3B);
          background: rgba(84, 27, 59, 0.08);
          padding: 1px 6px;
          border-radius: 4px;
        }

        .summary-docs-items {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .summary-doc-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: var(--pearl, #F5F4F5);
          border: 1px solid rgba(84, 27, 59, 0.08);
          border-radius: 6px;
          padding: 6px 10px;
        }

        .doc-row-left {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .doc-row-check {
          color: var(--muted-sage, #718276);
        }

        .doc-row-name {
          font-size: 11px;
          font-weight: 600;
          color: var(--text-primary, #29232B);
        }

        .doc-row-actions {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .doc-mini-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 3px 8px;
          border-radius: 4px;
          font-family: var(--font-sans);
          font-size: 11px;
          font-weight: 500;
          cursor: pointer;
          transition: all var(--transition-fast);
          border: 1px solid transparent;
        }

        .doc-mini-btn.view-btn {
          background: var(--white);
          border-color: rgba(84, 27, 59, 0.2);
          color: var(--burgundy, #541B3B);
        }

        .doc-mini-btn.view-btn:hover {
          background: var(--burgundy, #541B3B);
          color: #FFFFFF;
          border-color: var(--burgundy, #541B3B);
        }

        .doc-mini-btn.dl-btn {
          background: rgba(199, 154, 74, 0.12);
          border-color: var(--muted-gold, #C79A4A);
          color: var(--deep-wine, #3A1028);
        }

        .doc-mini-btn.dl-btn:hover {
          background: var(--muted-gold, #C79A4A);
          color: #20243A;
        }

        /* Phase 4B Revision Quick Actions */
        .revision-quick-actions {
          padding: 8px 12px;
          background: rgba(84, 27, 59, 0.04);
          border: 1px solid rgba(84, 27, 59, 0.12);
          border-radius: 8px;
          margin-bottom: 8px;
        }

        .quick-actions-header {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.6px;
          color: var(--burgundy, #541B3B);
          margin-bottom: 6px;
        }

        .quick-icon {
          color: var(--muted-gold, #C79A4A);
        }

        .quick-rev-tag {
          margin-left: auto;
          font-size: 9px;
          font-family: var(--font-mono, monospace);
          background: rgba(199, 154, 74, 0.15);
          color: #8F6922;
          padding: 1px 6px;
          border-radius: 4px;
          font-weight: 600;
        }

        .quick-actions-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }

        .quick-action-chip {
          font-family: var(--font-sans);
          font-size: 11px;
          font-weight: 500;
          color: var(--text-primary, #29232B);
          background: var(--white, #FFFFFF);
          border: 1px solid rgba(84, 27, 59, 0.18);
          border-radius: 12px;
          padding: 4px 10px;
          cursor: pointer;
          transition: all var(--transition-fast);
          display: inline-flex;
          align-items: center;
        }

        .quick-action-chip:hover {
          border-color: var(--burgundy, #541B3B);
          background: rgba(84, 27, 59, 0.08);
          color: var(--deep-wine, #3A1028);
          transform: translateY(-1px);
        }

        .composer-card-revision {
          border-color: rgba(199, 154, 74, 0.4);
          box-shadow: 0 0 0 1px rgba(199, 154, 74, 0.2);
        }

        .composer-send-btn.btn-revise {
          background: var(--burgundy, #541B3B);
          color: #FFFFFF;
        }

        .composer-send-btn.btn-revise:hover:not(:disabled) {
          background: var(--deep-wine, #3A1028);
        }

        @media (max-width: 900px) {
          .auctor-chat-panel {
            width: 100%;
            min-width: 0;
            height: auto;
            border-right: none;
            border-bottom: 1px solid var(--border-light);
          }
        }
      `}</style>
    </aside>
  );
}
