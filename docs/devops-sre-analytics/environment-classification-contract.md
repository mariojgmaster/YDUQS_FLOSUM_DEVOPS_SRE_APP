# Contrato proposto — classificação dos destinos Flosum

**Estado:** proposta de domínio; NOT_READY_FOR_IMPLEMENTATION.
**Data:** 24/10/2026.
**Origem:** solicitação do responsável para configurar quais organizações representam PROD, UAT, SIT e DEV. As inspeções #40135475770 e #40136690923 foram executadas na DevSreFeat; a segunda comprovou amostra de logs e referência candidata de organização. A semântica dos campos e o destino PROD continuam pendentes.

## Objetivo e limites

Classificar o destino real de cada deployment por referência estável à organização, sem inferir ambiente pelo nome da Branch, Pipeline, Step, usuário ou URL. A consulta é executada na DevSreFeat; isso não significa que todo destino registrado no Flosum seja DEV.

Este catálogo é configuração de negócio da aplicação. Não é a allowlist de autenticação dos GitHub Environments, não concede acesso a uma org e não autoriza deploy. Nenhuma escrita no Flosum é necessária para classificar os eventos.

## Informações mínimas por mapeamento

| Informação conceitual | Regra |
| --- | --- |
| Contexto da fonte | Identifica a instalação/origem Flosum à qual a referência pertence; não presumir IDs portáveis entre orgs |
| Referência da organização de destino | Deve ser comprovada pelo schema e pelo evento; API name observado no print: `Flosum__Organisation__c`; tipo e objeto referenciado ainda por confirmar no describe |
| Classe | PROD, UAT, SIT ou DEV; ausência de correspondência resulta em UNKNOWN |
| Vigência | Início inclusivo e fim exclusivo; fim pode ser aberto |
| Evidência e revisão | Justificativa, responsável e data da revisão, conforme política de acesso |
| Versão da configuração | Permite rastrear e invalidar resultados afetados por correções |

Podem existir várias organizações por classe. Uma organização não pode possuir duas classificações com vigências sobrepostas no mesmo contexto. A normalização da referência depende do tipo real confirmado na inspeção; não comparar apenas labels.

## Resolução de um evento

1. Obter a referência de destino do evento por relacionamento verificado no schema. Não substituir destino por org de origem nem pelo ambiente do runner.
2. Identificar o instante do evento segundo contrato temporal validado. Se não houver instante confiável para selecionar a vigência, a elegibilidade histórica permanece pendente.
3. Resolver exatamente um mapeamento vigente para a combinação contexto + referência de destino.
4. Zero correspondências resulta em UNKNOWN; múltiplas correspondências resultam em AMBIGUOUS. Nenhum dos estados pode ser tratado como PROD ou convertido silenciosamente em zero.
5. Uma correspondência PROD é condição necessária, mas insuficiente: status final, instante real de conclusão, identidade/deduplicação e cobertura continuam obrigatórios.
6. Se o destino for obtido da Branch, comprovar que o vínculo representa o destino daquele evento histórico; o estado atual da Branch sozinho não certifica o passado.

Alterações retroativas na configuração invalidam a certificação dos períodos afetados, conforme o contrato DORA existente. Eventos sem classificação permanecem visíveis como lacuna; não descartá-los para apresentar uma população aparentemente completa.

## Critérios de aceitação

| Cenário | Resultado esperado |
| --- | --- |
| Nome da Branch contém PROD, sem destino comprovado | UNKNOWN; não elegível por inferência |
| Evento aponta para organização classificada como UAT | Excluído da população PROD |
| Duas organizações distintas são PROD | Ambas podem contribuir, após os demais gates |
| Há dois mapeamentos vigentes para o mesmo destino | AMBIGUOUS; bloquear certificação do escopo afetado |
| Mapeamento termina no mesmo instante em que outro começa | Usar o segundo, sem sobreposição |
| Destino PROD, mas status ou conclusão não foram validados | Não mensurável |
| Destino ausente ou sem permissão de leitura | Lacuna explícita; não presumir ausência de deployments |
| Branch mudou de destino após um deployment | Exigir evidência histórica do destino do evento |
| Configuração histórica foi corrigida | Invalidar e revisar a certificação afetada |

## Pendências antes de plan/tasks de implementação

- Diagnóstico executado: [#40136690923](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40136690923), SUCCESS. Uma referência candidata de organização no Metadata Log, preenchida em sete de oito linhas do slot 1; slot 2 sem linhas. Não repetir a mesma amostragem para tentar inferir semântica.
- Campos exibidos no registro identificados pelo print: Branch `Flosum__Branch__c` e Organization `Flosum__Organisation__c`. Confirmar tipos, objetos referenciados, cardinalidade, acesso e semântica histórica no describe; o segundo lookup de Branch continua sem nome/papel confirmados.
- Confirmar quais logs representam tentativas, validações ou deployments reais; identificar status terminal, timestamp de conclusão, unidade e timezone.
- Confirmar a chave autoritativa da organização e os registros que correspondem a cada classe, sem publicar IDs ou valores corporativos no repositório público.
- Definir quem administra/revisa essa configuração e o mecanismo Salesforce adequado. Custom Metadata, Custom Settings ou armazenamento de dados permanecem escolhas técnicas em aberto.
- Confirmar serviços/aplicações e responsável por certificar cobertura (SPEC-003 T006c/T007/T008).
- Definir teste completo de permissões e revisão de histórico antes de liberar indicadores.

O diagnóstico de uma Branch com até oito logs fornece uma amostra de investigação, não prova completude de um período.

## Rastreabilidade

- [Descoberta Flosum](flosum-schema-discovery.md)
- [Elegibilidade DORA](../../specs/003-incident-foundation/contracts/dora-readiness.md)
- [Tarefas SPEC-003](../../specs/003-incident-foundation/tasks.md)

Nenhuma configuração real, novo objeto, Apex/LWC, fórmula, workflow ou deploy é criado por este documento.

## Mapeamento observado no print fornecido pelo responsável — 24/10/2026

Evidência de tela de um registro de `Flosum__Metadata_Log__c`, com API names anotados. Identifica os campos e o comportamento visual daquele exemplo; não equivale a describe, leitura dos valores brutos ou certificação da população. Não versionar imagem, IDs, nomes de registros, conteúdo de logs ou informações de usuários.

| Uso no contrato | API name visível | Evidência / limite |
| --- | --- | --- |
| Relação com Branch exibida na tela | `Flosum__Branch__c` | Há link de Branch; confirmar objeto referenciado pelo describe. O segundo vínculo descoberto não é identificado pelo print |
| Organização do evento | `Flosum__Organisation__c` | Há link de organização apresentada como produção; o mapeamento usa referência validada, não label |
| Tipo de operação | `Flosum__Process_Type__c` | Exemplo exibe `Deployment`; consultar domínio completo para distinguir validações e outras operações |
| Estado | `Flosum__Status__c` | Exemplo exibe `Completed`; não substitui a verificação do resultado |
| Finalização do job | `Flosum__Job_Completed__c` | Checkbox marcado no exemplo; confirmar tipo e valor bruto |
| Resultado | `Flosum__Result__c` | Renderiza badge `Success`; não presumir valor bruto textual, booleano ou fórmula sem describe/leitura |
| Data apresentada como Deployment Date | `Flosum__Deployment_Date__c` | Campo existe; não está comprovado que represente conclusão efetiva, nem seu timezone |
| Correlação com requisição | `Flosum__Async_Request_Id__c` | Identifica requisição no exemplo; validar preenchimento, unicidade e relação com tentativas antes de deduplicar |
| Nome de exibição do deployment | `Flosum__Deployment_Name_Generate__c` | Não usar nome como identidade ou relógio |
| Registro relacionado, label Deployment | `Flosum__Patch__c` | Exemplo vazio; tipo e papel permanecem pendentes |

**Regra candidata, ainda sem implementação:** considerar processo Deployment, estado Completed, job finalizado e resultado de sucesso verificado em valor bruto, combinados com organização explicitamente mapeada como PROD. Validar a interação entre os campos com exemplos de sucesso, falha, validação e tentativas repetidas antes de usar como filtro definitivo. Um campo visual de resultado pode ser derivado e não consultável como filtro; não definir SOQL por suposição.

**Contrato temporal ainda aberto:** a tela mostra Deployment Date no mesmo minuto da criação e Last Modified dois minutos depois. Isso torna inadequado assumir conclusão a partir do nome do campo; também não autoriza usar LastModifiedDate, que pode refletir outras alterações. Confirmar semântica do campo com a fonte e/ou uma evidência de conclusão da requisição. Não calcular Lead Time ou janelas de deployments certificados com data ainda não verificada.

**Próximo passo técnico:** describe e consulta pontual dos campos explicitamente identificados, conferindo tipos, valores brutos mínimos e referências, pelo mecanismo de leitura autorizado. Substituir seleção heurística por campos comprovados, sem publicar payloads ou dados corporativos em logs do repo público. O print já atende à identificação visual; não solicitar novamente a mesma lista de campos.
