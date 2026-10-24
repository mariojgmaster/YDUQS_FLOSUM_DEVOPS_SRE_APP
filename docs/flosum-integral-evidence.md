# Coleta integral de evidências Flosum — somente leitura

Autorização: responsável autorizou criar workflows e reunir as informações necessárias à próxima fase em 24/10/2026. Escopo Salesforce: somente sandbox DevSreFeat, GitHub Environment existente `sf-devsrefeat-read`, ECA/JWT existentes. Não inclui acesso à organização PROD nem escrita Salesforce.

## Entrada e execução

Workflow `Salesforce Flosum - Integral Read Only Evidence`, manual em master ou por Issue do proprietário com título e corpo exatos:

Título: `SDOA COLLECT DevSreFeat Flosum evidence`

```text
SDOA-FLOSUM-EVIDENCE/1
operation=collect
target=DevSreFeat
```

O evento, autor, remetente, primeira tentativa, master protegida, SHA e catálogo são conferidos antes das credenciais. Código é revisado por PR e testes. Não executar código vindo do corpo da Issue. A classificação como coleta não autoriza deploy.

## Dados coletados

- Describe integral de Branch e Metadata Log: tipos, referências, campos calculados, fórmulas disponíveis, picklists, relacionamentos filhos e demais propriedades retornadas pela API.
- Tooling FieldDefinition de ambos os objetos, com definição explícita de falha/indisponibilidade se ocorrer.
- Branch previamente selecionada pelo responsável: localização por SHA-256 do ID, sem versionar o ID. A consulta de índice lê somente IDs, até 10.001; mais de 10.000 bloqueia a coleta e exige filtro mais seletivo.
- Todos os logs retornados para essa Branch por até quatro relacionamentos comprovados, em consulta única com OR, até 1.001 linhas. Mais de 1.000 bloqueia, sem truncamento silencioso. Valores completos dos campos identificados no print, todos os campos temporais e referências pertinentes; não inclui conteúdo indiscriminado de logs/componentes ou credenciais.
- Describe da organização referenciada e apenas identidade/nome dos registros relacionados. Nunca ler os campos de autenticação, senha ou token desses registros.

“Integral” significa valores completos e schema completo dentro desse escopo explicitamente revisado. Não significa extração indiscriminada de todos os dados da org. Nenhuma métrica é certificada por esse workflow; início/fim do deployment continuam sujeitos à interpretação das evidências.

## Transporte do resultado

O JSON completo é criptografado em memória com OpenSSL CMS, AES-256-GCM e certificado RSA. Somente o arquivo `.cms` é publicado como artifact, por um dia. A chave privada de análise permanece fora do GitHub/runner/repositório e nunca é impressa. Logs contêm apenas status operacional, sem nomes/valores de registros, fórmulas ou IDs privados.

Baixar o artifact real, validar/decriptar localmente e ler o JSON antes de afirmar análise integral. O arquivo público criptografado não substitui a leitura efetiva do conteúdo. Se não houver download/decriptação, registrar o bloqueio exato. Certificado expira em 14 dias e é validado antes de coletar; nova coleta após expiração requer novo par de análise.

Falhas não viram dados vazios válidos. Ausência de schema/campo/destino ou limite excedido é reportada explicitamente. Falta de acesso Tooling é uma lacuna no JSON, enquanto Describe/consultas fundamentais são obrigatórios.

## Validação

Testes: contexto/Issue falsificados, limites, seletor, proibição de comandos de escrita, preservação integral do JSON, ausência de saída pública de dados, criptografia/decriptografia real e configuração de artifact.

Fontes técnicas: https://developer.salesforce.com/docs/platform/api-rest/guide/resources-sobject-describe.html ; https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/api_tooling.pdf .
