# Modelo de dados candidato — Incident Domain (não implantado)

O modelo abaixo é a base para futuras Custom Objects Salesforce, **não é descrição de objetos já existentes**.

## Entidades propostas

### `DevSre_Incident__c` — Incidente

- Identificação: `Name` AutoNumber (ex.: `INC-{000000}`), `Title__c` (Text), `Description__c` (LongTextArea, restrita), `Source__c` (Picklist: Manual, Monitoring, External), `OwnerId` (Salesforce padrão).
- Contexto: `ServiceKey__c` (**transitório**: Text controlado até confirmar catálogo autoritativo de aplicação/serviço), `EnvironmentClass__c` (Production, NonProduction, Unknown), `Severity__c` (SEV1-4), `Status__c` (Open, Investigating, Mitigating, Restored, Closed).
- Linha do tempo: `ImpactStartedAt__c`, `DetectedAt__c`, `RestoredAt__c`, `ClosedAt__c` (DateTime, nullable; não inventar instantes).
- Causalidade: `CauseType__c` (Unconfirmed, DeploymentRelated, Other), `CauseReviewStatus__c` (Pending, Confirmed, Rejected), `CauseJustification__c` (LongTextArea).
- Salesforce padrão: `CreatedDate, CreatedById, LastModifiedDate, LastModifiedById`. Definir Field History Tracking dos campos críticos na implementação.

### `DevSre_RecoveryAction__c` — Ação de recuperação

- Lookup `Incident__c` → Incidente (1:N; evitar exclusão em cascata inadvertida).
- `ActionType__c` (Rollback, Hotfix, FixForward, Mitigation, Other).
- `Status__c` (Planned, Running, Completed, Failed, Cancelled).
- `StartedAt__c`, `CompletedAt__c`, `EvidenceNotes__c`, identificador/auditoria.
- Resultado da ação não substitui `RestoredAt__c` do incidente.

### `DevSre_IncidentDeployment__c` — vínculo de evidência

- Lookup `Incident__c` → Incidente.
- Destino lógico: deployment de produção, identificado por contrato de origem ainda desconhecido. **Não criar Lookup Flosum antes de validar o objeto-fonte real**.
- `RelationRole__c` (CausedBy, RemediatedBy, Related).
- `VerificationStatus__c` (Pending, Verified, Rejected), revisor/data e justificativa de causalidade.
- Chave lógica de origem `SourceSystem__c + SourceObjectApiName__c + SourceRecordId__c` somente se inventário Flosum recomendar vínculo por ID; preferir Lookup real após validação e sem aceitar URL arbitrária.
- Um deployment pode estar associado a vários incidentes; deduplicação por identidade de origem+deployment na leitura.

### `DevSre_MeasurementCoverage__c` — certificação do período

- Janela `From__c / To__c`, `ServiceKey__c`, `EnvironmentClass__c`.
- `Status__c` (Unavailable, Partial, Certified), versões de regras, escopo coberto, fontes presentes e lacunas.
- `ReviewedBy__c`, `ReviewedAt__c` / trilha de auditoria.
- Não marcar `Certified` automaticamente porque todas as linhas conhecidas passaram na validação: é necessária reconciliação da população de deployments e incidentes.

## Relações

```text
[Incidente] 1 ── N [RecoveryAction]
     │
     └── 1 ── N [IncidentDeployment] N ── 1 [Deployment real Flosum, contrato pendente]

[MeasurementCoverage] → Escopo {Service, Period, Environment, RulesVersion}
```

## Campos derivados (não persistir por padrão)

- `RecoveryDuration` depende de `ImpactStartedAt__c` e `RestoredAt__c` consistentes e causa confirmada.
- `IsDoraEligible` depende de ambiente, deployment válido, intervenção, causa revisada e período certificado.
- `IsUnplannedRemediationDeployment` requer vínculo a deployment em produção classificado como não planejado.

## Decisões antes de gerar CustomObject XML

1. O catálogo de serviços oficial existe em objeto Flosum/Salesforce ou precisamos do nosso?
2. Quem mantém os incidentes, revisa o vínculo causal e atesta cobertura?
3. Quais objetos Flosum representam **deployments efetivamente concluídos em produção** e quais campos guardam IDs/timestamps?
4. Qual é a política de visibilidade/retention e campos obrigatórios no registro manual?
