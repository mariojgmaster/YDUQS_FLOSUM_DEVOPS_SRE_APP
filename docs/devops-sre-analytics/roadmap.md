# Roadmap incremental — DevOps & SRE Analytics

Este roadmap apresenta **candidatos futuros**, não autorização para implementar funcionalidades além da SPEC ativa.

| Incremento | Capacidade | Fonte / decisão necessária | Estado |
| --- | --- | --- | --- |
| F1 | Pipeline Monitor read-only: buscar Pipelines e listar seus Steps | Objetos Flosum previamente usados em ClonePipelineController | **Implementação iniciada** |
| F2 | Lightning App com navegação completa e acessos por persona | Tab/App metadata + Permission Sets + validação na DevSreFeat | Proposto |
| F3 | Execuções operacionais, status e histórico real | Inventário parcial validado na DevSreFeat (run #40130263390); contrato de identidade/timestamps PROD pendente | Bloqueado por fonte — descoberta iniciada |
| F4 | DORA Cockpit com cinco métricas oficiais | Sem timestamps de conclusão/contrato elegível de deployment em produção; causalidade e cobertura por certificar | Bloqueado por fonte — Não mensurável |
| F5 | Lead Time Tracker | Identidade/correlação commit → mudança → deployment de produção | Bloqueado por fonte |
| F6 | Incidents & Rollbacks | Cadastro manual e recuperação homologados; vínculo causal a deployments verificados e cobertura continuam pendentes | Fundação manual homologada; correlação bloqueada por fonte |
| F7 | Visões analíticas | Métricas auditáveis, qualidade dos dados e volumes medidos | Planejamento futuro |

**Fora de escopo inicial:** automação de deploy, rollback por UI, integração externa sem ADR, dados sintéticos em runtime, ranking individual.

**Decisão a obter:** quais fontes registram deploys de produção, falha em produção, recuperação e retrabalho, e como são correlacionadas aos registros Flosum?

## Próximo incremento — classificação dos destinos

O [contrato proposto de ambientes](environment-classification-contract.md) descreve a classificação explícita PROD/UAT/SIT/DEV por destino verificado, com vigência, ambiguidade e invalidação histórica. A escolha do mecanismo de configuração e a implementação dependem da inspeção real Branch/Metadata Log preparada no PR #93. O catálogo de negócio não substitui controles de autenticação/deploy do GitHub.

A fundação manual F6 foi homologada e a aba duplicada removida: deploy #40124487168, limpeza #40128322847 e validação posterior #40128701599 (SUCCESS). Esses resultados não liberam F3/F4/F5 nem certificam permissões para todas as personas.
