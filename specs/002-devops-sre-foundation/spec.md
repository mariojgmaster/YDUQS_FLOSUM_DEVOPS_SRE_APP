# SPEC-002 — Lightning App foundation / Pipeline Monitor (primeiro incremento)

**Data:** 2026-10-23  
**Estado:** direção funcional autorizada para início; homologação pendente.  
**Escopo implementável agora:** somente o primeiro fluxo vertical de consulta de Pipelines Flosum e seus Steps.  
**Pré-requisitos externos:** org com pacote Flosum, direitos de leitura e acesso autorizado à classe Apex; custom tab/app configurados na org após validação.

## Contexto

O produto DevOps & SRE Analytics é uma Lightning App destinada a DevOps/SRE/COE. Quatro áreas estão previstas (DORA Cockpit, Pipeline Monitor, Lead Time Tracker e Incidents & Rollbacks), com visão Operacional como default e Analítica como aprofundamento. Esta SPEC **não autoriza** ainda cálculos DORA nem status de execução Flosum que não tenham fontes e contratos confirmados.

## User stories

### US1 — Consultar pipelines (P1)

Como usuário DevOps/SRE/COE com permissão, quero pesquisar os pipelines Flosum acessíveis a mim, para localizar uma configuração real sem recorrer a relatórios externos.

**Aceite:** listagem de até 50 registros por busca; filtro por parte do nome aplicado pelo servidor; aviso de truncamento quando existem mais registros; empty state; erro seguro; nada inventado.

### US2 — Inspecionar Steps (P1)

Como usuário autorizado, quero selecionar um pipeline e ver a ordem, a descrição, a ação e os desvios pass/fail dos Steps para compreender a configuração.

**Aceite:** consulta por Id validado; até 100 Steps exibidos em ordem; campos opcionais indisponíveis por FLS são omitidos; referenciais de transição existentes são exibidos com clareza; aviso de truncamento quando houver; nenhum registro é alterado.

### US3 — Navegar à origem e atualizar (P2)

Como usuário autorizado, quero abrir o registro Flosum e atualizar os dados sob demanda.

**Aceite:** navegação padrão `standard__recordPage`; botão Atualizar refaz consulta real; estado de carregamento, falha e sucesso diferenciados; nenhum botão decorativo.

## Requisitos não funcionais

- Salesforce DX, API 67.0 alinhada ao repositório, Apex com `with sharing` e `WITH USER_MODE`.
- CRUD/FLS por fonte; apenas leitura; sem SOQL/DML em loops; queries limitadas.
- O UI não infere execução/sucesso/falha a partir de registros de definição.
- Lightning Base Components e SLDS 2; sem CSS forçando subárvore interna de componentes base.
- Testes Apex e Jest; execução de testes de org é uma etapa de validação, não assumida.
- Error messages sem stack trace, dado protegido ou detalhes técnicos.
- Não alterar o Clone Pipeline nem os workflows de deploy existentes.

## Limites e exclusões

- Nenhuma modificação em objetos Flosum, nenhuma chamada a API de deploy.
- Sem métricas DORA neste incremento; sem indicadores de execução.
- Nenhuma paginação ilimitada: o usuário recebe aviso de limite.
- Configuração de aba Lightning e App Manager depende de metadados/validação da org; a LWC será exposta via `lightning__Tab` e `lightning__AppPage`.

## Critérios de sucesso

- Listagem e pesquisa só retornam registros visíveis conforme permissões da org.
- Seleção mostra Step count correspondente à resposta lida, sem confundir total com contagem parcial.
- Falha de autorização não expõe dados.
- Nenhum DML é executado nos controllers.
- Validação técnica e funcional na DevSreFeat será registrada antes de marcar a SPEC como Done.
