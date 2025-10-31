import ChatInterface from '@/components/ChatInterface';

export default function Chat() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Chat with Opencode</h1>
        <p className="text-muted-foreground">
          Interact with the opencode assistant in a chat interface.
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}