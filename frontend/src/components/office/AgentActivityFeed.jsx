import React, { useRef, useEffect } from 'react';
import { ArrowRight, Sparkles, MessageSquare, CheckCircle2, AlertTriangle, Radio } from 'lucide-react';

export default function AgentActivityFeed({ activityLog = [], isGenerating, orchestratorStatusText }) {
  const feedEndRef = useRef(null);

  useEffect(() => {
    if (feedEndRef.current) {
      feedEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activityLog.length]);

  const renderEventIcon = (type, status) => {
    switch (type) {
      case 'handoff':
        return <Radio size={12} className="type-icon handoff-icon" />;
      case 'question':
      case 'answer':
      case 'dialogue':
        return <MessageSquare size={12} className="type-icon dialogue-icon" />;
      case 'review':
        return <AlertTriangle size={12} className="type-icon review-icon" />;
      case 'completed':
        return <CheckCircle2 size={12} className="type-icon completed-icon" />;
      default:
        return <Sparkles size={12} className="type-icon working-icon" />;
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'completed':
        return 'badge-sage';
      case 'working':
        return 'badge-burgundy';
      case 'communicating':
        return 'badge-gold';
      case 'thinking':
        return 'badge-rose';
      case 'error':
        return 'badge-error';
      default:
        return 'badge-idle';
    }
  };

  return (
    <div className="agent-activity-feed-container">
      {/* Feed Sub-Header */}
      <div className="activity-feed-header">
        <div className="feed-header-left">
          <span className="live-dot-pulse" />
          <span className="feed-header-title">Studio Activity & Dialogue Stream</span>
        </div>
        <span className="feed-events-count font-mono">{activityLog.length} events logged</span>
      </div>

      {/* Events List */}
      <div className="activity-events-scroll">
        {activityLog.length === 0 ? (
          <div className="empty-activity-state">
            <MessageSquare size={20} className="empty-icon" />
            <p>Studio is quiet. Describe your website in the Director's Console to initiate the 8-agent collaboration.</p>
          </div>
        ) : (
          <div className="activity-items-list">
            {activityLog.map((event) => {
              const isHandoff = event.type === 'handoff';
              const isReview = event.type === 'review';
              const isQuestion = event.type === 'question';

              return (
                <div
                  key={event.id}
                  className={`activity-event-card ${event.type} ${isHandoff ? 'card-handoff' : ''} ${isReview ? 'card-review' : ''}`}
                >
                  <div className="event-meta-row">
                    <div className="meta-actors">
                      {renderEventIcon(event.type, event.status)}
                      <span className="actor-from font-serif">{event.fromName || event.from}</span>
                      {event.toName && (
                        <>
                          <ArrowRight size={10} className="handoff-arrow" />
                          <span className="actor-to font-serif">{event.toName}</span>
                        </>
                      )}
                    </div>

                    <div className="meta-right">
                      <span className={`status-pill ${getStatusBadgeClass(event.status)}`}>
                        {event.status}
                      </span>
                      <span className="event-time font-mono">{event.timestamp}</span>
                    </div>
                  </div>

                  <div className="event-body-text">
                    <p>{event.message}</p>
                  </div>
                </div>
              );
            })}
            <div ref={feedEndRef} />
          </div>
        )}
      </div>

      <style>{`
        .agent-activity-feed-container {
          display: flex;
          flex-direction: column;
          height: 180px;
          background: var(--pearl);
          border-top: 1px solid var(--border-light);
          overflow: hidden;
        }

        .activity-feed-header {
          height: 30px;
          padding: 0 16px;
          background: var(--white);
          border-bottom: 1px solid var(--border-light);
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 11px;
        }

        .feed-header-left {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .live-dot-pulse {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--rose);
          animation: pulse-rose 1.5s infinite;
        }

        .feed-header-title {
          font-weight: 600;
          color: var(--text-primary);
          letter-spacing: 0.2px;
        }

        .feed-events-count {
          font-size: 10px;
          color: var(--text-secondary);
        }

        .activity-events-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 8px 16px;
        }

        .empty-activity-state {
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 6px;
          color: var(--text-secondary);
          font-size: 11.5px;
          text-align: center;
          padding: 12px;
        }

        .empty-icon {
          color: var(--rose);
          opacity: 0.6;
        }

        .activity-items-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .activity-event-card {
          background: var(--white);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-sm);
          padding: 8px 10px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          transition: all var(--transition-fast);
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        }

        .activity-event-card.card-handoff {
          border-left: 3px solid var(--gold);
          background: #FDFAF5;
        }

        .activity-event-card.card-review {
          border-left: 3px solid var(--error);
          background: #FCF8F8;
        }

        .event-meta-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }

        .meta-actors {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 11px;
        }

        .type-icon {
          flex-shrink: 0;
        }

        .handoff-icon { color: var(--gold); }
        .dialogue-icon { color: var(--rose); }
        .review-icon { color: var(--error); }
        .completed-icon { color: var(--sage); }
        .working-icon { color: var(--burgundy); }

        .actor-from, .actor-to {
          font-weight: 700;
          color: var(--text-primary);
        }

        .handoff-arrow {
          color: var(--text-secondary);
        }

        .meta-right {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .status-pill {
          font-size: 8.5px;
          font-weight: 700;
          text-transform: uppercase;
          padding: 1px 5px;
          border-radius: 3px;
        }

        .badge-sage {
          background: rgba(113, 130, 118, 0.15);
          color: var(--sage);
        }

        .badge-burgundy {
          background: var(--burgundy);
          color: var(--white);
        }

        .badge-gold {
          background: rgba(199, 154, 74, 0.18);
          color: #8F6922;
        }

        .badge-rose {
          background: rgba(182, 138, 154, 0.18);
          color: var(--wine);
        }

        .badge-error {
          background: rgba(184, 92, 92, 0.15);
          color: var(--error);
        }

        .badge-idle {
          background: var(--pearl-dark);
          color: var(--text-secondary);
        }

        .event-time {
          font-size: 9.5px;
          color: var(--text-secondary);
        }

        .event-body-text {
          font-size: 11.5px;
          color: var(--text-primary);
          line-height: 1.4;
        }
      `}</style>
    </div>
  );
}
