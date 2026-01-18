'use client';

import { useMigration } from '@/hooks/useMigration';
import { MigrationCard } from '@/components/MigrationCard';
import Link from 'next/link';

export default function MigratePage() {
  const {
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
  } = useMigration();

  const currentNote = notes[currentNoteIndex];

  // Handle deck selection
  const handleDeckChange = async (deckName: string) => {
    setSelectedDeck(deckName);
    if (deckName) {
      await loadNotes(deckName);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Note Migration</h1>
              <p className="text-sm text-gray-500 mt-1">
                Migrate old notes to the new Japanese Vocabulary (Agent) format
              </p>
            </div>
            <Link
              href="/"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Back to Card Generator
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* Connection Status */}
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Anki Connection:</span>
                {isCheckingConnection ? (
                  <span className="text-sm text-gray-500">Checking...</span>
                ) : connectionStatus?.connected ? (
                  <span className="flex items-center gap-2 text-sm text-green-600">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    Connected
                  </span>
                ) : (
                  <span className="flex items-center gap-2 text-sm text-red-600">
                    <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                    {connectionStatus?.message || 'Not connected'}
                  </span>
                )}
              </div>
              <button
                onClick={checkConnection}
                disabled={isCheckingConnection}
                className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {!connectionStatus?.connected ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-medium text-yellow-800 mb-2">
              AnkiConnect Not Available
            </h3>
            <p className="text-sm text-yellow-700 mb-4">
              Please make sure Anki is running with the AnkiConnect add-on installed (code: 2055492159).
            </p>
            <button
              onClick={checkConnection}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
            >
              Try Again
            </button>
          </div>
        ) : (
          <>
            {/* Deck Selection */}
            <div className="mb-6">
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center gap-4">
                  <label className="text-sm font-medium text-gray-700">Select Deck:</label>
                  <select
                    value={selectedDeck || ''}
                    onChange={(e) => handleDeckChange(e.target.value)}
                    disabled={isLoadingDecks || isLoadingNotes}
                    className="flex-1 max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    <option value="">-- Select a deck --</option>
                    {decks.map((deck) => (
                      <option key={deck.name} value={deck.name}>
                        {deck.name} ({deck.note_count} notes)
                      </option>
                    ))}
                  </select>
                  {isLoadingDecks && (
                    <span className="text-sm text-gray-500">Loading decks...</span>
                  )}
                </div>
                {decksError && (
                  <p className="mt-2 text-sm text-red-600">{decksError}</p>
                )}
                {decks.length === 0 && !isLoadingDecks && !decksError && (
                  <p className="mt-2 text-sm text-gray-500">
                    No decks found with the old note type. Make sure you have notes with &quot;Philippe&apos;s Japanese v3&quot; note type.
                  </p>
                )}
              </div>
            </div>

            {/* Source Selection */}
            {config?.sources && config.sources.length > 0 && (
              <div className="mb-6">
                <div className="bg-white rounded-lg shadow-sm p-4">
                  <div className="flex items-center gap-4">
                    <label className="text-sm font-medium text-gray-700">Source Tag:</label>
                    <select
                      value={source}
                      onChange={(e) => setSource(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {config.sources.map((s) => (
                        <option key={s.tag} value={s.tag}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                    <span className="text-sm text-gray-500">
                      This tag will be added to all approved cards
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Progress Bar */}
            {selectedDeck && totalCount > 0 && (
              <div className="mb-6">
                <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
                  {/* Generation progress */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">Generating previews</span>
                      <span className="text-sm text-gray-500">
                        {generatedCount} / {totalCount}
                        {generatedCount < totalCount && ' (running in background...)'}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${(generatedCount / totalCount) * 100}%` }}
                      />
                    </div>
                  </div>
                  {/* Approval progress */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">Reviewed</span>
                      <span className="text-sm text-gray-500">
                        {approvedCount + skippedCount} / {totalCount}
                        ({approvedCount} approved, {skippedCount} skipped)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-green-500 transition-all duration-300"
                        style={{ width: `${((approvedCount + skippedCount) / totalCount) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Note Navigation */}
            {selectedDeck && notes.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentNoteIndex(Math.max(0, currentNoteIndex - 1))}
                      disabled={currentNoteIndex === 0}
                      className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="text-sm text-gray-600">
                      Note {currentNoteIndex + 1} of {totalCount}
                    </span>
                    <button
                      onClick={() => setCurrentNoteIndex(Math.min(totalCount - 1, currentNoteIndex + 1))}
                      disabled={currentNoteIndex === totalCount - 1}
                      className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600">Jump to:</label>
                    <select
                      value={currentNoteIndex}
                      onChange={(e) => setCurrentNoteIndex(Number(e.target.value))}
                      className="px-2 py-1 text-sm border border-gray-300 rounded-md"
                    >
                      {notes.map((note, index) => (
                        <option key={note.note.note_id} value={index}>
                          {index + 1}. {note.note.old_fields['Kana']?.slice(0, 20) || 'Note'}{' '}
                          [{note.status}]
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Loading Notes */}
            {isLoadingNotes && (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading notes...</p>
              </div>
            )}

            {/* Notes Error */}
            {notesError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700">{notesError}</p>
              </div>
            )}

            {/* Current Note Card */}
            {currentNote && !isLoadingNotes && (
              <MigrationCard
                noteState={currentNote}
                onRegenerate={() => regeneratePreview(currentNoteIndex)}
                onUpdateField={(field, value) => updatePreviewField(currentNoteIndex, field, value)}
                onUpdateCardType={(cardType) => updateCardType(currentNoteIndex, cardType)}
                onToggleCore={() => toggleCore(currentNoteIndex)}
                onApprove={() => approveNote(currentNoteIndex)}
                onSkip={() => skipNote(currentNoteIndex)}
              />
            )}

            {/* All Done Message */}
            {selectedDeck && totalCount > 0 && approvedCount + skippedCount === totalCount && (
              <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  Migration Complete!
                </h3>
                <p className="text-sm text-green-700">
                  Processed all {totalCount} notes ({approvedCount} approved, {skippedCount} skipped).
                </p>
              </div>
            )}

            {/* No Deck Selected */}
            {!selectedDeck && decks.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <p className="text-gray-600">Select a deck above to start migrating notes.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
