import React from "react";
import { Box, Lock, Printer, Ruler, UserRound, Wrench } from "lucide-react";
import { socialApi } from "../services/socialApi";
import type { PublicPrinter } from "../types";

interface PublicPrinterScreenProps {
  printerId: string;
}

export function PublicPrinterScreen({ printerId }: PublicPrinterScreenProps) {
  const [printer, setPrinter] = React.useState<PublicPrinter | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let active = true;
    async function loadPrinter() {
      setLoading(true);
      setError(null);
      try {
        const payload = await socialApi.publicPrinter(printerId);
        if (active) setPrinter(payload);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Impressora pública indisponível");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadPrinter();
    return () => {
      active = false;
    };
  }, [printerId]);

  return (
    <main className="public-profile-shell">
      <section className="public-profile-topbar">
        <img src="/brand/printora-logo-horizontal-color.png" alt="Printora" />
        <a href="/" className="secondary-button">Entrar</a>
      </section>

      {loading ? (
        <section className="public-profile-empty">Carregando impressora pública...</section>
      ) : error ? (
        <section className="public-profile-empty">
          <Lock size={22} />
          <h1>Impressora indisponível</h1>
          <p>{error}</p>
        </section>
      ) : printer ? (
        <section className="public-profile-page">
          <header className="public-profile-hero public-printer-hero">
            <div className="public-avatar">
              {printer.public_images[0] ? <img src={printer.public_images[0]} alt="" /> : <Printer size={34} />}
            </div>
            <div>
              <span className="account-eyebrow">Impressora pública Printora</span>
              <h1>{printer.public_name}</h1>
              {printer.public_description ? <p>{printer.public_description}</p> : null}
              <div className="public-profile-meta">
                <span><UserRound size={15} />{printer.owner_display_name ?? printer.owner_slug ?? "Perfil público"}</span>
                {printer.owner_slug ? <a href={`/u/${printer.owner_slug}`}>Ver perfil</a> : null}
              </div>
            </div>
          </header>

          <section className="public-profile-grid">
            <article className="panel public-profile-panel">
              <h2>Inventário público</h2>
              <div className="public-spec-list">
                <span><Printer size={15} />{printer.manufacturer_name} / {printer.model_name}</span>
                <span><Box size={15} />{printer.variant_name}</span>
                <span><Ruler size={15} />{formatBuildVolume(printer.build_volume)}</span>
                <span><Wrench size={15} />{printer.kinematics}</span>
              </div>
              {printer.public_mods.length ? <p>Mods públicos: {printer.public_mods.join(", ")}</p> : <p>Nenhum mod público informado.</p>}
            </article>

            <article className="panel public-profile-panel">
              <h2>Imagens públicas</h2>
              <div className="public-image-grid">
                {printer.public_images.map((imageUrl) => (
                  <a key={imageUrl} href={imageUrl} target="_blank" rel="noreferrer">
                    <img src={imageUrl} alt="" />
                  </a>
                ))}
                {printer.public_images.length === 0 ? <p>Nenhuma imagem pública informada.</p> : null}
              </div>
            </article>
          </section>
        </section>
      ) : null}
    </main>
  );
}

function formatBuildVolume(value: Record<string, unknown>) {
  const dimensions = ["x", "y", "z"].map((key) => value[key]).filter((item) => item !== undefined && item !== null);
  return dimensions.length === 3 ? `${dimensions.join(" x ")} mm` : "Volume não informado";
}
