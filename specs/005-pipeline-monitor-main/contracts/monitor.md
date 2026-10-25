# Contratos de leitura

listDeployments permanece compatível. listMonitorDeployments(fromUtc,toUtc,organizationId,environmentClass,outcome,searchTerm,cursorCreated,cursorId) retorna o mesmo DeploymentPage de até 50 correspondências/200 candidatos, cursor estável e hasMore. Busca aplica Name ou Branch.Name no servidor, até 80 caracteres, curingas tratados como texto.

getMonitorSummary(fromUtc,toUtc,organizationId,environmentClass,searchTerm) retorna complete,total,pending,succeeded,failed,partial,notRun,unknown,successRate. Não recebe filtro de resultado para preservar o contexto completo dos cards. Até 2.000 candidatos; complete=false com contagens nulas quando excede o limite. Limite é aplicado antes do filtro por ambiente, e a UI orienta período/organização para reduzir candidatos. Respeita a classificação temporal e não infere ambiente por nome.

Endpoint não diferencia fila/em execução; pending é a ausência de conclusão de processamento no contrato atual. Rate considera apenas Success/Failed/Partial. A lista mantém resultados separados e observações da fonte.

O resumo e a página são leituras separadas, não um snapshot transacional comum. Ambos são atualizados no refresh; alterações concorrentes na fonte podem produzir pequenas diferenças temporárias. Os cartões não têm certificação DORA.
