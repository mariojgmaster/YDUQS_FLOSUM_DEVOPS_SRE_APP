# Roadmap incremental — DevOps & SRE Analytics

Este roadmap apresenta **candidatos futuros**, não autorização para implementar funcionalidades além da SPEC ativa.

| Incremento | Capacidade | Fonte / decisão necessária | Estado |
| --- | --- | --- | --- |
| F1 | Pipeline Monitor read-only: buscar Pipelines e listar seus Steps | Objetos Flosum previamente usados em ClonePipelineController | **Implementação iniciada** |
| F2 | Lightning App com navegação completa e acessos por persona | Tab/App metadata + Permission Sets + validação na DevSreFeat | Proposto |
| F3 | Execuções operacionais, status e histórico real | Inventário autorizado de execução Flosum, API names e timestamps | Bloqueado por fonte |
| F4 | DORA Cockpit com cinco métricas oficiais | Mapeamento de implantação em produção, falha, recuperação, retrabalho e commit | Bloqueado por fonte |
| F5 | Lead Time Tracker | Identidade/correlação commit → mudança → deployment de produção | Bloqueado por fonte |
| F6 | Incidents & Rollbacks | Fonte autorizada de incidentes de produção e vínculos às mudanças | Bloqueado por fonte |
| F7 | Visões analíticas | Métricas auditáveis, qualidade dos dados e volumes medidos | Planejamento futuro |

**Fora de escopo inicial:** automação de deploy, rollback por UI, criação de objetos de incidentes, integração externa sem ADR, dados sintéticos em runtime, ranking individual.

**Decisão a obter:** quais fontes registram deploys de produção, falha em produção, recuperação e retrabalho, e como são correlacionadas aos registros Flosum?
