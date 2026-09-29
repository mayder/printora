import React from "react";
import { FilePlus2 } from "lucide-react";
import { printProjectsApi } from "../../services/printProjectsApi";
import type { PrintProjectDetail, PrintProjectVisibility } from "../../types/printProjects";

interface ProjectCreateModalProps {
  disabled: boolean;
  onClose: () => void;
  onCreated: (detail: PrintProjectDetail) => void;
  setError: (message: string | null) => void;
}

export function ProjectCreateModal({ disabled, onClose, onCreated, setError }: ProjectCreateModalProps) {
  const [title, setTitle] = React.useState("");
  const [visibility, setVisibility] = React.useState<PrintProjectVisibility>("private");
  const [license, setLicense] = React.useState("cc-by");
  const [tags, setTags] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) onClose();
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [busy, onClose]);

  async function createProject(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const detail = await printProjectsApi.create({
        title: title.trim(),
        visibility,
        license: license.trim(),
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      });
      onCreated(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar projeto");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Cadastrar projeto">
      <div className="modal-card project-create-modal-card">
        <div className="modal-header">
          <div>
            <h2><FilePlus2 size={21} />Cadastrar projeto</h2>
            <p>Crie o projeto privado primeiro. Depois você poderá enviar arquivos ou fotografar um objeto real.</p>
          </div>
          <button type="button" className="ghost-button" onClick={onClose} disabled={busy}>Fechar</button>
        </div>
        <form className="project-create-modal-form" onSubmit={(event) => void createProject(event)}>
          <section className="form-section">
            <div className="form-section-heading">
              <strong>Informações básicas</strong>
              <span>Use um nome fácil de reconhecer. Você poderá completar e publicar o projeto depois.</span>
            </div>
            <div className="form-grid two-columns">
              <label className="form-field">
                <span>Nome do projeto</span>
                <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Ex.: Suporte de mesa" required autoFocus disabled={disabled || busy} />
              </label>
              <label className="form-field">
                <span>Visibilidade</span>
                <select value={visibility} onChange={(event) => setVisibility(event.target.value as PrintProjectVisibility)} disabled={disabled || busy}>
                  <option value="private">Privado</option>
                  <option value="unlisted">Não listado</option>
                  <option value="public">Público</option>
                </select>
              </label>
              <label className="form-field">
                <span>Licença</span>
                <input value={license} onChange={(event) => setLicense(event.target.value)} disabled={disabled || busy} />
              </label>
              <label className="form-field">
                <span>Tags</span>
                <input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="mesa, pla, suporte" disabled={disabled || busy} />
              </label>
            </div>
          </section>
          <div className="modal-footer">
            <button type="button" className="ghost-button" onClick={onClose} disabled={busy}>Cancelar</button>
            <button type="submit" className="primary-button" disabled={disabled || busy || !title.trim()}>
              <FilePlus2 size={16} />{busy ? "Criando projeto..." : "Criar projeto"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
