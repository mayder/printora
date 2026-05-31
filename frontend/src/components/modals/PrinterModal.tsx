import { ConnectionTestRow } from "../common";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

export type PrinterModalProps = ScreenPropsFor<
  | "authUser"
  | "Plus"
  | "Radio"
  | "Search"
  | "createPrinter"
  | "discoverPrinters"
  | "discovery"
  | "loading"
  | "maintenanceDoneDisableReminder"
  | "maintenanceDoneIntervalKind"
  | "maintenancePrintHoursAvailable"
  | "newPrinterName"
  | "newPrinterCloudModel"
  | "newPrinterCloudTags"
  | "newPrinterLocation"
  | "newPrinterNotes"
  | "newPrinterOrganizationId"
  | "newPrinterSshCredential"
  | "newPrinterSshHost"
  | "newPrinterSshPort"
  | "newPrinterSshUser"
  | "newPrinterUrl"
  | "printerConnectionTest"
  | "printerModalMode"
  | "printerModalOpen"
  | "setNewPrinterName"
  | "setNewPrinterCloudModel"
  | "setNewPrinterCloudTags"
  | "setNewPrinterLocation"
  | "setNewPrinterNotes"
  | "setNewPrinterOrganizationId"
  | "setNewPrinterSshCredential"
  | "setNewPrinterSshHost"
  | "setNewPrinterSshPort"
  | "setNewPrinterSshUser"
  | "setNewPrinterUrl"
  | "setPrinterModalOpen"
  | "snapshots"
  | "status"
  | "testPrinterConnections"
  | "useDiscoveredPrinter"
>;

export function PrinterModal(props: PrinterModalProps) {
  const {
    authUser,
    Plus,
    Radio,
    Search,
    createPrinter,
    discoverPrinters,
    discovery,
    loading,
    maintenanceDoneDisableReminder,
    maintenanceDoneIntervalKind,
    maintenancePrintHoursAvailable,
    newPrinterName,
    newPrinterCloudModel,
    newPrinterCloudTags,
    newPrinterLocation,
    newPrinterNotes,
    newPrinterOrganizationId,
    newPrinterSshCredential,
    newPrinterSshHost,
    newPrinterSshPort,
    newPrinterSshUser,
    newPrinterUrl,
    printerConnectionTest,
    printerModalMode,
    printerModalOpen,
    setNewPrinterName,
    setNewPrinterCloudModel,
    setNewPrinterCloudTags,
    setNewPrinterLocation,
    setNewPrinterNotes,
    setNewPrinterOrganizationId,
    setNewPrinterSshCredential,
    setNewPrinterSshHost,
    setNewPrinterSshPort,
    setNewPrinterSshUser,
    setNewPrinterUrl,
    setPrinterModalOpen,
    snapshots,
    status,
    testPrinterConnections,
    useDiscoveredPrinter,
  } = props;

  return (
    <>
        {printerModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Cadastrar impressora">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <h2>{printerModalMode === "edit" ? "Editar impressora" : "Cadastrar impressora"}</h2>
                  <p>Configure Moonraker e, se quiser auditoria completa, o acesso SSH do host.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                  Fechar
                </button>
              </div>
              <div className="modal-actions">
                {printerModalMode === "create" ? (
                  <button type="button" className="secondary-button" onClick={() => void discoverPrinters()} disabled={loading}>
                    <Search size={16} />
                    Buscar na rede
                  </button>
                ) : null}
                <button type="button" className="secondary-button" onClick={() => void testPrinterConnections()} disabled={loading}>
                  <Radio size={16} />
                  Testar conexões
                </button>
                <span>
                  {printerModalMode === "create"
                    ? "Buscar usa HTTP GET em `/server/info`, sem G-code e sem cadastro automático."
                    : "Teste seguro: valida Moonraker e porta SSH sem enviar G-code."}
                </span>
              </div>
              {printerModalMode === "create" && discovery ? (
                <div className="discovery-box">
                  <div className="discovery-summary">
                    <strong>
                      {discovery.candidates.length} Moonraker encontrado(s) em {discovery.cidr}
                    </strong>
                    <span>
                      {discovery.scanned_hosts} hosts verificados · modo {discovery.safe_mode}
                    </span>
                  </div>
                  {discovery.warnings.map((warning: any) => (
                    <small key={warning} className="muted">
                      {warning}
                    </small>
                  ))}
                  <div className="discovery-list">
                    {discovery.candidates.length === 0 ? <p className="muted">Nenhuma impressora encontrada na rede atual.</p> : null}
                    {discovery.candidates.map((candidate: any) => (
                      <div key={candidate.moonraker_url} className="discovery-row">
                        <div>
                          <strong>{candidate.name}</strong>
                          <span>{candidate.moonraker_url}</span>
                          <small>
                            Klippy: {candidate.klippy_state ?? "-"} · Moonraker: {candidate.moonraker_version ?? "-"}
                          </small>
                        </div>
                        {candidate.already_registered ? (
                          <span className="registered-badge">já cadastrada</span>
                        ) : (
                          <button type="button" onClick={() => useDiscoveredPrinter(candidate)} disabled={loading}>
                            Usar dados
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              {printerConnectionTest ? (
                <div className="connection-test-box">
                  <ConnectionTestRow label="Moonraker" result={printerConnectionTest.moonraker} />
                  <ConnectionTestRow label="SSH" result={printerConnectionTest.ssh} emptyDetail="Preencha host SSH para testar a porta." />
                </div>
              ) : null}
              <form className="printer-access-form" onSubmit={(event: any) => void createPrinter(event)}>
                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Cadastro cloud</strong>
                    <span>Identificação operacional e compartilhamento opcional por organização.</span>
                  </div>
                  <div className="form-grid two-columns">
                    <label className="form-field">
                      <span>Nome</span>
                      <input
                        aria-label="Nome da impressora"
                        value={newPrinterName}
                        onChange={(event: any) => setNewPrinterName(event.target.value)}
                        placeholder="Voron 2.4"
                      />
                    </label>
                    <label className="form-field">
                      <span>Modelo</span>
                      <input
                        aria-label="Modelo da impressora"
                        value={newPrinterCloudModel}
                        onChange={(event: any) => setNewPrinterCloudModel(event.target.value)}
                        placeholder="Voron 2.4 R2"
                      />
                    </label>
                    <label className="form-field">
                      <span>Localização</span>
                      <input
                        aria-label="Localização da impressora"
                        value={newPrinterLocation}
                        onChange={(event: any) => setNewPrinterLocation(event.target.value)}
                        placeholder="Laboratório / rack 1"
                      />
                    </label>
                    <label className="form-field">
                      <span>Organização</span>
                      <select
                        aria-label="Organização da impressora"
                        value={newPrinterOrganizationId}
                        onChange={(event: any) => setNewPrinterOrganizationId(event.target.value ? Number(event.target.value) : "")}
                      >
                        <option value="">Uso individual</option>
                        {(authUser?.organizations ?? []).map((organization: any) => (
                          <option key={organization.id} value={organization.id}>
                            {organization.name} · {organization.role}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="form-field wide-field">
                      <span>Tags</span>
                      <input
                        aria-label="Tags da impressora"
                        value={newPrinterCloudTags}
                        onChange={(event: any) => setNewPrinterCloudTags(event.target.value)}
                        placeholder="produção, abs, corexy"
                      />
                    </label>
                    <label className="form-field wide-field">
                      <span>Observações</span>
                      <textarea
                        aria-label="Observações da impressora"
                        value={newPrinterNotes}
                        onChange={(event: any) => setNewPrinterNotes(event.target.value)}
                        placeholder="Informações úteis para suporte e operação."
                      />
                    </label>
                  </div>
                </section>

                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Conexão Moonraker</strong>
                    <span>Usada para status, snapshots e leitura segura via HTTP.</span>
                  </div>
                  <div className="form-grid two-columns">
                    <label className="form-field">
                      <span>URL Moonraker</span>
                      <input
                        aria-label="URL Moonraker"
                        value={newPrinterUrl}
                        onChange={(event: any) => setNewPrinterUrl(event.target.value)}
                        placeholder="http://voron.local:7125"
                      />
                    </label>
                  </div>
                </section>

                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Acesso SSH</strong>
                    <span>Necessário para auditoria profunda, CAN, systemd, backups locais e firmware.</span>
                  </div>
                  <div className="form-grid ssh-grid">
                    <label className="form-field">
                      <span>Host SSH</span>
                      <input
                        aria-label="Host SSH"
                        value={newPrinterSshHost}
                        onChange={(event: any) => setNewPrinterSshHost(event.target.value)}
                        placeholder="voron.local"
                      />
                    </label>
                    <label className="form-field compact-field">
                      <span>Porta</span>
                      <input
                        aria-label="Porta SSH"
                        type="number"
                        min="1"
                        max="65535"
                        value={newPrinterSshPort}
                        onChange={(event: any) => setNewPrinterSshPort(Number(event.target.value))}
                        placeholder="22"
                      />
                    </label>
                    <label className="form-field">
                      <span>Usuário</span>
                      <input
                        aria-label="Usuário SSH"
                        value={newPrinterSshUser}
                        onChange={(event: any) => setNewPrinterSshUser(event.target.value)}
                        placeholder="pi"
                      />
                    </label>
                    <label className="form-field">
                      <span>{printerModalMode === "edit" ? "Nova senha opcional" : "Senha"}</span>
                      <input
                        aria-label="Senha SSH"
                        type="password"
                        value={newPrinterSshCredential}
                        onChange={(event: any) => setNewPrinterSshCredential(event.target.value)}
                        placeholder={printerModalMode === "edit" ? "Deixe vazio para manter a atual" : "Senha SSH"}
                      />
                    </label>
                  </div>
                  <small className="form-note">
                    O valor sensível não é retornado pela API. Em edição, deixe a senha vazia para manter a credencial atual.
                  </small>
                </section>

                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading || (!maintenanceDoneDisableReminder && maintenanceDoneIntervalKind === "print_hours" && !maintenancePrintHoursAvailable)}>
                    <Plus size={16} />
                    {printerModalMode === "edit" ? "Salvar impressora" : "Cadastrar impressora"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
    </>
  );
}
