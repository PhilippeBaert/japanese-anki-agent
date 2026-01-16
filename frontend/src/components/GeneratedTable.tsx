'use client';

import { useState, useRef, useMemo, useCallback, memo } from 'react';
import { GeneratedCard, CardType } from '@/types';
import { CardTypeTag, needsRegeneration } from './CardTypeTag';

// Memoized table row component to prevent re-renders when other rows change
interface TableRowProps {
  card: GeneratedCard;
  cardIndex: number;
  cardId: string;
  fields: string[];
  editingCell: { cardIndex: number; field: string } | null;
  cardsLength: number;
  onCellClick: (cardIndex: number, field: string) => void;
  onCellBlur: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onUpdateField: (cardIndex: number, field: string, value: string) => void;
  onTypeChange: (cardIndex: number, newType: CardType) => Promise<void>;
  onRemove: (cardIndex: number) => void;
  onToggleCore: (cardIndex: number) => void;
}

const TableRow = memo(function TableRow({
  card,
  cardIndex,
  cardId,
  fields,
  editingCell,
  cardsLength,
  onCellClick,
  onCellBlur,
  onKeyDown,
  onUpdateField,
  onTypeChange,
  onRemove,
  onToggleCore,
}: TableRowProps) {
  const originalType = card.originalType || card.autoClassifiedType;
  const showRerunIndicator = originalType !== card.autoClassifiedType &&
    needsRegeneration(originalType, card.autoClassifiedType);

  return (
    <tr className={`hover:bg-gray-50 ${card.isCore ? 'bg-yellow-50' : ''}`}>
      <td className="px-3 py-2 text-sm text-gray-500">{cardIndex + 1}</td>
      <td className="px-3 py-2">
        <CardTypeTag
          type={card.autoClassifiedType}
          isEditable={true}
          onChange={(newType) => onTypeChange(cardIndex, newType)}
          isLoading={card.isRegenerating}
          showRerunIndicator={showRerunIndicator}
        />
      </td>
      {fields.map(field => {
        const isEditing =
          editingCell?.cardIndex === cardIndex &&
          editingCell?.field === field;
        const value = card.fields[field] || '';

        return (
          <td
            key={field}
            className="px-3 py-2 text-sm text-gray-900"
            onClick={() => onCellClick(cardIndex, field)}
          >
            {isEditing ? (
              <textarea
                value={value}
                onChange={e => onUpdateField(cardIndex, field, e.target.value)}
                onBlur={onCellBlur}
                onKeyDown={onKeyDown}
                autoFocus
                aria-label={`Edit ${field} for card ${cardIndex + 1}`}
                className="w-full min-w-[200px] px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
                rows={Math.max(2, value.split('\n').length)}
              />
            ) : (
              <div
                role="button"
                tabIndex={0}
                aria-label={`Click to edit ${field} for card ${cardIndex + 1}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onCellClick(cardIndex, field);
                  }
                }}
                className="min-h-[24px] cursor-pointer hover:bg-blue-50 rounded px-1 whitespace-pre-wrap"
                title="Click to edit"
              >
                {value || <span className="text-gray-400 italic">empty</span>}
              </div>
            )}
          </td>
        );
      })}
      <td className="px-3 py-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onToggleCore(cardIndex)}
            className="text-xl hover:scale-110 transition-transform"
            aria-label={card.isCore ? 'Remove from Core (mark as Extra)' : 'Mark as Core priority'}
            title={card.isCore ? 'Core - click to mark as Extra' : 'Extra - click to mark as Core'}
          >
            {card.isCore ? '⭐' : '☆'}
          </button>
          <button
            type="button"
            onClick={() => onRemove(cardIndex)}
            className="text-red-500 hover:text-red-700 text-sm"
            disabled={cardsLength <= 1}
            aria-label={`Remove card ${cardIndex + 1}`}
            aria-disabled={cardsLength <= 1}
          >
            Remove
          </button>
        </div>
      </td>
    </tr>
  );
});

interface GeneratedTableProps {
  cards: GeneratedCard[];
  fields: string[];
  onCardsChange: (cards: GeneratedCard[]) => void;
  onRegenerateCard: (cardIndex: number, targetType: CardType) => Promise<void>;
}

export function GeneratedTable({
  cards,
  fields,
  onCardsChange,
  onRegenerateCard,
}: GeneratedTableProps) {
  const [editingCell, setEditingCell] = useState<{
    cardIndex: number;
    field: string;
  } | null>(null);

  // Generate stable IDs for cards using a ref
  // IDs are regenerated only when the cards array length changes
  const cardIdsRef = useRef<string[]>([]);
  if (cardIdsRef.current.length !== cards.length) {
    cardIdsRef.current = cards.map(() => crypto.randomUUID());
  }

  const updateField = useCallback((cardIndex: number, field: string, value: string) => {
    const newCards = [...cards];
    newCards[cardIndex] = {
      ...newCards[cardIndex],
      fields: {
        ...newCards[cardIndex].fields,
        [field]: value,
      },
    };
    onCardsChange(newCards);
  }, [cards, onCardsChange]);

  // Handle card type change
  const handleTypeChange = useCallback(async (cardIndex: number, newType: CardType) => {
    const card = cards[cardIndex];
    const currentType = card.autoClassifiedType;

    if (currentType === newType) return;

    if (needsRegeneration(currentType, newType)) {
      // Need to regenerate - call the API
      await onRegenerateCard(cardIndex, newType);
    } else {
      // Just update the type locally (word <-> phrase)
      const newCards = [...cards];
      newCards[cardIndex] = {
        ...newCards[cardIndex],
        autoClassifiedType: newType,
        tags: [newType],
      };
      onCardsChange(newCards);
    }
  }, [cards, onCardsChange, onRegenerateCard]);

  const removeCard = useCallback((index: number) => {
    onCardsChange(cards.filter((_, i) => i !== index));
  }, [cards, onCardsChange]);

  const handleRemove = useCallback((cardIndex: number) => {
    if (window.confirm('Are you sure you want to remove this card?')) {
      removeCard(cardIndex);
    }
  }, [removeCard]);

  const handleToggleCore = useCallback((cardIndex: number) => {
    const newCards = [...cards];
    newCards[cardIndex] = {
      ...newCards[cardIndex],
      isCore: !newCards[cardIndex].isCore,
    };
    onCardsChange(newCards);
  }, [cards, onCardsChange]);

  const addEmptyCard = useCallback(() => {
    const emptyFields: Record<string, string> = {};
    fields.forEach(field => {
      emptyFields[field] = '';
    });
    onCardsChange([...cards, { fields: emptyFields, tags: ['word'], autoClassifiedType: 'word', isCore: true }]);
  }, [cards, fields, onCardsChange]);

  const handleCellClick = useCallback((cardIndex: number, field: string) => {
    setEditingCell({ cardIndex, field });
  }, []);

  const handleCellBlur = useCallback(() => {
    setEditingCell(null);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      setEditingCell(null);
    }
  }, []);

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto border border-gray-300 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                #
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[140px]">
                Type
              </th>
              {fields.map(field => (
                <th
                  key={field}
                  className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[150px]"
                >
                  {field}
                </th>
              ))}
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {cards.map((card, cardIndex) => (
              <TableRow
                key={cardIdsRef.current[cardIndex]}
                card={card}
                cardIndex={cardIndex}
                cardId={cardIdsRef.current[cardIndex]}
                fields={fields}
                editingCell={editingCell}
                cardsLength={cards.length}
                onCellClick={handleCellClick}
                onCellBlur={handleCellBlur}
                onKeyDown={handleKeyDown}
                onUpdateField={updateField}
                onTypeChange={handleTypeChange}
                onRemove={handleRemove}
                onToggleCore={handleToggleCore}
              />
            ))}
          </tbody>
        </table>
      </div>

      <button
        type="button"
        onClick={addEmptyCard}
        aria-label="Add a new empty card row"
        className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-500 transition-colors"
      >
        + Add Row
      </button>
    </div>
  );
}
