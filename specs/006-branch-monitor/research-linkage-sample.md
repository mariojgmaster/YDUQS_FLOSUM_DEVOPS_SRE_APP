# G0 — Prova limitada do vínculo History → Component → Branch

**Operação:** leitura somente dos campos Id e dois lookups previamente comprovados por describe na sandbox DevSreFeat. O script usa nomes de campo descobertos por `referenceTo`, exige referência única para evitar relações ambiguamente escolhidas e valida a sintaxe antes de SOQL.

## Evidência pretendida
1. Até 100 Components com Branch preenchida, ordenados do mais recente.
2. Até 100 Component Histories com Component preenchido, ordenados do mais recente.
3. Resolver os componentes referidos nesse conjunto de Histories em até 100 IDs e verificar quantos possuem Branch preenchida.
4. Emitir exclusivamente contagens, flags de truncamento da amostra e estado `positive_sample_only` ou `not_demonstrated`. Nenhum Id, nome, código, texto de campo ou corpo XML irá ao log.

O script não demonstra completude global, versão histórica, identidade FullName ou inclusão efetiva do componente em um deploy. `positive_sample_only` comprova apenas referências **preenchidas e resolvidas na amostra**. `not_demonstrated` não significa que o vínculo inexista fora do recorte.

## Disparo e salvaguardas
Reaproveita o workflow `.github/workflows/sf-devsrefeat-diagnostics.yml`, com GitHub Environment `sf-devsrefeat-read` e JWT ECA já configurados. Evento apenas do proprietário na `master` protegida, primeira tentativa. O workflow não é de escrita e não é um caminho de deploy.

Issue exata:
- Título: `SDOA COMPONENT LINKS DevSreFeat Flosum`
- Corpo:
```text
SDOA-FLOSUM-LINKS/1
operation=linkage-sample
target=DevSreFeat
```

Preflight: PR, CI, revisão de não exposição e merge na `master`. Depois, somente o proprietário abre a Issue para o diagnóstico.

## Próximo passo
Com prova positiva de preenchimento, identificar os campos exatos de identidade/revisão por evidência protegida, confirmar se duas revisões têm conteúdo comparável e só então liberar Diff V1/V2 conforme SPEC-006.
