# SPEC-004 — entrega validada / aguardando implantação

## Comportamento
A aba original Pipeline Monitor passa a hospedar Deployments, Ambientes e Visão original. Nenhuma nova aba global é criada, nenhum bundle original é modificado. Leitura paginada dos Metadata Logs do tipo Deployment; filtros UTC/organização/Branch/ambiente/resultado, origem acessível, datas próprias de início e conclusão, UNKNOWN/AMBIGUOUS e qualidade explícitos. Cadastro de classificação temporal com justificativa, histórico, perfis leitor/gerente e integridade transacional.

## Evidência real
- CI da implementação #40141155237 e M4 #40141155200 PASS; correções com CI próprio aprovado.
- Dry-run aprovado: https://github.com/mariojgmaster/YDUQS_FLOSUM_DEVOPS_SRE_APP/actions/runs/40141697664
- SHA validado: 2bb23fc78b7fbcac490847de056af49da220ee67; job 121014600466; artifact 12578389219.
- Artifact ZIP SHA-256 f9f7e8c75d765f5815de18a61d37bcd42d8e720ddf76f5fb1ec29c8ea1ffb545, conferido. JSON descriptografado e lido integralmente.
- 20/20 componentes aceitos, 9 testes Apex concluídos, zero erros/advertências de cobertura.
- Cobertura: controller de deployments 189/205 (92,2%); controller de ambientes 108/122 (88,5%); guard 65/69 (94,2%); trigger 4/4 (100%).
- 9 Jest, ESLint e testes de política locais/CI aprovados. Homologação visual/funcional após implantação ainda pendente.

## Implantação preparada, não executada
Workflow específico de primeira instalação, separado do kit universal, aceita somente Issue exata do proprietário com SHA atual da master e confirmação textual DEPLOY DevSreFeat SPEC004. Antes de escrever, confere proteção, destino, pacote, drift da tab, ausência de componentes inesperadamente já instalados e novo dry-run com os mesmos 9 testes. Deploy usa o mesmo diretório MDAPI validado; resultado integral criptografado e estado não confirmado exige reconciliação antes de nova escrita. Nenhuma Issue DEPLOY foi criada nesta solicitação.

O pacote de metadata permanece idêntico ao dry-run acima; a preparação posterior adiciona apenas automação/testes/documentação, sem mudar os componentes Salesforce.

## Limites e homologação
A implantação não cria mapeamentos com IDs corporativos nem atribui permissões a usuários automaticamente. Atribuir DevSreEnvironment_Manager ao responsável autorizado (ou DevSreDeployment_Reader ao leitor) e cadastrar vigências explícitas. Acesso Flosum permanece dependente do perfil/pacote existente. A relação Restrict impede excluir uma organização Flosum referenciada; registros de configuração não podem ser excluídos e identidades não podem ser reescritas, preservando rastreabilidade.

A consulta é operacional e não certifica métricas DORA. Até 50 resultados por página, até 200 candidatos examinados por chamada; páginas sem correspondências podem ter continuação explícita. Datas/ambientes incompletos ficam identificados. Nenhuma fonte de commit foi implementada. FHT segue retenção nativa; não há promessa de auditoria indefinida.
