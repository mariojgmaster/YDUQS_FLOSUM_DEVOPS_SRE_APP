# Plano técnico — Incidentes e governança da fonte

## Fase A — aprovar domínio e processo

- Adotar ADR-001. Confirmar fonte humana de abertura, revisor causal, responsável de reconciliação e registro oficial de serviços.
- Identificar o deployment de produção que permita vínculos reais; usar GitHub Actions ECA/JWT de consulta **somente** com autorização e objeto/campos confirmados, nunca supor API names de Flosum.
- Registrar decisões adicionais de metadados em ADR incremental.

## Fase B — schema Salesforce (PR próprio, ainda não preparado nesta entrega)

- Criar Custom Objects propostos no `data-model.md` com Owner/sharing, histórico para campos críticos, Permission Sets distintos `Reader`, `Operator`, `Reviewer`.
- Definir obrigatoriedade progressiva por status, validações temporais e de duplicidade e proteção de alterações após certificação.
- Preferir lookups tipados quando modelo de Flosum estiver conhecido; não criar links indiretos frágeis para campos de objeto inventados.
- Criar manifesto allowlisted específico, isolado de `clone-pipeline` e do PR #34.

## Fase C — MVP funcional de incidentes

- Lightning tab Incidents & Rollbacks em SLDS 2 com lista/filtros, criação manual e detalhamento; UX Operacional como padrão.
- LWC ou Flow orientado a fluxo controlado, sem escrita em Flosum, acesso respeitando CRUD/FLS/sharing.
- Permitir ações de recuperação múltiplas, time-line auditável, datas de início de impacto e restauração.
- Cobrir tests negativos de permissão, estados e timestamps.

## Fase D — governança de métricas

- Ingestão de deployments PROD somente após inventário e contrato documentado.
- Associação e revisão causal, reconciliação de população por serviço/período.
- DORA Cockpit usa `MetricReadiness` antes de exibir qualquer KPI consolidado.
- Testes das dez situações do contrato de readiness, auditabilidade e performance.

## Deploy / piloto

**Nenhum deploy autorizado por esta SPEC.** `DevSreFeat` é sandbox catalogada no repositório, Environment legado `sf-devsrefeat-read`; secrets ECA JWT não foram lidos. Após implementação validada e autorização específica, executar dry-run/RunSpecifiedTests para pacote fixado, depois considerar deploy real em sandbox. Respeitar controles Flosum e produção.

## Riscos

- Histórico de incidentes inexistente => impossibilidade de reconstituição retrospectiva sem evidências independentes.
- Campos livres de serviço/ambiente => inconsistência de agregação; exigir catálogo.
- Falha de deployment não equivale a impacto de serviço => possível distorção de DORA.
- Deployment duplicado em múltiplos incidentes => risco de numerador inflado.
- Sem rotinas de revisão e reconciliação, app vira cadastro incompleto que não sustenta métricas.
