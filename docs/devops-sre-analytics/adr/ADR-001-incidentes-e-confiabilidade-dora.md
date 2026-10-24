# ADR-001 — Incidentes como domínio próprio e qualidade de dados DORA

- **Data:** 2026-10-23
- **Status:** decisão de domínio confirmada; especificação técnica em revisão
- **Contexto:** DevOps & SRE Analytics / Flosum / Salesforce Lightning Experience
- **Origem da decisão:** usuário confirmou que **não existe hoje uma tabela de incidentes** na YDUQS e explicitou que a confiabilidade das fontes e dos cálculos DORA é requisito crítico.

## Decisão confirmada

1. Criar uma estrutura **própria do aplicativo**, em Salesforce, para registrar incidentes de produção, ações de recuperação (rollback, hotfix, fix forward etc.) e suas evidências. O esquema detalhado é candidato da SPEC-003 e exige revisão antes do deploy.
2. **Flosum permanece fonte de mudanças, pipelines e deployments somente onde objetos/campos forem verificados**. Uma falha de Step, validação ou Pipeline em sandbox não prova impacto em produção.
3. Um incidente **não é automaticamente** uma falha causada por deployment. A causalidade e a recuperação requerem evidência verificável e revisão/autorização humana.
4. O dashboard NÃO apresenta **0** incidentes, **0%** Change Fail Rate, tempo de recuperação ou qualquer métrica aparentemente válida quando a fonte estiver ausente ou incompleta. Exibir **Não mensurável**, com motivo, período, serviço e fontes faltantes.
5. O registro de incidentes será preferencialmente alimentado por **formulário Lightning auditável no MVP**, com possibilidade futura de automação controlada, desde que o responsável pelo processo confirme o fluxo. Não inventar histórico retroativo.
6. Ações de recuperação no app são **registros do que ocorreu**, e não botões de execução Flosum ou rollback automático.
7. **Fluxo inicial aprovado em 23/10/2026:** DevOps/SRE cadastra incidentes manualmente; a atribuição de causalidade a deployments só poderá alimentar DORA após revisão de responsável autorizado, com responsabilidade inicial definida para os **RMs de DevOps** (aceite posterior do proprietário). A confirmação adicional pelo COE fica fora do MVP.
8. Não criar, alterar ou inferir registros de incidentes a partir de um deploy sem contrato de integração validado.

## Regras de ouro

- **Configuração != execução**: `Flosum__Pipeline__c` e `Flosum__PipelineStep__c` descrevem configuração, não eventos de produção.
- **Execução != alteração de serviço**: deploy que falha antes de produzir impacto operacional pode ter comportamento diferente de uma falha de mudança em produção.
- **Incidente != falha de mudança**: indisponibilidade por infraestrutura, rede ou operação externa não aumenta Change Fail Rate por padrão.
- **Rollback != incidente**: rollback pode ser ação de remediação, mas precisa do vínculo causal correspondente.
- **Uma alteração / deployment pode causar múltiplos incidentes**: deduplicar no numerador do Change Fail Rate.
- **Uma única resposta pode ter múltiplas ações**: rollback, mitigação, hotfix e fix forward não devem sobrescrever a primeira ação.
- **Cobertura deve ser certificada**: zero incidentes no mês só é dado válido depois da conferência do período e da fonte de ocorrências.
- **Timestamp correto**: guardar UTC/DateTime e apresentação na timezone do usuário, preservando fonte e informação original; intervalo negativo/ausente torna duração não mensurável.

## Separar tipos de evidência

| Camada | Fonte candidata | Necessária para |
| --- | --- | --- |
| Mudanças/commits | Flosum (contrato a confirmar) | Change Lead Time |
| Deployments concluídos em produção | Flosum (contrato a confirmar) | Deployment Frequency e denominadores |
| Incidente / impacto / restauração | Novo registro próprio do app | Change Fail Rate e Failed Deployment Recovery Time |
| Associação causal incidente↔deploy | Relação explícita auditável, revisada | Atribuição correta da falha |
| Ações de recuperação e deploys não planejados | Novo registro próprio + implantação real vinculada | Deployment Rework Rate |
| Cobertura do período/serviço | Reconciliação/certificação auditável | Saber se os números podem ser exibidos |

## Métricas: política de cálculo

- **Change Lead Time:** duração de commit até deploy concluído em produção, apenas quando existir rastreabilidade individual confiável.
- **Deployment Frequency:** contabilizar deployments reais em produção por serviço/período, não etapas de pipeline nem todos os ambientes.
- **Change Fail Rate:** numerador = deployments distintos em produção que causaram necessidade de intervenção confirmada; denominador = deployments de produção elegíveis no período; atribuição por deployment sem contagem duplicada de incidentes.
- **Failed Deployment Recovery Time:** intervalo entre início de impacto atribuído ao deployment e restauração do serviço, com timestamps válidos e revisão; falhas sem impacto em serviço ficam fora do universo de restauração de serviço.
- **Deployment Rework Rate:** proporção de deployments de produção não planejados realizados para corrigir falha/incidente de produção, sobre total de deployments elegíveis, com identidade de deployment e tipo de mudança confirmados.
- Cada fórmula deverá ter **versão**, população, exclusões, janela temporal, timezone, origem e cobertura documentadas. Não efetuar cálculo em runtime a partir de campos livres ou não validados.

Referência de definição: https://dora.dev/guides/dora-metrics/

## Regras de publicação de KPIs

Estados por métrica e serviço/período:

1. **Não mensurável:** fonte ausente, denominador desconhecido, vínculo causal não confirmado ou cobertura insuficiente.
2. **Parcial:** dados presentes mas período, serviço ou relações com lacunas conhecidas. Pode-se exibir amostras explicitamente rotuladas, **não** KPI DORA consolidado.
3. **Certificado:** contrato verificado, população/escopo definidos, reconciliação realizada e carimbo de auditoria. Só então exibir resultado consolidado.

Toda mudança que reabra ou corrija uma evidência pode invalidar uma certificação anterior; cálculo precisa ser recalculável e auditável.

## Implicações e limites

- São necessários metadados personalizados; detalhes propostos em `specs/003-incident-foundation/`.
- Custo de armazenamento, histórico de campos, licenciamento e governança de dados deverão ser avaliados para dados sensíveis; nenhuma informação de cliente, token ou stack trace deve ser exigida no formulário.
- Implementação do Pipeline Monitor no PR #34 permanece isolada, sem dependências deste domínio.
- **Este ADR NÃO autoriza deploy nem implica que as tabelas foram criadas na org.**

## Decisões ainda a confirmar

- **Cadastro aprovado:** DevOps/SRE, manual e auditável. **Revisão causal inicial aprovada:** equipe DevOps — RMs; COE é evolução futura, sem aprovação adicional agora. **Ainda decidir:** responsável pela certificação de cobertura, compartilhamento entre operadores e RMs, e inventário dos deployments.
- Fonte oficial e API names dos **deployments executados em produção no Flosum**.
- Catálogo oficial de serviços/aplicações afetados para impedir agrupamento de nomes livres.
- Política de incidentes pré-existentes e início da janela mensurável. Não fabricar backfill.

## Decisão complementar — revisão pela equipe DevOps (RMs)

- Os **RMs de DevOps** são os responsáveis iniciais por **gerir e revisar** incidentes; cadastro permanece com operadores DevOps/SRE.
- Não há aprovação obrigatória do COE neste ciclo. Sua futura participação exigirá nova especificação, sem incluir controles não solicitados agora.
- A pessoa do RM recebe `DevSreIncident_Operator` conforme atribuição explícita. O próprio Permission Set de Operador concede `DevSre_ReviewIncidentCausality` e a FLS dos campos de revisão; não concede `View All` nem contorna o `Private`.
- Revisão da **causa por outros fatores** pode ser confirmada ou rejeitada com justificativa. **Confirmação de `DeploymentRelated` permanece bloqueada**, inclusive pela API, até existir vínculo auditável com deployment real; criar essa associação é fase posterior.
- Alterações manuais ao campo causal são impedidas para não RMs por regra de validação com `$Permission`. As regras exigem novos incidentes `Unconfirmed/Pending` e justificativa para conclusões.
- **Nada nesta decisão libera cálculos DORA**. Fonte de deployments, vínculo causal, reconciliação e cobertura por serviço/período continuam gates obrigatórios.

## Retificação de estrutura organizacional e homologação

- O termo **RMs** designa a **equipe DevOps/SRE**, e não uma equipe ou nível gerencial acima dos operadores. Toda a equipe autorizada pode registrar, gerir e revisar incidentes.
- Permissão única de operação: `DevSreIncident_Operator`, com custom permission de revisão; `DevSreIncident_Reader` para usuários somente de consulta. Não há perfil de aprovação extra. COE futuro.
- Incidentes e ações seguem `Private` e são compartilhados exclusivamente com membros aprovados do grupo público `DevSre_Incident_RMs`, sem `View All` nem compartilhar com toda a org. A administração de membros do grupo é uma etapa pós-deploy da sandbox.
- Toda implementação Salesforce deverá ser validada via Metadata API no **DevSreFeat** antes de marcar como homologada, além de CI e testes de permissão. Usar deploy dry-run; deploy real somente com autorização específica.
