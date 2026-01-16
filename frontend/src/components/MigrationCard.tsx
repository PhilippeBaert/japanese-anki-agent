'use client';

import { useState } from 'react';
import { MigrationNoteState } from '@/types';

// Field mapping from old to new
const FIELD_MAPPING: Record<string, string> = {
  'Kana': 'Hiragana/Katakana',
  'Romaji': 'Romaji',
  'Kanji': 'Kanji',
  'English': 'English',
  'Nederlands': 'Dutch',
  'Example': 'Example sentence hiragana/katakana',
  'Example Kanji': 'Example sentence kanji',
  'Example translation': 'Example sentence translation',
  'Extra': 'Extra notes',
  'Sound': 'Sound',
};

// Order of fields to display
const OLD_FIELDS_ORDER = [
  'Kana',
  'Romaji',
  'Kanji',
  'English',
  'Nederlands',
  'Example',
  'Example Kanji',
  'Example translation',
  'Extra',
  'Sound',
];

const NEW_FIELDS_ORDER = [
  'Hiragana/Katakana',
  'Romaji',
  'Kanji',
  'English',
  'Dutch',
  'Example sentence hiragana/katakana',
  'Example sentence kanji',
  'Example sentence translation',
  'Extra notes',
  'Sound',
];

interface MigrationCardProps {
  noteState: MigrationNoteState;
  onRegenerate: () => void;
  onUpdateField: (field: string, value: string) => void;
  onApprove: () => void;
  onSkip: () => void;
}

export function MigrationCard({
  noteState,
  onRegenerate,
  onUpdateField,
  onApprove,
  onSkip,
}: MigrationCardProps) {
  const [editingField, setEditingField] = useState<string | null>(null);
  const { note, preview, status, error } = noteState;

  const isLoading = status === 'previewing' || status === 'approving';
  const canApprove = status === 'ready' && preview !== null;

  return (
    <div className="border rounded-lg shadow-sm bg-white">
      {/* Header with status */}
      <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-medium text-gray-900">
            Note ID: {note.note_id}
          </span>
          <StatusBadge status={status} />
        </div>
        {preview && (
          <span className="text-sm text-gray-500">
            Type: <span className="font-medium">{preview.auto_classified_type}</span>
          </span>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-200">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Side-by-side comparison */}
      <div className="grid grid-cols-2 divide-x">
        {/* Old fields (left) */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
            Original (Old Format)
          </h3>
          <div className="space-y-2">
            {OLD_FIELDS_ORDER.map(fieldName => {
              const value = note.old_fields[fieldName] || '';
              return (
                <FieldRow
                  key={fieldName}
                  label={fieldName}
                  value={value}
                  isEditable={false}
                />
              );
            })}
          </div>
        </div>

        {/* New fields (right) */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
            Preview (New Format)
          </h3>
          {isLoading && status === 'previewing' ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Generating preview...</span>
            </div>
          ) : preview ? (
            <div className="space-y-2">
              {NEW_FIELDS_ORDER.map(fieldName => {
                const value = preview.new_fields[fieldName] || '';
                const isEditing = editingField === fieldName;
                return (
                  <FieldRow
                    key={fieldName}
                    label={fieldName}
                    value={value}
                    isEditable={true}
                    isEditing={isEditing}
                    onStartEdit={() => setEditingField(fieldName)}
                    onEndEdit={() => setEditingField(null)}
                    onChange={(newValue) => onUpdateField(fieldName, newValue)}
                  />
                );
              })}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              {status === 'pending' ? 'Loading preview...' : 'No preview available'}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="px-4 py-3 border-t bg-gray-50 flex items-center justify-end gap-3">
        <button
          onClick={onSkip}
          disabled={isLoading || status === 'approved' || status === 'skipped'}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Skip
        </button>
        <button
          onClick={onRegenerate}
          disabled={isLoading || status === 'approved'}
          className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {status === 'previewing' ? 'Generating...' : 'Regenerate'}
        </button>
        <button
          onClick={onApprove}
          disabled={!canApprove || isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {status === 'approving' ? 'Approving...' : 'Approve'}
        </button>
      </div>
    </div>
  );
}

// Status badge component
function StatusBadge({ status }: { status: MigrationNoteState['status'] }) {
  const styles: Record<MigrationNoteState['status'], string> = {
    pending: 'bg-gray-100 text-gray-700',
    previewing: 'bg-blue-100 text-blue-700',
    ready: 'bg-yellow-100 text-yellow-700',
    approving: 'bg-blue-100 text-blue-700',
    approved: 'bg-green-100 text-green-700',
    skipped: 'bg-gray-100 text-gray-500',
    error: 'bg-red-100 text-red-700',
  };

  const labels: Record<MigrationNoteState['status'], string> = {
    pending: 'Pending',
    previewing: 'Generating...',
    ready: 'Ready to Approve',
    approving: 'Approving...',
    approved: 'Approved',
    skipped: 'Skipped',
    error: 'Error',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

// Field row component
interface FieldRowProps {
  label: string;
  value: string;
  isEditable: boolean;
  isEditing?: boolean;
  onStartEdit?: () => void;
  onEndEdit?: () => void;
  onChange?: (value: string) => void;
}

function FieldRow({
  label,
  value,
  isEditable,
  isEditing,
  onStartEdit,
  onEndEdit,
  onChange,
}: FieldRowProps) {
  // Highlight differences (new content)
  const hasContent = value.trim() !== '';

  return (
    <div className="flex flex-col">
      <label className="text-xs font-medium text-gray-500 mb-1">{label}</label>
      {isEditable && isEditing ? (
        <textarea
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onBlur={onEndEdit}
          autoFocus
          className="w-full px-2 py-1 text-sm border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y min-h-[60px]"
          rows={Math.max(2, value.split('\n').length)}
        />
      ) : (
        <div
          onClick={isEditable ? onStartEdit : undefined}
          className={`
            px-2 py-1 text-sm rounded min-h-[28px]
            ${hasContent ? 'text-gray-900' : 'text-gray-400 italic'}
            ${isEditable ? 'cursor-pointer hover:bg-blue-50 border border-transparent hover:border-blue-200' : 'bg-gray-50'}
          `}
        >
          {hasContent ? (
            <span className="whitespace-pre-wrap break-words">{value}</span>
          ) : (
            <span>(empty)</span>
          )}
        </div>
      )}
    </div>
  );
}
