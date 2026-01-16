'use client';

import { useRef, useEffect, useCallback } from 'react';
import { DraftCard } from '@/types';
import { DraftCardForm, DraftCardFormHandle } from './DraftCardForm';

interface DraftCardListProps {
  cards: DraftCard[];
  onCardsChange: (cards: DraftCard[]) => void;
}

export function DraftCardList({ cards, onCardsChange }: DraftCardListProps) {
  const cardRefs = useRef<Map<string, DraftCardFormHandle>>(new Map());
  const pendingFocusId = useRef<string | null>(null);

  const createEmptyCard = (): DraftCard => ({
    id: crypto.randomUUID(),
    rawInput: '',
    fixedEnglish: '',
    fixedDutch: '',
    extraNotes: '',
  });

  useEffect(() => {
    if (pendingFocusId.current) {
      const ref = cardRefs.current.get(pendingFocusId.current);
      if (ref) {
        ref.focusInput();
        pendingFocusId.current = null;
      }
    }
  }, [cards]);

  const updateCard = (index: number, card: DraftCard) => {
    const newCards = [...cards];
    newCards[index] = card;
    onCardsChange(newCards);
  };

  const removeCard = (index: number) => {
    onCardsChange(cards.filter((_, i) => i !== index));
  };

  const addCard = () => {
    onCardsChange([...cards, createEmptyCard()]);
  };

  const addCardAndFocus = useCallback(() => {
    const newCard = createEmptyCard();
    pendingFocusId.current = newCard.id;
    onCardsChange([...cards, newCard]);
  }, [cards, onCardsChange]);

  return (
    <div className="space-y-4">
      {cards.map((card, index) => (
        <DraftCardForm
          key={card.id}
          ref={el => {
            if (el) {
              cardRefs.current.set(card.id, el);
            } else {
              cardRefs.current.delete(card.id);
            }
          }}
          card={card}
          index={index}
          onChange={updatedCard => updateCard(index, updatedCard)}
          onRemove={() => removeCard(index)}
          canRemove={cards.length > 1}
          onAddCardAfter={addCardAndFocus}
        />
      ))}

      <button
        type="button"
        onClick={addCard}
        className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-500 transition-colors"
      >
        + Add Card
      </button>
    </div>
  );
}
