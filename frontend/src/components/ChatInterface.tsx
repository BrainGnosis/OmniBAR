import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { sendChatMessage } from '@/lib/api';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

type ChatSession = {
  id: string;
  name: string;
  messages: Message[];
};

export default function ChatInterface() {
  const [sessions, setSessions] = useState<ChatSession[]>([
    { id: '1', name: 'Chat 1', messages: [] },
  ]);
  const [activeSessionId, setActiveSessionId] = useState('1');
  const [input, setInput] = useState('');

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  const handleSend = async () => {
    if (!input.trim() || !activeSession) return;

    const userMessage: Message = { role: 'user', content: input };
    const newMessages = [...activeSession.messages, userMessage];

    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId ? { ...s, messages: newMessages } : s
      )
    );
    setInput('');

    try {
      const response = await sendChatMessage(input);
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
      };
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId
            ? { ...s, messages: [...newMessages, assistantMessage] }
            : s
        )
      );
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId
            ? { ...s, messages: [...newMessages, errorMessage] }
            : s
        )
      );
    }
  };

  const addNewChat = () => {
    const newId = (sessions.length + 1).toString();
    const newSession: ChatSession = {
      id: newId,
      name: `Chat ${newId}`,
      messages: [],
    };
    setSessions((prev) => [...prev, newSession]);
    setActiveSessionId(newId);
  };

  return (
    <div className="flex h-96 flex-col gap-4">
      <div className="flex items-center gap-2">
        {sessions.map((session) => (
          <Button
            key={session.id}
            variant={activeSessionId === session.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSessionId(session.id)}
          >
            {session.name}
          </Button>
        ))}
        <Button variant="outline" size="sm" onClick={addNewChat}>
          + New Chat
        </Button>
      </div>
      <Card className="flex-1 overflow-hidden">
        <div className="flex h-full flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {activeSession?.messages.map((msg, idx) => (
              <div
                key={idx}
                className={`rounded p-2 ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground ml-auto max-w-xs'
                    : 'bg-muted max-w-xs'
                }`}
              >
                {msg.content}
              </div>
            ))}
          </div>
          <div className="flex gap-2 p-4 border-t">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            />
            <Button onClick={handleSend}>Send</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}