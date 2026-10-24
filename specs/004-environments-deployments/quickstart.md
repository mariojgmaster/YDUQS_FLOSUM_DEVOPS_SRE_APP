# Homologação

1. Implantar somente após dry-run aprovado e autorização específica; atribuir DevSreDeployment_Reader ou DevSreEnvironment_Manager conforme persona.
2. Gerente consulta uma organização visível, registra classificação e vigência explícitas. Nenhum mapeamento é gerado pelo nome da organização.
3. Leitor filtra uma janela UTC, compara deployments com o Metadata Log e abre o registro original. Validar ausência de validações/etapas auxiliares.
4. Verificar falha, não executado, relógio incompleto, ambiente desconhecido e paginação. Conferir histórico de campos no registro de configuração.
5. Não apresentar os resultados como KPI DORA certificado. Reversão: remover acesso à UI; conservar configurações/histórico. Sem destructive changes ou alteração dos registros gerenciados.
