# Quickstart — Pipeline Monitor

## Pré-requisitos

- Org Salesforce com Flosum; usuário autorizado a ler `Flosum__Pipeline__c`, `Name`, `Flosum__PipelineStep__c`, lookup de Pipeline e campos opcionais exibidos.
- Autorização de acesso à Apex class `DevSrePipelineMonitorController` concedida à persona adequada.
- Repositório com Salesforce CLI/ECA JWT homologado; não compartilhar segredos.
- Configuração do App e da tab SLDS 2 validada na org.

## Testes do repositório

```sh
npm ci --ignore-scripts --no-audit --no-fund
npx eslint force-app/main/default/lwc/devSrePipelineMonitor/devSrePipelineMonitor.js
npm run test:unit -- --runInBand --runTestsByPath force-app/main/default/lwc/devSrePipelineMonitor/__tests__/devSrePipelineMonitor.test.js
```

## Para validação posterior na DevSreFeat (não executar por este PR)

Revisar `manifest/sf-devops-sre-pipeline-monitor.xml`, o SHA exato, branch, permissões e alvo allowlisted. Usar fluxo aprovado de validação Salesforce no GitHub Actions; não adicionar pacote à allowlist nem implantar implicitamente. Executar `DevSrePipelineMonitorControllerTest` na mesma validação.

Após aprovação e deploy explícito, criar **Lightning Component Tab** para `devSrePipelineMonitor` (Setup → Tabs) e inserir a aba no Lightning App pelo App Manager, ou revisar metadata equivalente antes de deploy. Exibir a área no Lightning Experience, preferencialmente com Cosmos se habilitado. Verificar busca, Steps, navigação, campos escondidos por FLS, erros e limites.

## Evidência

Anotar aqui os IDs dos jobs, URL do run e resultados somente **após execução real**. No estado inicial: testes na org **não executados**; deploy real **não executado**.
