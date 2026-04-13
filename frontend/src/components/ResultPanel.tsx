import { motion } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  FolderOpen,
  File,
  ChevronDown,
} from "lucide-react";
import { useState } from "react";
import type { ValidationResult } from "../types";
import ScoreRing from "./ScoreRing";
import FileTree from "./FileTree";

interface Props {
  data: ValidationResult;
  onReset: () => void;
}

export default function ResultPanel({ data, onReset }: Props) {
  const { summary, details, zip_structure } = data;
  const [openSection, setOpenSection] = useState<string | null>("present");

  const toggle = (key: string) =>
    setOpenSection((prev) => (prev === key ? null : key));

  const verdictColor = summary.passed
    ? "var(--green)"
    : summary.total_missing === 0
    ? "var(--yellow)"
    : "var(--red)";

  const verdictText = summary.passed
    ? "CUMPLE COMPLETAMENTE"
    : summary.total_missing === 0
    ? "CUMPLE CON ADVERTENCIAS"
    : "NO CUMPLE";

  const VerdictIcon = summary.passed
    ? CheckCircle
    : summary.total_missing === 0
    ? AlertTriangle
    : XCircle;

  return (
    <motion.div
      className="result"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Veredicto */}
      <div className="result__verdict" style={{ borderColor: verdictColor }}>
        <ScoreRing score={summary.score} />
        <div className="result__verdict-info">
          <div className="result__verdict-label" style={{ color: verdictColor }}>
            <VerdictIcon size={22} />
            <span>{verdictText}</span>
          </div>
          {summary.strict_mode && (
            <span className="result__badge result__badge--strict">STRICT</span>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="result__stats">
        <Stat label="Requeridos" value={summary.total_required} />
        <Stat label="Presentes" value={summary.total_present} color="var(--green)" />
        <Stat label="Faltantes" value={summary.total_missing} color="var(--red)" />
        <Stat label="Fuzzy" value={summary.total_fuzzy} color="var(--yellow)" />
        <Stat label="En ZIP" value={summary.zip_file_count} />
      </div>

      {/* Secciones colapsables */}
      <div className="result__sections">
        {details.present_files.length > 0 && (
          <Section
            title={`Archivos presentes (${details.present_files.length})`}
            icon={<CheckCircle size={16} color="var(--green)" />}
            id="present"
            open={openSection === "present"}
            onToggle={() => toggle("present")}
          >
            {details.present_files.map((f, i) => (
              <div key={i} className="result__file result__file--ok">
                <File size={14} />
                <span>{f.required}</span>
                {f.match === "name_only" && (
                  <span className="result__file-note">ruta distinta: {f.found}</span>
                )}
              </div>
            ))}
          </Section>
        )}

        {details.present_folders.length > 0 && (
          <Section
            title={`Carpetas presentes (${details.present_folders.length})`}
            icon={<FolderOpen size={16} color="var(--green)" />}
            id="folders"
            open={openSection === "folders"}
            onToggle={() => toggle("folders")}
          >
            {details.present_folders.map((f, i) => (
              <div key={i} className="result__file result__file--ok">
                <FolderOpen size={14} />
                <span>{f.required}</span>
              </div>
            ))}
          </Section>
        )}

        {details.fuzzy_matches.length > 0 && (
          <Section
            title={`Coincidencias aproximadas (${details.fuzzy_matches.length})`}
            icon={<AlertTriangle size={16} color="var(--yellow)" />}
            id="fuzzy"
            open={openSection === "fuzzy"}
            onToggle={() => toggle("fuzzy")}
          >
            {details.fuzzy_matches.map((f, i) => (
              <div key={i} className="result__file result__file--warn">
                <AlertTriangle size={14} />
                <span>{f.required}</span>
                <span className="result__file-arrow">-&gt;</span>
                <span className="result__file-match">{f.closest}</span>
                <span className="result__file-score">{f.score}%</span>
              </div>
            ))}
          </Section>
        )}

        {details.missing_files.length > 0 && (
          <Section
            title={`Archivos faltantes (${details.missing_files.length})`}
            icon={<XCircle size={16} color="var(--red)" />}
            id="missing"
            open={openSection === "missing"}
            onToggle={() => toggle("missing")}
          >
            {details.missing_files.map((f, i) => (
              <div key={i} className="result__file result__file--err">
                <XCircle size={14} />
                <span>{f}</span>
              </div>
            ))}
          </Section>
        )}

        {details.missing_folders.length > 0 && (
          <Section
            title={`Carpetas faltantes (${details.missing_folders.length})`}
            icon={<XCircle size={16} color="var(--red)" />}
            id="missing-folders"
            open={openSection === "missing-folders"}
            onToggle={() => toggle("missing-folders")}
          >
            {details.missing_folders.map((f, i) => (
              <div key={i} className="result__file result__file--err">
                <FolderOpen size={14} />
                <span>{f}</span>
              </div>
            ))}
          </Section>
        )}

        {details.extra_files.length > 0 && (
          <Section
            title={`Archivos extra (${details.extra_files.length})`}
            icon={<File size={16} color="var(--muted)" />}
            id="extra"
            open={openSection === "extra"}
            onToggle={() => toggle("extra")}
          >
            {details.extra_files.map((f, i) => (
              <div key={i} className="result__file result__file--extra">
                <File size={14} />
                <span>{f}</span>
              </div>
            ))}
          </Section>
        )}

        {zip_structure.length > 0 && (
          <Section
            title={`Estructura del ZIP (${zip_structure.length} entradas)`}
            icon={<FileTree entries={[]} isIcon />}
            id="tree"
            open={openSection === "tree"}
            onToggle={() => toggle("tree")}
          >
            <FileTree entries={zip_structure} />
          </Section>
        )}
      </div>

      <button className="btn btn--secondary" onClick={onReset}>
        Validar otro archivo
      </button>
    </motion.div>
  );
}

/* --- Sub-components --- */

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="result__stat">
      <span className="result__stat-value" style={color ? { color } : {}}>
        {value}
      </span>
      <span className="result__stat-label">{label}</span>
    </div>
  );
}

function Section({
  title,
  icon,
  open,
  onToggle,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className={`result__section ${open ? "result__section--open" : ""}`}>
      <button className="result__section-header" onClick={onToggle}>
        {icon}
        <span>{title}</span>
        <ChevronDown size={16} className="result__section-chevron" />
      </button>
      {open && (
        <motion.div
          className="result__section-body"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
        >
          {children}
        </motion.div>
      )}
    </div>
  );
}
