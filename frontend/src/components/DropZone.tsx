import { useCallback, useState } from "react";
import { Upload, FileArchive, FileText } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  label: string;
  accept: string;
  icon: "zip" | "source";
  file: File | null;
  onFile: (f: File) => void;
}

export default function DropZone({ label, accept, icon, file, onFile }: Props) {
  const [drag, setDrag] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDrag(false);
      const f = e.dataTransfer.files[0];
      if (f) onFile(f);
    },
    [onFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) onFile(f);
  };

  const Icon = icon === "zip" ? FileArchive : FileText;

  return (
    <motion.label
      className={`dropzone ${drag ? "dropzone--active" : ""} ${file ? "dropzone--has-file" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <input
        type="file"
        accept={accept}
        onChange={handleChange}
        hidden
      />

      <AnimatePresence mode="wait">
        {file ? (
          <motion.div
            key="file"
            className="dropzone__content"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <Icon size={28} className="dropzone__icon dropzone__icon--done" />
            <span className="dropzone__filename">{file.name}</span>
            <span className="dropzone__size">
              {(file.size / 1024).toFixed(1)} KB
            </span>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            className="dropzone__content"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <Upload size={28} className="dropzone__icon" />
            <span className="dropzone__label">{label}</span>
            <span className="dropzone__hint">Arrastra o haz clic</span>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.label>
  );
}
