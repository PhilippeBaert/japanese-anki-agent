'use client';

import { DraftCard } from '@/types';
import { DraftCardForm } from './DraftCardForm';

interface DraftCardListProps {
  cards: DraftCard[];
  onCardsChange: (cards: DraftCard[]) => void;
}

export function DraftCardList({ cards, onCardsChange }: DraftCardListProps) {
  const createEmptyCard = (): DraftCard => ({
    id: crypto.randomUUID(),
    rawInput: '',
    fixedEnglish: '',
    fixedDutch: '',
    extraNotes: '',
  });

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

  return (
    <div className="space-y-4">
      {cards.map((card, index) => (
        <DraftCardForm
          key={card.id}
          card={card}
          index={index}
          onChange={updatedCard => updateCard(index, updatedCard)}
          onRemove={() => removeCard(index)}
          canRemove={cards.length > 1}
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
