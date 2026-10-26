# SPEC-006 / M2A — Branch Describer por nome registrado (incremento G2)

## Implementado no código (não implica deploy)
- `DevSreComponentDescriberController`: consulta **somente leitura**, com `with sharing`, `AccessLevel.USER_MODE`, CRUD e FLS. O campo de busca inicial é **`Flosum__Component__c.Name`**, e não FullName canônico; não atribuir a ele semântica de metadata type/namespace nem versão.
- O lookup `Flosum__Component__c → Flosum__Branch__c` é resolvido por **describe tipado** em tempo de execução, exigindo **exatamente um** campo referência legível e nome validado; se faltar, bloquear o endpoint. Não usar `Flosum__Last_Commit__c`.
- Busca automática após 2 caracteres, limite de 80, escape de caracteres de wildcard, cursor (`Name,Id`), paginação 25+1; cada ocorrência preserva Id e vínculo de Branch. ID de Branch inacessível não é exposto no DTO.
- Detalhe `describeComponent` valida Id tipado, consulta o registro real, verifica History→Component por describe e lê no máximo 21 `Flosum__Component_History__c` associados (20 exibidos + hasMore). Dados do histórico: **somente Id e CreatedDate**; não exibe conteúdo de código, XML, version, commit ou dados supostos de deploy.
- A ausência de acesso a History aparece como `UNAVAILABLE`, nunca como história vazia comprovada. A ligação positiva é `TYPED_LINK_SAMPLE`, não prova versão ou cobertura global.
- LWC filho `devSreComponentDescriber` é montado na subaba **Componentes** do shell `devSreBranchMonitor`, com paginação, debounce, navegação via `NavigationMixin`, proteção contra resposta obsoleta, foco/teclado, ellipsis, estados de erro e transparência de fontes.
- Nenhum vínculo componente→Metadata Log/deploy é produzido; `deployEvidenceQuality='UNVERIFIED'`.

## Release / segurança
- Catálogo de deployment `branch-monitor-m2-describer`, manifesto do núcleo limitado a **2 classes Apex + 1 LWC filho**, tests: `DevSreComponentDescriberTest` e `DevSreBranchMonitorTest`; sem destrutivos.
- A concessão do novo controller para os Reader users exige **alteração e deployment separado** de `DevSreBranchMonitor_Reader` (permissão `classAccesses DevSreComponentDescriberController=true`). Não implantar como se o Reader tivesse acesso automaticamente. O pacote M2A **não** inclui PermissionSet.
- CI Jest/ESLint e Apex dry-run são gates; deploy real somente com aprovação explícita de pacote, SHA e sandbox.
- Visibilidade da subaba não é evidência de que o método Apex esteja autorizado para cada usuário; homologar Reader real.
- Gate seguinte M2B: verificar campos reais para `MetadataType + FullName + Namespace`, demonstrar versões em dois histories da mesma identidade e vínculo direto componente→Metadata Log, sem expor dados sensíveis no repo público. Só então habilitar filtro canônico, versões ou timeline de deployments.

## Homologação funcional planejada
1. Pesquisar por substring de um `Name` real e verificar ocorrências distintas de mesmo nome e Branches distintas.
2. Abrir registro de Component e Branch diretamente via Salesforce Navigation.
3. Selecionar ocorrência e verificar até 20 Histories com referência tipada; não confundir `CreatedDate` com data de versão.
4. Validar 2/80 caracteres, paginação, recarregar, fonte indisponível e registro sem Branch.
5. Testar com usuário Reader e verificar CRUD/FLS e classe Apex.

## Ajuste de rollout após dry-run na DevSreFeat
- Primeiro dry-run [#40267385253](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40267385253) falhou **antes dos testes**: um componente de metadata rejeitado, identificado no relatório sanitizado como `devSreBranchMonitor`. A referência ao LWC filho ainda não publicado precisa ser resolvida antes de alterar o shell da aba.
- **Fase M2A-core**: pacote `branch-monitor-m2-describer`, duas classes Apex e **somente** `devSreComponentDescriber`. Dry-run e deploy devem preceder a ativação do shell.
- **Fase M2A-activate**: pacote `branch-monitor-m2-activate`, somente `devSreBranchMonitor`, após o filho estar instalado e validado. Dry-run distinto.
- **Permissão Reader** para o novo controlador é uma terceira mudança específica e deverá usar processo seguro com manifest revisado, após testar classe Apex; não alterar o PermissionSet da Fase 1 implicitamente.
- Nenhuma implantação real aconteceu no dry-run rejeitado; source versionado não é prova de presença na org.
