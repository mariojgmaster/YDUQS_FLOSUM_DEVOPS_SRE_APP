# Plano técnico

API 67.0, Apex + LWC nativos. Seguir AGENTS.md e contratos já observados; a autorização da feature não ratifica globalmente a Constituição proposta.

## Decisões
- Objeto de configuração DevSre_EnvironmentMapping__c com Lookup para organização Flosum, classe, ValidFrom/ValidTo e justificativa; PublicReadOnly com CRUD somente via Permission Sets. Registro é dado local à org, precisa de edição em runtime e referência real; Custom Metadata não é adequado para esse vínculo de dados e edição transacional. FHT nativo habilitado. Não duplicar deployments.
- Apex EnvController controla UI, USER_MODE nas consultas/DML. Trigger/handler protege intervalos também em DML externo; bloqueio FOR UPDATE no registro de organização serializa por destino. Leitura interna de integridade em SYSTEM_MODE, restrita às organizações da transação, sem devolver dados nem alterar Flosum; necessária para enxergar todos os intervalos mesmo sob sharing.
- Configuração append-only em identidade: organization/class/from imutáveis; somente encerramento do fim e justificativa podem mudar, com FHT. Delete bloqueado. Alterações retroativas têm alerta; certificação não é implementada.
- DeploymentController usa SOQL com binds e USER_MODE, filtro fixo Process_Type=Deployment e paginação por CreatedDate/Id. Data de filtro é conclusão; registros sem conclusão usam Start_Date ou CreatedDate como fallback operacional explícito. Janela UTC [from,to), filtros server-side. Sem campos HTML/logs integrais no DTO.
- Classificação e qualidade são determinísticas em método testável; mapping devolve UNKNOWN/AMBIGUOUS. Identidade de correlação org+requestId, fallback ao Id; não há agregação DORA.
- UI devSreDeployments e devSreEnvironments, superfície SLDS com tabs internas e acesso por metadados de navegação preservados/inspecionados.

## Segurança e escala
Acesso às fontes Flosum permanece governado pelo pacote/perfil existente; novos Permission Sets não concedem ModifyAll/ViewAll nem credenciais. Não exibir dados sem USER_MODE. Até 51 logs/página, configuração até 2.001 linhas com erro explícito se exceder. Sem N+1; consultas de configurações limitadas às organizações da página. Tipos/IDs/input validados; sem SQL concatenando valores do usuário. Sem cache materializado, filas ou backend.

## Entrega
Manifest específico; CI Jest/Python e validação Metadata API com testes Apex especificados. O kit universal atual não suporta objetos/triggers/permission sets: usar workflow de validação separado, limitado ao manifest desta SPEC, mantendo o kit canônico intacto. Relatório integral de validação criptografado para análise local; sem dados privados nos logs. Nenhum deploy real nesta fase.

## Referências oficiais
https://developer.salesforce.com/docs/platform/secure-coding/guide/secure-coding-access-control-protect-from-crud-fls-vulnerabilities.html
https://developer.salesforce.com/docs/platform/lwc/guide/apex-security.html
https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_meta.pdf
