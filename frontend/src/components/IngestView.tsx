'use client';

import { useState, useRef, useCallback } from 'react';
import {
  Upload,
  FileText,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  FolderOpen,
  Hash,
  Tag,
  AlignLeft,
  Database,
  X,
} from 'lucide-react';
import clsx from 'clsx';
import { uploadDocument, deleteDocument } from '@/lib/api';
import type { Document, UploadResult } from '@/lib/types';

interface IngestViewProps {
  documents: Document[];
  onDocumentsChange: () => void;
}

type UploadStage = 'idle' | 'uploading' | 'parsing' | 'indexing' | 'done' | 'error';

const ACCEPTED_TYPES = [
  'application/pdf',
  'text/plain',
  'image/png',
  'image/jpeg',
  'image/tiff',
  'image/webp',
];

const ACCEPTED_EXTENSIONS = '.pdf,.txt,.png,.jpg,.jpeg,.tiff,.tif,.webp';

function getStageLabel(stage: UploadStage): string {
  switch (stage) {
    case 'uploading': return 'Uploading file...';
    case 'parsing': return 'Parsing document...';
    case 'indexing': return 'Indexing chunks...';
    case 'done': return 'Processing complete';
    case 'error': return 'Processing failed';
    default: return '';
  }
}

function PipelineStep({ label, done, active, error }: { label: string; done: boolean; active: boolean; error?: boolean }) {
  return (
    <div className={clsx(
      'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border',
      error
        ? 'bg-error/10 border-error/30 text-error-light'
        : done
          ? 'bg-success/10 border-success/30 text-success-light'
          : active
            ? 'bg-primary/10 border-primary/30 text-primary-hover'
            : 'bg-bg-card border-border text-text-muted'
    )}>
      {error ? (
        <X size={12} />
      ) : done ? (
        <CheckCircle size={12} />
      ) : active ? (
        <Loader2 size={12} className="animate-spin" />
      ) : (
        <div className="w-3 h-3 rounded-full border border-current opacity-40" />
      )}
      {label}
    </div>
  );
}

export default function IngestView({ documents, onDocumentsChange }: IngestViewProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle');
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string>('');
  const [currentFileName, setCurrentFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(pdf|txt|png|jpg|jpeg|tiff|tif|webp)$/i)) {
      setUploadError('Unsupported file type. Please upload PDF, TXT, PNG, JPG, or TIFF files.');
      return;
    }

    setUploadError('');
    setUploadResult(null);
    setCurrentFileName(file.name);
    setUploadStage('uploading');

    try {
      // Simulate stage progression for UX
      const stageTimer = setTimeout(() => setUploadStage('parsing'), 800);
      const indexTimer = setTimeout(() => setUploadStage('indexing'), 1800);

      const result = await uploadDocument(file);
      clearTimeout(stageTimer);
      clearTimeout(indexTimer);
      setUploadStage('done');
      setUploadResult(result);
      onDocumentsChange();
    } catch (err) {
      setUploadStage('error');
      setUploadError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    }
  }, [onDocumentsChange]);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  const handleDelete = async (docId: string, fileName: string) => {
    if (!confirm(`Delete "${fileName}" and all its indexed data?`)) return;
    setDeletingId(docId);
    setDeleteError('');
    try {
      await deleteDocument(docId);
      onDocumentsChange();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Delete failed.');
    } finally {
      setDeletingId(null);
    }
  };

  const resetUpload = () => {
    setUploadStage('idle');
    setUploadResult(null);
    setUploadError('');
    setCurrentFileName('');
  };

  const isUploading = ['uploading', 'parsing', 'indexing'].includes(uploadStage);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Document Ingestion</h1>
          <p className="text-sm text-text-secondary mt-1">
            Upload legal documents to extract, parse, and index them for AI analysis
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-bg-card border border-border rounded-lg">
          <Database size={14} className="text-primary" />
          <span className="text-sm text-text-secondary">
            <span className="text-text-primary font-semibold">{documents.length}</span> document
            {documents.length !== 1 ? 's' : ''} indexed
          </span>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !isUploading && uploadStage !== 'done' && fileInputRef.current?.click()}
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200',
          isUploading || uploadStage === 'done'
            ? 'cursor-default'
            : 'cursor-pointer hover:border-primary hover:bg-primary/5',
          isDragging
            ? 'border-primary bg-primary/10 scale-[1.01]'
            : uploadStage === 'done'
              ? 'border-success/50 bg-success/5'
              : uploadStage === 'error'
                ? 'border-error/50 bg-error/5'
                : 'border-border bg-bg-card'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          className="hidden"
          onChange={handleFileInput}
        />

        {uploadStage === 'idle' && (
          <>
            <div className="w-16 h-16 mx-auto mb-4 bg-bg-card-hover rounded-2xl flex items-center justify-center border border-border">
              <Upload size={28} className="text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Drop your document here
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              or click to browse your files
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {['PDF', 'TXT', 'PNG', 'JPG', 'TIFF'].map((ext) => (
                <span
                  key={ext}
                  className="text-xs px-2 py-0.5 bg-bg-primary border border-border rounded text-text-muted"
                >
                  .{ext.toLowerCase()}
                </span>
              ))}
            </div>
          </>
        )}

        {isUploading && (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-primary/10 rounded-2xl flex items-center justify-center border border-primary/30">
              <Loader2 size={28} className="text-primary animate-spin" />
            </div>
            <div>
              <p className="text-text-primary font-medium">{currentFileName}</p>
              <p className="text-sm text-text-secondary mt-1">{getStageLabel(uploadStage)}</p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              <PipelineStep label="Upload" done={['parsing','indexing','done'].includes(uploadStage)} active={uploadStage === 'uploading'} />
              <PipelineStep label="Parse" done={['indexing','done'].includes(uploadStage)} active={uploadStage === 'parsing'} />
              <PipelineStep label="Index" done={uploadStage === 'done'} active={uploadStage === 'indexing'} />
            </div>
          </div>
        )}

        {uploadStage === 'done' && uploadResult && (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-success/10 rounded-2xl flex items-center justify-center border border-success/30">
              <CheckCircle size={28} className="text-success-light" />
            </div>
            <div>
              <p className="text-text-primary font-semibold">{uploadResult.file_name}</p>
              <p className="text-sm text-success-light mt-1">Successfully indexed!</p>
            </div>

            {/* Structured fields */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-xl mx-auto mt-4">
              <div className="bg-bg-primary border border-border rounded-lg p-3 text-left">
                <div className="flex items-center gap-1.5 mb-1">
                  <Tag size={12} className="text-primary" />
                  <span className="text-xs text-text-muted">Type</span>
                </div>
                <p className="text-sm font-medium text-text-primary truncate">
                  {String(uploadResult.structured_fields?.document_type || 'Unknown')}
                </p>
              </div>
              <div className="bg-bg-primary border border-border rounded-lg p-3 text-left">
                <div className="flex items-center gap-1.5 mb-1">
                  <Hash size={12} className="text-primary" />
                  <span className="text-xs text-text-muted">Chunks</span>
                </div>
                <p className="text-sm font-medium text-text-primary">
                  {uploadResult.chunks_indexed} / {uploadResult.chunk_count}
                </p>
              </div>
              {uploadResult.structured_fields && Object.entries(uploadResult.structured_fields)
                .filter(([k]) => k !== 'document_type' && k !== 'summary')
                .slice(0, 4)
                .map(([key, val]) => (
                  <div key={key} className="bg-bg-primary border border-border rounded-lg p-3 text-left">
                    <div className="flex items-center gap-1.5 mb-1">
                      <AlignLeft size={12} className="text-accent-gold" />
                      <span className="text-xs text-text-muted capitalize">{key.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="text-sm font-medium text-text-primary truncate">
                      {String(val ?? 'N/A')}
                    </p>
                  </div>
                ))}
            </div>

            {uploadResult.structured_fields?.summary && (
              <div className="bg-bg-primary border border-border rounded-lg p-4 max-w-xl mx-auto text-left">
                <div className="flex items-center gap-2 mb-2">
                  <AlignLeft size={14} className="text-accent-gold" />
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">Summary</span>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {String(uploadResult.structured_fields.summary)}
                </p>
              </div>
            )}

            <button
              onClick={(e) => { e.stopPropagation(); resetUpload(); }}
              className="mt-2 text-sm text-primary hover:text-primary-hover underline"
            >
              Upload another document
            </button>
          </div>
        )}

        {uploadStage === 'error' && (
          <div className="space-y-3">
            <div className="w-16 h-16 mx-auto bg-error/10 rounded-2xl flex items-center justify-center border border-error/30">
              <AlertCircle size={28} className="text-error-light" />
            </div>
            <p className="text-text-primary font-medium">Upload Failed</p>
            <p className="text-sm text-error-light">{uploadError}</p>
            <button
              onClick={(e) => { e.stopPropagation(); resetUpload(); }}
              className="text-sm text-primary hover:text-primary-hover underline"
            >
              Try again
            </button>
          </div>
        )}
      </div>

      {/* Pipeline stages legend (when idle) */}
      {uploadStage === 'idle' && (
        <div className="flex items-center gap-3 px-4 py-3 bg-bg-card border border-border rounded-lg">
          <span className="text-xs text-text-muted font-medium uppercase tracking-wider">Pipeline:</span>
          <div className="flex flex-wrap gap-2">
            <PipelineStep label="Upload" done={false} active={false} />
            <PipelineStep label="Parse & Extract" done={false} active={false} />
            <PipelineStep label="Chunk & Index" done={false} active={false} />
          </div>
        </div>
      )}

      {/* Error banner for upload errors outside upload zone */}
      {uploadError && uploadStage === 'idle' && (
        <div className="flex items-center gap-3 p-4 bg-error/10 border border-error/30 rounded-lg text-error-light">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span className="text-sm">{uploadError}</span>
          <button onClick={() => setUploadError('')} className="ml-auto">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Delete error */}
      {deleteError && (
        <div className="flex items-center gap-3 p-4 bg-error/10 border border-error/30 rounded-lg text-error-light">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span className="text-sm">{deleteError}</span>
          <button onClick={() => setDeleteError('')} className="ml-auto">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Document Library Table */}
      <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <FolderOpen size={16} className="text-primary" />
            <h2 className="text-sm font-semibold text-text-primary">Indexed Documents</h2>
          </div>
          <span className="text-xs text-text-muted">{documents.length} total</span>
        </div>

        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <FileText size={40} className="text-text-muted mb-4 opacity-40" />
            <p className="text-text-secondary font-medium">No documents indexed yet</p>
            <p className="text-sm text-text-muted mt-1">
              Upload a document above to get started
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-bg-primary/50">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Document
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Type
                  </th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Summary
                  </th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-subtle">
                {documents.map((doc) => (
                  <tr
                    key={doc.doc_id}
                    className="hover:bg-bg-card-hover transition-colors duration-100 group"
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FileText size={14} className="text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-text-primary">{doc.file_name}</p>
                          <p className="text-xs text-text-muted font-mono">{doc.doc_id.slice(0, 12)}...</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-accent-gold/10 border border-accent-gold/20 rounded-full text-xs font-medium text-accent-gold-light">
                        <Tag size={10} />
                        {doc.document_type || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 max-w-xs">
                      <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                        {doc.summary || 'No summary available'}
                      </p>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(doc.doc_id, doc.file_name)}
                        disabled={deletingId === doc.doc_id}
                        className={clsx(
                          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150',
                          deletingId === doc.doc_id
                            ? 'bg-error/10 text-error-light cursor-not-allowed'
                            : 'text-text-muted hover:bg-error/10 hover:text-error-light border border-transparent hover:border-error/20'
                        )}
                      >
                        {deletingId === doc.doc_id ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <Trash2 size={12} />
                        )}
                        {deletingId === doc.doc_id ? 'Deleting...' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
