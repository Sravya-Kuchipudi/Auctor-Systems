import React from 'react';
import { ProjectProvider } from './context/ProjectContext';
import Header from './components/layout/Header';
import Workspace from './components/layout/Workspace';

export default function App() {
  return (
    <ProjectProvider>
      <div className="auctor-app-shell">
        <Header />
        <Workspace />
      </div>

      <style>{`
        .auctor-app-shell {
          display: flex;
          flex-direction: column;
          width: 100vw;
          height: 100vh;
          overflow: hidden;
          background: var(--pearl);
        }
      `}</style>
    </ProjectProvider>
  );
}
