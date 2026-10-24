# Salesforce DevOps Assistant — catálogo padrão de operações (contrato v1)

> **Domínio do plugin: Salesforce Metadata API/CLI, não o negócio da aplicação.**
> A instalação padronizada cobre exclusivamente **Retrieve, Compare, Validate (dry-run) e Deploy**. Outras Actions presentes no repositório podem pertencer à aplicação; não integram o kit nem devem ser copiadas para outros projetos.

## Quatro capacidades canônicas

| Nome / intenção | Semântica | Saída exigida | Situação REAL no piloto |
|---|---|---|---|
| `retrieve` | Recuperar metadata de ambiente e pacote cadastrados sem alterar Git ou org | Identidade da operação, inventário, sucesso/falhas, resultado integral via canal permitido | Existe **M3 legado**, limitado a duas ApexClass; ainda NÃO é genérico |
| `compare` | Comparar metadata remoto recuperado com fonte Git (ou dois ambientes previamente cadastrados) sem alterar nenhum lado | Relatório por componente/arquivo de igual/diferente/ausente, detalhes e evidência em artefato | Existe **M3 legado**, limitado a duas classes, com resumo; ainda NÃO é genérico |
| `validate` | Converter o pacote Git autorizado e enviar `sf project deploy start --dry-run` + testes definidos no catálogo | Resultado completo da validação, testes, cobertura, erros, deployment ID/status conforme disponibilidade | **Homologado** em DevSreFeat no M4.2/M5 (`plan`) |
| `deploy` | Pedido explícito de escrita no target cadastrado: primeiro dry-run + testes, depois deploy do mesmo pacote/SHA | Validação, ID/status da implantação real, componentes e testes, resultado confirmado ou incerto | **Homologado via M4.2 manual**; modo ChatOps implementado, ainda requer aceite de deploy real |

Em todos os casos, os inputs operacionais são `repository`, `target`, `package_id` e, quando aplicável, `source_target`/revisão Git. A edição manual do SHA não deve ser exigida quando o workflow puder fixá-lo pelo GitHub. O pacote vem do catálogo e manifesto revisados: não aceitar manifestos arbitrários redigidos na Issue.

Para o piloto, `validate` corresponde ao antigo `plan` **sem escrita**. Conservar o nome legado nos workflows ativos até migração testada.

## Workflows operacionais existentes (não confundir com aplicação)

| Arquivo presente na master | Uso correto |
|---|---|
| `.github/workflows/sf-m5-chatops-plan.yml` | ChatOps **validate/plan** e **deploy** por Issue rigidamente autorizada; não faz retrieve/compare atualmente |
| `.github/workflows/sf-universal-m4.yml` | Alternativa de `workflow_dispatch` manual para `plan`/`deploy` |
| `.github/workflows/sf-devsrefeat-metadata.yml` | M3 de `retrieve`, `compare` e `validate` **somente do antigo escopo Apex fixo**; não copiar como kit universal |
| `.github/workflows/sf-m4-policy-ci.yml` | Testes de política, não operação sobre Salesforce |

Os workflows de **Incident Intake / Incidentes / Pipeline Monitor / Clone Pipeline UI** são **específicos da aplicação**. Não usá-los como operações genéricas, não instalá-los em outros repositórios em nome do Salesforce DevOps Assistant e não interpretar "Incident" como incidente de implantação. Também não escolher os M4 preview/deploy legados para novos projetos.

## Política de criação de workflows — CORRIGIDA

**O assistente PODE instalar workflows padronizados faltantes em qualquer repositório que o usuário tenha autorizado.**

A distinção obrigatória:

1. **Instalação permitida:** selecionar uma versão **já aprovada** do kit canônico de quatro operações; ler o template fonte de revisão Git imutável; verificar conteúdo/hash e compatibilidade, copiar arquivos **sem inventar novos comandos ou triggers** para uma branch do repositório escolhido; registrar configurações específicas de target, ambiente GitHub, catálogo e manifestos; executar validações e abrir PR; mesclar quando CI/aprovações aplicáveis permitirem. Não copiar chaves, secrets nem URLs sensíveis para código.
2. **Operação normal:** quando já instalado, **executar/reutilizar** o workflow aprovado, sem modificar YAML. Solicitações de dry-run, deploy, comparação e diagnóstico não são autorização para projetar Actions inéditas.
3. **Ausência de template aprovado:** NÃO fabricar um novo workflow como improviso. Informar que a operação está pendente no kit, e propor o desenvolvimento/revisão de um template canônico em PR separado.
4. **Conflito ou workflow existente:** não sobrescrever um YAML diferente. Analisar e abrir PR de migração, preservando controles de execução, branch protection e rollback.
5. **Repositórios distintos:** nenhuma configuração do piloto DevSreFeat (organização, URL, usuário, pacotes ou testes específicos) deve ser presumida em novo projeto. A instalação precisa de permissões GitHub e uma ECA/JWT autorizada por **ambiente**; comparação entre duas orgs requer ambas cadastradas, em modo read-only.
6. **Deploy:** autorização explícita e inequívoca para alvo/pacote/revisão, confirmação literal, novo dry-run e testes. Não repetir deploy automaticamente. GitHub Environment e política podem impor aprovações adicionais, que jamais devem ser burladas.

**Status de distribuição:** antes de copiar para terceiros, ainda precisa ser concluída e testada uma implementação **realmente genérica** de `retrieve`/`compare` e de parametrização dos targets. Os arquivos de M3 atuais não constituem templates portáveis. O plugin não deve afirmar que já instalou esse kit completo.

## Retorno integral: contrato e privacidade

- Cada execução deve conservar no runner as respostas Salesforce CLI/Metadata API relevantes em formato estruturado, inclusive lista de componentes, testes, classes/métodos, erros, warnings, cobertura, status e IDs de deployment quando a API os retornar.
- **Repositório privado + política de acesso explicitamente aprovada:** pode ser oferecido **artefato integral protegido**, com retenção curta, acesso `Actions: read`, auditoria, classificação e revisão de segredos/PII. O ChatGPT precisa ter conexão/autorização real para ler o artefato. Não pressupor acesso apenas por ele existir.
- **Repositório público (caso piloto):** somente **artefato sanitizado**; não publicar JSON bruto, stack trace, Apex/metadata recuperado, identificadores privados, segredos ou dados de negócio. Um relatório completo *em ocorrências* não é equivalente a conteúdo bruto integral. Artefatos públicos podem ser obtidos por pessoas com acesso de leitura ao repositório.
- Quando o pedido exigir literalmente todo o payload e não houver canal privado autorizado, informar a restrição **antes** de executar. Não camuflar truncamento nem prometer análise de payload que o conector não consegue recuperar.
- Padrão dos resultados: `operation`, `repo_sha`, `target`, `package_id`, `request_id` quando houver, `status`, `success`, `components`, `tests`, `warnings`, `errors`, `artifact_ref`, `executed_real_deploy`, `raw_result_available`. O schema é um contrato de implementação, não afirmação de campos já existentes.

## Próxima entrega de engenharia (necessária antes da instalação universal)

- Parametrizar `retrieve` por pacote/target do catálogo, sem alterar `force-app`, sem gravar metadata bruto no Git público.
- Parametrizar `compare` (Git↔org e org↔org com dois targets cadastrados), com semântica explícita e comparação não destrutiva, inclusive metadados XML relevantes.
- Consolidar `validate`/`deploy` M4.2/M5 sem regressões na segurança; expor os quatro nomes de operação ao ChatOps sem scripts/Issues ad hoc.
- Publicar **templates imutáveis** mais testes de instalação idempotente, schema do catálogo, CI, documentação ECA/GitHub e rollback. Só marcar `installable: true` após CI e homologação operacional.

Sempre consultar a master e não usar este documento como prova de estado em tempo real de uma execução.
