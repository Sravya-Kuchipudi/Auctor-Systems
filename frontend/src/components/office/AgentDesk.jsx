import React from 'react';
import { CheckCircle2, Sparkles, Radio } from 'lucide-react';

export default function AgentDesk({ agent, status, snippet, isActive, isCompleted, hasIncomingSignal }) {
  // SVG illustrations preserving natural character details with Palette 4 workstation accents
  const renderWorkstationIllustration = () => {
    switch (agent.id) {
      case 'planning':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Background Studio Wall & Blueprint Board */}
            <rect x="15" y="10" width="130" height="40" rx="3" fill="#FAF9FA" stroke="#E2DFE3" strokeWidth="1" />
            <line x1="25" y1="20" x2="65" y2="20" stroke="#3A1028" strokeWidth="1.5" strokeDasharray="3 2" />
            <line x1="25" y1="28" x2="85" y2="28" stroke="#3A1028" strokeWidth="1.5" />
            <rect x="95" y="18" width="40" height="24" rx="2" fill="#FFFFFF" stroke="#D8D5DA" />
            <circle cx="102" cy="24" r="2" fill="#C79A4A" />
            <line x1="108" y1="24" x2="128" y2="24" stroke="#6B6C78" strokeWidth="1" />

            {/* Victoria: Seated at Desk with Tweed Vest & Hair Bun */}
            <circle cx="80" cy="42" r="11" fill="#E8C39E" />
            <circle cx="80" cy="36" r="12" fill="#422817" />
            <path d="M72 40 Q80 32 88 40" stroke="#422817" strokeWidth="3" fill="none" />
            <path d="M66 53 L94 53 L90 75 L70 75 Z" fill="#541B3B" /> {/* Burgundy Vest */}
            <path d="M74 53 L80 63 L86 53 Z" fill="#FFFFFF" />

            {/* Walnut Drafting Table */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#8C5835" />
            <rect x="25" y="85" width="6" height="22" fill="#6B3E1F" />
            <rect x="129" y="85" width="6" height="22" fill="#6B3E1F" />

            {/* Drafting Tools */}
            <path d="M30 68 L60 74 L40 75 Z" fill="#FFFFFF" stroke="#3A1028" strokeWidth="0.8" />
            <circle cx="120" cy="71" r="5" fill="#FAF9FA" stroke="#C79A4A" strokeWidth="1" />
            <line x1="95" y1="73" x2="110" y2="67" stroke="#C79A4A" strokeWidth="1.5" />
          </svg>
        );

      case 'requirements':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Cork Pinboard & Colored Sticky Matrix */}
            <rect x="15" y="10" width="130" height="40" rx="3" fill="#EAE5DC" stroke="#D3CABE" strokeWidth="1" />
            <rect x="25" y="16" width="16" height="14" fill="#FDF3B0" />
            <rect x="45" y="16" width="16" height="14" fill="#E4EBF4" />
            <rect x="65" y="16" width="16" height="14" fill="#F4ECF1" />
            <rect x="85" y="16" width="22" height="26" fill="#FFFFFF" stroke="#B0ACB3" strokeWidth="0.5" />

            {/* Beatrice: Forest Cardigan & Spectacles */}
            <circle cx="80" cy="43" r="11" fill="#EDCBB1" />
            <path d="M68 38 Q80 28 92 38" fill="#2E1C0C" />
            <circle cx="76" cy="43" r="2.5" stroke="#C79A4A" strokeWidth="1" fill="none" />
            <circle cx="84" cy="43" r="2.5" stroke="#C79A4A" strokeWidth="1" fill="none" />
            <line x1="78.5" y1="43" x2="81.5" y2="43" stroke="#C79A4A" strokeWidth="1" />
            <path d="M65 54 L95 54 L91 75 L69 75 Z" fill="#2C4C38" />

            {/* Oak Analysis Desk */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#A06D3B" />
            <rect x="25" y="85" width="6" height="22" fill="#7D4F24" />
            <rect x="129" y="85" width="6" height="22" fill="#7D4F24" />

            {/* Open Spec Ledger & Glass */}
            <rect x="45" y="69" width="30" height="6" fill="#FFFFFF" stroke="#4D4548" strokeWidth="0.8" />
            <circle cx="120" cy="72" r="4" fill="#E6EEF5" stroke="#3D5A80" />
          </svg>
        );

      case 'design':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Swatch Moodboard & Palette 4 Color Tiles */}
            <rect x="15" y="8" width="130" height="42" rx="3" fill="#FAF9FA" stroke="#E2DFE3" strokeWidth="1" />
            <rect x="25" y="14" width="10" height="12" fill="#3A1028" /> {/* Deep Wine */}
            <rect x="38" y="14" width="10" height="12" fill="#541B3B" /> {/* Burgundy */}
            <rect x="51" y="14" width="10" height="12" fill="#B68A9A" /> {/* Dusty Rose */}
            <rect x="64" y="14" width="10" height="12" fill="#20243A" /> {/* Midnight Navy */}
            <rect x="90" y="14" width="45" height="28" fill="#FFFFFF" stroke="#D8D5DA" />
            <circle cx="102" cy="22" r="4" fill="#B68A9A" />

            {/* Clara: Plum Knitwear & Chic Bob Cut */}
            <circle cx="80" cy="42" r="11" fill="#E5BFA3" />
            <path d="M68 36 Q80 26 92 36 L92 46 L68 46 Z" fill="#1C1318" />
            <path d="M65 53 L95 53 L91 75 L69 75 Z" fill="#541B3B" />

            {/* Birch Atelier Table */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#CBB69D" />
            <rect x="25" y="85" width="6" height="22" fill="#9F886F" />
            <rect x="129" y="85" width="6" height="22" fill="#9F886F" />

            {/* Stylus Tablet & Dried Botanical Branch */}
            <rect x="42" y="68" width="28" height="7" rx="1" fill="#20243A" />
            <path d="M115 75 Q120 62 125 58" stroke="#718276" strokeWidth="1.5" fill="none" />
            <circle cx="125" cy="58" r="2.5" fill="#718276" />
          </svg>
        );

      case 'development':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Dual Glow Monitors (Midnight Navy Frame #20243A) */}
            <rect x="20" y="15" width="48" height="34" rx="2" fill="#20243A" stroke="#273049" strokeWidth="1.5" />
            <rect x="23" y="18" width="42" height="28" fill="#161827" />
            <line x1="26" y1="22" x2="45" y2="22" stroke="#B68A9A" strokeWidth="1" />
            <line x1="26" y1="26" x2="56" y2="26" stroke="#718276" strokeWidth="1" />
            <line x1="26" y1="30" x2="50" y2="30" stroke="#C79A4A" strokeWidth="1" />

            <rect x="74" y="15" width="48" height="34" rx="2" fill="#20243A" stroke="#273049" strokeWidth="1.5" />
            <rect x="77" y="18" width="42" height="28" fill="#161827" />
            <line x1="80" y1="22" x2="105" y2="22" stroke="#E29578" strokeWidth="1" />
            <line x1="80" y1="26" x2="115" y2="26" stroke="#F5F4F5" strokeWidth="1" />

            {/* Maya: Black Turtleneck */}
            <circle cx="70" cy="46" r="10" fill="#E8C39E" />
            <path d="M60 40 Q70 30 80 40 L80 46 L60 46 Z" fill="#181414" />
            <path d="M58 56 L82 56 L80 75 L60 75 Z" fill="#20243A" />

            {/* Industrial Steel & Walnut Desk */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#4D3B31" />
            <rect x="25" y="85" width="6" height="22" fill="#273049" />
            <rect x="129" y="85" width="6" height="22" fill="#273049" />

            {/* Mechanical Keyboard & Espresso */}
            <rect x="52" y="70" width="36" height="5" rx="1" fill="#273049" />
            <circle cx="120" cy="72" r="4" fill="#FFFFFF" stroke="#C79A4A" strokeWidth="0.8" />
            <circle cx="120" cy="72" r="2.5" fill="#3A1028" />
          </svg>
        );

      case 'testing':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Audit Chart & Compliance Benchmark Display */}
            <rect x="15" y="10" width="130" height="40" rx="3" fill="#FAF9FA" stroke="#E2DFE3" strokeWidth="1" />
            <circle cx="40" cy="30" r="12" stroke="#718276" strokeWidth="2.5" fill="none" />
            <text x="35" y="34" fill="#718276" fontSize="9" fontWeight="bold">98</text>
            <line x1="65" y1="22" x2="125" y2="22" stroke="#718276" strokeWidth="2" />
            <line x1="65" y1="30" x2="110" y2="30" stroke="#718276" strokeWidth="2" />
            <line x1="65" y1="38" x2="118" y2="38" stroke="#718276" strokeWidth="2" />

            {/* Astrid: Structured Navy Blazer & Blonde Chignon */}
            <circle cx="80" cy="42" r="11" fill="#F5D0B5" />
            <circle cx="80" cy="36" r="11" fill="#E6C875" />
            <path d="M66 53 L94 53 L90 75 L70 75 Z" fill="#20243A" /> {/* Midnight Navy Blazer */}
            <path d="M75 53 L80 62 L85 53 Z" fill="#FFFFFF" />

            {/* Audit Workstation Table */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#7C6352" />
            <rect x="25" y="85" width="6" height="22" fill="#594435" />
            <rect x="129" y="85" width="6" height="22" fill="#594435" />

            {/* Inspection Magnifier & Stamp */}
            <circle cx="50" cy="71" r="5" fill="none" stroke="#20243A" strokeWidth="1.5" />
            <line x1="53.5" y1="74.5" x2="58" y2="79" stroke="#20243A" strokeWidth="2" />
            <circle cx="120" cy="71" r="4.5" fill="#718276" />
          </svg>
        );

      case 'documentation':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Library Bookshelf Backdrop */}
            <rect x="15" y="8" width="130" height="42" rx="3" fill="#FAF9FA" stroke="#E2DFE3" strokeWidth="1" />
            <rect x="22" y="14" width="8" height="28" fill="#3A1028" />
            <rect x="31" y="16" width="6" height="26" fill="#718276" />
            <rect x="38" y="14" width="10" height="28" fill="#20243A" />
            <rect x="105" y="14" width="30" height="30" fill="#FFFFFF" stroke="#D8D5DA" strokeWidth="0.8" />
            <line x1="110" y1="20" x2="130" y2="20" stroke="#29232B" strokeWidth="1" />
            <line x1="110" y1="25" x2="125" y2="25" stroke="#6B6C78" strokeWidth="1" />

            {/* Genevieve: Cream Wool Sweater & Velvet Headband */}
            <circle cx="80" cy="42" r="11" fill="#E8C39E" />
            <path d="M68 36 Q80 26 92 36" fill="#54311C" />
            <path d="M70 33 Q80 28 90 33" stroke="#3A1028" strokeWidth="2.5" fill="none" />
            <path d="M65 53 L95 53 L91 75 L69 75 Z" fill="#FFFFFF" stroke="#E2DFE3" strokeWidth="1" />

            {/* Antique Mahogany Writing Desk */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#5E2B1E" />
            <rect x="25" y="85" width="6" height="22" fill="#421E15" />
            <rect x="129" y="85" width="6" height="22" fill="#421E15" />

            {/* Leather Bound Journal & Fountain Pen */}
            <rect x="45" y="69" width="30" height="6" fill="#541B3B" stroke="#C79A4A" strokeWidth="0.5" />
            <line x1="80" y1="71" x2="95" y2="67" stroke="#C79A4A" strokeWidth="1.2" />
          </svg>
        );

      case 'deployment':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Server Rack & Telemetry Console in Midnight Navy */}
            <rect x="15" y="10" width="130" height="40" rx="3" fill="#20243A" stroke="#273049" strokeWidth="1" />
            <rect x="22" y="16" width="32" height="28" fill="#161827" />
            <circle cx="28" cy="22" r="1.5" fill="#718276" />
            <circle cx="34" cy="22" r="1.5" fill="#718276" />
            <circle cx="40" cy="22" r="1.5" fill="#B68A9A" />
            <circle cx="28" cy="28" r="1.5" fill="#718276" />
            <circle cx="34" cy="28" r="1.5" fill="#718276" />
            <circle cx="40" cy="28" r="1.5" fill="#718276" />

            <path d="M75 30 L95 18 L115 30 Z" fill="none" stroke="#B68A9A" strokeWidth="1.5" />

            {/* Nadia: Slate Work Shirt & Sleek Ponytail */}
            <circle cx="70" cy="44" r="10.5" fill="#E5BA98" />
            <path d="M60 38 Q70 28 80 38 L84 32 L86 42" fill="#1F1B1C" />
            <path d="M58 55 L82 55 L80 75 L60 75 Z" fill="#273049" />

            {/* Modular Terminal Console */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#3D444F" />
            <rect x="25" y="85" width="6" height="22" fill="#20243A" />
            <rect x="129" y="85" width="6" height="22" fill="#20243A" />

            {/* Network Console & Pulse Antenna */}
            <rect x="42" y="68" width="28" height="7" fill="#1C1F24" stroke="#718276" strokeWidth="0.8" />
            <line x1="125" y1="75" x2="125" y2="55" stroke="#CBD5E0" strokeWidth="1.5" />
            <circle cx="125" cy="55" r="3" fill="#C79A4A" className="animate-glow" />
          </svg>
        );

      case 'marketing':
        return (
          <svg className="desk-svg" viewBox="0 0 160 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Campaign Moodboard & Social Wave */}
            <rect x="15" y="8" width="130" height="42" rx="3" fill="#FAF9FA" stroke="#E2DFE3" strokeWidth="1" />
            <rect x="25" y="14" width="25" height="30" fill="#3A1028" />
            <text x="29" y="32" fill="#FFFFFF" fontSize="9" fontWeight="bold" fontFamily="serif">VOGUE</text>
            <path d="M60 30 Q70 18 80 30 T100 30" stroke="#B68A9A" strokeWidth="1.5" fill="none" />
            <circle cx="120" cy="24" r="10" fill="#F4ECF1" />
            <text x="114" y="27" fill="#541B3B" fontSize="8" fontWeight="bold">LAUNCH</text>

            {/* Sophia: Burgundy Trench & Silk Scarf */}
            <circle cx="80" cy="42" r="11" fill="#E8C39E" />
            <path d="M68 34 Q80 24 92 34 L94 48 L66 48 Z" fill="#2A1810" />
            <circle cx="68" cy="44" r="2.5" fill="#C79A4A" />
            <path d="M65 53 L95 53 L91 75 L69 75 Z" fill="#541B3B" />
            <path d="M74 53 L80 61 L86 53 Z" fill="#E5C3A6" />

            {/* Rosewood Launch Desk */}
            <path d="M10 75 L150 75 L145 85 L15 85 Z" fill="#6E333F" />
            <rect x="25" y="85" width="6" height="22" fill="#4A202A" />
            <rect x="129" y="85" width="6" height="22" fill="#4A202A" />

            {/* Retro Ribbon Mic & Bell */}
            <ellipse cx="45" cy="70" rx="3" ry="5" fill="#CBD5E0" stroke="#4A5568" />
            <line x1="45" y1="75" x2="45" y2="78" stroke="#4A5568" strokeWidth="1.5" />
            <circle cx="120" cy="72" r="4" fill="#C79A4A" />
          </svg>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`agent-desk-card ${status} ${isActive ? 'is-active' : ''} ${isCompleted ? 'is-completed' : ''} ${hasIncomingSignal ? 'incoming-signal' : ''}`}>
      {/* Station Title & Status Pill */}
      <div className="desk-card-header">
        <div className="agent-meta-wrap">
          <span className="desk-agent-name font-serif">{agent.name}</span>
          <span className="desk-station-role">{agent.role}</span>
        </div>

        <div className={`desk-status-pill pill-${status}`}>
          {isCompleted || status === 'completed' ? (
            <span className="status-completed-badge">
              <CheckCircle2 size={11} /> Done
            </span>
          ) : isActive || status === 'working' || status === 'active' ? (
            <span className="status-active-badge">
              <Sparkles size={11} className="badge-sparkle" /> Working
            </span>
          ) : status === 'thinking' ? (
            <span className="status-thinking-badge">
              <span className="thinking-pulse-dot" /> Thinking
            </span>
          ) : hasIncomingSignal || status === 'communicating' ? (
            <span className="status-signal-badge">
              <Radio size={11} /> Signal
            </span>
          ) : status === 'error' ? (
            <span className="status-error-badge">
              Error
            </span>
          ) : (
            <span className="status-idle-badge">Idle</span>
          )}
        </div>
      </div>

      {/* Illustrated Workstation Environment */}
      <div className="desk-illustration-box">
        {renderWorkstationIllustration()}
      </div>

      {/* Props & Environmental Description */}
      <div className="desk-details-footer">
        <div className="props-row">
          {agent.props.slice(0, 2).map((prop, idx) => (
            <span key={idx} className="prop-tag">{prop}</span>
          ))}
        </div>

        {isActive && snippet && (
          <div className="active-thought-pill font-mono">
            {snippet.slice(0, 75)}...
          </div>
        )}
      </div>

      <style>{`
        .agent-desk-card {
          width: 180px;
          flex-shrink: 0;
          background: var(--white);
          border: 1px solid var(--border-light);
          border-radius: var(--radius-md);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          transition: all var(--transition-normal);
          position: relative;
          box-shadow: var(--shadow-sm);
        }

        .agent-desk-card:hover {
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
          border-color: var(--rose);
        }

        .agent-desk-card.is-active {
          border-color: var(--burgundy);
          border-top: 3px solid var(--burgundy);
          background: var(--white);
          box-shadow: 0 4px 16px rgba(84, 27, 59, 0.12);
        }

        .agent-desk-card.is-active .desk-illustration-box {
          background: #FAF8F9;
        }

        .agent-desk-card.is-completed {
          border-color: rgba(113, 130, 118, 0.4);
          border-top: 2px solid var(--sage);
          background: #FAFCFA;
        }

        .agent-desk-card.incoming-signal {
          border-color: var(--gold);
        }

        .desk-card-header {
          padding: 8px 10px;
          border-bottom: 1px solid var(--border-subtle);
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 6px;
          min-height: 48px;
        }

        .agent-meta-wrap {
          display: flex;
          flex-direction: column;
          min-width: 0;
          flex: 1;
        }

        .desk-agent-name {
          font-size: 12px;
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1.2;
        }

        .desk-station-role {
          font-size: 9.5px;
          color: var(--text-secondary);
          line-height: 1.25;
          margin-top: 2px;
        }

        .desk-status-pill {
          font-size: 9px;
          font-weight: 700;
          flex-shrink: 0;
        }

        .status-completed-badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          color: var(--white);
          background: var(--sage);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .status-active-badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          color: var(--white);
          background: var(--burgundy);
          padding: 2px 6px;
          border-radius: 4px;
          box-shadow: 0 1px 4px rgba(84, 27, 59, 0.25);
        }

        .status-thinking-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          color: var(--wine);
          background: rgba(182, 138, 154, 0.2);
          border: 1px solid var(--rose);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .thinking-pulse-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: var(--rose);
          animation: pulse-rose 1.5s infinite;
        }

        .status-signal-badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          color: var(--white);
          background: var(--gold);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .status-error-badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          color: var(--white);
          background: var(--error);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .badge-sparkle {
          animation: pulse-rose 1.5s infinite;
        }

        .status-idle-badge {
          color: var(--text-secondary);
          background: var(--pearl-dark);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .desk-illustration-box {
          height: 90px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #FAFAFB;
          padding: 4px;
          transition: background var(--transition-fast);
        }

        .desk-svg {
          width: 100%;
          height: 100%;
        }

        .agent-desk-card.is-active .desk-svg {
          animation: gentle-desk-activity 3s infinite ease-in-out;
        }

        @keyframes gentle-desk-activity {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-1.5px); }
        }

        .desk-details-footer {
          padding: 6px 8px;
          border-top: 1px solid var(--border-subtle);
          display: flex;
          flex-direction: column;
          gap: 4px;
          background: var(--white);
        }

        .props-row {
          display: flex;
          gap: 4px;
          overflow: hidden;
        }

        .prop-tag {
          font-size: 8.5px;
          color: var(--text-secondary);
          background: var(--pearl);
          border: 1px solid var(--border-light);
          padding: 1px 4px;
          border-radius: 3px;
          white-space: nowrap;
        }

        .active-thought-pill {
          font-size: 8.5px;
          background: var(--burgundy-light);
          color: var(--burgundy);
          padding: 2px 5px;
          border-radius: 3px;
          border-left: 2px solid var(--rose);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      `}</style>
    </div>
  );
}
