import type { ObjectiveResult } from '@/types';

export interface ObjectivesListProps {
  objectives: ObjectiveResult[];
}

export function ObjectivesList({ objectives }: ObjectivesListProps) {
  return (
    <ul className="space-y-2">
      {objectives.map((objective) => (
        <li key={objective.id} className="flex items-center gap-2 text-sm">
          <span aria-hidden>{objective.pass ? '✅' : '❌'}</span>
          <span>{objective.name}</span>
          {objective.details ? <span className="text-xs text-muted-foreground">({objective.details})</span> : null}
        </li>
      ))}
    </ul>
  );
}
