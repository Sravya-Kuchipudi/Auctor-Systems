import React, { useState } from 'react';
import { useProject } from '../../context/ProjectContext';
import { AGENTS } from './agentData';
import AgentDesk from './AgentDesk';
import AgentActivityFeed from './AgentActivityFeed';
import { ChevronDown, ChevronUp, Users, Sparkles, MessageSquare, LayoutGrid } from 'lucide-react';

export default function LivingOffice() {
  const {
    agentStatuses,
    currentAgentIndex,
    currentAgentName,
    agentSnippets,
    isGenerating,
    orchestratorState,
    activityLog,
  } = useProject();

  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState('stations'); // 'stations' | 'activity'

  const latestEvent = activityLog && activityLog.length > 0 ? activityLog[activityLog.length - 1] : null;

  return (
    <div className={`living-office-container ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Studio Header Bar (White / Pearl with Burgundy accent) */}
      <div className="office-header-bar">
        <div className="office-header-title">
          <Users size={14} className="office-icon" />
          <span className="office-title font-serif">Living Office Studio</span>
          <span className="office-subtitle">· 8 Orchestrated Specialized Agents</span>

          {/* View Mode Toggle: Workstations vs Live Activity */}
          {!isCollapsed && (
            <div className="studio-tabs-toggle">
              <button
                type="button"
                className={`tab-btn ${activeTab === 'stations' ? 'active' : ''}`}
                onClick={() => setActiveTab('stations')}
                title="View 8 Agent Workstations"
              >
                <LayoutGrid size={11} />
                <span>Workstations</span>
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
                onClick={() => setActiveTab('activity')}
                title="View Live Agent Dialogues & Collaboration Stream"
              >
                <MessageSquare size={11} />
                <span>Live Activity</span>
                {activityLog.length > 0 && (
                  <span className="tab-badge">{activityLog.length}</span>
                )}
              </button>
            </div>
          )}
        </div>

        <div className="office-header-right">
          {isGenerating && (
            <span className="office-pipeline-status">
              <Sparkles size={12} className="icon-pulse" />
              <span>{orchestratorState?.statusText || `${currentAgentName} Agent working`}</span>
            </span>
          )}

          <button
            type="button"
            className="collapse-toggle-btn"
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? 'Expand Studio' : 'Collapse Studio'}
          >
            {isCollapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {/* Main Studio View Body */}
      {!isCollapsed && (
        <>
          {activeTab === 'activity' ? (
            <AgentActivityFeed
              activityLog={activityLog}
              isGenerating={isGenerating}
              orchestratorStatusText={orchestratorState?.statusText}
            />
          ) : (
            <div className="office-stations-wrapper">
              <div className="office-panorama-scroll">
                <div className="office-workstations-row">
                  {AGENTS.map((agent, i) => {
                    const status = agentStatuses[agent.backendName] || 'idle';
                    const isActive = status === 'working' || status === 'active';
                    const isCompleted = status === 'completed';
                    const snippet = agentSnippets[agent.backendName];

                    // Check if there is an active handoff signal traveling to this station
                    const isHandoffTarget = Boolean(
                      orchestratorState?.activeHandoff &&
                      orchestratorState.activeHandoff.toIndex === i
                    );
                    const hasIncomingSignal = isHandoffTarget || (isGenerating && i === currentAgentIndex && i > 0);

                    return (
                      <React.Fragment key={agent.id}>
                        {/* Subtle Communication Handoff Connector between stations */}
                        {i > 0 && (
                          <div
                            className={`workstation-connector ${
                              i <= currentAgentIndex || isCompleted ? 'connector-active' : ''
                            } ${isHandoffTarget ? 'connector-pulsing' : ''}`}
                          >
                            <div className="connector-line" />
                            {hasIncomingSignal && <span className="signal-orb" />}
                          </div>
                        )}

                        <AgentDesk
                          agent={agent}
                          status={status}
                          snippet={snippet}
                          isActive={isActive}
                          isCompleted={isCompleted}
                          hasIncomingSignal={hasIncomingSignal}
                        />
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>

              {/* Latest Live Dispatch Ticker */}
              {latestEvent && (
                <div className="studio-dispatch-ticker" onClick={() => setActiveTab('activity')}>
                  <span className="ticker-tag font-mono">LIVE STUDIO DISPATCH:</span>
                  <span className="ticker-actor font-serif">{latestEvent.fromName || latestEvent.from}:</span>
                  <span className="ticker-msg">{latestEvent.message}</span>
                  <span className="ticker-link">Open Dialogue Stream →</span>
                </div>
              )}
            </div>
          )}
        </>
      )}

      <style>{`
        .living-office-container {
          background: var(--pearl);
          border-top: 1px solid var(--border-light);
          display: flex;
          flex-direction: column;
          box-shadow: 0 -2px 10px rgba(32, 36, 58, 0.03);
          z-index: 20;
          transition: all var(--transition-fast);
        }

        .living-office-container.collapsed {
          height: 34px;
        }

        .office-header-bar {
          height: 34px;
          padding: 0 16px;
          background: var(--white);
          border-bottom: 1px solid var(--border-light);
          display: flex;
          align-items: center;
          justify-content: space-between;
          user-select: none;
        }

        .office-header-title {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .office-icon {
          color: var(--burgundy);
        }

        .office-title {
          font-size: 12.5px;
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: 0.3px;
        }

        .office-subtitle {
          font-size: 11px;
          color: var(--text-secondary);
        }

        .office-header-right {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .office-pipeline-status {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 11px;
          color: var(--burgundy);
          font-weight: 600;
        }

        .icon-pulse {
          color: var(--rose);
          animation: pulse-rose 1.5s infinite;
        }

        .collapse-toggle-btn {
          width: 22px;
          height: 22px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: 1px solid var(--border-light);
          border-radius: 4px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .collapse-toggle-btn:hover {
          background: var(--pearl);
          color: var(--burgundy);
          border-color: var(--rose);
        }

        .office-panorama-scroll {
          overflow-x: auto;
          overflow-y: hidden;
          padding: 10px 16px;
          background: var(--pearl);
        }

        .office-workstations-row {
          display: flex;
          align-items: center;
          gap: 0;
          min-width: max-content;
        }

        .workstation-connector {
          width: 22px;
          height: 2px;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          margin: 0 3px;
        }

        .connector-line {
          width: 100%;
          height: 1px;
          background: var(--border-medium);
          transition: all var(--transition-normal);
        }

        .workstation-connector.connector-active .connector-line {
          background: var(--sage);
        }

        .signal-orb {
          position: absolute;
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--gold);
          box-shadow: 0 0 6px var(--gold);
          animation: travel-signal 1.4s infinite ease-in-out;
        }

        .studio-tabs-toggle {
          display: flex;
          align-items: center;
          background: var(--pearl);
          border-radius: var(--radius-pill);
          padding: 2px;
          margin-left: 10px;
          gap: 2px;
        }

        .tab-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 3px 9px;
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-size: 11px;
          font-weight: 600;
          border-radius: var(--radius-pill);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .tab-btn:hover {
          color: var(--burgundy);
        }

        .tab-btn.active {
          background: var(--white);
          color: var(--burgundy);
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }

        .tab-badge {
          background: var(--burgundy);
          color: var(--white);
          font-size: 9px;
          font-weight: 700;
          padding: 1px 5px;
          border-radius: 9999px;
        }

        .office-stations-wrapper {
          display: flex;
          flex-direction: column;
        }

        .studio-dispatch-ticker {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 16px;
          background: var(--white);
          border-top: 1px solid var(--border-light);
          font-size: 11px;
          cursor: pointer;
          transition: background var(--transition-fast);
        }

        .studio-dispatch-ticker:hover {
          background: #FAF8F9;
        }

        .ticker-tag {
          font-size: 9px;
          font-weight: 700;
          color: var(--rose);
          letter-spacing: 0.8px;
          flex-shrink: 0;
        }

        .ticker-actor {
          font-weight: 700;
          color: var(--wine);
          flex-shrink: 0;
        }

        .ticker-msg {
          color: var(--text-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          flex: 1;
        }

        .ticker-link {
          font-size: 10px;
          font-weight: 600;
          color: var(--burgundy);
          flex-shrink: 0;
        }

        .connector-pulsing .connector-line {
          background: var(--gold) !important;
          height: 2px !important;
          box-shadow: 0 0 6px var(--gold);
        }

        @keyframes travel-signal {
          0% { left: 0%; opacity: 0.2; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
          100% { left: 100%; opacity: 0.2; transform: scale(0.8); }
        }
      `}</style>
    </div>
  );
}
