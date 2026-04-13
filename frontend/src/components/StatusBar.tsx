import { useEffect, useState } from "react";
import { Wifi, WifiOff } from "lucide-react";
import { healthCheck } from "../lib/api";

export default function StatusBar() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    healthCheck().then(setOnline);
    const id = setInterval(() => healthCheck().then(setOnline), 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={`status-bar ${online === false ? "status-bar--off" : ""}`}>
      {online === null ? (
        <span className="status-bar__dot status-bar__dot--loading" />
      ) : online ? (
        <Wifi size={14} />
      ) : (
        <WifiOff size={14} />
      )}
      <span>
        {online === null
          ? "Conectando..."
          : online
          ? "API conectada"
          : "API no disponible — ejecuta: uvicorn api.main:app --port 8000"}
      </span>
    </div>
  );
}
