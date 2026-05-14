'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Upload,
  Search,
  Edit3,
  BarChart2,
  Scale,
  FileText,
  ChevronRight,
  Wifi,
  WifiOff,
} from 'lucide-react';
import clsx from 'clsx';
import { getDocuments } from '@/lib/api';
import type { Document, DraftResult, Source } from '@/lib/types';
import IngestView from '@/components/IngestView';
import AnalyzeView from '@/components/AnalyzeView';
import LearnView from '@/components/LearnView';
import IntelligenceView from '@/components/IntelligenceView';

type ActiveView = 'ingest' | 'analyze' | 'learn' | 'intelligence';

interface NavItem {
  id: ActiveView;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const navItems: NavItem[] = [
  {
    id: 'ingest',
    label: 'Ingest',
    icon: <Upload size={18} />,
    description: 'Upload & index documents',
  },
  {
    id: 'analyze',
    label: 'Analyze',
    icon: <Search size={18} />,
    description: 'Generate legal drafts',
  },
  {
    id: 'learn',
    label: 'Edit & Learn',
    icon: <Edit3 size={18} />,
    description: 'Refine and train the model',
  },
  {
    id: 'intelligence',
    label: 'Intelligence',
    icon: <BarChart2 size={18} />,
    description: 'Metrics & preferences',
  },
];

export default function Home() {
  const [activeView, setActiveView] = useState<ActiveView>('ingest');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedDocName, setSelectedDocName] = useState<string>('');
  const [lastDraft, setLastDraft] = useState<string>('');
  const [lastQuery, setLastQuery] = useState<string>('');
  const [lastSources, setLastSources] = useState<Source[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(loadDocuments, 30000);
    return () => clearInterval(interval);
  }, [loadDocuments]);

  const handleSelectDoc = (doc: Document) => {
    setSelectedDocId(doc.doc_id);
    setSelectedDocName(doc.file_name);
    setLastDraft('');
    setLastQuery('');
    setLastSources([]);
    setActiveView('analyze');
  };

  const handleClearDocFilter = () => {
    setSelectedDocId(null);
    setSelectedDocName('');
    setLastDraft('');
    setLastQuery('');
    setLastSources([]);
  };

  const handleDraftGenerated = (result: DraftResult, query: string) => {
    setLastDraft(result.draft);
    setLastQuery(query);
    setLastSources(result.sources);
  };

  const handleNavClick = (viewId: ActiveView) => {
    setActiveView(viewId);
  };

  return (
    <div className="flex h-screen bg-bg-primary overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-bg-sidebar border-r border-border flex flex-col h-full">
        {/* Logo */}
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
              <Scale size={20} className="text-white" />
            </div>
            <div>
              <div className="text-xs font-bold text-accent-gold tracking-widest uppercase">
                Pearson Specter
              </div>
              <div className="text-xs text-text-muted tracking-wide">Legal Intelligence</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150',
                activeView === item.id
                  ? 'bg-primary text-white shadow-lg shadow-primary/20'
                  : 'text-text-secondary hover:bg-bg-card-hover hover:text-text-primary'
              )}
            >
              <span className={clsx(activeView === item.id ? 'text-white' : 'text-text-muted')}>
                {item.icon}
              </span>
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                <div
                  className={clsx(
                    'text-xs',
                    activeView === item.id ? 'text-blue-200' : 'text-text-muted'
                  )}
                >
                  {item.description}
                </div>
              </div>
            </button>
          ))}
        </nav>

        {/* Document Library */}
        <div className="flex-1 overflow-hidden flex flex-col min-h-0 mt-2">
          <div className="px-4 py-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-widest">
              Document Library
            </span>
            <span className="text-xs text-text-muted bg-bg-card px-1.5 py-0.5 rounded">
              {documents.length}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
            {/* All documents option */}
            <button
              onClick={handleClearDocFilter}
              className={clsx(
                'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs transition-all duration-150',
                !selectedDocId
                  ? 'bg-primary/20 text-primary border border-primary/30'
                  : 'text-text-secondary hover:bg-bg-card hover:text-text-primary'
              )}
            >
              <Search size={12} className="flex-shrink-0" />
              <span className="font-medium truncate">All Documents</span>
            </button>

            {documents.length === 0 ? (
              <div className="text-xs text-text-muted text-center py-4 px-2">
                No documents indexed yet
              </div>
            ) : (
              documents.map((doc) => (
                <button
                  key={doc.doc_id}
                  onClick={() => handleSelectDoc(doc)}
                  className={clsx(
                    'w-full flex items-start gap-2 px-3 py-2 rounded-lg text-left transition-all duration-150 group',
                    selectedDocId === doc.doc_id
                      ? 'bg-primary/20 text-primary border border-primary/30'
                      : 'text-text-secondary hover:bg-bg-card hover:text-text-primary'
                  )}
                >
                  <FileText
                    size={12}
                    className={clsx(
                      'mt-0.5 flex-shrink-0',
                      selectedDocId === doc.doc_id ? 'text-primary' : 'text-text-muted'
                    )}
                  />
                  <div className="min-w-0">
                    <div className="text-xs font-medium truncate">{doc.file_name}</div>
                    <div className="text-xs text-text-muted truncate">{doc.document_type}</div>
                  </div>
                  {selectedDocId === doc.doc_id && (
                    <ChevronRight size={12} className="text-primary flex-shrink-0 mt-0.5" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* API Status */}
        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-card">
            {apiOnline === null ? (
              <>
                <div className="w-2 h-2 rounded-full bg-text-muted animate-pulse" />
                <span className="text-xs text-text-muted">Connecting...</span>
              </>
            ) : apiOnline ? (
              <>
                <Wifi size={12} className="text-success-light" />
                <span className="text-xs text-success-light">API Connected</span>
              </>
            ) : (
              <>
                <WifiOff size={12} className="text-error-light" />
                <span className="text-xs text-error-light">API Offline</span>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {activeView === 'ingest' && (
          <IngestView
            documents={documents}
            onDocumentsChange={loadDocuments}
          />
        )}
        {activeView === 'analyze' && (
          <AnalyzeView
            selectedDocId={selectedDocId}
            selectedDocName={selectedDocName}
            onDraftGenerated={handleDraftGenerated}
          />
        )}
        {activeView === 'learn' && (
          <LearnView
            lastDraft={lastDraft}
            lastQuery={lastQuery}
            lastSources={lastSources}
            onFeedbackSubmitted={() => {}}
            onGoToAnalyze={() => setActiveView('analyze')}
          />
        )}
        {activeView === 'intelligence' && <IntelligenceView />}
      </main>
    </div>
  );
}
