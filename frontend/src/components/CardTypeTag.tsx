'use client';

import { CardType } from '@/types';

interface CardTypeTagProps {
  type: CardType;
  isEditable?: boolean;
  onChange?: (newType: CardType) => void;
  isLoading?: boolean;
  showRerunIndicator?: boolean;
}

// Color scheme: distinct and accessible
const TAG_STYLES: Record<CardType, { bg: string; text: string; border: string; selectedBg: string }> = {
  word: {
    bg: 'bg-emerald-100',
    text: 'text-emerald-800',
    border: 'border-emerald-300',
    selectedBg: 'bg-emerald-200',
  },
  phrase: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    border: 'border-amber-300',
    selectedBg: 'bg-amber-200',
  },
  sentence: {
    bg: 'bg-violet-100',
    text: 'text-violet-800',
    border: 'border-violet-300',
    selectedBg: 'bg-violet-200',
  },
};

const CARD_TYPES: CardType[] = ['word', 'phrase', 'sentence'];

// Helper to determine if tag change requires re-run
function needsRegeneration(oldType: CardType, newType: CardType): boolean {
  // Word <-> Phrase: No re-run (both have example sentences)
  if ((oldType === 'word' && newType === 'phrase') ||
      (oldType === 'phrase' && newType === 'word')) {
    return false;
  }
  // Sentence <-> Word/Phrase: Re-run needed (example sentences change)
  return oldType !== newType;
}

export { needsRegeneration };

export function CardTypeTag({
  type,
  isEditable = false,
  onChange,
  isLoading = false,
  showRerunIndicator = false,
}: CardTypeTagProps) {
  const style = TAG_STYLES[type];

  if (!isEditable) {
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}
      >
        {type}
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-1" role="group" aria-label="Card type selection">
      <div className="flex gap-1">
        {CARD_TYPES.map(cardType => {
          const typeStyle = TAG_STYLES[cardType];
          const isSelected = cardType === type;

          return (
            <button
              key={cardType}
              type="button"
              onClick={() => onChange?.(cardType)}
              disabled={isLoading}
              aria-pressed={isSelected}
              aria-disabled={isLoading}
              aria-label={`Set card type to ${cardType}${isSelected ? ' (currently selected)' : ''}`}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors border ${
                isSelected
                  ? `${typeStyle.selectedBg} ${typeStyle.text} ${typeStyle.border}`
                  : 'bg-gray-100 text-gray-500 border-gray-200 hover:bg-gray-200'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {cardType}
            </button>
          );
        })}
      </div>
      {showRerunIndicator && !isLoading && (
        <span className="text-xs text-orange-600 flex items-center gap-1" role="status" aria-live="polite">
          <svg className="w-3 h-3" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
          Will re-run
        </span>
      )}
      {isLoading && (
        <span className="text-xs text-blue-600 flex items-center gap-1" role="status" aria-live="polite">
          <svg className="animate-spin w-3 h-3" aria-hidden="true" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Regenerating...
        </span>
      )}
    </div>
  );
}
