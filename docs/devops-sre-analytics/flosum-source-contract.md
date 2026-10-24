# Contrato técnico observado — Metadata Log / próxima fase

**Estado:** descoberta concluída para a Branch selecionada; pronto para especificar o cadastro de ambientes e o adaptador de leitura. Não representa certificação de cobertura DORA.
**Fonte:** API autenticada na DevSreFeat, somente leitura. Nenhum acesso à org Salesforce PROD ou escrita Salesforce.

## Aquisição e análise efetiva

- Coleta inicial: [#40138960350](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40138960350), Issue #98, SHA `01f02cf4d9c8bbad56d2da5218c5147c007e024f`.
- Coleta complementar: [#40139152470](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40139152470), Issue #100, job `121006979343`, SHA `6d12c87af6e7dda3012b9419b6bcf23ef4eb2cdf`. **SUCCESS**.
- Ambos os artifacts foram efetivamente baixados e descriptografados; SHA-256 dos ZIPs conferidos com o GitHub. Não apenas listados.
- Schema integral: Branch 68 campos, Metadata Log 55 campos, organização 32 campos. Tooling FieldDefinition de Branch e Metadata Log disponível, sem lacunas de consulta.
- Registros: uma Branch, 26 logs e duas organizações relacionadas; nenhum limite atingido, nenhum campo esperado ausente. Completude limitada ao escopo visível dessa Branch.

## Mapeamento verificado

| Informação | Campo | Tipo / comportamento observado |
| --- | --- | --- |
| Branch da operação | `Flosum__Branch__c` | Lookup para Branch; preenchido nos 26 logs |
| Branch de origem | `Flosum__Source_Branch__c` | Outro lookup para Branch; sem valor nesses 26 logs; não confundir com a Branch principal |
| Organização | `Flosum__Organisation__c` | Lookup para `Flosum__Organisation__c` |
| Operação | `Flosum__Process_Type__c` | Picklist; preservar valores históricos também quando não constam da lista ativa |
| Status do processo | `Flosum__Status__c` | Picklist; Completed, por si só, não significa sucesso |
| Job finalizado | `Flosum__Job_Completed__c` | Boolean |
| Sucesso | `Flosum__Succeed__c` | Boolean |
| Erros / resultado parcial | `Flosum__Is_Error__c` | Boolean |
| Resultado visual | `Flosum__Result__c` | Fórmula Text com IMAGE/HTML; não usar o HTML como estado de domínio |
| Início | `Flosum__Start_Date__c` | DateTime, não calculado |
| Conclusão | `Flosum__Completed_Date__c` | DateTime, não calculado; fonte temporal candidata a adotar no adaptador |
| Deployment Date | `Flosum__Deployment_Date__c` | Fórmula DateTime = CreatedDate; não é conclusão |
| Requisição | `Flosum__Async_Request_Id__c` | Texto, correlação de tentativa com o destino |
| Log pai | `Flosum__Parent_Log__c` | Lookup para Metadata Log; vazio no escopo observado |
| Automação completa | `Flosum__Automation_Completed__c` | Boolean; não substitui conclusão do deployment |
| Último commit da Branch | `Flosum__Last_Commit__c` | Texto, não lookup; vazio na Branch observada |

## Regra de leitura a implementar na próxima fase

Deployment bem-sucedido candidato: operação `Deployment`, status `Completed`, Job Completed = true, Succeed = true e Is Error = false. Organização deve resolver uma configuração explícita de ambiente. Para elegibilidade temporal, exigir Completed Date válido, início não posterior ao fim quando presente, identidade única e demais gates da métrica.

A fórmula de Result confirma que a distinção visual entre sucesso e parcial depende de Job Completed, Succeed e Is Error. O HTML, tradução, label e ícone não são contrato de negócio.

Validações e outros passos não são deployments. Na Branch observada há 26 logs: cinco de operação Deployment (três concluídos com sucesso e dois Did Not Run), seis Validate e quinze passos auxiliares. Há validações com status Completed e Succeed=false. Os três deployments de sucesso têm três request IDs distintos, sem vínculo pai preenchido. Esses fatos demonstram por que contar todos os logs ou todos os Completed produziria resultado incorreto.

Operações como rollback efetivo e tipos especiais precisam de classificação explícita na SPEC do adaptador; não generalizar por substring, lista ativa de picklist ou boolean de sucesso. Repetições devem ser reconciliadas por contexto da fonte + organização + requisição quando disponível; usar Id do log como identidade de origem, sem colapsar todos os deploys da mesma Branch.

## Contrato temporal

A amostra comprova três instantes distintos: criação do log, início e conclusão. LastModifiedDate é posterior à conclusão nos exemplos observados. Usar CreatedDate, Deployment Date ou LastModifiedDate como conclusão distorceria o relógio.

O adaptador deve preservar timestamps originais UTC, considerar Completed Date como campo de conclusão da fonte e testar ausência/inversão. Não usar ABS, FLOOR ou diferenças de LastModifiedDate como reparo de dados inválidos. Há fórmula local de duração baseada em LastModifiedDate e criação: não adotar essa duração para DORA.

A investigação identifica o relógio disponível na fonte; não comprova imutabilidade histórica, cobertura de todos os deployments ou semântica de operações fora da amostra.

## Próxima fase destravada

1. Especificar o cadastro de ambientes por referência estável à organização Flosum, com vigência, autorização e auditoria. IDs reais permanecem fora do repositório público.
2. Implementar o adaptador somente leitura e a reconciliação das tentativas, preservando a proveniência e os estados desconhecidos.
3. Validar matriz de operações, permissões e consistência temporal com fixtures sintéticas e teste real do período escolhido.
4. Só depois certificar cobertura e liberar métricas. Lead Time ainda exige identidade/timestamp do commit e correlação individual; incidentes/recuperação exigem seus próprios vínculos.

Não é necessário novo print dos campos nem repetir o diagnóstico agregado. A coleta integral agora é reutilizável pelo protocolo owner-only documentado em [flosum-integral-evidence.md](../flosum-integral-evidence.md).
