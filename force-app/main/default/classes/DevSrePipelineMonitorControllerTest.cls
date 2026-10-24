@IsTest
private class DevSrePipelineMonitorControllerTest {
  @TestSetup
  static void setupPipelines() {
    Flosum__Pipeline__c first = new Flosum__Pipeline__c(Name = 'Monitor Alfa');
    Flosum__Pipeline__c second = new Flosum__Pipeline__c(Name = 'Monitor Beta');
    insert new List<Flosum__Pipeline__c>{ first, second };

    List<Flosum__PipelineStep__c> steps = new List<Flosum__PipelineStep__c>{
      new Flosum__PipelineStep__c(
        Flosum__Pipeline__c = first.Id,
        Flosum__Number__c = 1,
        Flosum__Description__c = 'Validar metadados',
        Flosum__Step__c = 'Validate'
      ),
      new Flosum__PipelineStep__c(
        Flosum__Pipeline__c = first.Id,
        Flosum__Number__c = 2,
        Flosum__Description__c = 'Publicar metadados',
        Flosum__Step__c = 'Deploy'
      )
    };
    insert steps;
    steps[0].Flosum__Next_Step_Id_On_Pass__c = steps[1].Id;
    update steps[0];
  }

  @IsTest
  static void listsAndSearchesPipelines() {
    Test.startTest();
    DevSrePipelineMonitorController.PipelinePage allRows =
      DevSrePipelineMonitorController.listPipelines(null);
    DevSrePipelineMonitorController.PipelinePage filtered =
      DevSrePipelineMonitorController.listPipelines('Alfa');
    Test.stopTest();

    Assert.areEqual(2, allRows.pipelines.size());
    Assert.isFalse(allRows.hasMore);
    Assert.areEqual('Monitor Alfa', filtered.pipelines[0].name);
    Assert.areEqual(1, filtered.pipelines.size());
  }

  @IsTest
  static void returnsRealStepsAndPassReferences() {
    Flosum__Pipeline__c source = [
      SELECT Id FROM Flosum__Pipeline__c WHERE Name = 'Monitor Alfa' LIMIT 1
    ];
    Test.startTest();
    DevSrePipelineMonitorController.PipelineDetail detail =
      DevSrePipelineMonitorController.getPipelineDetail(source.Id);
    Test.stopTest();

    Assert.areEqual('Monitor Alfa', detail.name);
    Assert.areEqual(2, detail.steps.size());
    Assert.isFalse(detail.hasMore);
    Assert.areEqual(Decimal.valueOf('1'), detail.steps[0].stepNumber);
    Assert.areEqual('Validar metadados', detail.steps[0].description);
    Assert.areEqual(detail.steps[1].id, detail.steps[0].nextOnPass);
  }

  @IsTest
  static void handlesPipelineWithoutSteps() {
    Flosum__Pipeline__c source = [
      SELECT Id FROM Flosum__Pipeline__c WHERE Name = 'Monitor Beta' LIMIT 1
    ];
    DevSrePipelineMonitorController.PipelineDetail detail =
      DevSrePipelineMonitorController.getPipelineDetail(source.Id);
    Assert.areEqual(0, detail.steps.size());
  }

  @IsTest
  static void rejectsInvalidIdAndOversizedSearch() {
    try {
      DevSrePipelineMonitorController.getPipelineDetail(UserInfo.getUserId());
      Assert.fail('Deveria recusar Id de outro objeto.');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
    try {
      DevSrePipelineMonitorController.listPipelines('X'.leftPad(81, 'X'));
      Assert.fail('Deveria recusar pesquisa acima do limite.');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
  }
}
