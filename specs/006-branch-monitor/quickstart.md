# Quickstart de desenvolvimento — SPEC-006

## Contexto de origem
Repositório: `mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP`. SFDX API 67; SLDS 2. Alvo de homologação: `DevSreFeat` (sandbox) no GitHub Environment allowlisted `sf-devsrefeat-read`. ECA/JWT já verificados em runs anteriores. Catálogo operacional: `config/salesforce-devops/catalog.json`; não pressupor `.salesforce-devops/environments.json`, ausente neste repositório.

## Ordem segura
1. Leia `spec.md`, `research.md`, `data-model.md`, `contracts/api.md`, `plan.md` e `tasks.md`.
2. Execute testes locais de scripts sem Salesforce (e.g. `python3 -m unittest tests.test_sf_flosum_component_research` ou descoberta via `unittest discover`).
3. Para G0 utilize apenas o workflow allowlisted de diagnóstico: `sf-devsrefeat-diagnostics.yml`, sem escrita. Não exiba JSON bruto do Salesforce em logs públicos.
4. Só implemente Apex/LWC do M1 a partir dos campos confirmados. Preview de Dados ilustrativos **apenas em wireframe/test fixture**, nunca em runtime da aplicação.
5. PR → CI Jest/ESLint + testes de política → dry-run DevSreFeat → deploy real sob pedido explícito do usuário, fixado a commit/pacote → compare pós-deploy.
6. Verifique manualmente a LWC no Salesforce Lightning: acesso Reader, responsividade, foco, navegação, filtros, reticências, dados incompletos e erros.

## Go/no-go
- É aceitável entregar M1 antes de G4; o Diff pode permanecer não disponível com razão explícita (nunca fake).
- Não oferecer Diff de conteúdo, histórico de deploy por componente ou inferência de alterações enquanto histórico/revisão/correlação não estiverem comprovados.
- Não modificar configuração legada do Pipeline Monitor/ambientes para produzir dados faltantes.
