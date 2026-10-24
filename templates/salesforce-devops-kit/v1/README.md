# Salesforce DevOps Universal Kit v1 — Templates fixos

O kit possui **um workflow operacional para quatro operações** e **um CI de política**. Os workflows de Incidentes, Pipeline Monitor e Clonar Pipeline pertencem à aplicação piloto e **não fazem parte deste kit**.

## Operações

- `retrieve` — Metadata API ZIP de pacote revisado em sandbox, sem alterar a org ou os arquivos do projeto.
- `compare` — mesmo ZIP remoto versus a conversão do manifesto Git revisado, por componente/arquivo. Diferença não é erro de implantação.
- `validate` — o usuário solicita Validate; no protocolo ChatOps v1 essa operação permanece `plan` (dry-run nativo Salesforce + testes).
- `deploy` — intenção explícita e irrepetível, confirmação literal e SHA imutável, sempre após dry-run e testes.

Issues aceitas pelo workflow versionado:

- `SDOA RETRIEVE <target> <package_id>` com corpo `SDOA-CHATOPS/3`, `operation=retrieve`, `target=<target>`, `package_id=<package_id>`.
- `SDOA COMPARE <target> <package_id>` com corpo análogo `operation=compare`.
- `SDOA PLAN <target> <package_id>` com protocolo `SDOA-CHATOPS/1` (Validate).
- `SDOA DEPLOY <target> <package_id>` com protocolo `SDOA-CHATOPS/2`, SHA 40 caracteres e confirmação literal.

Corpos: campos `key=value` exatos, em linhas, sem Markdown, com newline final; consulte os parsers de contrato para formato completo.

## Instalação em outro repositório — sem criação inventada

O instalador `scripts/ci/sf-kit-install.py` lê exclusivamente `templates/salesforce-devops-kit/v1/manifest.json`, valida **Git blob SHA-1** de todos os arquivos aprovados e inspeciona o destino sem escrever por padrão:

```bash
python3 scripts/ci/sf-kit-install.py --target-root /caminho/checkout/destino
```

O destino deve ter `sfdx-project.json` e `config/salesforce-devops/catalog.json` configurados para SEUS próprios alvos e pacotes. A cópia somente é permitida quando o manifest declarar `status=approved`, após testes e homologação do kit:

```bash
python3 scripts/ci/sf-kit-install.py --target-root /caminho/checkout/destino --apply
```

O instalador não sobrescreve arquivos existentes divergentes; se um deles conflitar, bloqueia o lote antes de escrever. Em outras instalações via GitHub connector, o plugin pode copiar os mesmos templates de um SHA de referência fixado para uma branch e abrir PR, conferindo hashes Git antes do merge. Nunca requer credenciais Salesforce no chat.

**Compatibilidade v1:** `master` como branch padrão, metadata source Salesforce DX com API 67.0, ApexClass e LightningComponentBundle explicitamente declarados, sandbox `*.sandbox.my.salesforce.com`, ECA/JWT no GitHub Environment do próprio repositório. Não assume autorização para produção e não compara duas orgs diretamente (Compare v1 é Git↔org).

## Retorno integral

- Repositório público: relatório estruturado *sanitizado*, nomes apenas de componentes revisados; nenhum ZIP bruto de metadata, erro ou stack trace no artifact.
- Repositório privado: administrador habilita variável de repositório `SDOA_EXPORT_RAW=true`; o workflow só publica ZIP/JSON bruto quando `github.event.repository.private == true`. Retenção 1 dia, acessível a quem tiver permissões GitHub Actions apropriadas. Evite habilitar sem revisar membros/leitores e conteúdo confidencial.
- Retorno integral significa **payload da CLI disponível no canal privado**; não pressupõe que o plugin o leu até efetivamente baixá-lo e abri-lo.

## Homologação

CI: sintaxe Bash, compilação Python, contrato das quatro operações, snapshots de comparação, injeções, hashes e instalação idempotente. Após merge, testar no piloto apenas Retrieve e Compare, sem real deploy. Só marcar o manifest aprovado e instalar em terceiros depois do teste de ponta a ponta.
