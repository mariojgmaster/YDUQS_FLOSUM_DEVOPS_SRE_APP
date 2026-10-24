# Inventário Flosum — descoberta controlada das fontes de deployment

**Situação inicial (24/10/2026):** o Pipeline Monitor conhece apenas `Flosum__Pipeline__c` e `Flosum__PipelineStep__c`, que são **configuração**, não execuções. A fundação de incidentes está homologada na `DevSreFeat` (deploy #40124487168 e limpeza #40128322847), mas não há contrato validado para métricas DORA.

## Incremento atual: descoberta sem leitura de registros

Sem criar outro workflow, a operação `flosum-schema-inventory` foi adicionada a `.github/workflows/sf-devsrefeat-diagnostics.yml`, reutilizando o Environment `sf-devsrefeat-read` e ECA/JWT existentes.

1. Ler **somente nomes técnicos dos objetos customizados** por `sf sobject list --sobject custom`, com saída JSON mantida em memória do runner; selecionar apenas objetos de namespaces `Flosum__` ou `git__` que tenham indícios de execução, release, commit, branch, mudança ou ambiente.
2. Descrever no máximo **seis objetos por categoria** (36 no total), por `sf sobject describe`, estritamente metadados, jamais `SELECT`, DML, deploy, triggers ou registros Flosum.
3. Logs **públicos sanitizados**: contagens, slots por categoria e marcadores booleanos de campos de lifecycle, ambiente, timestamp, commit e release. Não publicar nomes reais de objetos/campos da org, IDs, labels, usuários, valores, fonte Apex ou payload bruto. Falhas e schema desconhecido não são convertidos em zero elegível.
4. A operação nunca certifica KPI; `metric_status=NOT_MEASURABLE` até validar fonte, identidade, timestamps, ambiente PROD, relação commit-deployment, completude e reconciliação.
5. Autorização: execução manual em `master` pelo owner ou Issue owner criada no repositório com título e corpo fixos:
   - Title: `SDOA INVENTORY DevSreFeat Flosum`
   - Body: `SDOA-FLOSUM-SCHEMA/1\noperation=inventory\ntarget=DevSreFeat`
   - O workflow executa **somente leitura**, sem novo workflow, sem privilégios ampliados.

## Critérios para a próxima fase

- [ ] CI dos parser/guardrails PASS e PR mesclado na `master` protegida.
- [ ] Run real conclui e divulga somente sinalização sanitizada do inventário.
- [ ] Se há candidatos, cruzar o inventário com contratos documentados da versão Flosum e identificar **fonte de deployments efetivamente concluídos em PROD**, timestamps auditáveis, tipo de operação, relações com commit e serviço.
- [ ] Confirmar permissão/visibilidade das fontes e responsável pela certificação do período.
- [ ] Somente então SPEC para coleta/correlação de deployments e fórmula DORA. Nenhuma inferência de KPI pelos Pipeline Steps.

## Restrições

Fonte incompleta ou desconhecida → **Não mensurável**. Não criar custom object paralelo sem decisão de domínio; não modificar Flosum nem PROD.
## Corrigir cancelamento por concorrência na primeira execução

A [Issue #89](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/issues/89) disparou o run [#40130022909](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40130022909), que terminou `cancelled` sem iniciar job. A hipótese técnica é colisão na fila compartilhada com os workflows `M5 ChatOps` e `Incident Validation`, também disparados pelo evento de Issue. O diagnóstico **somente leitura** passa a usar grupo de concorrência distinto `sf-devsrefeat-read-diagnostics` e `queue: max`, sem tocar nas filas de escrita/Metadata API.

Nova Issue e novo run devem comprovar a hipótese; a execução cancelada **não representa** inventário nem consulta Salesforce.
