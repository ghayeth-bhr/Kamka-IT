'use client';

import { useState } from 'react';
import { BookOpen } from 'lucide-react';
import { ChatInterface } from '@/components/ChatInterface';
import { DocumentUpload } from '@/components/DocumentUpload';
import { DocumentMeta } from '@/lib/types';

export default function Home() {
  const [uploadedDocs, setUploadedDocs] = useState<DocumentMeta[]>([]);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[#eadfce] bg-[#fffaf2]/80 backdrop-blur px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-[#f3e3cf] flex items-center justify-center">
            <BookOpen size={20} className="text-[#cc6b2c]" />
          </div>
          <div>
            <h1 className="font-semibold text-[#1b1b1f] text-lg tracking-tight">
              RAG Assistant
            </h1>
            <p className="text-xs text-[#6f6458]">
              Document-grounded answers with explicit citations
            </p>
          </div>
          {uploadedDocs.length > 0 && (
            <span className="ml-auto text-xs bg-[#f3e3cf] text-[#a9541f] px-2 py-1 rounded-full">
              {uploadedDocs.length} doc{uploadedDocs.length > 1 ? 's' : ''} loaded
            </span>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6 grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <aside className="flex flex-col gap-4">
          <div className="bg-[#fffaf2] rounded-2xl border border-[#eadfce] p-4 shadow-[0_12px_30px_-24px_rgba(0,0,0,0.35)]">
            <h2 className="text-sm font-semibold text-[#2a2a31] mb-3">Documents</h2>
            <DocumentUpload
              onUploadSuccess={(docs) =>
                setUploadedDocs((prev) => [...prev, ...docs])
              }
            />
          </div>

          <div className="bg-[#cfe4db]/60 rounded-2xl p-4 text-xs text-[#2a2a31] space-y-2 border border-[#b6d8cd]">
            <p className="font-semibold uppercase tracking-wide text-[11px] text-[#4d5b54]">
              How it works
            </p>
            <p>1. Upload a PDF or text file.</p>
            <p>2. Ask a question in the chat.</p>
            <p>3. The agent retrieves relevant chunks and cites them.</p>
          </div>
        </aside>

        <div className="bg-[#fffaf2] rounded-2xl border border-[#eadfce] shadow-[0_14px_40px_-28px_rgba(0,0,0,0.45)] overflow-hidden flex flex-col h-[calc(100vh-140px)]">
          <ChatInterface />
        </div>
      </main>
    </div>
  );
}
