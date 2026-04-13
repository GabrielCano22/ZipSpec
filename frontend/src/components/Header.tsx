import { Shield } from "lucide-react";

export default function Header() {
  return (
    <header className="header">
      <div className="header__brand">
        <Shield size={28} className="header__logo" />
        <h1>
          Zip<span>Spec</span>
        </h1>
      </div>
      <p className="header__tagline">
        Valida la estructura de tus archivos .zip contra requisitos PDF o YAML
      </p>
    </header>
  );
}
