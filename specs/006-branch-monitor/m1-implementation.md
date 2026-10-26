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
