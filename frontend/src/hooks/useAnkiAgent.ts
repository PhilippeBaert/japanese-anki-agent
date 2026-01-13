'use client';

import { useState, useEffect, useCallback } from 'react';
import { DraftCard, GeneratedCard, AnkiConfig, CardType } from '@/types';
import { fetchConfig, generateCards, exportCSV, regenerateCard } from '@/lib/api';

type View = 'draft' | 'generated';

interface UseAnkiAgentReturn {
  // Config
  config: AnkiConfig | null;
  configLoading: boolean;
  configError: string | null;

  // Draft cards
  draftCards: DraftCard[];
  setDraftCards: (cards: DraftCard[]) => void;

  // Generated cards
  generatedCards: GeneratedCard[];
  setGeneratedCards: (cards: GeneratedCard[]) => void;

  // Filename
  filename: string;
  setFilename: (name: string) => void;

  // Source
  source: string;
  setSource: (source: string) => void;

  // View state
  view: View;
  setView: (view: View) => void;

  // Actions
  handleGenerate: () => Promise<void>;
  handleExport: () => Promise<void>;
  handleBackToDraft: () => void;
  handleRegenerateCard: (cardIndex: number, targetType: CardType) => Promise<void>;

  // Loading states
  isGenerating: boolean;
  isExporting: boolean;

  // Errors
  generateError: string | null;
  exportError: string | null;
}

function createEmptyDraftCard(): DraftCard {
  return {
    id: crypto.randomUUID(),
    rawInput: '',
    fixedEnglish: '',
    fixedDutch: '',
    extraNotes: '',
  };
}

export function useAnkiAgent(): UseAnkiAgentReturn {
  // Config state
  const [config, setConfig] = useState<AnkiConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);

  // Draft cards
  const [draftCards, setDraftCards] = useState<DraftCard[]>([createEmptyDraftCard()]);

  // Generated cards
  const [generatedCards, setGeneratedCards] = useState<GeneratedCard[]>([]);

  // Store original drafts for regeneration
  const [originalDrafts, setOriginalDrafts] = useState<DraftCard[]>([]);

  // Filename
  const [filename, setFilename] = useState('anki_cards');

  // Source - initialized to empty, set from config after load
  const [source, setSource] = useState<string>('');

  // View
  const [view, setView] = useState<View>('draft');

  // Loading states
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Errors
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Load config on mount
  useEffect(() => {
    async function loadConfig() {
      try {
        setConfigLoading(true);
        const data = await fetchConfig();
        setConfig(data);
        // Set default source from config
        if (data.defaultSource) {
          setSource(data.defaultSource);
        } else if (data.sources && data.sources.length > 0) {
          setSource(data.sources[0].tag);
        }
        setConfigError(null);
      } catch (err) {
        setConfigError(err instanceof Error ? err.message : 'Failed to load config');
      } finally {
        setConfigLoading(false);
      }
    }
    loadConfig();
  }, []);

  // Generate cards
  const handleGenerate = useCallback(async () => {
    if (!config) return;

    // Filter out empty cards
    const validCards = draftCards.filter(card => card.rawInput.trim());
    if (validCards.length === 0) {
      setGenerateError('Please enter at least one card with input');
      return;
    }

    setIsGenerating(true);
    setGenerateError(null);

    try {
      const request = {
        draft_cards: validCards.map(card => ({
          raw_input: card.rawInput,
          fixed_english: card.fixedEnglish || undefined,
          fixed_dutch: card.fixedDutch || undefined,
          extra_notes: card.extraNotes || undefined,
        })),
        filename: filename || undefined,
      };

      const response = await generateCards(request);

      // Store original drafts for potential regeneration
      setOriginalDrafts(validCards);

      // Convert response cards and add tracking fields
      const cardsWithTracking = response.cards.map((card: { fields: Record<string, string>; tags: string[]; auto_classified_type?: CardType }) => ({
        fields: card.fields,
        tags: card.tags,
        autoClassifiedType: card.auto_classified_type || 'word',
        originalType: card.auto_classified_type || 'word',
      }));

      setGeneratedCards(cardsWithTracking);
      setFilename(response.filename);
      setView('generated');
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  }, [config, draftCards, filename]);

  // Export to CSV
  const handleExport = useCallback(async () => {
    if (generatedCards.length === 0) {
      setExportError('No cards to export');
      return;
    }

    setIsExporting(true);
    setExportError(null);

    try {
      const blob = await exportCSV({
        cards: generatedCards,
        filename: filename || 'anki_cards',
        source: source || undefined,
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename || 'anki_cards'}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  }, [generatedCards, filename, source]);

  // Go back to draft view
  const handleBackToDraft = useCallback(() => {
    setView('draft');
    setGenerateError(null);
    setExportError(null);
  }, []);

  // Regenerate a single card with a new type
  const handleRegenerateCard = useCallback(async (cardIndex: number, targetType: CardType) => {
    const draft = originalDrafts[cardIndex];
    if (!draft) {
      return;
    }

    // Set loading state for this card
    setGeneratedCards(prev => {
      const newCards = [...prev];
      newCards[cardIndex] = { ...newCards[cardIndex], isRegenerating: true };
      return newCards;
    });

    try {
      const regenerated = await regenerateCard({
        raw_input: draft.rawInput,
        fixed_english: draft.fixedEnglish || undefined,
        fixed_dutch: draft.fixedDutch || undefined,
        extra_notes: draft.extraNotes || undefined,
        target_type: targetType,
      });

      // Update the card with regenerated content
      setGeneratedCards(prev => {
        const newCards = [...prev];
        newCards[cardIndex] = {
          ...regenerated,
          originalType: regenerated.autoClassifiedType,
          isRegenerating: false,
        };
        return newCards;
      });
    } catch (err) {
      // Reset loading state on error
      setGeneratedCards(prev => {
        const newCards = [...prev];
        newCards[cardIndex] = { ...newCards[cardIndex], isRegenerating: false };
        return newCards;
      });
    }
  }, [originalDrafts]);

  return {
    config,
    configLoading,
    configError,
    draftCards,
    setDraftCards,
    generatedCards,
    setGeneratedCards,
    filename,
    setFilename,
    source,
    setSource,
    view,
    setView,
    handleGenerate,
    handleExport,
    handleBackToDraft,
    handleRegenerateCard,
    isGenerating,
    isExporting,
    generateError,
    exportError,
  };
}
