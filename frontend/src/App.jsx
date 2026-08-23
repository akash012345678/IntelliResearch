import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import KnowledgeGraph from './pages/KnowledgeGraph';
import ResearchIntelligence from './pages/ResearchIntelligence';
import ResearchAnalysis from './pages/ResearchAnalysis';
import ResearchProjects from './pages/ResearchProjects';
import ResearchProjectDetails from './pages/ResearchProjectDetails';

import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-grow">
          <ErrorBoundary fallbackTitle="Application Error Encountered">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
              <Route path="/research-intelligence" element={<ResearchIntelligence />} />
              <Route path="/research-analysis" element={<ResearchAnalysis />} />
              <Route path="/research-projects" element={<ResearchProjects />} />
              <Route path="/research-projects/:projectId" element={<ResearchProjectDetails />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </Router>
  );
}




export default App;

