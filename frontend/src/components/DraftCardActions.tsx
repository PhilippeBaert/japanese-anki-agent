'use client';

import { useRef } from 'react';

interface DraftCardActionsProps {
  onExport: () => void;
  onImport: (file: File) => Promise<void>;
  hasCards: boolean;
  importError: string | null;
}

export function DraftCardActions({
  onExport,
  onImport,
  hasCards,
  importError
}: DraftCardActionsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await onImport(file);
      // Reset input so same file can be selected again
      e.target.value = '';
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        onChange={handleFileChange}
        className="hidden"
        aria-label="Import draft cards from JSON file"
      />

      {/* Import Button */}
      <button
        type="button"
        onClick={handleImportClick}
        className="px-3 py-1.5 text-sm border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
        aria-label="Import draft cards from JSON"
      >
        Import JSON
      </button>

      {/* Export Button */}
      <button
        type="button"
        onClick={onExport}
        disabled={!hasCards}
        className={`px-3 py-1.5 text-sm border rounded-md transition-colors ${
          hasCards
            ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
            : 'border-gray-200 text-gray-400 cursor-not-allowed'
        }`}
        aria-label="Export draft cards to JSON"
      >
        Export JSON
      </button>

      {/* Error display */}
      {importError && (
        <span className="text-red-600 text-sm ml-2">{importError}</span>
      )}
    </div>
  );
}
