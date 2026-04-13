export interface FileMatch {
  required: string;
  found: string;
  match: "exact" | "name_only";
  note?: string;
}

export interface FolderMatch {
  required: string;
  match: string;
}

export interface FuzzyMatch {
  required: string;
  closest: string;
  score: number;
  type?: string;
}

export interface ValidationSummary {
  passed: boolean;
  score: number;
  strict_mode: boolean;
  total_required: number;
  total_present: number;
  total_missing: number;
  total_fuzzy: number;
  zip_file_count: number;
}

export interface ValidationDetails {
  present_files: FileMatch[];
  missing_files: string[];
  present_folders: FolderMatch[];
  missing_folders: string[];
  fuzzy_matches: FuzzyMatch[];
  extra_files: string[];
}

export interface ValidationInput {
  zip: string;
  zip_name: string;
  source: string;
  source_type: string;
}

export interface ValidationResult {
  zipspec_version: string;
  generated_at: string;
  input: ValidationInput;
  summary: ValidationSummary;
  details: ValidationDetails;
  zip_structure: string[];
}

export type AppState = "idle" | "uploading" | "validating" | "done" | "error";
