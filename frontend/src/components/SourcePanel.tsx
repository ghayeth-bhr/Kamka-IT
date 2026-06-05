'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, Wrench } from 'lucide-react';
import { AgentStep, SourceChunk } from '@/lib/types';

interface Props {
  sources: SourceChunk[];
  agentSteps: AgentStep[];
}

export function SourcePanel({ sources, agentSteps }: Props) {
  const [showSteps, setShowSteps] = useState(false);

  if (sources.length === 0 && agentSteps.length === 0) return null;

  return (
    <div className="border-t border-[#eadfce] pt-3 mt-3 space-y-4">
      {sources.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[#8a7b6b] mb-2">
            Sources
          </p>
          <div className="space-y-2">
            {sources.map((s, i) => (
              <div key={i} className="bg-[#fff2e4] rounded-lg px-3 py-2 text-xs">
                <div className="flex items-center gap-1.5 font-medium text-[#2a2a31] mb-1">
                  <FileText size={12} />
                  <span className="font-mono">{s.filename}</span>
                  {s.page != null && (
                    <span className="text-[#8a7b6b]">- p.{s.page}</span>
                  )}
                </div>
                <p className="text-[#5e564d] leading-relaxed">
                  {s.content_preview}
                  {s.content_preview.length === 200 ? '...' : ''}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {agentSteps.length > 0 && (
        <div>
          <button
            onClick={() => setShowSteps((v) => !v)}
            className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[#8a7b6b] hover:text-[#5e564d] transition-colors"
          >
            <Wrench size={12} />
            Agent reasoning ({agentSteps.length} step{agentSteps.length > 1 ? 's' : ''})
            {showSteps ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {showSteps && (
            <ol className="mt-2 space-y-1.5">
              {agentSteps.map((step, i) => (
                <li key={i} className="bg-[#f3efe8] rounded-lg px-3 py-2 text-xs">
                  <span className="font-medium text-[#cc6b2c]">{step.tool}</span>
                  <span className="text-[#8a7b6b] mx-1">&lt;-</span>
                  <span className="text-[#5e564d] font-mono">{step.input}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
}
