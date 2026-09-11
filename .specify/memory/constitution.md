<!--

Sync Impact Report

- Version: 1.0.0
- Rationale: Constituição inicial do projeto Salesforce DevOps/SRE DORA Metrics App.
- Baseline estrutural: derivada dos princípios de engenharia, segurança, governança,
  incrementalidade e SpecKit adotados no projeto Salesforce OAuth Login Manager,
  substituindo regras específicas de Chrome Extension por regras adequadas à
  Salesforce Platform.
- Product scope: Lightning App para observabilidade do ciclo de vida de entregas
  através das cinco métricas atuais de Software Delivery Performance do DORA.
- Salesforce architecture baseline: Salesforce Well-Architected — Trusted, Easy,
  Adaptable.
- Development model: desenvolvimento individual assistido por GPTCodex em sandbox
  Flosum dedicada ao projeto.
- Primary users: DevOps, SRE e Salesforce Center of Excellence (COE).
- DORA model: Change Lead Time, Deployment Frequency,
  Failed Deployment Recovery Time, Change Fail Rate e Deployment Rework Rate.
- Templates: revisar plan-template.md, spec-template.md, tasks-template.md e
  checklist-template.md após ratificação.
- Follow-up: aprovação desta versão está pendente; decisões arquiteturais ainda
  não validadas devem ser tratadas como ADR ou UNVERIFIED_PLATFORM_BEHAVIOR.

-->

# Salesforce DevOps/SRE DORA Metrics App — Project Constitution

**Status**: Proposta — aguardando aprovação

**Aplicação**: Todas as SPECs, ADRs, alterações arquiteturais, modelos de dados,
integrações, automações, componentes Lightning, código Apex, configurações,
deployments e implementações futuras deste projeto.

## 1. Princípio Salesforce Well-Architected

A solução MUST ser projetada segundo os princípios Salesforce Well-Architected:
Trusted, Easy e Adaptable.

Decisões arquiteturais MUST considerar segurança, confiabilidade, performance,
escalabilidade, manutenibilidade, experiência do usuário, automação, resiliência,
interoperabilidade e evolução.

Uma solução tecnicamente funcional que introduza risco operacional,
complexidade desnecessária ou dificuldade significativa de manutenção MUST NOT
ser considerada arquiteturalmente concluída.

## 2. Segurança por Design

Segurança MUST ser requisito arquitetural e não etapa posterior.

Toda feature MUST avaliar, quando aplicável:

* autenticação;
* autorização;
* sharing;
* CRUD;
* Field-Level Security;
* exposição de dados;
* integração;
* secrets;
* logs;
* dados sensíveis;
* permissões;
* execução em contexto de usuário ou sistema;
* superfícies de ataque;
* auditabilidade.

Redução relevante de segurança exige decisão arquitetural explícita e
documentada.

## 3. Least Privilege

Usuários, Permission Sets, Permission Set Groups, integrações, Connected Apps,
External Client Apps, Named Credentials, External Credentials, OAuth scopes e
acesso a objetos/campos MUST seguir menor privilégio.

Permissão MUST existir por necessidade funcional atual.

"Pode ser necessário futuramente" MUST NOT justificar privilégio adicional.

A aplicação MUST NOT depender de perfis excessivamente permissivos,
Modify All Data, View All Data ou permissões administrativas como mecanismo
normal de funcionamento, salvo requisito formalmente justificado.

## 4. Sharing, CRUD e Field-Level Security

A segurança de dados MUST ser aplicada explicitamente.

Código Apex MUST considerar separadamente:

1. record-level access;
2. object-level access;
3. field-level access.

`with sharing`, `inherited sharing`, User Mode e mecanismos oficiais equivalentes
MUST ser avaliados conforme o contexto.

`without sharing` exige necessidade explícita e justificativa arquitetural ou de
segurança.

A existência de sharing MUST NOT ser interpretada como garantia automática de
CRUD/FLS.

## 5. Personas de Segurança

A aplicação MUST definir personas de autorização, inicialmente incluindo quando
aplicável:

* DevOps;
* SRE;
* COE;
* Administrador da aplicação.

Acesso SHOULD ser concedido por Permission Sets e/ou Permission Set Groups.

Permissões individuais ad hoc SHOULD NOT constituir o modelo principal de
autorização.

## 6. Configuração Antes de Hardcode

IDs, usernames, endpoints, nomes de orgs, thresholds, janelas temporais,
categorizações, filtros, regras operacionais e parâmetros configuráveis MUST NOT
ser hardcoded quando forem sujeitos a variação entre ambientes ou evolução do
produto.

Usar mecanismo Salesforce adequado conforme natureza do dado, por exemplo:

* Custom Metadata Types;
* Custom Settings quando justificável;
* Custom Labels;
* Named Credentials;
* External Credentials;
* metadata nativa da plataforma.

A escolha MUST refletir ciclo de vida, segurança, deployabilidade e ownership da
configuração.

## 7. Declarativo versus Programático

A solução MUST escolher a ferramenta Salesforce mais simples que satisfaça
corretamente o requisito.

Flow, fórmulas, validation rules, Lightning App Builder e recursos declarativos
SHOULD ser considerados antes de código quando reduzirem complexidade sem
prejudicar performance, governança, segurança, testabilidade ou manutenção.

Apex MUST ser usado quando houver necessidade técnica clara.

Declarativo MUST NOT ser escolhido apenas para evitar código quando produzir
automação opaca, difícil de testar, duplicada, excessivamente acoplada ou
operacionalmente frágil.

Código MUST NOT substituir desnecessariamente uma capacidade nativa simples e
adequada da plataforma.

## 8. Lightning Web Components

Lightning Web Components (LWC) MUST ser a tecnologia padrão para componentes
customizados de UI, salvo necessidade comprovada de tecnologia diferente
suportada pela Salesforce.

Componentes SHOULD ser pequenos, coesos, reutilizáveis quando houver reutilização
real e separados entre apresentação, estado e acesso a serviços.

LWC MUST NOT concentrar regras de negócio críticas que pertençam ao domínio ou
Application Layer.

A UI MUST NOT assumir que dados recebidos do servidor estão autorizados apenas
porque foram renderizados por Salesforce.

## 9. Separação de Responsabilidades

A arquitetura MUST separar responsabilidades de apresentação, aplicação,
domínio e infraestrutura quando a complexidade justificar.

Fluxo preferencial para comportamento customizado:

`LWC / Flow → Application Service → Domain Logic → Data/Integration Adapter`

Triggers MUST NOT conter lógica de negócio complexa.

Controllers LWC/Aura MUST NOT se transformar em classes monolíticas contendo
orquestração, queries, regras de domínio, integrações e persistência
indiscriminadamente.

Abstrações adicionais exigem benefício concreto.

## 10. Apex com Responsabilidade Clara

Classes Apex MUST possuir responsabilidade compreensível.

Priorizar:

* alta coesão;
* baixo acoplamento;
* nomes explícitos;
* métodos pequenos;
* contratos claros;
* comportamento determinístico quando possível;
* separação de integração e domínio.

God classes, utility classes genéricas sem domínio claro e abstrações
especulativas são proibidas.

## 11. Bulkification

Todo Apex aplicável MUST ser bulk-safe.

SOQL, SOSL, DML e callouts MUST NOT ser executados dentro de loops quando isso
criar consumo proporcional evitável de governor limits.

Código MUST funcionar corretamente para coleções e operações em massa quando o
entry point puder recebê-las.

Implementação que funciona apenas para um registro quando o contexto Salesforce
permite múltiplos registros MUST ser considerada defeituosa.

## 12. Governor Limits como Restrição Arquitetural

Governor limits MUST ser tratados como restrições arquiteturais fundamentais da
Salesforce Platform.

Toda solução relevante MUST avaliar consumo de:

* SOQL;
* linhas consultadas;
* DML;
* CPU;
* heap;
* callouts;
* async execution;
* limites de API;
* limites específicos do recurso Salesforce utilizado.

A arquitetura MUST NOT depender de comportamento próximo ao limite nominal em
condições normais.

Limites críticos MUST possuir margem operacional razoável.

## 13. SOQL e Acesso a Dados

Queries MUST recuperar somente os dados necessários.

Evitar:

* SELECT indiscriminado;
* consultas repetidas;
* N+1 queries;
* consultas sem seletividade em alto volume;
* carregamento de datasets completos para filtragem em memória;
* relacionamento excessivo sem necessidade.

Query design MUST considerar volume atual e crescimento esperado.

Otimização prematura é proibida, mas padrões sabidamente não escaláveis também
são proibidos.

## 14. DML e Transações

Operações DML MUST ser agrupadas quando apropriado.

A implementação MUST compreender explicitamente sua boundary transacional.

Falha parcial versus rollback total MUST ser decisão consciente.

Quando partial success for requisito, mecanismos Salesforce adequados MUST ser
avaliados explicitamente.

Transações MUST NOT realizar trabalho síncrono desnecessário que aumente CPU,
latência, lock contention ou risco de timeout.

## 15. Large Data Volume

Modelos de dados e queries MUST considerar crescimento futuro razoavelmente
previsível.

Quando volumes elevados forem possíveis, o design MUST avaliar:

* seletividade;
* índices;
* cardinalidade;
* skew;
* ownership;
* sharing;
* retenção;
* agregação;
* arquivamento;
* purge;
* estratégia de consulta.

LDV MUST ser tratado no design antes de se tornar incidente de produção.

## 16. Modelo de Dados Intencional

Objetos, campos, relacionamentos e registros MUST representar conceitos claros
do domínio DevOps/SRE.

O modelo MUST distinguir, quando aplicável:

* aplicação/serviço;
* ambiente;
* pipeline;
* mudança;
* commit;
* deployment;
* incidente;
* recuperação;
* período de medição;
* resultado agregado;
* origem do dado.

Duplicação de informação exige justificativa.

Campos derivados SHOULD ser calculados ou agregados de forma controlada quando
isso reduzir inconsistência.

## 17. Identidade e Correlação de Entidades

Registros originados de sistemas externos MUST possuir estratégia explícita de
identidade e correlação.

Nome visível MUST NOT ser usado como identificador técnico quando houver chave
estável disponível.

External IDs, IDs compostos ou outra estratégia formalmente definida SHOULD ser
utilizados para garantir idempotência e reconciliação.

A mesma entidade externa MUST NOT gerar duplicatas silenciosas em ingestões
repetidas.

## 18. DORA como Contrato de Domínio

O produto MUST tratar as cinco métricas atuais de Software Delivery Performance
do DORA como conceitos formais de domínio:

1. Change Lead Time;
2. Deployment Frequency;
3. Failed Deployment Recovery Time;
4. Change Fail Rate;
5. Deployment Rework Rate.

Definições MUST permanecer alinhadas à documentação oficial atual do DORA.

Uma SPEC MUST NOT alterar semanticamente uma métrica apenas para facilitar sua
implementação.

Adaptações organizacionais são permitidas somente quando explicitamente
identificadas como extensão ou interpretação local e não como definição oficial
DORA.

## 19. Throughput e Instability

As métricas MUST preservar a organização conceitual DORA vigente.

Throughput:

* Change Lead Time;
* Deployment Frequency;
* Failed Deployment Recovery Time.

Instability:

* Change Fail Rate;
* Deployment Rework Rate.

Dashboards MAY apresentar agregações adicionais, scores, tendências e
indicadores derivados, mas MUST NOT confundi-los com métricas DORA oficiais.

## 20. Contexto das Métricas

Métricas DORA MUST ser contextualizadas por aplicação ou serviço e período de
análise quando aplicável.

Agregações entre aplicações, equipes, tecnologias ou contextos distintos MUST
ser explicitamente identificadas.

O produto MUST evitar induzir comparações enganosas entre contextos
materialmente diferentes.

Métricas MUST ser usadas como instrumento de melhoria contínua, não como
mecanismo simplista de ranking individual.

## 21. Proveniência dos Dados

Todo dado utilizado para produzir métrica relevante MUST possuir proveniência
suficiente para auditoria.

Quando aplicável, MUST ser possível identificar:

* origem;
* entidade externa;
* timestamp de origem;
* timestamp de ingestão;
* transformação aplicada;
* período considerado;
* versão ou regra de cálculo.

Resultado sem rastreabilidade adequada MUST NOT ser apresentado como métrica
confiável.

## 22. Cálculos Determinísticos

Cálculos DORA MUST ser determinísticos para a mesma entrada, configuração e
versão da regra.

Fórmulas e critérios MUST ser centralizados.

A mesma métrica MUST NOT possuir implementações divergentes em LWC, Apex, Flow,
reports ou outros componentes.

Alterações em fórmulas que modifiquem resultados históricos exigem análise de
impacto e estratégia explícita de versionamento ou recálculo.

## 23. Qualidade dos Dados

Dados externos MUST ser considerados não confiáveis até validação.

Ingestão MUST considerar:

* ausência;
* duplicidade;
* timestamp inválido;
* timezone;
* ordem de eventos;
* atraso;
* reprocessamento;
* evento fora de sequência;
* campos inesperados;
* referências inexistentes;
* dados parcialmente disponíveis.

Dados inválidos MUST NOT contaminar silenciosamente métricas agregadas.

## 24. Timezone e Tempo

Datas e horários são parte crítica do domínio.

Persistência e cálculo MUST seguir comportamento temporal suportado pela
Salesforce e definir claramente timezone de origem, armazenamento, apresentação
e agregação.

Cálculo MUST NOT depender implicitamente do timezone do desenvolvedor ou usuário
quando isso alterar a semântica da métrica.

Janelas como dia, semana, mês e período customizado MUST possuir definição
inequívoca.

## 25. Integrações

Integrações externas MUST possuir contrato explícito.

Cada integração relevante MUST definir:

* autenticação;
* autorização;
* endpoint;
* payload;
* timeout;
* volume;
* rate limits;
* retry;
* idempotência;
* erro;
* observabilidade;
* ownership;
* comportamento em indisponibilidade.

Integração MUST NOT assumir disponibilidade permanente do sistema externo.

## 26. Credenciais e Secrets

Secrets, passwords, tokens, API keys e credenciais MUST NOT existir hardcoded em
Apex, LWC, Flow, Custom Metadata, Custom Labels, source control, logs ou fixtures.

Named Credentials, External Credentials e mecanismos oficiais atuais da
Salesforce SHOULD ser usados conforme aplicabilidade.

Credenciais MUST seguir least privilege e possuir lifecycle administrável.

## 27. Processamento Assíncrono

Processamento assíncrono MUST ser utilizado quando houver justificativa por
volume, callout, desacoplamento, latência ou limite transacional.

Queueable Apex, Batch Apex, Scheduled Apex, Platform Events, Change Data Capture
e outros mecanismos MUST ser escolhidos segundo o problema real.

Async MUST NOT ser usado apenas como workaround para arquitetura síncrona
ineficiente.

Toda cadeia assíncrona relevante MUST considerar falha, retry, duplicidade,
ordenação, monitoramento e recuperação.

## 28. Event-Driven Architecture sem Overengineering

Platform Events, CDC ou arquitetura orientada a eventos MUST ser usados somente
quando desacoplamento temporal, fan-out, integração ou escala justificarem.

Um event bus MUST NOT substituir chamada simples e previsível apenas por
flexibilidade futura.

Eventos relevantes MUST possuir contrato, ownership, versionamento e estratégia
de idempotência.

## 29. Idempotência

Ingestões, retries, processamento assíncrono e integrações suscetíveis a
reexecução MUST ser idempotentes quando tecnicamente aplicável.

A mesma mensagem, deployment ou evento recebido novamente MUST NOT produzir
duplicidade ou distorção silenciosa das métricas.

Quando idempotência perfeita não for possível, a limitação MUST ser documentada
e mitigada.

## 30. Tratamento de Erros

Falhas MUST possuir comportamento explícito.

Integrações e processos MUST considerar:

* timeout;
* autenticação;
* autorização;
* rate limit;
* resposta inválida;
* indisponibilidade;
* dado inválido;
* limite Salesforce;
* falha de processamento;
* duplicidade;
* configuração inválida.

Erro técnico e mensagem segura ao usuário MUST ser separados.

Stack traces, secrets e payloads sensíveis MUST NOT ser exibidos na UI.

## 31. Taxonomia de Erros

Erros relevantes SHOULD possuir taxonomia consistente.

Categorias iniciais:

`AUTHENTICATION_ERROR`
`AUTHORIZATION_ERROR`
`VALIDATION_ERROR`
`CONFIGURATION_ERROR`
`INTEGRATION_ERROR`
`REQUEST_TIMEOUT`
`RATE_LIMITED`
`EXTERNAL_SYSTEM_UNAVAILABLE`
`DATA_QUALITY_ERROR`
`DUPLICATE_EVENT`
`PROCESSING_ERROR`
`GOVERNOR_LIMIT_RISK`
`ASYNC_PROCESSING_ERROR`
`METRIC_CALCULATION_ERROR`
`UNKNOWN_ERROR`

Quando aplicável, erro MUST conter:

* código;
* categoria;
* mensagem segura;
* retryability;
* severity;
* ação recomendada;
* contexto técnico não sensível.

## 32. Retry Seguro

Operações MUST ser classificadas como retryable, conditionally retryable ou
non-retryable quando retry fizer parte do fluxo.

Retry cego ou infinito é proibido.

Retry MUST considerar:

* idempotência;
* backoff;
* limite máximo;
* governor limits;
* rate limit externo;
* duplicidade;
* impacto operacional.

Erro permanente MUST NOT ser mascarado por retries contínuos.

## 33. Observabilidade

Processos críticos MUST ser observáveis proporcionalmente ao risco.

Quando aplicável, registrar:

* operação;
* correlation ID;
* integração;
* duração;
* resultado;
* quantidade processada;
* erro não sensível;
* timestamp;
* contexto suficiente para diagnóstico.

Logs MUST NOT conter secrets ou dados sensíveis desnecessários.

Observabilidade MUST permitir distinguir falha funcional, falha de integração,
falha de dados e falha da plataforma quando tecnicamente possível.

## 34. Auditabilidade das Métricas

Um usuário autorizado SHOULD conseguir compreender por que determinada métrica
possui determinado valor.

Quando economicamente razoável, o sistema SHOULD permitir drill-down da métrica
agregada até eventos ou registros que contribuíram para seu cálculo.

Correções de dados MUST preservar rastreabilidade suficiente para investigação.

## 35. Performance de UI

Lightning pages e LWCs MUST ser projetados para carregamento progressivo e
volume realista.

A UI MUST NOT carregar datasets inteiros quando agregação, paginação,
lazy loading ou consulta específica resolverem o requisito.

Cálculos pesados SHOULD ocorrer no layer apropriado e não repetidamente no
browser.

Performance percebida pelo usuário é requisito de qualidade.

## 36. UX para DevOps, SRE e COE

A aplicação MUST priorizar clareza operacional.

Dashboards MUST favorecer:

* tendência;
* contexto;
* comparação temporal válida;
* identificação de degradação;
* investigação;
* ação.

Vanity metrics e visualizações sem decisão associada SHOULD ser evitadas.

Cor, ícones ou posição MUST NOT ser o único meio de comunicar estado crítico.

Acessibilidade Salesforce aplicável MUST ser preservada.

## 37. Cache e Dados Derivados

Cache ou materialização de métricas MUST existir somente quando houver
necessidade comprovada de performance, custo ou escala.

Dados derivados MUST possuir estratégia explícita de:

* invalidação;
* atualização;
* reconstrução;
* consistência;
* versionamento da fórmula.

Cache MUST NOT se tornar fonte de verdade acidental.

## 38. Testabilidade

Regras de domínio críticas MUST ser testáveis independentemente da UI.

Testes proporcionais ao risco MUST cobrir, quando aplicável:

* cálculos DORA;
* bulkification;
* segurança;
* sharing;
* CRUD/FLS;
* integração;
* parsing;
* idempotência;
* duplicatas;
* timezones;
* erros;
* processamento assíncrono;
* volumes relevantes.

Bug crítico corrigido exige teste de regressão quando tecnicamente possível.

## 39. Apex Tests

Apex customizado MUST possuir testes significativos.

Cobertura percentual exigida pela plataforma é condição necessária, mas MUST NOT
ser tratada como evidência suficiente de qualidade.

Testes MUST validar comportamento e não apenas executar linhas.

Testes SHOULD cobrir:

* happy path;
* boundary conditions;
* bulk scenarios;
* erros;
* autorização quando aplicável;
* dados inválidos;
* reprocessamento;
* comportamento assíncrono.

`SeeAllData=true` é proibido salvo necessidade excepcional documentada.

## 40. Test Data

Testes MUST criar dados controlados e determinísticos.

Factories ou builders de teste MAY ser introduzidos quando reduzirem duplicação
real e aumentarem legibilidade.

Testes MUST NOT depender de IDs, usuários, metadata ou dados mutáveis de uma org
específica sem mecanismo explícito e justificado.

## 41. Testes de Integração

Integrações MUST ser testáveis sem depender permanentemente do sistema externo
real.

Callout mocks ou mecanismos oficiais equivalentes MUST ser usados em automated
tests quando aplicável.

Contratos externos críticos SHOULD possuir validação de integração apropriada
fora do unit test quando possível.

## 42. Security Testing

Features aplicáveis MUST testar cenários de segurança, incluindo:

* usuário sem Permission Set;
* acesso indevido a objeto;
* acesso indevido a campo;
* acesso indevido a registro;
* input malformado;
* injection;
* exposição de segredo;
* endpoint inválido;
* payload malicioso;
* execução em contexto inadequado.

Segurança MUST NOT depender apenas de code review.

## 43. Metadata e Source of Truth

Metadata do projeto MUST ser versionável.

A sandbox Flosum é ambiente de desenvolvimento, não fonte única de verdade
arquitetural.

Mudanças relevantes MUST possuir representação rastreável em source control ou
mecanismo de versionamento definido pelo projeto.

Alterações manuais impossíveis de reproduzir MUST ser evitadas.

## 44. Desenvolvimento Assistido por IA

GPTCodex é ferramenta de implementação, não autoridade arquitetural.

Código ou metadata gerados por IA MUST obedecer integralmente esta Constituição.

IA MUST NOT:

* inventar APIs Salesforce;
* inventar metadata;
* inventar governor limits;
* assumir comportamento não documentado;
* adicionar dependências sem necessidade;
* criar abstrações especulativas;
* alterar arquitetura silenciosamente;
* ignorar segurança para concluir uma task.

Output gerado por IA MUST ser validado por testes, análise estática e
documentação oficial quando aplicável.

## 45. Sandbox Flosum

A sandbox Flosum dedicada é o ambiente principal de desenvolvimento inicial.

Configuração específica da sandbox MUST NOT criar dependência arquitetural
implícita.

Código MUST evitar referências fixas a:

* Org ID;
* Record IDs;
* usernames;
* URLs da sandbox;
* endpoints específicos;
* dados existentes;
* configurações locais não versionadas.

A solução SHOULD permanecer promovível para outros ambientes sem alteração de
código-fonte.

## 46. Deployabilidade

Todo incremento MUST considerar sua promoção entre ambientes.

Mudanças MUST identificar, quando aplicável:

* metadata necessária;
* dependências;
* Permission Sets;
* Custom Metadata;
* Named Credentials;
* External Credentials;
* data migration;
* post-deployment steps;
* rollback;
* backward compatibility.

Deploy manual não documentado MUST NOT ser requisito oculto.

## 47. CI/CD Ready

Mesmo que o projeto inicialmente seja desenvolvido individualmente e diretamente
em sandbox Flosum, a arquitetura MUST permanecer compatível com evolução para
pipeline CI/CD automatizado.

Código MUST permitir execução automatizada de:

* testes;
* validações;
* análise estática;
* deployment validation.

Ausência inicial de pipeline completo MUST NOT justificar práticas incompatíveis
com automação futura.

## 48. Análise Estática e Qualidade

Ferramentas oficiais ou amplamente aceitas para análise Salesforce SHOULD ser
incorporadas conforme maturidade do projeto.

Problemas críticos de:

* segurança;
* SOQL/DML;
* complexidade;
* performance;
* práticas Apex;
* qualidade LWC;

MUST ser corrigidos ou explicitamente justificados antes de release produtivo.

## 49. Dependências

Dependência externa exige benefício concreto e avaliação de:

* necessidade;
* manutenção;
* segurança;
* supply chain;
* licença;
* compatibilidade Salesforce;
* impacto operacional;
* vendor lock-in.

Biblioteca ou framework para problema trivial é proibido.

Funcionalidade nativa adequada SHOULD ser preferida.

## 50. Abstrações Não Devem Ser Especulativas

Interfaces, repositories, selectors, domains, factories, service layers,
strategies, event buses e frameworks internos exigem pelo menos um motivo
concreto:

* boundary arquitetural;
* testabilidade;
* múltiplas implementações reais;
* isolamento externo;
* regra de domínio significativa;
* redução comprovável de complexidade.

"Pode ser útil futuramente" não basta.

## 51. Simplicidade Antes de Distribuição

A solução SHOULD permanecer Salesforce-native enquanto isso atender requisitos
de segurança, escala, integração e operação.

Backend externo, middleware, data lake, warehouse, Redis, filas externas,
microservices ou cloud runtime adicional exigem problema comprovado e decisão
arquitetural explícita.

Complexidade distribuída MUST NOT ser introduzida apenas por possibilidade de
crescimento futuro.

## 52. Salesforce como Plataforma, Não Necessariamente Data Lake

Salesforce MUST NOT ser automaticamente escolhido como armazenamento de todo
evento bruto do SDLC.

Para cada fonte e volume relevante, o design MUST avaliar:

* quantidade de eventos;
* frequência;
* retenção;
* crescimento;
* custo;
* limites;
* necessidade de drill-down;
* agregação;
* reporting;
* compliance.

Se o volume tornar Salesforce inadequado como repositório bruto, uma arquitetura
externa MAY ser proposta via ADR.

## 53. Retenção e Lifecycle de Dados

Dados operacionais e históricos MUST possuir política de lifecycle quando volume
ou sensibilidade justificarem.

O design MUST considerar:

* retenção;
* arquivamento;
* purge;
* reconstrução;
* agregados históricos;
* impacto em métricas.

Crescimento ilimitado sem estratégia é proibido.

## 54. Privacidade e Minimização

Coletar somente dados necessários para métricas, análise operacional e features
aprovadas.

Dados pessoais de desenvolvedores MUST NOT ser coletados apenas porque estão
disponíveis nas ferramentas de DevOps.

A aplicação SHOULD medir sistemas, fluxos e resultados, não criar mecanismo de
vigilância individual.

Uso de métricas para avaliação individual exige requisito, governança e análise
de privacidade explícitos.

## 55. DORA Não Deve Virar Ranking de Pessoas

Métricas DORA MUST NOT ser usadas pelo produto para produzir ranking de
desenvolvedores individuais.

A unidade principal de análise SHOULD ser aplicação, serviço, produto, fluxo ou
outro contexto coletivo aprovado.

Gamificação que incentive manipulação de métricas é proibida sem decisão
explícita.

## 56. Fonte Técnica de Verdade

Prioridade para decisões técnicas:

1. documentação oficial Salesforce;
2. Salesforce Architects / Well-Architected;
3. documentação oficial DORA para definições DORA;
4. padrões oficiais aplicáveis;
5. documentação oficial de produtos integrados;
6. outras fontes somente como apoio.

Documentação oficial atual prevalece sobre conhecimento histórico, posts,
exemplos antigos ou comportamento incidental observado.

MUST NOT inventar:

* APIs;
* limits;
* metadata;
* annotations;
* scopes;
* eventos;
* objetos;
* capabilities;
* comportamento de runtime.

Fato crítico incerto vira `UNVERIFIED_PLATFORM_BEHAVIOR`.

## 57. Comportamento Salesforce Deve Ser Confirmado

Comportamento crítico relacionado a governor limits, Apex, LWC, Flow, security,
sharing, async processing, Platform Events, APIs, Named Credentials, metadata,
deployment e demais recursos Salesforce MUST ser confirmado em documentação
oficial atual quando influenciar arquitetura.

Achado experimental MAY complementar documentação, mas MUST NOT silenciosamente
substituí-la.

## 58. ADRs

Decisão arquitetural de alto impacto exige ADR.

ADRs iniciais esperados conforme surgirem requisitos concretos:

**ADR-001 — DORA Data Model and Event Granularity**

Definir entidades, granularidade dos eventos, identidade, agregações e
rastreabilidade.

**ADR-002 — DevOps Data Ingestion Strategy**

Comparar pull, push, APIs, eventos, batch e mecanismos disponíveis nas fontes.

**ADR-003 — Raw Events versus Aggregated Metrics Storage**

Definir quais dados permanecem no Salesforce, granularidade histórica, retenção
e eventual necessidade de armazenamento externo.

**ADR-004 — DORA Calculation Strategy**

Definir cálculo on-demand, incremental, scheduled/materialized ou combinação.

**ADR-005 — Integration Authentication Strategy**

Quando integrações forem definidas, documentar autenticação e gestão de
credenciais.

Um ADR MUST conter:

* contexto;
* problema;
* decisão;
* alternativas;
* benefícios;
* trade-offs;
* riscos;
* segurança;
* impacto operacional;
* consequências.

SPEC posterior MUST NOT contradizer ADR aprovado silenciosamente.

## 59. Alterações Arquiteturais

Requirement contraditório com decisão aprovada exige `CHANGE_REQUEST` antes da
implementação.

O registro MUST avaliar:

* decisão alterada;
* SPECs;
* ADRs;
* modelo de dados;
* backward compatibility;
* migration;
* segurança;
* testes;
* deployment;
* impacto nas métricas históricas.

## 60. Technical Debt

Dívida técnica inevitável MUST ser registrada como `TECHNICAL_DEBT`.

Registro inclui:

* descrição;
* justificativa;
* impacto;
* risco;
* solução futura;
* condição de resolução quando conhecida.

Dívida crítica de segurança ou integridade de métricas MUST NOT chegar a release
produtivo.

## 61. Controle de Scope Creep

Implementação MUST corresponder à SPEC ativa.

Feature fora do escopo MUST ser registrada como:

`FUTURE_CANDIDATE`

incluindo:

* feature;
* motivação;
* valor potencial;
* SPEC futura sugerida.

A existência de oportunidade futura MUST NOT autorizar implementação antecipada.

## 62. Separação entre Requisito e Tecnologia

`/speckit.specify` MUST focar:

* problema;
* usuário;
* comportamento;
* regras;
* domínio;
* escopo;
* critérios de aceitação.

Detalhes como classes Apex, LWCs, objetos, campos, Flow, Platform Events,
Queueable, Batch, patterns ou estrutura de código pertencem principalmente ao
`/speckit.plan`.

Requirement MUST NOT ser artificialmente moldado pela implementação desejada.

## 63. Pipeline SpecKit

Toda feature MUST seguir:

`/speckit.specify`
→ `/speckit.clarify`
→ `/speckit.checklist`
→ `/speckit.plan`
→ `/speckit.tasks`
→ `/speckit.analyze`
→ `/speckit.implement`

Ideia MUST NOT ir diretamente para código.

GPTCodex MUST receber contexto suficiente da SPEC, plan e tasks aprovadas antes
da implementação.

## 64. Definition of Ready

Implementação exige:

* requisitos claros;
* escopo definido;
* ambiguidades críticas resolvidas;
* critérios de aceitação;
* dependências conhecidas;
* plano técnico;
* tasks;
* modelo de segurança considerado;
* impacto em governor limits considerado;
* ADR aplicável concluído;
* consistência analisada;
* zero blockers arquiteturais conhecidos.

Caso contrário:

`NOT_READY_FOR_IMPLEMENTATION`

## 65. Incrementalidade

Cada SPEC MUST produzir incremento pequeno, verificável e demonstrável.

Grandes entregas SHOULD ser decompostas por capacidade de negócio ou fluxo
vertical.

Antecipar implementação de SPEC futura é proibido.

Preparação para futuro é aceitável somente quando não introduzir complexidade
especulativa relevante.

## 66. Compatibilidade

Nova SPEC MUST preservar contratos aprovados quando possível.

Breaking change exige avaliação explícita de:

* metadata;
* Apex contracts;
* integrações;
* modelo de dados;
* métricas históricas;
* configuração;
* permissões;
* dashboards;
* testes;
* usuários.

Incompatibilidade MUST ser decisão, nunca efeito colateral silencioso.

## 67. Definition of Done

"Deployou na sandbox" não significa Done.

Quando aplicável, Done exige:

* implementação concluída;
* critérios de aceitação atendidos;
* Apex tests;
* testes relevantes de LWC;
* bulk behavior validado;
* segurança validada;
* erros tratados;
* integrações testadas;
* governor limits avaliados;
* qualidade de dados considerada;
* documentação atualizada;
* metadata rastreável;
* análise estática aplicável;
* deployment validável;
* ausência de secrets;
* ausência de logs sensíveis;
* limitações conhecidas registradas.

## 68. Qualidade versus Velocidade

Prioridade:

1. segurança;
2. correção das métricas;
3. integridade dos dados;
4. simplicidade;
5. manutenibilidade;
6. testabilidade;
7. confiabilidade;
8. UX;
9. velocidade.

Velocidade MUST NOT justificar violação desses princípios.

Perfeccionismo MUST NOT justificar overengineering.

## 69. Decisões Baseadas em Evidência

O produto é uma ferramenta de observabilidade e melhoria contínua.

Dashboards MUST diferenciar, quando aplicável:

* fato observado;
* métrica calculada;
* benchmark;
* tendência;
* interpretação;
* recomendação.

Correlação MUST NOT ser apresentada como causalidade sem evidência.

Ausência ou baixa qualidade de dados MUST ser comunicada em vez de produzir
precisão artificial.

## 70. Regra Final da Constituição

O ciclo obrigatório é:

`Requirement`
→ `Clarification`
→ `Validation`
→ `Architecture`
→ `Tasks`
→ `Consistency Analysis`
→ `Implementation`
→ `Automated Validation`
→ `Deployment Validation`
→ `Next Increment`

Nunca:

`Idea → Immediate Code`

O objetivo é construir um Lightning App Salesforce seguro, confiável,
auditável, escalável e manutenível que forneça às equipes de DevOps, SRE e COE
uma visão clara e tecnicamente defensável do ciclo de vida das entregas e de sua
evolução através das métricas DORA.

# Governança

Esta Constituição prevalece sobre decisões locais de implementação.

Toda SPEC, ADR, plan, task e implementação MUST revisar conformidade com esta
Constituição.

Emendas exigem:

* motivo;
* impacto;
* aprovação explícita;
* atualização dos artefatos afetados.

Versionamento SemVer:

* **MAJOR** — remoção ou redefinição incompatível de princípio ou obrigação;
* **MINOR** — nova obrigação material compatível;
* **PATCH** — esclarecimento sem mudança material de obrigação.

Quando esta Constituição e uma sugestão gerada por IA divergirem, esta
Constituição prevalece.

Quando esta Constituição e comportamento oficialmente documentado da Salesforce
divergirem, a implementação MUST ser interrompida e a divergência analisada; a
Constituição MUST NOT ser usada para exigir comportamento tecnicamente inválido.

Quando a documentação DORA alterar materialmente a definição das métricas, o
impacto MUST ser avaliado antes de alterar cálculos existentes.

Até aprovação explícita desta versão, nenhuma nova funcionalidade é considerada
arquiteturalmente autorizada.

Após aprovação, o próximo passo recomendado é:

**SPEC-001 — Application Foundation & DORA Domain Model**

via:

`/speckit.specify`

Essa SPEC SHOULD estabelecer somente a fundação necessária para o primeiro
incremento, incluindo identidade da aplicação, personas, boundaries iniciais do
domínio DORA e requisitos fundamentais, sem antecipar integrações ou arquitetura
de ingestão ainda não decididas.

**Version**: 1.0.0
**Ratified**: PENDING
**Last Amended**: 2026-09-11