# Plano técnico

Reutilizar DevSreDeploymentController e o contrato de status/classificação de ambientes já comprovado. Manter listDeployments e seu DTO compatíveis. Extrair somente consulta de fonte/vigências comuns, adicionar listMonitorDeployments com busca e getMonitorSummary sem cursor. Todas as leituras continuam em USER_MODE, with sharing e com limites explícitos. Resumo agrupa vigências por organização para evitar cruzamento global desnecessário.

Nova LWC devSrePipelineOverview, usando o módulo de estilos compartilhado, Base Components e tokens semânticos. O host devSreDeliveryHub passa a renderizá-la antes das abas atuais e a atualiza após mudança de classificação. Sem mudanças nas abas.

Kit universal existente, sem alterar workflows: manifesto pipeline-monitor-main contém os dois Apex e os bundles Overview/Hub; pipeline-monitor-existing permite comparar os três componentes já presentes antes da escrita. O módulo CSS compartilhado e permissões de acesso à classe já estão implantados. Validação integral alternativa pela SPEC004 inclui a dependência nova. Mesclar após checks e validar na DevSreFeat antes de qualquer implantação.

Constitution: feature explicitamente autorizada, sem alteração constitucional ou nova infraestrutura. SFDX API67, source sharing/FLS, simplicidade e nenhuma operação destrutiva preservados.
