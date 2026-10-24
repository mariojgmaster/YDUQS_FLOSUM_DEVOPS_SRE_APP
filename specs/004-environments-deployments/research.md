# Pesquisa / plataforma confirmada

Run #40140644663 (Issue #103) recuperou CustomTab pipelineMonitor com lwcComponent=pipelineMonitor e app DevOps_SRE_Analytics com as quatro abas originais. O app não precisa ser modificado. A integração reutiliza a tab pipelineMonitor por novo host, preservando label/motif e a Visão original c-pipeline-monitor, sem modificar o bundle original instalado.

O baseline XML será conferido na validação; qualquer drift bloqueia a proposta. A lista de metadados e o XML cru foram transportados criptografados. Nenhum registro Salesforce foi alterado.

Dry-run #40141430930 aceitou os 20 componentes, mas a fixture de deployments violou a restrição nativa de unicidade de Async_Request_Id. Describe integral confirma unique=true e caseSensitive=false. Não consultar duplicidades impossíveis: preservar cada tentativa/Id e usar org+request como correlação; se o schema perder essa restrição, sinalizar qualidade incompleta. Nenhuma regra de produção foi reduzida para fazer o teste passar.
