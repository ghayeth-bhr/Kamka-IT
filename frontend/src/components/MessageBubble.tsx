'use client';

import clsx from 'clsx';
import { Bot, User } from 'lucide-react';
import { Message } from '@/lib/types';
import { SourcePanel } from './SourcePanel';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={clsx('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="shrink-0 w-7 h-7 bg-[#f3e3cf] rounded-full flex items-center justify-center mt-1">
          <Bot size={14} className="text-[#cc6b2c]" />
        </div>
      )}

      <div
        className={clsx(
          'max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-[#cc6b2c] text-white rounded-br-sm'
            : 'bg-[#fffaf2] text-[#2a2a31] shadow-sm border border-[#eadfce] rounded-bl-sm animate-[fadeUp_0.35s_ease-out]'
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {!isUser && message.sources && message.agent_steps && (
          <SourcePanel sources={message.sources} agentSteps={message.agent_steps} />
        )}
      </div>

      {isUser && (
        <div className="shrink-0 w-7 h-7 bg-[#eadfce] rounded-full flex items-center justify-center mt-1">
          <User size={14} className="text-[#7b6f62]" />
        </div>
      )}
    </div>
  );
}
