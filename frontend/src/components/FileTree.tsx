import { Folder, FileCode } from "lucide-react";

interface Props {
  entries: string[];
  isIcon?: boolean;
}

export default function FileTree({ entries, isIcon }: Props) {
  if (isIcon) {
    return <Folder size={16} color="var(--purple)" />;
  }

  return (
    <div className="file-tree">
      {entries.map((entry, i) => {
        const isDir = entry.endsWith("/");
        const depth = entry.replace(/\\/g, "/").replace(/\/$/, "").split("/").length - 1;
        const name = entry.replace(/\\/g, "/").replace(/\/$/, "").split("/").pop() || entry;

        return (
          <div
            key={i}
            className={`file-tree__item ${isDir ? "file-tree__item--dir" : ""}`}
            style={{ paddingLeft: `${depth * 20 + 8}px` }}
          >
            {isDir ? (
              <Folder size={14} className="file-tree__icon file-tree__icon--dir" />
            ) : (
              <FileCode size={14} className="file-tree__icon" />
            )}
            <span>{name}{isDir ? "/" : ""}</span>
          </div>
        );
      })}
    </div>
  );
}
