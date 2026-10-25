# Branch Monitor — descoberta segura de componentes (25/10/2026)

## Fontes em investigação
- `Flosum__Branch__c`: identidade da branch; vínculo de referência já verificado para Metadata Log.
- `Flosum__Metadata_Log__c`: Process Type, status, resultado, timestamps, vínculo com organização e branch, comprovados nos relatórios anteriores.
- `Flosum__Components__c` e `Flosum__Component_History__c`: **relacionamentos ainda não verificados** na DevSreFeat; nenhuma consulta deve supor nomes de campos.
- Para descobri-los, operação somente leitura no workflow existente `sf-devsrefeat-diagnostics.yml`, evento proprietário `SDOA COMPONENTS DevSreFeat Flosum`, via script allowlisted `sf-flosum-component-research.py`.

## Perguntas a responder
1. Há lookup direto de Components para Branch?
2. Component History aponta para Components, Branch, Commit ou Metadata Log? Qual cardinalidade?
3. Qual a identidade estável de componente: Metadata Type + Full Name + namespace + versão?
4. O conteúdo XML/código da versão está legível por User Mode ou apenas arquivo/Storage gerenciado?
5. É possível reconstruir o estado de uma Branch num instante sem recorrer a Last_Commit?
6. Componentes e históricos preservam múltiplas versões na mesma Branch ou apenas o último estado?

## Branch Describer por componente
Entrada: nome completo e tipo de metadata, com pesquisa e sugestões reais.
Resultados: branches que contêm o componente, identidade/versão associada, alterações cronológicas com autor/commit quando comprovados, deploys e validações relacionados, duração e resultado. Não inferir deploy a partir do simples vínculo do componente: é necessária trilha comprovada por execução.
Suportar normalização de FullName, versões duplicadas e componentes em múltiplas branches.
Comparador: etapa 1 inventário; etapa 2 conteúdo (se efetivamente disponível); etapa 3 semântica tipada e impacto/dependência.

## Privacidade e fidelidade
O script imprime somente contagens e flags de referências e armazena respostas CLI apenas em memória. Não lê payload de componente nem libera IDs, fontes, nomes de campos privados ou secrets em logs. O relatório não constitui prova de diff disponível até analisar conteúdo versionado sob autorização separada.

## Dependências
Os indicadores operacionais são de Metadata Logs, não métricas DORA certificadas. Nenhum PR desta pesquisa altera registros Flosum nem instala funcionalidades Branch Monitor.
