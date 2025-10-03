import { Fragment } from 'react';

import type { RunRecord } from '@/types';

export interface RunDrawerProps {
  open: boolean;
  onClose: () => void;
  record?: RunRecord;
}

export function RunDrawer({ open, onClose, record }: RunDrawerProps) {
  if (!open || !record) {
    return null;
  }

  return (
    <aside className="fixed inset-y-0 right-0 w-full max-w-lg border-l bg-background p-6 shadow-lg">
      <button type="button" onClick={onClose} className="mb-4 text-sm underline">
        Close
      </button>
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Run details</h2>
        <p className="text-sm text-muted-foreground">Drawer stub — wire up Sheet+JsonPanel+ObjectivesList.</p>
      </div>
    </aside>
  );
}
