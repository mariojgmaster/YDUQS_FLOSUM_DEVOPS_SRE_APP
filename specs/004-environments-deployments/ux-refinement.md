# Revisão de clareza e Design System — SPEC-004

## Problema e resultado esperado

O cadastro anterior apresentava termos de integridade temporal como tarefa principal e mantinha o formulário permanentemente aberto. A consulta de deployments expunha referências técnicas antes de explicar a ação disponível. O usuário pediu finalidade clara para as abas e aderência ao Design System aprovado.

| Aba         | Pergunta respondida                                            | Ação principal                                                                  |
| ----------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Deployments | O que foi entregue, para qual organização, com qual resultado? | Filtrar e abrir o registro de origem ou a Branch no Flosum.                     |
| Ambientes   | Qual é o uso de cada organização e desde quando?               | Consultar classificações atuais; gerente cadastra ou encerra uma classificação. |
| Pipeline    | Qual é a visão operacional anterior de pipelines?              | Usar o componente original, preservado.                                         |

## Interações

- Ambientes abre em **Classificações atuais**. Visões futuras, histórico encerrado e todas são explícitas; não se infere classificação por nome. As contagens se referem à consulta acessível.
- O formulário aparece em **Classificar organização** ou na ação **Atualizar classificação**. A data inicial obrigatória não recebe “agora” automaticamente: isso deixaria entregas anteriores sem classificação.
- “Esta classificação vale desde” substitui o jargão na tarefa. A opção de término revela “Vale até”; sem término o uso continua válido. O formulário usa o fuso do usuário e a lista explicita UTC.
- O exemplo UAT até junho / PROD a partir de julho explica a preservação histórica. O intervalo continua [início,fim), sem alterar Apex ou a integridade dos dados.
- Organização, uso e início permanecem imutáveis. Registros encerrados não podem ser reabertos ou ampliados. Não há exclusão, carga inicial ou atribuição de permissões nesta alteração.
- Após salvar, o formulário fecha e a consulta exibe todas as classificações da organização salva, para não ocultar registros futuros ou históricos recém-criados. A consulta de deployments é atualizada pelo evento existente.
- Deployments apresenta período, organização, ambiente e resultado como filtros principais; busca de organizações e ID de Branch ficam em seção recolhível. Alterar filtros invalida cursor e solicita **Aplicar filtros**; buscar opções de organizações preserva os resultados existentes.
- Ausência de classificação e conflito aparecem como **Não identificado** e **Classificação conflitante**, sem alterar os valores internos ou supor PROD. Orientação leva o usuário à aba Ambientes.
- Nenhum KPI ou total global é apresentado. Fonte, fallback do período e limitações ficam em **Sobre os dados e o período consultado**.

## Aplicação do Design System

Referência: `docs/design-system.md`, especialmente tokens, Page Header, List View, formulários, progressive disclosure, Empty State, permissões e estados assíncronos. A linguagem deste app é Lightning/SLDS; referências visuais de outros produtos não se aplicam.

`devSreDeliveryStyles` concentra tokens semânticos, defaults de fundação e a ponte para o tema Lightning. As telas usam os mesmos cabeçalhos, superfícies, toolbar, espaçamentos, tabela, formulário e mensagens. Componentes Lightning mantêm seus estilos e interações públicas; não há override de seu DOM interno. Grid responsivo, overflow horizontal de tabelas, labels, foco ao abrir/fechar formulário e status textuais acompanham a composição.

Não há afirmação de conformidade completa do Design System a partir de Jest. Contraste no tema da org, teclado, 200% de zoom, mobile e aparência dos Base Components dependem de homologação visual real.

## Validação e publicação

Alteração limitada à UI, estilos compartilhados, manifesto, configuração Jest para resolver módulos CSS e cobertura de CI. Sem mudanças em Apex, objeto, permissões ou dados reais. O pacote passa a incluir o módulo de estilos, totalizando 21 componentes Salesforce se validado integralmente.

Testes cobrem navegação entre classificações atuais/futuras/encerradas e limite temporal inclusivo/exclusivo, início explícito, cancelamento sem escrita, término opcional, identidade imutável, erro de sobreposição, recuperação de consultas, filtros/cursor e resposta obsoleta.

A revisão ainda precisa de implantação como **atualização** e homologação na DevSreFeat. O workflow de primeira instalação não é reutilizável para esse fim: ele recusa componentes já existentes. Nenhuma nova implantação foi disparada por esta revisão.
