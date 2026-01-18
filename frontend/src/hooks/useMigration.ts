'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { AnkiConfig, CardType, DeckInfo, MigrationNote, MigrationNoteState, PreviewResponse, BatchPreviewItem } from '@/types';
import {
  checkAnkiConnection,
  fetchConfig,
  getMigrationDecks,
  getMigrationNotes,
  generateMigrationPreview,
  generateBatchMigrationPreview,
  approveMigration,
  ConnectionStatus,
} from '@/lib/api';

const BATCH_SIZE = 10;

interface UseMigrationReturn {
  // Connection status
  connectionStatus: ConnectionStatus | null;
  isCheckingConnection: boolean;
  checkConnection: () => Promise<void>;

  // Config and source
  config: AnkiConfig | null;
  source: string;
  setSource: (source: string) => void;

  // Decks
  decks: DeckInfo[];
  isLoadingDecks: boolean;
  decksError: string | null;
  loadDecks: () => Promise<void>;

  // Selected deck
  selectedDeck: string | null;
  setSelectedDeck: (deck: string | null) => void;

  // Notes
  notes: MigrationNoteState[];
  isLoadingNotes: boolean;
  notesError: string | null;
  loadNotes: (deckName: string) => Promise<void>;

  // Current note index for navigation
  currentNoteIndex: number;
  setCurrentNoteIndex: (index: number) => void;

  // Actions
  regeneratePreview: (noteIndex: number) => Promise<void>;
  updatePreviewField: (noteIndex: number, field: string, value: string) => void;
  updateCardType: (noteIndex: number, cardType: CardType) => void;
  toggleCore: (noteIndex: number) => void;
  approveNote: (noteIndex: number) => Promise<void>;
  skipNote: (noteIndex: number) => void;

  // Progress
  approvedCount: number;
  skippedCount: number;
  totalCount: number;
  generatedCount: number;
}

export function useMigration(): UseMigrationReturn {
  // Connection status
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [isCheckingConnection, setIsCheckingConnection] = useState(false);

  // Config and source
  const [config, setConfig] = useState<AnkiConfig | null>(null);
  const [source, setSource] = useState<string>('japanese_class');

  // Decks
  const [decks, setDecks] = useState<DeckInfo[]>([]);
  const [isLoadingDecks, setIsLoadingDecks] = useState(false);
  const [decksError, setDecksError] = useState<string | null>(null);
  const [selectedDeck, setSelectedDeck] = useState<string | null>(null);

  // Notes
  const [notes, setNotes] = useState<MigrationNoteState[]>([]);
  const [isLoadingNotes, setIsLoadingNotes] = useState(false);
  const [notesError, setNotesError] = useState<string | null>(null);

  // Navigation
  const [currentNoteIndex, setCurrentNoteIndex] = useState(0);

  // Background generation control
  const isGeneratingRef = useRef(false);
  const abortGenerationRef = useRef(false);

  // Keep a stable reference to current notes for async operations
  const notesRef = useRef<MigrationNoteState[]>(notes);
  useEffect(() => {
    notesRef.current = notes;
  }, [notes]);

  // Check Anki connection
  const checkConnection = useCallback(async () => {
    setIsCheckingConnection(true);
    try {
      const status = await checkAnkiConnection();
      setConnectionStatus(status);
    } catch (err) {
      setConnectionStatus({
        connected: false,
        message: err instanceof Error ? err.message : 'Connection check failed',
      });
    } finally {
      setIsCheckingConnection(false);
    }
  }, []);

  // Load decks
  const loadDecks = useCallback(async () => {
    setIsLoadingDecks(true);
    setDecksError(null);
    try {
      const deckList = await getMigrationDecks();
      setDecks(deckList);
    } catch (err) {
      setDecksError(err instanceof Error ? err.message : 'Failed to load decks');
    } finally {
      setIsLoadingDecks(false);
    }
  }, []);

  // Load notes for a deck
  const loadNotes = useCallback(async (deckName: string) => {
    // Stop any ongoing background generation
    abortGenerationRef.current = true;

    setIsLoadingNotes(true);
    setNotesError(null);
    setNotes([]);
    setCurrentNoteIndex(0);

    try {
      const noteList = await getMigrationNotes(deckName);
      // Convert to note states
      const noteStates: MigrationNoteState[] = noteList.map(note => ({
        note,
        preview: null,
        status: 'pending',
        isCore: true,
      }));
      setNotes(noteStates);
      // Reset abort flag for new generation
      abortGenerationRef.current = false;
    } catch (err) {
      setNotesError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setIsLoadingNotes(false);
    }
  }, []);

  // Generate preview for a single note (internal helper)
  const generateSinglePreview = useCallback(async (
    noteState: MigrationNoteState,
    noteIndex: number
  ): Promise<PreviewResponse | null> => {
    try {
      const preview = await generateMigrationPreview({
        noteId: noteState.note.note_id,
        rawInput: noteState.note.old_fields['Kana'] || '',
        // Don't pass old translations - let agent generate new ones
        extraNotes: noteState.note.old_fields['Extra'] || undefined,
        preserveSound: noteState.note.sound || undefined,
        preserveSoundExample: noteState.note.sound_example || undefined,
      });
      return preview;
    } catch (err) {
      console.error(`Failed to generate preview for note ${noteIndex}:`, err);
      return null;
    }
  }, []);

  // Background batch generation of all previews
  useEffect(() => {
    if (notes.length === 0 || isGeneratingRef.current) return;

    const generateAllPreviews = async () => {
      isGeneratingRef.current = true;

      // Find all notes that need preview generation
      const pendingIndices: number[] = [];
      for (let i = 0; i < notes.length; i++) {
        const note = notes[i];
        if (
          note.status === 'pending' &&
          note.preview === null
        ) {
          pendingIndices.push(i);
        }
      }

      // Process in batches of BATCH_SIZE
      for (let batchStart = 0; batchStart < pendingIndices.length; batchStart += BATCH_SIZE) {
        // Check for abort
        if (abortGenerationRef.current) break;

        const batchIndices = pendingIndices.slice(batchStart, batchStart + BATCH_SIZE);

        // Mark all notes in this batch as 'previewing'
        setNotes(prev => {
          const newNotes = [...prev];
          for (const idx of batchIndices) {
            if (newNotes[idx].status === 'pending') {
              newNotes[idx] = { ...newNotes[idx], status: 'previewing' };
            }
          }
          return newNotes;
        });

        // Build batch request items - use ref to get current state
        const currentNotes = notesRef.current;
        const batchItems: BatchPreviewItem[] = batchIndices.map(idx => {
          const noteState = currentNotes[idx];
          return {
            noteId: noteState.note.note_id,
            rawInput: noteState.note.old_fields['Kana'] || '',
            // Don't pass old translations - let agent generate new ones
            extraNotes: noteState.note.old_fields['Extra'] || undefined,
            preserveSound: noteState.note.sound || undefined,
            preserveSoundExample: noteState.note.sound_example || undefined,
          };
        });

        try {
          const response = await generateBatchMigrationPreview(batchItems);

          // Check abort again after async operation
          if (abortGenerationRef.current) break;

          // Update notes with results
          setNotes(prev => {
            const newNotes = [...prev];

            for (const result of response.results) {
              // Find the index for this note_id
              const noteIdx = batchIndices.find(idx =>
                newNotes[idx].note.note_id === result.note_id
              );

              if (noteIdx !== undefined) {
                if (result.success && result.new_fields) {
                  newNotes[noteIdx] = {
                    ...newNotes[noteIdx],
                    preview: {
                      note_id: result.note_id,
                      new_fields: result.new_fields,
                      auto_classified_type: result.auto_classified_type!,
                    },
                    status: 'ready',
                  };
                } else {
                  newNotes[noteIdx] = {
                    ...newNotes[noteIdx],
                    status: 'error',
                    error: result.error || 'Preview generation failed',
                  };
                }
              }
            }

            return newNotes;
          });

        } catch (error) {
          // Batch request failed - mark all items in batch as error
          setNotes(prev => {
            const newNotes = [...prev];
            for (const idx of batchIndices) {
              newNotes[idx] = {
                ...newNotes[idx],
                status: 'error',
                error: error instanceof Error ? error.message : 'Batch preview failed',
              };
            }
            return newNotes;
          });
        }
      }

      isGeneratingRef.current = false;
    };

    generateAllPreviews();
  }, [notes.filter(n => n.status === 'pending' && n.preview === null).length]); // Trigger when pending notes needing preview changes

  // Regenerate preview for a specific note
  const regeneratePreview = useCallback(async (noteIndex: number) => {
    // Use ref to get current state to avoid stale closure
    const noteState = notesRef.current[noteIndex];
    if (!noteState) return;

    // Mark as previewing
    setNotes(prev => {
      const newNotes = [...prev];
      newNotes[noteIndex] = { ...newNotes[noteIndex], preview: null, status: 'previewing', error: undefined };
      return newNotes;
    });

    const preview = await generateSinglePreview(noteState, noteIndex);

    setNotes(prev => {
      const newNotes = [...prev];
      if (preview) {
        newNotes[noteIndex] = { ...newNotes[noteIndex], preview, status: 'ready' };
      } else {
        newNotes[noteIndex] = {
          ...newNotes[noteIndex],
          status: 'error',
          error: 'Preview generation failed',
        };
      }
      return newNotes;
    });
  }, [generateSinglePreview]);

  // Update a field in the preview
  const updatePreviewField = useCallback((noteIndex: number, field: string, value: string) => {
    setNotes(prev => {
      const newNotes = [...prev];
      const current = newNotes[noteIndex];
      if (!current.preview) return prev;

      newNotes[noteIndex] = {
        ...current,
        preview: {
          ...current.preview,
          new_fields: {
            ...current.preview.new_fields,
            [field]: value,
          },
        },
      };
      return newNotes;
    });
  }, []);

  // Update the card type in the preview
  const updateCardType = useCallback((noteIndex: number, cardType: CardType) => {
    setNotes(prev => {
      const newNotes = [...prev];
      const current = newNotes[noteIndex];
      if (!current.preview) return prev;

      newNotes[noteIndex] = {
        ...current,
        preview: {
          ...current.preview,
          auto_classified_type: cardType,
        },
      };
      return newNotes;
    });
  }, []);

  // Toggle core/extra status
  const toggleCore = useCallback((noteIndex: number) => {
    setNotes(prev => {
      const newNotes = [...prev];
      const current = newNotes[noteIndex];
      newNotes[noteIndex] = { ...current, isCore: !current.isCore };
      return newNotes;
    });
  }, []);

  // Approve a note (commit to Anki)
  const approveNote = useCallback(async (noteIndex: number) => {
    // Use ref to get current state to avoid stale closure
    const noteState = notesRef.current[noteIndex];
    if (!noteState || !noteState.preview || noteState.status === 'approving') return;

    setNotes(prev => {
      const newNotes = [...prev];
      newNotes[noteIndex] = { ...newNotes[noteIndex], status: 'approving' };
      return newNotes;
    });

    try {
      await approveMigration({
        noteId: noteState.note.note_id,
        newFields: noteState.preview.new_fields,
        tags: [source, noteState.isCore !== false ? 'core' : 'extra', noteState.preview.auto_classified_type],
      });

      setNotes(prev => {
        const newNotes = [...prev];
        newNotes[noteIndex] = { ...newNotes[noteIndex], status: 'approved' };
        return newNotes;
      });

      // Move to next non-approved/non-skipped note - use ref for current state
      const currentNotes = notesRef.current;
      const nextIndex = currentNotes.findIndex(
        (n, i) => i > noteIndex && n.status !== 'approved' && n.status !== 'skipped'
      );
      if (nextIndex !== -1) {
        setCurrentNoteIndex(nextIndex);
      }
    } catch (err) {
      setNotes(prev => {
        const newNotes = [...prev];
        newNotes[noteIndex] = {
          ...newNotes[noteIndex],
          status: 'error',
          error: err instanceof Error ? err.message : 'Approval failed',
        };
        return newNotes;
      });
    }
  }, [source]);

  // Skip a note
  const skipNote = useCallback((noteIndex: number) => {
    setNotes(prev => {
      const newNotes = [...prev];
      newNotes[noteIndex] = { ...newNotes[noteIndex], status: 'skipped' };
      return newNotes;
    });

    // Move to next non-approved/non-skipped note - use ref for current state
    const currentNotes = notesRef.current;
    const nextIndex = currentNotes.findIndex(
      (n, i) => i > noteIndex && n.status !== 'approved' && n.status !== 'skipped'
    );
    if (nextIndex !== -1) {
      setCurrentNoteIndex(nextIndex);
    }
  }, []);

  // Check connection on mount
  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  // Fetch config on mount (for source options)
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const configData = await fetchConfig();
        setConfig(configData);
        if (configData.defaultSource) {
          setSource(configData.defaultSource);
        }
      } catch (err) {
        console.error('Failed to load config:', err);
      }
    };
    loadConfig();
  }, []);

  // Load decks when connected
  useEffect(() => {
    if (connectionStatus?.connected) {
      loadDecks();
    }
  }, [connectionStatus?.connected, loadDecks]);

  // Calculate progress
  const approvedCount = notes.filter(n => n.status === 'approved').length;
  const skippedCount = notes.filter(n => n.status === 'skipped').length;
  const generatedCount = notes.filter(n => n.status === 'ready' || n.status === 'approved' || n.status === 'skipped').length;
  const totalCount = notes.length;

  return {
    connectionStatus,
    isCheckingConnection,
    checkConnection,
    config,
    source,
    setSource,
    decks,
    isLoadingDecks,
    decksError,
    loadDecks,
    selectedDeck,
    setSelectedDeck,
    notes,
    isLoadingNotes,
    notesError,
    loadNotes,
    currentNoteIndex,
    setCurrentNoteIndex,
    regeneratePreview,
    updatePreviewField,
    updateCardType,
    toggleCore,
    approveNote,
    skipNote,
    approvedCount,
    skippedCount,
    totalCount,
    generatedCount,
  };
}
