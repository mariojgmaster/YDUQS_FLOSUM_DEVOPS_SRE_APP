# SPEC-004 — Ambientes e deployments reais

Autorização: pedido explícito “Implemente isso” em 24/10/2026, após definição do escopo e descoberta integral. Esse pedido autoriza preparação, implementação e validação; implantação persistente na DevSreFeat depende da proposta final e aceite.

## Requisitos
- R1 Administrador da aplicação classifica uma organização Flosum como PROD/UAT/SIT/DEV, por vigência UTC [início,fim), com justificativa e histórico. Não inferir pelo nome.
- R2 Leitores consultam deployments reais por período (máximo 366 dias), organização, ambiente, Branch e resultado. Lista paginada de 50 linhas, sem total global fabricado.
- R3 Fonte: Metadata Log; apenas Process Type = Deployment neste incremento. Sucesso requer Completed, Job Completed, Succeed e NOT Is Error. Validar datas e mapear vigência pela conclusão; início é referência operacional para eventos ainda sem término. Sem relógio, classificação é UNKNOWN.
- R4 Falhas, não executados, parciais, ausência de datas/organização/mapeamento e conflitos são apresentados explicitamente. UNKNOWN/AMBIGUOUS não são PROD. Não implementar KPI DORA, commit/Lead Time ou certificação.
- R5 Navegar ao registro original via NavigationMixin. Não modificar Flosum, não executar deploy/rollback pelo produto.
- R6 CRUD/FLS/sharing, paginação e mensagens seguras no servidor. Configuração administrável somente com permissão granular. Impedir intervalos sobrepostos, inclusive concorrentes; preservar identidade/classificação/início de registros existentes.
- R7 Abas Deployments, Ambientes e Pipeline (visão original preservada). Seguir o Design System versionado em `docs/design-system.md` com Base Components Lightning, tokens semânticos, estados de carregamento/vazio/erro, atualização e prevenção de respostas obsoletas.
- R8 Ambientes abre nas classificações atuais; futuras e encerradas têm visões explícitas. O cadastro aparece sob ação do gerente, explica “vale desde” e revela término opcional sob demanda. Não presumir data inicial nem classificação de organizações. Ver `ux-refinement.md`.

## Aceitação
- Deployment Completed/Succeed=false nunca é Sucesso; Validate não aparece.
- Dois períodos adjacentes são aceitos; overlap é rejeitado na UI e na API/DML.
- Edição não reescreve organização, classe ou início; é possível encerrar a vigência e registrar novo período. Exclusão proibida.
- Leitor não cria/edita; gerente sem acesso à organização não a enumera nem cadastra.
- Fim anterior ao início do deploy gera lacuna, nunca ABS/duração negativa.
- Mais de 50 linhas gera cursor e paginação, sem sugerir contagem global. Requisições repetidas recebem sinalização/identidade de correlação, sem somar logs como KPI.
- Nenhum ID corporativo ou mapeamento inicial hardcoded.
