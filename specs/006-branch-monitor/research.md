# Pesquisa e decisões técnicas — SPEC-006

## Evidências observadas na sandbox, 25/10/2026
Origem: GitHub Actions read-only [run 40225283951](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40225283951), ECA/JWT na DevSreFeat, sem consulta a registros nesta etapa.

| Objeto | Estado real | Relações/sinais observados |
| --- | --- | --- |
| `Flosum__Branch__c` | Confirmado no contrato já existente | identidade e referência por Metadata Log |
| `Flosum__Metadata_Log__c` | Confirmado | lookup Branch e organização, Process_Type, Status, Job_Completed, Succeed, Is_Error, Start_Date, Completed_Date |
| `Flosum__Components__c` | **Describe indisponível** | não utilizar como API name confirmado |
| `Flosum__Component__c` | Describe OK, **37 campos** | exatamente 1 referência tipada a `Flosum__Branch__c`; sinais de versão/commit; nenhum body detectado por tipo textarea/base64/encryptedstring |
| `Flosum__Component_History__c` | Describe OK, **32 campos** | **1 referência tipada a \`Flosum__Component__c\` (singular)**, sem referência tipada direta ao objeto Branch ou Metadata Log; sinais nominais branch=1, component=1, commit=4, version=3; possível campo tipo texto longo |

O nome exato dos campos de identidade, FullName, conteúdo, revisão e vínculos internos do histórico **ainda não está documentado como comprovado**. Os sinais de nomes são heurísticos: não criam relações. `Flosum__Last_Commit__c` é texto e não deve ser a fonte exclusiva de revisão.

## Decisões
**D-001:** usar `Flosum__Component__c` (singular); não construir consultas contra o plural até nova evidência.

**D-002:** separar `BranchPresence`, `HistoryVersion` e `DeploymentEvidence`; presença em branch não prova publicação em produção.

**D-003:** implementar capacidades por gate, não por aparência do wireframe. Branch Directory pode seguir depois de validar permissões e paginação; Diff textual somente após versão + payload e imutabilidade comprovados.

**D-004:** não fazer join pela coincidência do nome do componente, nem apenas pelo texto `Last_Commit`; definir vínculo por chave de fonte e verificar cardinalidade em amostra limitada (incluindo versões múltiplas).

**D-005:** comparar timestamps em UTC; separar Create/Start/Complete, com status de resultados próprios por operação; P95 só com amostra completa e elegível, exibindo o universo contabilizado.

## Lacunas prioritárias — bloquear até resolver
1. API names, data types, acessibilidade/FLS, referência e significado dos campos de `Flosum__Component__c` usados para identidade de componente, tipo e versão.
2. **Lookup History→Component tipado confirmado**. Validar preenchimento e cardinalidade real, assim como vínculos de commit/versão e registros sem relacionamento.
3. Se há snapshot/código/XML acessível por API para **duas revisões** da mesma identidade de componente e o que significa uma versão.
4. Fonte de associação componente → tentativa de deploy/validate; a presença de um componente na Branch não basta.
5. Completude por branch: limite de registros, deletes, renames, namespaces e mudanças concorrentes; captura de watermark/revisão.
6. Segurança de acesso a conteúdo de metadados, tamanho por resposta e artefato sensível.

## Metodologia empírica de descoberta
- Etapa A: describe de Branch, Component, Component History, Metadata Log; classificar campos por função/tipo/relacionamento com saídas **sanitizadas**, sem nomes de campos internos publicamente.
- Etapa B: decidir consultas pontuais após descobrir o contrato; read-only, user mode/integração autorizada, linhas e colunas minimizadas, logs sem IDs/nomes/valores, prova de vínculos por contagem + amostra sinalizada.
- Etapa C: validar fonte de conteúdo de duas revisões; caso não exista, registrar Diff apenas de inventário e impedir comparação textual.
- Etapa D: formalizar contrato e testes de ambiguidade e completude antes de implementar UI de diff.

## Confiança
`confirmed`: relação/timestamp/schema comprovados em resultado da fonte. `candidate`: indício estrutural ainda não correlacionado. `unverified`: ausência de evidência. `unavailable`: fonte sem acesso ou limite. `incomplete`: consulta truncada/escopo parcial. Nunca transformar unverified em false.
