# Passos manuais — Clone Pipeline

## Objetivo

Disponibilizar a ação **Clonar Pipeline** na página de registro do objeto Flosum Pipeline após o deployment dos metadados da solução.

## Por que há uma etapa manual?

Os layouts de `Flosum__Pipeline__c` pertencem ao pacote gerenciado Flosum. Eles não podem ser recuperados e alterados com segurança por este projeto. Por isso, a Quick Action é implantada pelo package XML, mas sua inclusão no layout deve ser feita diretamente na org de destino.

## Pré-requisito

Realizar o deployment do manifesto [`manifest/clone-pipeline-package.xml`](../../../manifest/clone-pipeline-package.xml) e confirmar que os seguintes componentes foram implantados:

- `ClonePipelineController`
- `ClonePipelineControllerTest`
- `clonePipelineAction`
- `Flosum__Pipeline__c.Clonar_Pipeline`

## 1. Adicionar a ação ao layout

1. Acesse **Setup**.
2. Abra **Object Manager**.
3. Localize e abra o objeto **Pipeline** do pacote Flosum (`Flosum__Pipeline__c`).
4. Acesse **Page Layouts**.
5. Abra o layout atribuído aos usuários que utilizarão a funcionalidade, por exemplo **Pipeline Layout**.
6. Na paleta do editor, selecione **Mobile & Lightning Actions**.
7. Localize a ação **Clonar Pipeline**.
8. Arraste a ação para a seção **Salesforce Mobile and Lightning Experience Actions**.
9. Posicione-a na ordem desejada e salve o layout.
10. Repita o procedimento para cada layout atribuído que deva disponibilizar a ação, como **Commerce Cloud Layout**, quando aplicável.

> Embora a seção do layout mencione Mobile, Quick Actions baseadas em LWC são utilizadas por esta solução somente no Lightning Experience desktop.

## 2. Conceder acesso à classe Apex

1. Em **Setup**, acesse **Permission Sets**.
2. Abra o Permission Set atribuído aos usuários de DevOps, SRE ou COE que poderão clonar Pipelines.
3. Acesse **Apex Class Access** e clique em **Edit**.
4. Adicione `ClonePipelineController` às classes habilitadas e salve.
5. Confirme que o Permission Set também possui acesso de leitura e criação aos objetos e campos necessários de:
   - `Flosum__Pipeline__c`
   - `Flosum__PipelineStep__c`

Não é necessário conceder acesso à classe de teste `ClonePipelineControllerTest`.

## 3. Validar a entrega

1. Entre como um usuário que recebeu as permissões acima.
2. Abra um registro de Pipeline que contenha Pipeline Steps.
3. Confirme que a ação **Clonar Pipeline** aparece no menu de ações.
4. Abra a ação, revise o nome sugerido e a quantidade de Steps.
5. Informe um nome válido e clique em **Clonar**.
6. Confirme que o novo Pipeline foi aberto e que:
   - a quantidade de Steps é igual à do Pipeline original;
   - os Steps pertencem ao novo Pipeline;
   - as referências de próximo Step em sucesso e falha apontam para os Steps clonados.

## Resultado esperado

O usuário consegue clonar o Pipeline e todos os seus Pipeline Steps em uma única operação. Se ocorrer uma falha, nenhum registro parcial permanece criado.
