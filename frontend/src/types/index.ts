export type CardType = 'word' | 'phrase' | 'sentence';

export interface Source {
  label: string;
  tag: string;
}

export interface DraftCard {
  id: string;
  rawInput: string;
  fixedEnglish: string;
  fixedDutch: string;
  extraNotes: string;
}

export interface GeneratedCard {
  fields: Record<string, string>;
  tags: string[];
  autoClassifiedType: CardType;
  // Frontend-only tracking fields
  originalType?: CardType;
  isRegenerating?: boolean;
  isCore?: boolean; // true = Core (priority), false = Extra (supplementary)
}

export interface AnkiConfig {
  fields: string[];
  tags: string[];
  tagsColumnEnabled: boolean;
  tagsColumnName: string;
  sources: Source[];
  defaultSource?: string;
}

export interface GenerateRequest {
  draft_cards: {
    raw_input: string;
    fixed_english?: string;
    fixed_dutch?: string;
    extra_notes?: string;
  }[];
  filename?: string;
}

export interface GenerateResponse {
  cards: GeneratedCard[];
  filename: string;
}

export interface ExportRequest {
  cards: GeneratedCard[];
  filename: string;
  source?: string;
}

export interface RegenerateCardRequest {
  raw_input: string;
  fixed_english?: string;
  fixed_dutch?: string;
  extra_notes?: string;
  target_type: CardType;
}

// Migration types
export interface DeckInfo {
  name: string;
  note_count: number;
}

export interface MigrationNote {
  note_id: number;
  old_fields: Record<string, string>;
  sound: string;
  sound_example: string;
}

export interface PreviewResponse {
  note_id: number;
  new_fields: Record<string, string>;
  auto_classified_type: CardType;
}

export interface MigrationNoteState {
  note: MigrationNote;
  preview: PreviewResponse | null;
  status: 'pending' | 'previewing' | 'ready' | 'approving' | 'approved' | 'skipped' | 'error';
  error?: string;
}
