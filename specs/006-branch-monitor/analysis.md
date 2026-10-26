# Análise SpecKit — SPEC-006 (25/10/2026)

| Critério | Avaliação | Tratamento |
| --- | --- | --- |
| Constituição: Trusted/Easy/Adaptable | OK planejado | LWC enxuto, read-only, versionamento de source |
| Sharing, CRUD/FLS | Requisito obrigatório | Apex with sharing + USER_MODE, testes por persona |
| Fonte Flosum real | Parcial | Branch, singular Component, Metadata Log confirmados; history com lookup tipado para Component, ainda sem prova de preenchimento/correspondência das versões |
| Semântica de versão | **BLOCK** para Diff textual | T006/T007/T008; não usar Last_Commit |
| Associação componente/deploy | **BLOCK** para timeline de deploy por componente | T009; não unir somente por Branch |
| UX aprovado | Aprovado | Quatro wireframes anotados; sem inventar dados de tela |
| Qualidade/completude | Definido | Unknown e incomplete explícitos; nenhuma contagem parcial como total |
| Segurança das evidências | Definido | consultas limitadas, sanitização em GitHub público, sem payloads |
| Escopo de escrita | Nenhum | nenhum DML, release, deploy ou merge Flosum |
| Integração na navegação | Posterior | M1 após controller/permissions testados |

## Interpretações e conflitos resolvidos
1. O catálogo de Branch Monitor não substitui a classificação legada de ambiente ainda utilizada em outros cálculos.
2. `Flosum__Components__c` não é objeto comprovado; usar o singular verificado.
3. O campo `Last_Commit` não é a versão canônica. Lookup History→Component confirmado no schema, mas revisão e preenchimento permanecem pendentes.
4. Presença em Branch ≠ participação em Deployment.
5. Resultado do Diff inventário não é por si uma diferença no conteúdo da versão.

## Bloqueios para Codex
Não é permitido gerar query Apex contra campos hipotéticos de Component/History. Primeiro produzir `research.md` atualizado com API names/semântica confirmados a partir de evidência protegida. Gate para G1: Branch Directory pode usar campos confirmados; para G2 é obrigatório contrato real de identidade Component. Para G3–G5 exigir completude, versionamento e/ou conteúdo conforme plano.
