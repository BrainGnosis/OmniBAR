import { FormEvent, useState } from 'react';

import { runOnce } from '@/lib/api';
import type { AgentInput, RunRecord } from '@/types';

export interface RunFormProps {
  onCompleted?: (result: RunRecord) => void;
}

export function RunForm({ onCompleted }: RunFormProps) {
  const [operation, setOperation] = useState<AgentInput['operation']>('add');
  const [a, setA] = useState<number>(0);
  const [b, setB] = useState<number>(0);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    const payload: AgentInput = { operation, a, b };
    try {
      const result = await runOnce(payload);
      onCompleted?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Run failed');
    } finally {
      setPending(false);
    }
  };

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      {/* TODO: replace with actual form controls */}
      <div>RunForm stub for operation {operation} with a={a} b={b}</div>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      <button type="submit" disabled={pending}>
        {pending ? 'Running…' : 'Run'}
      </button>
    </form>
  );
}
