# M1 — Visão geral e Branch Directory — implementação incremental

- Controller read-only `DevSreBranchMonitorController` com `with sharing` e `USER_MODE`.
- `listBranches`: busca literal por nome, cursor Name/Id, até 30 por página; nenhuma totalização global declarada.
- `getOverview`: recorte por CreatedDate dos Metadata Logs (7/30/90 dias), limite de 500 logs para indicadores completos; 8 recentes disponíveis mesmo quando excedido, com aviso. Contagens de operação e sucesso **não** são DORA.
- `getBranchDetail`: Branch real, últimos 90 dias de logs referidos, 50 itens e flag de continuação.
- LWC `devSreBranchMonitor`: shell com quatro abas (Visão geral, Branches, Comparar, Componentes), primeiras duas funcionais, próximas duas explicitamente pendentes sem dados fake; filtros imediatos, debounce 350 ms, proteção contra respostas obsoletas, teclado e navegação ao Flosum.
- `branchMonitor.tab-meta.xml`: CustomTab preparado, **não incluído** no pacote universal M1 por limitação atual da política ChatOps a ApexClass e LightningComponentBundle.
- `sf-branch-monitor-navigation-pending.xml`: manifesto separado, ainda sem autorização de escrita. A CustomApplication real não está versionada no repositório: recuperar metadata e preservar order/visibility de outras tabs antes de publicá-la.
- **Permissões:** criar/atualizar PermissionSet para acesso ao novo controller em implantação independente, antes do uso por Reader; atual allowlist ChatOps não aceita PermissionSet. Não tratar controller publicado como acesso concedido a todos.
- Package allowlisted `branch-monitor-m1`: somente classe Apex/teste e bundle LWC. Dry-run/aprovação para deploy real específicos de SHA, não automáticos.
- Limitações M1: o vínculo Component→History foi validado na amostra, mas os campos FullName, versão/snapshot e correlação por deploy ainda não são fonte implementada. Sem promessas de Diff ou Describer funcional.

## Integração observada em 25/10/2026 — rollout em duas fases
- Inspeção read-only [run #40259837765](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40259837765): CustomApplication `DevOps_SRE_Analytics`, label confirmado, 4 tabs, Pipeline Monitor na posição 2, Branch Monitor ausente. SHA256 do XML atual fixado no script.
- Validação integrada única [run #40260380002](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40260380002) montou Apex/LWC/CustomTab/PermissionSet/CustomApplication, mas Salesforce rejeitou um metadata component antes dos testes. Diagnóstico específico [run #40260592359](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40260592359): `LightningComponentBundle:devSreBranchMonitor`, categoria `TAB_REFERENCE`. Isso indica falha na resolução da referência do LWC durante a implantação conjunta; a causa exata não foi publicamente exposta. Dry-run **não passou**.
- Rollout corrigido: **Fase 1** `branch-monitor-m1` (Apex/LWC, 6 testes Apex, dry-run já aprovado no SHA anterior, revalidar no commit corrente); **Fase 2** `branch-monitor-m1-integration` (CustomTab, Reader PermissionSet e CustomApplication recuperada, modificando exclusivamente a posição da nova tab). A Fase 2 bloqueia por padrão se as classes e LWC da Fase 1 não estiverem publicados.
- O `sf-branch-monitor-integrated-plan.py` é somente dry-run e usa hash pré-inspeção da Application, para impedir sobrescrita se houver alterações administrativas posteriores.
- **Deploy persistente exige autorização explícita para cada fase** e comparação pós-deploy. Atribuir `DevSreBranchMonitor_Reader` ao público autorizado separadamente, conforme política de usuários; publicar Permission Set não atribui permissões automaticamente.
- Não alterar metadados da CustomApplication por template incompleto. Não limpar/reescrever outras abas ou configurações da app.
