'use client';

import { DraftCardList } from '@/components/DraftCardList';
import { GeneratedTable } from '@/components/GeneratedTable';
import { ExportButton } from '@/components/ExportButton';
import { useAnkiAgent } from '@/hooks/useAnkiAgent';

export default function Home() {
  const {
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
    handleGenerate,
    handleExport,
    handleBackToDraft,
    handleRegenerateCard,
    isGenerating,
    isExporting,
    generateError,
    exportError,
  } = useAnkiAgent();

  if (configLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading configuration...</div>
      </div>
    );
  }

  if (configError || !config) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600 text-center">
          <p className="text-lg font-semibold">Failed to load configuration</p>
          <p className="text-sm mt-2">{configError}</p>
          <p className="text-sm mt-2">Make sure the backend is running at http://localhost:8000</p>
        </div>
      </div>
    );
  }

  return (
    <main className="mx-auto px-4 py-8 lg:px-8 max-w-7xl 2xl:max-w-none">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Japanese Anki Agent</h1>
      <p className="text-gray-600 mb-6">
        Generate Japanese Anki flashcards with AI assistance
      </p>

      {/* Filename and Source inputs */}
      <div className="mb-6 flex flex-wrap gap-4">
        {/* Filename input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Output Filename
          </label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={filename}
              onChange={e => setFilename(e.target.value)}
              placeholder="anki_cards"
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64"
            />
            <span className="text-gray-500">.csv</span>
          </div>
        </div>

        {/* Source dropdown */}
        {config?.sources && config.sources.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <select
              value={source}
              onChange={e => setSource(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent w-48"
            >
              {config.sources.map(s => (
                <option key={s.tag} value={s.tag}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {view === 'draft' ? (
        <>
          {/* Draft Cards View */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Draft Cards</h2>
            <DraftCardList
              cards={draftCards}
              onCardsChange={setDraftCards}
            />
          </div>

          {/* Generate Button */}
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={isGenerating || draftCards.every(c => !c.rawInput.trim())}
              aria-busy={isGenerating}
              aria-disabled={isGenerating || draftCards.every(c => !c.rawInput.trim())}
              aria-label={isGenerating ? 'Generating cards, please wait' : 'Generate Anki flashcards from draft inputs'}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                isGenerating || draftCards.every(c => !c.rawInput.trim())
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isGenerating ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" aria-hidden="true" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Generating...
                </span>
              ) : (
                'Generate Cards'
              )}
            </button>

            {generateError && (
              <span className="text-red-600 text-sm">{generateError}</span>
            )}
          </div>
        </>
      ) : (
        <>
          {/* Generated Cards View */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-700">
                Generated Cards ({generatedCards.length})
              </h2>
              <button
                type="button"
                onClick={handleBackToDraft}
                aria-label="Go back to draft cards view"
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                &larr; Back to Draft
              </button>
            </div>

            <GeneratedTable
              cards={generatedCards}
              fields={config.fields}
              onCardsChange={setGeneratedCards}
              onRegenerateCard={handleRegenerateCard}
            />
          </div>

          {/* Export Button */}
          <div className="flex items-center gap-4">
            <ExportButton
              onClick={handleExport}
              isLoading={isExporting}
              disabled={generatedCards.length === 0}
            />

            {exportError && (
              <span className="text-red-600 text-sm">{exportError}</span>
            )}
          </div>
        </>
      )}
    </main>
  );
}
