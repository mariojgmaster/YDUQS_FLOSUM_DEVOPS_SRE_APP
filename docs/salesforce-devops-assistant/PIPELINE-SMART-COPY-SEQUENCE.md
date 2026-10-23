# Numeração inteligente — Clonar Pipeline (Flosum)

## Objetivo
O campo sugerido passa de `Teste - Cópia` para `Teste - Cópia 01`, `Teste - Cópia 02`, etc. Clonar `Teste - Cópia 02` continua a sequência da raiz `Teste` em vez de produzir `Teste - Cópia 02 - Cópia`.

A melhoria é **exclusivamente da sugestão de nome**, gerada pelo Apex `ClonePipelineController.getPreview`. O usuário continua podendo editar o nome antes de clonar.

## Regras
- Consulta `Flosum__Pipeline__c.Name` em `WITH USER_MODE`, respeitando permissões; evita expor nomes em logs.
- Ignora nomes com o mesmo prefixo que não sejam cópias numeradas.
- Reconhece nomes legados com sufixo apenas ` - Cópia` como número 1.
- Identifica o **maior número utilizado + 1**; não reutiliza lacunas de numeração.
- Ao clonar uma cópia, remove sufixos anteriores e preserva uma única sequência numérica.
- Limita o nome a 80 caracteres, reservando espaço para o sufixo; limita a 9.999 cópias e busca a 2.001 resultados, interrompendo com erro seguro quando necessário.
- O preview deixa de ser cacheável, para calcular com dados atuais da org.
- **Limitação:** se duas pessoas clonarem simultaneamente, as sugestões podem coincidir. Isso não é um contador transacional nem garantia de unicidade; manter/editar nomes manualmente é permitido.

## Testes
- Apex: nome inicial 01, cópias legadas, sequência a partir de cópia, outros prefixos e limite de 80 caracteres.
- Jest: fixture do preview atualizado para `Pipeline Origem - Cópia 01`; a lógica de UI não mudou.
- Homologar: a partir de Pipeline **Teste**, obter `Teste - Cópia 01` se ainda não existir; repetir e esperar `Teste - Cópia 02`. Clonar a cópia 02 deve sugerir 03, e nunca ` - Cópia - Cópia`.

## Deployment seguro

Pacote novo `clone-pipeline-apex`: `manifest/sf-clone-pipeline-apex.xml`, contendo apenas `ClonePipelineController` e `ClonePipelineControllerTest`. O LWC implantado anteriormente já consome a resposta sugerida e não precisa ser reinstalado para ativar o comportamento.

**Nunca usar o pacote `clone-pipeline-lwc` para tentar implantar a alteração Apex.** Após revisão/merge e baseline comprovado, executar `operation=plan` para `clone-pipeline-apex`, usando o baseline do commit correspondente à versão Apex efetivamente publicada na DevSreFeat; só depois, com autorização explícita, executar `deploy` e validar Salesforce Deployment Status.

O M4.1 exige a comparação da org com o baseline e `RunSpecifiedTests ClonePipelineControllerTest`; mantém as travas originais. Nenhum deploy é executado automaticamente.
