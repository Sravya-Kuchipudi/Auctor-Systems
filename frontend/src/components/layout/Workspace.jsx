import React from 'react';
import AuctorChat from '../chat/AuctorChat';
import LivePreview from '../preview/LivePreview';
import LivingOffice from '../office/LivingOffice';
import DocViewerModal from '../preview/DocViewerModal';

export default function Workspace() {
  return (
    <main className="auctor-workspace-grid">
      {/* 1. Main Auctor Chat (Primary User Interaction Area) */}
      <AuctorChat />

      {/* 2 & 3. Hero Canvas & Living Office Atelier */}
      <div className="workspace-main-stage">
        {/* Primary Product Output: Live Website Preview Canvas */}
        <div className="preview-canvas-wrapper">
          <LivePreview />
        </div>

        {/* Visual Intelligence Representation: Living Office Strip */}
        <div className="living-office-wrapper">
          <LivingOffice />
        </div>
      </div>

      {/* In-Workspace Documentation Viewer */}
      <DocViewerModal />

      <style>{`
        .auctor-workspace-grid {
          display: flex;
          height: calc(100vh - 60px);
          width: 100vw;
          overflow: hidden;
          background: var(--pearl);
        }

        .workspace-main-stage {
          flex: 1;
          display: flex;
          flex-direction: column;
          height: 100%;
          min-width: 0;
          overflow: hidden;
        }

        .preview-canvas-wrapper {
          flex: 1;
          min-height: 0;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .living-office-wrapper {
          flex-shrink: 0;
          z-index: 20;
        }

        @media (max-width: 900px) {
          .auctor-workspace-grid {
            flex-direction: column;
            overflow-y: auto;
            height: auto;
            min-height: calc(100vh - 54px);
          }

          .workspace-main-stage {
            height: auto;
            min-height: 640px;
          }
        }
      `}</style>
    </main>
  );
}
