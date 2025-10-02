export type JudgeNotesProps = {
  notes: string[];
};

export function JudgeNotes({ notes }: JudgeNotesProps) {
  if (!notes.length) {
    return null;
  }

  return (
    <div className="rounded-2xl border bg-card/80 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-[hsl(var(--heading))]">Judge Notes</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
        {notes.map((note, index) => (
          <li key={index}>{note}</li>
        ))}
      </ul>
    </div>
  );
}
