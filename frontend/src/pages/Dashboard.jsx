import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import SearchBar from '../components/SearchBar';
import PaperCard from '../components/PaperCard';
import PaperViewModal from '../components/PaperViewModal';

export default function Dashboard() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewingPaperId, setViewingPaperId] = useState(null);
  const [deletingPaperId, setDeletingPaperId] = useState(null);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success'); // success or error

  // Load papers (debounced for search query)
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchPapers(searchQuery);
    }, 250); // 250ms debounce

    return () => clearTimeout(handler);
  }, [searchQuery]);

  const fetchPapers = async (query = '') => {
    setLoading(true);
    try {
      const response = await apiService.getPapers(query);
      setPapers(response.data);
    } catch (err) {
      console.error(err);
      showToast('Failed to fetch research papers. Check connection.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToastMessage(message);
    setToastType(type);
    setTimeout(() => {
      setToastMessage('');
    }, 4000);
  };

  // Trigger paper view modal
  const handleViewPaper = (id) => {
    setViewingPaperId(id);
  };

  // Open delete confirmation modal
  const handleConfirmDelete = (id) => {
    setDeletingPaperId(id);
  };

  // Execute paper deletion
  const handleDeletePaper = async () => {
    if (!deletingPaperId) return;
    
    try {
      await apiService.deletePaper(deletingPaperId);
      // Remove from local state list
      setPapers(prev => prev.filter(p => p.id !== deletingPaperId));
      showToast('Research paper and associated text files removed successfully.');
    } catch (err) {
      console.error(err);
      showToast('Failed to delete paper. Please try again.', 'error');
    } finally {
      setDeletingPaperId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 animate-fade-in">
      
      {/* Toast Alert overlay */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 animate-slide-up">
          <div className={`px-5 py-3.5 rounded-2xl shadow-2xl border flex items-center gap-3 text-sm font-medium ${
            toastType === 'success' 
              ? 'bg-emerald-950/90 border-emerald-500/30 text-emerald-350' 
              : 'bg-rose-950/90 border-rose-500/30 text-rose-350'
          }`}>
            <span className={`w-2 h-2 rounded-full ${toastType === 'success' ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
            {toastMessage}
          </div>
        </div>
      )}

      {/* Header controls section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 border-b border-slate-800/80 pb-6">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            Research Repository
          </h2>
          <p className="text-sm text-slate-450 mt-1">
            Analyze, query, and browse uploaded manuscripts ({papers.length} indexing records found)
          </p>
        </div>
        
        {/* Search */}
        <SearchBar value={searchQuery} onChange={setSearchQuery} />
      </div>

      {/* Main Grid View */}
      {loading && papers.length === 0 ? (
        // Skeletal loading indicators
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((idx) => (
            <div key={idx} className="glass-card rounded-2xl p-6 h-[230px] flex flex-col justify-between border border-slate-900 animate-pulse">
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="h-4 bg-slate-800 rounded w-5/6"></div>
                  <div className="h-4 bg-slate-800 rounded w-2/3"></div>
                </div>
                <div className="space-y-1.5 pt-2">
                  <div className="h-3 bg-slate-900 rounded w-1/2"></div>
                  <div className="h-3 bg-slate-900 rounded w-1/3"></div>
                </div>
              </div>
              <div className="flex justify-between items-center border-t border-slate-900 pt-4 mt-4">
                <div className="h-4 bg-slate-800 rounded w-24"></div>
                <div className="h-4 bg-slate-900 rounded w-12"></div>
              </div>
            </div>
          ))}
        </div>
      ) : papers.length > 0 ? (
        // List cards
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {papers.map((paper) => (
            <PaperCard
              key={paper.id}
              paper={paper}
              onView={handleViewPaper}
              onDelete={handleConfirmDelete}
            />
          ))}
        </div>
      ) : (
        // Empty State Banner
        <div className="glass-card rounded-3xl p-12 text-center max-w-xl mx-auto space-y-6 border border-slate-900 animate-slide-up">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400 mx-auto">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-slate-100">No Publications Indexed</h3>
            <p className="text-sm text-slate-450 max-w-sm mx-auto leading-relaxed">
              {searchQuery 
                ? `No results match your search term "${searchQuery}". Clear query to view all items.`
                : "Your digital paper collection is empty. Start by uploading files into the gap engine."}
            </p>
          </div>
          <div>
            {searchQuery ? (
              <button
                onClick={() => setSearchQuery('')}
                className="btn-secondary py-2 text-xs"
              >
                Clear Search Filter
              </button>
            ) : (
              <Link
                to="/"
                className="btn-primary inline-flex items-center gap-2 py-2.5 text-xs font-semibold"
              >
                Upload Research Paper
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Viewing Paper Detail Modal overlay */}
      {viewingPaperId && (
        <PaperViewModal
          paperId={viewingPaperId}
          onClose={() => setViewingPaperId(null)}
        />
      )}

      {/* Delete Confirmation Modal Overlay */}
      {deletingPaperId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md glass-card rounded-3xl p-6 border border-slate-800 shadow-2xl space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-slate-100 text-lg leading-snug">Confirm Deletion</h3>
                <p className="text-xs text-slate-400 mt-1">This operation is destructive and cannot be undone.</p>
              </div>
            </div>
            
            <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-2xl border border-slate-900 select-all font-mono break-all">
              {papers.find(p => p.id === deletingPaperId)?.filename}
            </p>
            
            <p className="text-xs text-slate-450 leading-relaxed">
              This will remove the publication metadata from the database, delete the original PDF from uploads/original_papers, and delete the extracted text file.
            </p>
            
            <div className="flex items-center justify-end gap-3 border-t border-slate-850 pt-4">
              <button
                onClick={() => setDeletingPaperId(null)}
                className="btn-secondary py-2 text-xs px-4"
              >
                Keep File
              </button>
              
              <button
                onClick={handleDeletePaper}
                className="btn-danger py-2 text-xs px-4 bg-rose-600 hover:bg-rose-500 hover:text-white border-0"
              >
                Yes, Delete Paper
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
