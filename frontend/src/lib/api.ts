import type { ValidationResult } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function validateZip(
  zipFile: File,
  sourceFile: File,
  options: {
    strict?: boolean;
    showExtra?: boolean;
    fuzzyThreshold?: number;
  } = {}
): Promise<ValidationResult> {
  const form = new FormData();
  form.append("zip_file", zipFile);
  form.append("source_file", sourceFile);
  form.append("strict", String(options.strict ?? false));
  form.append("show_extra", String(options.showExtra ?? true));
  form.append("fuzzy_threshold", String(options.fuzzyThreshold ?? 0.82));

  const res = await fetch(`${API_URL}/validate`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Error al validar");
  }

  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
