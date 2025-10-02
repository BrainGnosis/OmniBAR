import { useMemo, useState } from 'react';
import {
  ColumnDef,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table';

import type { BenchmarkRow } from '@/types';
import { useAppStore } from '@/lib/store';

export interface BenchmarkTableProps {
  data: BenchmarkRow[];
}

export function BenchmarkTable({ data }: BenchmarkTableProps) {
  const { status, q, setSelectedBenchmarkId, selectedBenchmarkId } = useAppStore();
  const [sorting, setSorting] = useState<SortingState>([]);
  const columns = useMemo<ColumnDef<BenchmarkRow>[]>(
    () => [
      { accessorKey: 'name', header: 'Name', enableSorting: false },
      { accessorKey: 'iterations', header: 'Iterations', enableSorting: false },
      {
        accessorKey: 'successRate',
        header: 'Success %',
        cell: (info) => `${Math.round((info.getValue<number>() ?? 0) * 100)}%`,
        enableSorting: true,
      },
      { accessorKey: 'status', header: 'Status', enableSorting: false },
      {
        accessorKey: 'lastUpdated',
        header: 'Last Updated',
        cell: (info) => new Date(info.getValue<string>()).toLocaleString(),
        enableSorting: true,
      },
    ],
    []
  );

  const filtered = useMemo(() => {
    return data.filter((row) => {
      const matchesStatus = status === 'all' || row.status === status;
      const query = q.toLowerCase();
      const matchesQuery = !query || row.name.toLowerCase().includes(query);
      return matchesStatus && matchesQuery;
    });
  }, [data, status, q]);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                if (header.isPlaceholder) {
                  return <th key={header.id} />;
                }
                const canSort = header.column.getCanSort();
                const sorted = header.column.getIsSorted();
                const ariaSort: 'none' | 'ascending' | 'descending' = !sorted
                  ? 'none'
                  : sorted === 'asc'
                  ? 'ascending'
                  : 'descending';
                return (
                  <th
                    key={header.id}
                    scope="col"
                    className="border-b px-3 py-2 font-medium"
                    aria-sort={ariaSort}
                  >
                    {canSort ? (
                      <button
                        type="button"
                        onClick={header.column.getToggleSortingHandler()}
                        className="flex items-center gap-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[hsl(var(--accent))]"
                      >
                        {header.column.columnDef.header as string}
                        {{ asc: '↑', desc: '↓' }[sorted as 'asc' | 'desc'] ?? ''}
                      </button>
                    ) : (
                      header.column.columnDef.header as string
                    )}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => setSelectedBenchmarkId(row.original.id)}
              className={
                row.original.id === selectedBenchmarkId
                  ? 'cursor-pointer bg-muted'
                  : 'cursor-pointer hover:bg-muted/60'
              }
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2">
                  {cell.renderValue() as string}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
