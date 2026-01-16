'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { DeckInfo, MigrationNote, MigrationNoteState, PreviewResponse } from '@/types';
import {
  checkAnkiConnection,
  getMigrationDecks,
  getMigrationNotes,
  generateMigrationPreview,
  approveMigration,
  ConnectionStatus,
} from '@/lib/api';

interface UseMigrationReturn {
  // Connection status
  connectionStatus: ConnectionStatus | null;
  isCheckingConnection: boolean;
  checkConnection: () => Promise<void>;

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
        fixedEnglish: noteState.note.old_fields['English'] || undefined,
        fixedDutch: noteState.note.old_fields['Nederlands'] || undefined,
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

  // Background sequential generation of all previews
  useEffect(() => {
    if (notes.length === 0 || isGeneratingRef.current) return;

    const generateAllPreviews = async () => {
      isGeneratingRef.current = true;

      for (let i = 0; i < notes.length; i++) {
        // Check if we should abort
        if (abortGenerationRef.current) {
          break;
        }

        // Get current state of this note (it may have changed)
        const currentNoteState = notes[i];

        // Skip if already has preview, approved, or skipped
        if (
          currentNoteState.status === 'ready' ||
          currentNoteState.status === 'approved' ||
          currentNoteState.status === 'skipped' ||
          currentNoteState.preview !== null
        ) {
          continue;
        }

        // Mark as previewing
        setNotes(prev => {
          const newNotes = [...prev];
          if (newNotes[i].status === 'pending') {
            newNotes[i] = { ...newNotes[i], status: 'previewing' };
          }
          return newNotes;
        });

        // Generate the preview
        const preview = await generateSinglePreview(currentNoteState, i);

        // Check abort again after async operation
        if (abortGenerationRef.current) {
          break;
        }

        // Update with result
        setNotes(prev => {
          const newNotes = [...prev];
          if (preview) {
            newNotes[i] = { ...newNotes[i], preview, status: 'ready' };
          } else {
            newNotes[i] = {
              ...newNotes[i],
              status: 'error',
              error: 'Preview generation failed',
            };
          }
          return newNotes;
        });
      }

      isGeneratingRef.current = false;
    };

    generateAllPreviews();
  }, [notes.length, generateSinglePreview]); // Only trigger when notes array length changes

  // Regenerate preview for a specific note
  const regeneratePreview = useCallback(async (noteIndex: number) => {
    const noteState = notes[noteIndex];
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
  }, [notes, generateSinglePreview]);

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

  // Approve a note (commit to Anki)
  const approveNote = useCallback(async (noteIndex: number) => {
    const noteState = notes[noteIndex];
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
        tags: [noteState.preview.auto_classified_type],
      });

      setNotes(prev => {
        const newNotes = [...prev];
        newNotes[noteIndex] = { ...newNotes[noteIndex], status: 'approved' };
        return newNotes;
      });

      // Move to next non-approved/non-skipped note
      const nextIndex = notes.findIndex(
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
  }, [notes]);

  // Skip a note
  const skipNote = useCallback((noteIndex: number) => {
    setNotes(prev => {
      const newNotes = [...prev];
      newNotes[noteIndex] = { ...newNotes[noteIndex], status: 'skipped' };
      return newNotes;
    });

    // Move to next non-approved/non-skipped note
    const nextIndex = notes.findIndex(
      (n, i) => i > noteIndex && n.status !== 'approved' && n.status !== 'skipped'
    );
    if (nextIndex !== -1) {
      setCurrentNoteIndex(nextIndex);
    }
  }, [notes]);

  // Check connection on mount
  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

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
    approveNote,
    skipNote,
    approvedCount,
    skippedCount,
    totalCount,
    generatedCount,
  };
}
