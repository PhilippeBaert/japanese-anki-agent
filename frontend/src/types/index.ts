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
