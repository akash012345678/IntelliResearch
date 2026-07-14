import React, { useState, useRef } from 'react';
import { apiService } from '../services/api';

export default function DragDropUpload() {
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [globalError, setGlobalError] = useState('');
  const [globalSuccess, setGlobalSuccess] = useState('');
  const fileInputRef = useRef(null);

  // Constants
  const MAX_FILE_SIZE_MB = 50;
  const ALLOWED_EXT = 'application/pdf';

  // Handle Drag Over
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  // Handle Drag Leave
  const handleDragLeave = () => {
    setIsDragging(false);
  };

  // Process Added Files (validation)
  const processFiles = (fileList) => {
    setGlobalError('');
    setGlobalSuccess('');
    const newFiles = [...files];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      let status = 'pending';
      let errorMsg = '';

      // Validate Extension
      if (file.type !== ALLOWED_EXT && !file.name.toLowerCase().endsWith('.pdf')) {
        status = 'error';
        errorMsg = 'Only PDF documents are allowed.';
      }
      // Validate Size (50 MB)
      else if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        status = 'error';
        errorMsg = `File exceeds the maximum ${MAX_FILE_SIZE_MB}MB limit.`;
      }
      
      // Prevent duplicates in current pending list
      if (!newFiles.some(f => f.file.name === file.name && f.file.size === file.size)) {
        newFiles.push({
          id: Date.now() + i + Math.random(),
          file: file,
          name: file.name,
          size: file.size,
          progress: 0,
          status: status,
          errorMsg: errorMsg,
        });
      }
    }
    setFiles(newFiles);
  };

  // Handle File Drop
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  // Handle File Selector Change
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  // Remove File from list
  const removeFile = (id) => {
    setFiles(files.filter(f => f.id !== id));
  };

  // Format File Size
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Upload Trigger
  const handleUpload = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) return;

    setGlobalError('');
    setGlobalSuccess('');

    // Mark current pending files as uploading
    setFiles(prev => prev.map(f => f.status === 'pending' ? { ...f, status: 'uploading', progress: 0 } : f));

    // Upload files concurrently
    const uploadPromises = pendingFiles.map(async (fileObj) => {
      try {
        const response = await apiService.uploadPaper(fileObj.file, (percent) => {
          // Update file progress
          setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, progress: percent } : f));
        });

        // Set status to success
        setFiles(prev => prev.map(f => f.id === fileObj.id ? { 
          ...f, 
          status: 'success', 
          progress: 100,
          dbId: response.data.paper_id,
          extractedTitle: response.data.title
        } : f));
      } catch (err) {
        logger_error(err);
        const errMsg = err.response?.data?.detail || 'Server upload failed.';
        setFiles(prev => prev.map(f => f.id === fileObj.id ? { 
          ...f, 
          status: 'error', 
          errorMsg: errMsg 
        } : f));
      }
    });

    await Promise.all(uploadPromises);

    // Calculate results count
    const updatedFiles = files; // reference values will be read in subsequent render
    setGlobalSuccess(`Successfully processed upload batch.`);
  };

  const logger_error = (err) => {
    console.error("Upload error details:", err);
  };

  const clickInput = () => {
    fileInputRef.current.click();
  };

  const hasPending = files.some(f => f.status === 'pending');
  const isUploading = files.some(f => f.status === 'uploading');

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 animate-fade-in">
      
      {/* Drop Zone Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={clickInput}
        className={`relative border-2 border-dashed rounded-3xl p-10 text-center cursor-pointer transition-all duration-300 ${
          isDragging 
            ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]' 
            : 'border-slate-800 bg-slate-900/40 hover:bg-slate-900/60 hover:border-slate-700'
        } glass-card`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          multiple
          accept=".pdf"
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div>
            <p className="text-lg font-semibold text-slate-100">
              Drag & Drop your research paper PDFs here
            </p>
            <p className="text-sm text-slate-400 mt-1">
              or <span className="text-indigo-400 font-medium hover:underline">browse files</span> from your local system
            </p>
          </div>
          <div className="text-xs text-slate-500 border border-slate-800/80 bg-slate-950/40 rounded-full px-4 py-1.5 mt-2">
            PDF only • Max size 50 MB per file
          </div>
        </div>
      </div>

      {/* Global Banners */}
      {globalError && (
        <div className="p-4 bg-rose-950/30 border border-rose-900/50 rounded-2xl text-rose-300 text-sm flex items-center gap-3">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {globalError}
        </div>
      )}

      {/* File List Container */}
      {files.length > 0 && (
        <div className="glass-card rounded-2xl overflow-hidden animate-slide-up border border-slate-800">
          <div className="px-6 py-4 bg-slate-900/50 border-b border-slate-800 flex justify-between items-center">
            <h3 className="font-semibold text-slate-200">Selected Papers ({files.length})</h3>
            {hasPending && !isUploading && (
              <button
                onClick={handleUpload}
                className="btn-primary flex items-center gap-2 py-2 text-sm"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Upload to Database
              </button>
            )}
          </div>
          <div className="divide-y divide-slate-800/60 max-h-96 overflow-y-auto custom-scrollbar">
            {files.map((fileObj) => (
              <div key={fileObj.id} className="p-4 flex items-center justify-between gap-4 bg-slate-950/15">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-slate-200 truncate pr-4">
                      {fileObj.name}
                    </p>
                    <span className="text-xs text-slate-500 font-mono flex-shrink-0">
                      {formatBytes(fileObj.size)}
                    </span>
                  </div>
                  
                  {/* Progress bar logic */}
                  {fileObj.status === 'uploading' && (
                    <div className="w-full bg-slate-850 h-1.5 rounded-full overflow-hidden mt-2">
                      <div 
                        className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${fileObj.progress}%` }}
                      ></div>
                    </div>
                  )}

                  {/* Success notification */}
                  {fileObj.status === 'success' && (
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span className="text-xs text-emerald-400">
                        Saved: {fileObj.extractedTitle ? `"${fileObj.extractedTitle}"` : 'Extracted details saved'}
                      </span>
                    </div>
                  )}

                  {/* Error notification */}
                  {fileObj.status === 'error' && (
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                      <span className="text-xs text-rose-400 truncate max-w-lg">
                        {fileObj.errorMsg}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0 flex items-center">
                  {fileObj.status !== 'uploading' && (
                    <button
                      onClick={() => removeFile(fileObj.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-slate-350 hover:bg-slate-800 transition-colors"
                      title="Remove from queue"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                  {fileObj.status === 'uploading' && (
                    <span className="text-xs text-indigo-400 font-mono font-semibold animate-pulse">
                      {fileObj.progress}%
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
