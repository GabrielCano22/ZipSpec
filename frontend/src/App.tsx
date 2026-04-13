import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import Header from "./components/Header";
import DropZone from "./components/DropZone";
import Options from "./components/Options";
import ResultPanel from "./components/ResultPanel";
import StatusBar from "./components/StatusBar";
import { validateZip } from "./lib/api";
import type { AppState, ValidationResult } from "./types";

export default function App() {
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [strict, setStrict] = useState(false);
  const [fuzzy, setFuzzy] = useState(0.82);
  const [state, setState] = useState<AppState>("idle");
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canValidate = zipFile && sourceFile && state !== "validating";

  const handleValidate = async () => {
    if (!zipFile || !sourceFile) return;
    setState("validating");
    setError(null);
    try {
      const data = await validateZip(zipFile, sourceFile, {
        strict,
        showExtra: true,
        fuzzyThreshold: fuzzy,
      });
      setResult(data);
      setState("done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error desconocido");
      setState("error");
    }
  };

  const handleReset = () => {
    setZipFile(null);
    setSourceFile(null);
    setResult(null);
    setError(null);
    setState("idle");
  };

  return (
    <div className="app">
      <div className="app__bg" />
      <main className="app__main">
        <Header />
        <StatusBar />

        <AnimatePresence mode="wait">
          {state === "done" && result ? (
            <ResultPanel key="result" data={result} onReset={handleReset} />
          ) : (
            <motion.div
              key="form"
              className="upload-form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="upload-form__zones">
                <DropZone
                  label="Archivo .zip"
                  accept=".zip"
                  icon="zip"
                  file={zipFile}
                  onFile={setZipFile}
                />
                <DropZone
                  label="Requisitos (.pdf o .yml)"
                  accept=".pdf,.yml,.yaml"
                  icon="source"
                  file={sourceFile}
                  onFile={setSourceFile}
                />
              </div>

              <Options
                strict={strict}
                setStrict={setStrict}
                fuzzyThreshold={fuzzy}
                setFuzzyThreshold={setFuzzy}
              />

              {error && (
                <motion.div
                  className="error-msg"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {error}
                </motion.div>
              )}

              <button
                className="btn btn--primary"
                disabled={!canValidate}
                onClick={handleValidate}
              >
                {state === "validating" ? (
                  <>
                    <Loader2 size={18} className="spin" />
                    Validando...
                  </>
                ) : (
                  "Validar ZIP"
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <footer className="footer">
          <span>ZipSpec v2.0</span>
          <span>Python + FastAPI + React</span>
        </footer>
      </main>
    </div>
  );
}
