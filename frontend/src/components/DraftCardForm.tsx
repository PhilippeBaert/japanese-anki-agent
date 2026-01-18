'use client';

import { forwardRef, useImperativeHandle, useRef } from 'react';
import { DraftCard } from '@/types';

export interface DraftCardFormHandle {
  focusInput: () => void;
}

interface DraftCardFormProps {
  card: DraftCard;
  index: number;
  onChange: (card: DraftCard) => void;
  onRemove: () => void;
  canRemove: boolean;
  onAddCardAfter?: () => void;
}

export const DraftCardForm = forwardRef<DraftCardFormHandle, DraftCardFormProps>(
  function DraftCardForm(
    { card, index, onChange, onRemove, canRemove, onAddCardAfter },
    ref
  ) {
    const inputRef = useRef<HTMLInputElement>(null);

    useImperativeHandle(ref, () => ({
      focusInput: () => {
        inputRef.current?.focus();
      },
    }));

    const updateField = (field: keyof DraftCard, value: string) => {
      onChange({ ...card, [field]: value });
    };

    const handleKeyDown = (e: React.KeyboardEvent, isTextarea = false) => {
      if (e.key === 'Enter') {
        // Allow Shift+Enter in textareas for newlines
        if (isTextarea && e.shiftKey) return;
        e.preventDefault();
        onAddCardAfter?.();
      }
    };

  return (
    <div className="border border-gray-300 rounded-lg p-4 bg-white shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-700">Card {index + 1}</h3>
        {canRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="text-red-500 hover:text-red-700 text-sm"
          >
            Remove
          </button>
        )}
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Input (romaji, kana, kanji, Dutch, or mixed) *
          </label>
          <input
            ref={inputRef}
            type="text"
            value={card.rawInput}
            onChange={e => updateField('rawInput', e.target.value)}
            onKeyDown={e => handleKeyDown(e)}
            placeholder="e.g., Nederland, futsuu, きょう は 9じ に ねます"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">
            Card type (word/phrase/sentence) will be auto-detected
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Fixed Dutch (optional)
            </label>
            <input
              type="text"
              value={card.fixedDutch}
              onChange={e => updateField('fixedDutch', e.target.value)}
              onKeyDown={e => handleKeyDown(e)}
              placeholder="e.g., gewoon"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Fixed English (optional)
            </label>
            <input
              type="text"
              value={card.fixedEnglish}
              onChange={e => updateField('fixedEnglish', e.target.value)}
              onKeyDown={e => handleKeyDown(e)}
              placeholder="e.g., Netherlands"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Extra Notes (optional)
          </label>
          <textarea
            value={card.extraNotes}
            onChange={e => updateField('extraNotes', e.target.value)}
            onKeyDown={e => handleKeyDown(e, true)}
            placeholder="Any additional notes about this word/sentence..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

      </div>
    </div>
  );
});
