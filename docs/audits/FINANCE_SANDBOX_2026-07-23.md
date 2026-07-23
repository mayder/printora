# Evidência financeira sandbox - 2026-07-23

- release publicada: `3b55e01bf9db487746b7d1ae671ae9833ee7e35d`;
- workflow blue/green: `29977187334`;
- modo efetivo: `sandbox`; dinheiro real permanece tecnicamente indisponível;
- prova sintética: captura, replay, reembolso parcial, conciliação, repasse com
  aprovador e executor distintos, saldo final e ledger balanceado passaram;
- segurança: nenhuma coluna PAN/CVV/payload bruto, checkout hospedado e segredo
  fora do Git;
- smoke público: passou;
- backup externo Restic: snapshot `c0df65fe`;
- restore isolado: 134 tabelas, 85 revisões, zero FK inválida, oito versões de
  objeto reconciliadas e 364 documentos reconstruídos;
- o restore não iniciou aplicação e nenhuma operação acessou impressora física,
  agente, Moonraker, Klipper ou MCU.

Controles fiscal, jurídico, LGPD/PCI, continuidade e segurança continuam como
gates explícitos; esta evidência não os aprova e não habilita dinheiro real.
