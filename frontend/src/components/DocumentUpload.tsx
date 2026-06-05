'use client';

import { useRef, useState } from 'react';
import { AlertCircle, CheckCircle, FileText, Upload } from 'lucide-react';
import { api } from '@/lib/api';
import { DocumentMeta } from '@/lib/types';

interface Props {
  onUploadSuccess: (docs: DocumentMeta[]) => void;
}

export function DocumentUpload({ onUploadSuccess }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<DocumentMeta[]>([]);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const validFiles = Array.from(files).filter(
      (f) => f.name.endsWith('.pdf') || f.name.endsWith('.txt')
    );
    if (validFiles.length === 0) {
      setError('Only PDF and .txt files are accepted.');
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const result = await api.uploadDocuments(validFiles);
      setUploadedDocs((prev) => [...prev, ...result.documents]);
      onUploadSuccess(result.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        className={[
          'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors',
          isDragging
            ? 'border-[#cc6b2c] bg-[#f3e3cf]'
            : 'border-[#eadfce] hover:border-[#cc6b2c] bg-white/60',
        ].join(' ')}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <Upload className="mx-auto mb-2 text-[#a3866a]" size={28} />
        {isUploading ? (
          <p className="text-sm text-[#cc6b2c] animate-pulse">Uploading and indexing...</p>
        ) : (
          <>
            <p className="text-sm font-medium text-[#2a2a31]">
              Drop files or click to upload
            </p>
            <p className="text-xs text-[#8a7b6b] mt-1">PDF, TXT - multiple files OK</p>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-[#f7d9d4] px-3 py-2 rounded-lg">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {uploadedDocs.length > 0 && (
        <ul className="space-y-1">
          {uploadedDocs.map((doc) => (
            <li
              key={doc.id}
              className="flex items-center gap-2 text-sm bg-[#e7f0ea] px-3 py-2 rounded-lg"
            >
              <CheckCircle size={14} className="text-[#2e7d5b] shrink-0" />
              <FileText size={14} className="text-[#8a7b6b] shrink-0" />
              <span className="truncate font-mono text-xs text-[#2a2a31]">
                {doc.filename}
              </span>
              <span className="ml-auto text-xs text-[#7b6f62] shrink-0">
                {doc.chunks_count} chunks
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
