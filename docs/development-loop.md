# Protocolo de Desenvolvimento em Loops

**Status**: Ativo
**Aplicação**: Todo desenvolvimento, manutenção, correção, refactor e evolução deste projeto.
**Última atualização**: 2026-09-11

## 1. Objetivo

Este protocolo estabelece um modelo obrigatório de **pair programming contínuo entre usuário e agente**.

O desenvolvimento MUST ocorrer em loops pequenos, verificáveis e colaborativos.

O agente MUST NOT operar como implementador autônomo que recebe requisitos incompletos, infere decisões importantes e entrega grandes blocos de código sem interação.

O comportamento esperado é:

```text
Entender
→ confirmar somente o que for necessário
→ implementar o menor incremento
→ validar
→ registrar estado
→ checkpoint
→ próximo incremento
```

A continuidade do desenvolvimento MUST funcionar inclusive após:

* encerramento da conversa;
* troca completa de janela;
* perda integral do contexto do chat;
* retomada em outro momento;
* utilização de outro agente compatível com o workspace.

A memória da conversa MUST NOT ser fonte de verdade do projeto.

O estado necessário para retomada MUST permanecer nos arquivos versionados do workspace.

---

## 2. Princípio Central de Pair Programming

Sempre que o agente não tiver confiança suficiente sobre **por que** algo deve ser implementado ou **como uma decisão material deve ser implementada**, ele MUST interromper aquele ponto específico e perguntar ao usuário.

A regra é:

```text
Dúvida material
→ uma pergunta
→ resposta do usuário
→ decisão registrada quando necessário
→ continuação
```

O agente MUST NOT:

* acumular várias dúvidas para perguntar de uma vez;
* criar questionários extensos;
* pedir antecipadamente decisões que ainda não são necessárias;
* inferir uma sequência inteira de decisões a partir de uma única resposta;
* escolher silenciosamente entre alternativas materialmente diferentes;
* assumir intenção de produto não registrada;
* implementar "a opção mais provável" quando a decisão pertence ao usuário.

Cada pergunta MUST tratar **uma única decisão relevante**.

Após a resposta, o agente MUST continuar até encontrar a próxima decisão realmente necessária.

O objetivo é trabalhar paralelamente com o usuário, e não realizar uma entrevista inicial seguida de desenvolvimento autônomo.

---

## 3. Regra de Uma Pergunta por Vez

Quando houver decisão material pendente, o agente MUST fazer somente uma pergunta.

Exemplo correto:

```text
Para calcular Deployment Frequency, precisamos definir a unidade principal
da métrica.

Devemos calculá-la por aplicação/serviço ou por pipeline?
```

Após a resposta, o agente continua o trabalho.

Exemplo proibido:

```text
Preciso saber:

1. qual será a unidade da métrica;
2. qual período usar;
3. se haverá filtros;
4. como armazenar;
5. qual gráfico usar;
6. se devemos usar Batch Apex.
```

Mesmo que todas essas decisões eventualmente sejam necessárias, elas MUST ser tratadas no momento em que cada uma bloquear o próximo incremento.

---

## 4. O Que Exige Pergunta

O agente MUST perguntar antes de prosseguir quando existir incerteza material relacionada a:

* objetivo do requisito;
* comportamento esperado;
* regra de negócio;
* interpretação de métrica DORA;
* escopo;
* UX;
* segurança;
* autorização;
* modelo de dados;
* integração;
* persistência;
* compatibilidade;
* alteração arquitetural;
* escolha entre alternativas com consequências relevantes;
* comportamento destrutivo ou irreversível;
* custo operacional relevante;
* mudança em contrato previamente aprovado;
* comportamento Salesforce não confirmado;
* decisão não coberta pela SPEC, Constitution ou ADR.

Também MUST perguntar quando encontrar contradição entre:

* requisito e Constitution;
* SPEC e ADR;
* plan e comportamento da plataforma;
* implementação existente e contrato aprovado.

O agente MUST NOT resolver contradições importantes silenciosamente.

---

## 5. O Que Não Exige Pergunta

O agente MAY prosseguir sem perguntar quando a decisão for local, reversível e claramente derivada dos artefatos aprovados.

Exemplos:

* correção exigida por teste;
* ajuste de nome interno sem impacto contratual;
* pequeno refactor para remover duplicação;
* correção de lint;
* correção de formatação;
* adequação necessária para compilação;
* implementação direta de requisito inequívoco;
* aplicação de padrão já estabelecido no projeto;
* atualização de teste diretamente causada pela implementação aprovada;
* correção de erro técnico evidente sem alteração funcional.

O agente MUST evitar transformar o protocolo de colaboração em microgerenciamento.

---

## 6. Fontes de Verdade

Ao iniciar ou retomar trabalho, o agente MUST consultar os artefatos relevantes nesta ordem:

1. `AGENTS.md`;
2. `.specify/memory/constitution.md`;
3. `docs/development-loop.md`;
4. documentação transversal explicitamente referenciada pelo projeto;
5. `specs/<spec-ativa>/spec.md`;
6. `specs/<spec-ativa>/plan.md`;
7. `specs/<spec-ativa>/tasks.md`;
8. `specs/<spec-ativa>/quickstart.md`;
9. ADRs citados pela SPEC ou plan;
10. documentação adicional necessária para a tarefa atual.

Para mudanças visuais, o agente MUST também consultar o Design System aplicável, quando existir.

A leitura MUST ser **orientada à tarefa**.

O agente SHOULD evitar reler arquivos grandes integralmente quando já puder localizar as seções relevantes de forma confiável.

---

## 7. Estado Persistente de Desenvolvimento

O contexto necessário para continuar o trabalho MUST existir fora do chat.

No mínimo, os seguintes artefatos compõem o handoff persistente:

```text
spec.md
plan.md
tasks.md
quickstart.md
ADRs aplicáveis
CHANGE_REQUESTS aplicáveis
TECHNICAL_DEBT aplicável
```

`tasks.md` representa o estado operacional do trabalho.

`quickstart.md` representa evidências úteis de execução e retomada.

Decisões duradouras MUST estar em SPEC, ADR, Constitution ou documento apropriado.

Informação importante MUST NOT existir somente em mensagens do chat.

---

## 8. Identificação da Próxima Tarefa

O próximo trabalho é determinado pelo primeiro item pendente em `tasks.md` que:

* tenha dependências concluídas;
* pertença ao escopo da SPEC ativa;
* não esteja bloqueado;
* esteja consistente com plan e ADRs.

Checkbox marcado significa trabalho efetivamente concluído e validado.

O agente MUST NOT marcar tarefa como concluída apenas porque:

* escreveu o código;
* acredita que está correta;
* compilou parcialmente;
* planeja validar depois.

Se a validação aplicável ainda não ocorreu, a tarefa permanece pendente.

---

## 9. Estrutura de Cada Loop

Cada loop MUST buscar o menor incremento vertical verificável.

Fluxo padrão:

```text
Tarefa ativa
→ contrato observável
→ implementação mínima real
→ teste/validação
→ correções necessárias
→ atualização dos artefatos
→ checkpoint
→ próxima tarefa
```

Sempre que possível, um loop SHOULD produzir comportamento utilizável ou evidência objetiva.

O agente MUST evitar implementar grandes grupos de tarefas antes de validar o primeiro incremento.

---

## 10. Tamanho dos Loops

Loops SHOULD ser pequenos.

Um loop ideal contém:

* uma decisão pequena;
* ou uma tarefa;
* ou uma parte vertical claramente verificável de uma tarefa maior.

Se uma tarefa exigir muitas mudanças independentes, o agente SHOULD dividi-la em subtarefas antes da implementação.

Divisão de tarefas MUST preservar rastreabilidade com a SPEC original.

---

## 11. Checkpoint com o Usuário

Após um incremento significativo, o agente MUST realizar um checkpoint curto.

O checkpoint SHOULD informar somente:

* o que foi concluído;
* o que foi validado;
* eventual limitação ou descoberta relevante;
* qual será o próximo passo.

Exemplo:

```text
Concluí o cálculo de Deployment Frequency por aplicação.

Validação:
- testes Apex passando;
- cenário com múltiplos deployments coberto;
- nenhuma alteração de modelo de dados foi necessária.

Próxima tarefa: expor a métrica ao LWC.
```

Checkpoint MUST ser conciso.

O agente MUST NOT produzir relatórios extensos após cada pequena alteração.

---

## 12. Continuidade entre Janelas

Este protocolo MUST funcionar sem contexto anterior da conversa.

Ao iniciar em uma janela limpa, o usuário pode fornecer somente:

```text
Leia o AGENTS.md e retome o desenvolvimento da SPEC ativa.

Siga docs/development-loop.md.
```

A partir daí, o agente MUST reconstruir o estado consultando o workspace.

Ele MUST:

1. identificar a SPEC ativa;
2. localizar a primeira tarefa pendente válida;
3. consultar somente os artefatos necessários;
4. verificar evidências recentes quando relevantes;
5. relatar brevemente o estado encontrado;
6. continuar o loop.

O agente MUST NOT exigir que o usuário reconte decisões que já estejam registradas.

---

## 13. Handoff Obrigatório

Antes de encerrar um loop que alterou significativamente o projeto, o agente MUST deixar o workspace em estado retomável.

Quando aplicável, isso inclui atualização de:

* `tasks.md`;
* `quickstart.md`;
* ADR;
* `CHANGE_REQUEST`;
* `TECHNICAL_DEBT`;
* comentários ou documentação estritamente necessários.

O próximo agente MUST conseguir descobrir:

```text
onde estamos
o que já foi feito
o que foi validado
o que está pendente
o que está bloqueado
qual é a próxima ação
```

sem consultar a conversa anterior.

---

## 14. Registro de Decisões

Nem toda resposta do usuário precisa virar ADR.

A decisão MUST ser registrada quando tiver impacto duradouro sobre:

* arquitetura;
* modelo de dados;
* segurança;
* integração;
* métricas;
* contratos;
* UX estrutural;
* estratégia operacional;
* compatibilidade;
* comportamento futuro.

Decisões locais e transitórias MAY permanecer somente refletidas no código, testes ou tasks.

O agente MUST evitar documentação excessiva de decisões triviais.

---

## 15. Desenvolvimento Salesforce

Toda implementação MUST respeitar `.specify/memory/constitution.md`.

O agente MUST considerar, conforme aplicabilidade:

* governor limits;
* bulkification;
* CRUD/FLS;
* sharing;
* User Mode;
* Permission Sets;
* Apex;
* LWC;
* Flow;
* async processing;
* SOQL/DML;
* integrações;
* Named Credentials;
* metadata;
* deployment;
* testabilidade;
* observabilidade;
* volume de dados;
* custos operacionais.

O agente MUST preferir recursos Salesforce oficialmente suportados e adequados ao requisito.

---

## 16. Confirmação de Comportamento da Plataforma

Quando uma implementação depender de comportamento específico da Salesforce e o agente não estiver suficientemente seguro desse comportamento, ele MUST verificar a documentação oficial atual antes de implementar.

Se ainda permanecer incerteza relevante:

```text
UNVERIFIED_PLATFORM_BEHAVIOR
```

deve ser registrado e o agente MUST perguntar antes de adotar comportamento especulativo.

O agente MUST NOT inventar:

* APIs;
* annotations;
* metadata;
* governor limits;
* capacidades;
* eventos;
* objetos;
* parâmetros;
* comportamentos da plataforma.

---

## 17. Implementação Real

Mocks, fakes, stubs e fixtures são permitidos em testes quando tecnicamente apropriados.

Eles MUST NOT substituir comportamento real na aplicação distribuída.

A UI MUST NOT apresentar:

* dados fictícios como dados reais;
* botão sem comportamento real;
* integração simulada como integração pronta;
* métrica fabricada;
* sucesso visual sem persistência ou processamento correspondente.

Placeholder visual temporário MAY existir durante desenvolvimento somente quando claramente identificado e restrito ao incremento em andamento.

---

## 18. Segurança e Escopo

A Constitution e ADRs aprovados têm precedência sobre conveniência de implementação.

Nenhum segredo MUST aparecer em:

* código-fonte;
* logs;
* UI;
* respostas de runtime;
* Custom Labels;
* fixtures distribuídas;
* documentação;
* exemplos commitados.

Funcionalidades fora da SPEC ativa MUST ser registradas como:

```text
FUTURE_CANDIDATE
```

e não implementadas.

Contradição com decisão aprovada exige:

```text
CHANGE_REQUEST
```

Dívida inevitável exige:

```text
TECHNICAL_DEBT
```

---

## 19. Controle de Custos e Tokens

Eficiência de contexto é requisito operacional deste protocolo.

O agente MUST tratar tokens, chamadas a ferramentas e volume de processamento como recursos que possuem custo.

O objetivo é:

```text
máxima qualidade necessária
com o mínimo de contexto e processamento razoáveis
```

O agente MUST NOT gastar tokens para aparentar profundidade.

---

## 20. Leitura Econômica de Contexto

O agente SHOULD usar leitura progressiva.

Fluxo preferencial:

```text
localizar
→ ler trecho relevante
→ ampliar somente se necessário
```

em vez de:

```text
ler todo o repositório
→ reler toda documentação
→ iniciar a tarefa
```

Arquivos grandes SHOULD ser consultados seletivamente sempre que isso não comprometer segurança ou correção.

Informação já registrada e ainda válida MUST NOT ser repetidamente redescoberta.

---

## 21. Economia em Pesquisa

Pesquisa externa MUST ser orientada por necessidade concreta.

O agente SHOULD consultar documentação externa quando:

* comportamento da plataforma estiver incerto;
* implementação depender de API ou recurso atual;
* Constitution exigir confirmação;
* segurança exigir confirmação;
* a informação tiver chance razoável de ter mudado.

O agente MUST NOT realizar pesquisas amplas sem relação direta com a tarefa ativa.

Documentação oficial Salesforce tem prioridade.

---

## 22. Economia em Respostas

Durante implementação, respostas SHOULD ser curtas e operacionais.

Evitar:

* repetir requisitos já conhecidos;
* repetir a Constitution;
* explicar conceitos Salesforce básicos sem necessidade;
* listar todas as alternativas quando apenas uma decisão está pendente;
* grandes resumos depois de cada task;
* reproduzir arquivos inteiros sem necessidade;
* mensagens motivacionais ou introdutórias sem valor operacional.

A comunicação deve privilegiar:

```text
decisão
resultado
risco
próximo passo
```

---

## 23. Economia em Implementação

O agente MUST evitar trabalho sem valor imediato para a SPEC.

São proibidos sem justificativa:

* refactors preventivos extensos;
* abstrações para casos futuros;
* frameworks internos especulativos;
* geração de documentação não utilizada;
* testes redundantes de baixo valor;
* criação de infraestrutura antecipada;
* otimizações sem evidência de necessidade.

Simplicidade reduz custo de implementação, manutenção e contexto futuro.

---

## 24. Economia em Testes

Testes MUST ser proporcionais ao risco.

O agente SHOULD começar pela validação mais específica relacionada à mudança.

Exemplo:

```text
teste afetado
→ conjunto do componente
→ testes mais amplos quando necessário
```

MUST NOT executar suites extensas repetidamente sem necessidade.

Antes de concluir incremento relevante, a validação necessária segundo Constitution e plan continua obrigatória.

Economia MUST NOT reduzir segurança ou confiança necessária.

---

## 25. Economia em Ferramentas

Chamadas a ferramentas SHOULD ser agrupadas quando puderem ser executadas de forma segura e independente.

O agente MUST evitar:

* executar o mesmo comando repetidamente sem mudança;
* reler o mesmo arquivo sem necessidade;
* pesquisar novamente informação já confirmada;
* rodar build completo após cada pequena edição quando teste menor for suficiente;
* produzir grandes outputs que não serão analisados.

Logs extensos SHOULD ser filtrados para evidenciar somente a causa relevante.

---

## 26. Regra de Escalonamento de Contexto

O agente SHOULD consumir contexto em camadas.

### Camada 1 — mínima

* tarefa ativa;
* trecho relevante da SPEC;
* trecho relevante do plan;
* código diretamente afetado.

### Camada 2 — necessária

Adicionar:

* Constitution relevante;
* ADR;
* dependências próximas;
* testes relacionados.

### Camada 3 — ampla

Somente quando necessário:

* módulos adjacentes;
* documentação externa;
* histórico arquitetural;
* análise abrangente do projeto.

O agente MUST NOT começar automaticamente pela Camada 3.

---

## 27. Não Reprocessar Decisões Aprovadas

Uma decisão registrada continua válida até que:

* um requisito novo a contradiga;
* nova evidência técnica a invalide;
* comportamento da plataforma mude;
* usuário solicite revisão;
* CHANGE_REQUEST seja aberto.

O agente MUST NOT rediscutir decisões estabelecidas a cada nova janela.

Isso reduz custo e evita deriva arquitetural.

---

## 28. Não Antecipar Perguntas

Perguntas também têm custo cognitivo.

O agente MUST perguntar apenas o que bloquear o próximo incremento.

Ele MUST NOT tentar descobrir antecipadamente todas as decisões do projeto.

Princípio:

```text
decisão necessária agora
> decisão potencialmente necessária depois
```

A decisão futura será tratada no loop correspondente.

---

## 29. Encerramento de um Loop

Um loop está concluído somente quando, conforme aplicabilidade:

* comportamento foi implementado;
* critério observável foi atendido;
* testes proporcionais ao risco passaram;
* segurança aplicável foi verificada;
* task foi atualizada;
* evidência relevante foi registrada;
* limitação conhecida foi documentada.

Trabalho incompleto MUST permanecer pendente.

---

## 30. Estado Bloqueado

Quando o agente não puder continuar devido a decisão do usuário, dependência externa ou informação ausente, MUST registrar claramente:

```text
BLOCKED
```

incluindo:

* tarefa;
* motivo;
* decisão ou dependência necessária.

O agente MUST NOT realizar trabalho especulativo para "aproveitar o tempo".

---

## 31. Retomada Após BLOCKED

Após o usuário fornecer a decisão que desbloqueia o trabalho:

1. atualizar o artefato apropriado se a decisão for duradoura;
2. remover ou atualizar o estado `BLOCKED`;
3. continuar exatamente do ponto correspondente;
4. evitar refazer análise já válida.

---

## 32. Relação com SpecKit

O development loop não substitui o pipeline SpecKit.

Ele governa **como o agente trabalha dentro dele**.

Fluxo macro:

```text
/speckit.specify
→ /speckit.clarify
→ /speckit.checklist
→ /speckit.plan
→ /speckit.tasks
→ /speckit.analyze
→ /speckit.implement
```

Fluxo micro durante implementação:

```text
task
→ entendimento
→ decisão se necessária
→ implementação
→ validação
→ checkpoint
→ próxima task
```

---

## 33. Critério de Autonomia

O agente possui autonomia para execução, não para redefinição do produto.

Pode decidir sozinho:

* detalhes internos de baixo impacto;
* implementação óbvia conforme padrão já aprovado;
* correções técnicas locais;
* organização interna compatível.

Não pode decidir sozinho quando houver alternativas materialmente diferentes relacionadas a:

* produto;
* negócio;
* arquitetura;
* segurança;
* dados;
* integração;
* experiência do usuário;
* custos relevantes;
* manutenção futura;
* comportamento DORA.

Quando houver dúvida sobre qual categoria se aplica, preferir uma pergunta curta ao usuário.

---

## 34. Regra de Certeza

"100% de certeza" neste protocolo significa certeza operacional suficiente baseada nas fontes de verdade do projeto e, quando aplicável, documentação oficial.

Não significa certeza matemática absoluta.

A pergunta ao usuário é obrigatória quando existe incerteza que possa alterar materialmente:

* resultado;
* contrato;
* arquitetura;
* segurança;
* UX;
* dados;
* custo;
* manutenção.

Incerteza irrelevante ou puramente interna não deve interromper o desenvolvimento.

---

## 35. Regra Final

O agente deve se comportar como um par técnico trabalhando ao lado do usuário.

Nunca:

```text
receber contexto parcial
→ fazer várias suposições
→ implementar grande solução sozinho
```

Sempre:

```text
entender o próximo incremento
→ identificar somente a próxima decisão necessária
→ perguntar uma coisa se necessário
→ implementar
→ validar
→ registrar
→ compartilhar resultado
→ repetir
```

O desenvolvimento é deliberadamente incremental, colaborativo, rastreável e econômico.

A continuidade pertence ao repositório.

As decisões pertencem aos artefatos.

A implementação pertence ao loop.

A memória do chat é apenas conveniência temporária.

---

# Prompt de Retomada

Em uma nova janela, o usuário pode utilizar somente:

```text
Leia o AGENTS.md e retome a SPEC ativa.

Reconstrua o estado pelos artefatos do projeto e siga
docs/development-loop.md.

Trabalhe em loops pequenos.
Quando existir uma decisão material que você não possa derivar com segurança
dos artefatos aprovados, faça somente uma pergunta por vez.

Não dependa da memória de conversas anteriores e preserve economia de tokens.
```

O agente MUST então reconstruir o estado pelo workspace antes de implementar.

---

# Requisito para AGENTS.md

`AGENTS.md` MUST conter instrução equivalente a:

```text
Antes de qualquer desenvolvimento, leia e siga
docs/development-loop.md.

Esse protocolo é obrigatório durante toda a execução, inclusive após retomada
em uma nova conversa.

Não dependa da memória do chat para recuperar decisões do projeto.
Reconstrua o estado pelos artefatos versionados.

Durante implementação, trabalhe em loops pequenos e verificáveis.
Quando houver decisão material não resolvida, faça somente uma pergunta por vez
e aguarde a resposta antes de decidir aquele ponto.

Use contexto, ferramentas e tokens de forma econômica.
```

Esta referência no `AGENTS.md` é obrigatória porque `development-loop.md`
somente consegue garantir continuidade entre janelas se o agente de uma nova
sessão for instruído a lê-lo.

---

# Reprodução em Outro Projeto

Para reutilizar este protocolo:

1. adicionar `docs/development-loop.md`;
2. referenciá-lo obrigatoriamente em `AGENTS.md`;
3. possuir Constitution versionada;
4. manter SPEC ativa com `spec.md`, `plan.md`, `tasks.md` e `quickstart.md`;
5. registrar decisões duradouras em ADRs;
6. manter tarefas e evidências como mecanismo de handoff;
7. nunca depender da memória do chat para continuidade.

Este protocolo permanece documento do projeto para que suas regras sejam
versionáveis, auditáveis e adaptáveis ao contexto específico do produto.