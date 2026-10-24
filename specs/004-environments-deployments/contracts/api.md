# Contratos Apex

EnvController: bootstrap/searchOrganizations -> opções visíveis e capacidade de gerência; listMappings -> até 2.000 vigências com sinalização de excesso; saveMapping(id,organizationId,class,from,to,reason) cria ou encerra/justifica um período, nunca altera sua identidade.

DeploymentController.listDeployments(from,to,organizationId,branchId,environmentClass,outcome,cursorCreated,cursorId): página de 50 com hasMore e próximo cursor. DTOs sem raw HTML, credenciais ou logs de componentes. Sem total global, sem KPI certificado.
