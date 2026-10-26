# Descoberta técnica — Branch Monitor / Componentes Flosum

**Escopo:** somente leitura na DevSreFeat, sem deploy de Flosum. Fontes de verificação: [run 40225283951](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40225283951) (classificação anterior) e [run 40251845636](https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40251845636) (reconhecimento do lookup singular).

## Evidências confirmadas
- `Flosum__Branch__c` e `Flosum__Metadata_Log__c`: contrato de Branch/logs e timestamps documentado em `docs/devops-sre-analytics/flosum-source-contract.md`.
- `Flosum__Component__c` **singular**: Describe OK, 37 campos, um lookup tipado para Branch, sinais nominais de commit/versão; não foi identificado body por tipos base64/textarea/encryptedstring.
- `Flosum__Component_History__c`: Describe OK, 32 campos; **um lookup tipado confirmado para \`Flosum__Component__c\` (singular)**, nenhum lookup tipado direto para Branch ou Metadata Log; há indícios em nomes de campos para branch/componente/commit/versão, além de um candidato de conteúdo.
- `Flosum__Components__c` **plural**: Describe indisponível; não usar sem nova prova.

A introspecção usa [`scripts/ci/sf-flosum-component-research.py`](../../scripts/ci/sf-flosum-component-research.py) no workflow existente `sf-devsrefeat-diagnostics.yml`, com Issue owner-only exata `SDOA COMPONENTS DevSreFeat Flosum`. O relatório de roles imprime somente nomes de papéis, grupos de tipos e contagens, **não** nomes de campos de negócio, IDs, valores, payload nem credenciais.

## Próxima inspeção
1. Categorizar os campos relacionados à identidade/versão/branch e seus tipos; isto só fornece candidatos.
2. Validar chaves de junção reais e cardinalidade do histórico **com amostragem limitada**, antes de montar qualquer SOQL de negócio.
3. Confirmar se duas versões têm conteúdo passível de comparação e vínculo à revisão (não basta um Long Text).
4. Identificar como uma alteração de componente chega ao Metadata Log de Validate/Deployment; simples Branch compartilhada não prova inclusão.
5. Comprovar completude de snapshots e renames/deletes.

## Branch Describer
Entrada por tipo + FullName + namespace; retorno por Branch com proveniência verificável, timeline de versões e execuções somente quando o vínculo for validado. A proposta completa foi consolidada em [SPEC-006](../../specs/006-branch-monitor/spec.md).

## Veredito atual
**BranchPresence: parcialmente viável**, pois há lookup tipado Component→Branch. **History→Component: lookup confirmado no schema, preenchimento e semântica ainda não verificados**. **Diff de conteúdo: não verificado**. **Deploy histórico por componente: não verificado**. Não apresentar hipótese como dado real no app.
