'use client';

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Loader2, Send, Trash2 } from 'lucide-react';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';

export function ChatInterface() {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim());
    setInput('');
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#eadfce]">
        <h2 className="font-semibold text-[#2a2a31] text-sm">Conversation</h2>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 text-xs text-[#8a7b6b] hover:text-[#b34a2e] transition-colors"
          >
            <Trash2 size={13} />
            Clear
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-[#8a7b6b] gap-2">
            <p className="text-sm font-medium">Upload a document, then ask anything.</p>
            <p className="text-xs">Your answers will be grounded in your files.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{ animationDelay: `${i * 40}ms` }}
            className="animate-[fadeUp_0.35s_ease-out]"
          >
            <MessageBubble message={msg} />
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-7 h-7 bg-[#f3e3cf] rounded-full flex items-center justify-center">
              <Loader2 size={14} className="text-[#cc6b2c] animate-spin" />
            </div>
            <div className="bg-[#fffaf2] rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-[#eadfce]">
              <div className="flex gap-1 items-center h-4">
                <span className="w-1.5 h-1.5 bg-[#8a7b6b] rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-[#8a7b6b] rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-[#8a7b6b] rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="text-xs text-[#b34a2e] bg-[#f7d9d4] px-3 py-2 rounded-lg">
            Warning: {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 px-4 py-3 border-t border-[#eadfce]"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents..."
          disabled={isLoading}
          className="flex-1 rounded-xl border border-[#eadfce] bg-white/70 px-4 py-2 text-sm text-[#2a2a31] placeholder-[#8a7b6b] focus:outline-none focus:ring-2 focus:ring-[#cc6b2c] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="rounded-xl bg-[#cc6b2c] hover:bg-[#a9541f] disabled:bg-[#eadfce] text-white px-4 py-2 transition-colors"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
