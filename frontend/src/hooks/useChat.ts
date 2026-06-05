'use client';

import { useCallback, useState } from 'react';
import { api } from '@/lib/api';
import { Message } from '@/lib/types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      setError(null);
      const userMsg: Message = { role: 'user', content, timestamp: new Date() };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const data = await api.chat(content, sessionId);
        setSessionId(data.session_id);
        const assistantMsg: Message = {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          agent_steps: data.agent_steps,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  const clearChat = useCallback(async () => {
    if (sessionId) await api.clearSession(sessionId).catch(() => {});
    setMessages([]);
    setSessionId(undefined);
    setError(null);
  }, [sessionId]);

  return { messages, isLoading, error, sendMessage, clearChat, sessionId };
}
