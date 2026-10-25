# Implantação da revisão de interface SPEC-004

Autorização: usuário solicitou implantar a revisão do PR #114 na DevSreFeat e informar os próximos passos. Este registro prepara o pacote; não comprova execução.

## Pacote e mecanismo

O kit universal já instalado é reutilizado sem alteração de workflows ou scripts. O catálogo recebe `spec004-delivery-ui`, limitado a quatro LightningComponentBundle: devSreDeliveryHub, devSreDeployments, devSreEnvironments e devSreDeliveryStyles. Testes Apex obrigatórios: DevSreEnvironmentTest e DevSreDeploymentTest. Sem Apex, objeto, campo, Permission Set, CustomTab ou CustomApplication no payload; sem dados de configuração ou ações destrutivas.

`spec004-delivery-existing-ui` contém os três bundles já instalados e permite a comparação prévia. A origem Git contém a revisão autorizada, portanto diferenças nesses bundles são esperadas. O módulo CSS é novo e não integra essa primeira comparação: a política do kit rejeita comparação quando um membro requerido está ausente. Após o deploy, comparar `spec004-delivery-ui` e exigir igualdade dos quatro bundles.

## Sequência e evidências

1. CI e revisão dos manifestos/catálogo, integração em master protegida.
2. Compare dos três bundles instalados; ler o relatório de membros e diferenças. Não interpretar diferenças como falha operacional. O relatório sanitizado não permite afirmar leitura integral do código remoto.
3. PLAN/dry-run do pacote de quatro bundles e nove testes Apex; inspecionar relatório e estado terminal.
4. Nova Issue DEPLOY estrita com o SHA completo da master atual. O próprio fluxo repete dry-run e testes antes da escrita. Não repetir execução de resultado desconhecido.
5. Conferir marcadores de deploy efetivo, resposta sanitizada Salesforce, testes e erros; comparar os quatro bundles após escrita.
6. Homologação visual/funcional pelo responsável, seguida da classificação real das organizações e validação de entregas conhecidas.

## Reversão e limites

Em regressão comprovada, preparar outro PR que restaure os três bundles do commit anterior ao PR #114, validar e implantar pelo mesmo kit autorizado. O módulo CSS pode permanecer instalado sem referência; não é necessário executar exclusões. Reversão não é automática.

O repositório é público: o kit exporta apenas relatório sanitizado. Não há retorno bruto integral ou Deployment ID no artifact público; relatar essa limitação sem afirmar acesso que não ocorreu. Não modificar visibilidade, segredos ou política de exportação.

Status: pacote preparado; comparação, validação e deploy ainda pendentes.
