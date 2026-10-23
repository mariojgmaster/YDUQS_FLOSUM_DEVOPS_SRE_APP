@IsTest
private class ClonePipelineControllerTest {
  @TestSetup
  static void createSourceData() {
    Flosum__Pipeline__c sourcePipeline = new Flosum__Pipeline__c(
      Name = 'Pipeline Origem'
    );
    insert sourcePipeline;

    List<Flosum__PipelineStep__c> steps = new List<Flosum__PipelineStep__c>{
      new Flosum__PipelineStep__c(
        Flosum__Pipeline__c = sourcePipeline.Id,
        Flosum__Number__c = 1,
        Flosum__Step__c = 'Deploy',
        Flosum__Description__c = 'Primeiro passo'
      ),
      new Flosum__PipelineStep__c(
        Flosum__Pipeline__c = sourcePipeline.Id,
        Flosum__Number__c = 2,
        Flosum__Step__c = 'Validate',
        Flosum__Description__c = 'Segundo passo'
      )
    };
    insert steps;
    steps[0].Flosum__Next_Step_Id_On_Pass__c = steps[1].Id;
    steps[0].Flosum__Next_Step_Id_On_Fail__c = steps[1].Id;
    update steps[0];
  }

  @IsTest
  static void returnsPreview() {
    Flosum__Pipeline__c source = [
      SELECT Id
      FROM Flosum__Pipeline__c
      WHERE Name = 'Pipeline Origem'
      LIMIT 1
    ];

    Test.startTest();
    ClonePipelineController.Preview preview = ClonePipelineController.getPreview(
      source.Id
    );
    Test.stopTest();

    Assert.areEqual('Pipeline Origem', preview.sourceName);
    Assert.areEqual('Pipeline Origem - Cópia 01', preview.suggestedName);
    Assert.areEqual(2, preview.stepCount);
    Assert.areEqual(80, preview.maxNameLength);
    Assert.areEqual(2, preview.steps.size());
    Assert.areEqual(Decimal.valueOf('1'), preview.steps[0].stepNumber);
    Assert.areEqual('Primeiro passo', preview.steps[0].description);
    Assert.areEqual('Deploy', preview.steps[0].action);
    Assert.areEqual(Decimal.valueOf('2'), preview.steps[1].stepNumber);
    Assert.areEqual('Segundo passo', preview.steps[1].description);
  }

  @IsTest
  static void returnsEmptyStepPreviewForPipelineWithoutSteps() {
    Flosum__Pipeline__c emptySource = new Flosum__Pipeline__c(
      Name = 'Pipeline Preview Vazio'
    );
    insert emptySource;

    ClonePipelineController.Preview preview = ClonePipelineController.getPreview(
      emptySource.Id
    );

    Assert.areEqual(0, preview.stepCount);
    Assert.isNotNull(preview.steps);
    Assert.areEqual(0, preview.steps.size());
  }

  @IsTest
  static void incrementsAcrossExistingClonesAndCloneOfClone() {
    insert new List<Flosum__Pipeline__c>{
      new Flosum__Pipeline__c(Name = 'Pipeline Origem - Cópia'),
      new Flosum__Pipeline__c(Name = 'Pipeline Origem - Cópia 01'),
      new Flosum__Pipeline__c(Name = 'Pipeline Origem - Cópia 04')
    };
    Flosum__Pipeline__c copiedSource = [
      SELECT Id FROM Flosum__Pipeline__c
      WHERE Name = 'Pipeline Origem - Cópia 04' LIMIT 1
    ];
    Test.startTest();
    ClonePipelineController.Preview preview = ClonePipelineController.getPreview(
      copiedSource.Id
    );
    Test.stopTest();
    Assert.areEqual('Pipeline Origem - Cópia 05', preview.suggestedName);
  }

  @IsTest
  static void ignoresNamesThatOnlyShareTheCopyPrefix() {
    insert new List<Flosum__Pipeline__c>{
      new Flosum__Pipeline__c(Name = 'Pipeline Origem - Cópia Extra'),
      new Flosum__Pipeline__c(Name = 'Pipeline Origem - Cópia XYZ')
    };
    Flosum__Pipeline__c source = [
      SELECT Id FROM Flosum__Pipeline__c
      WHERE Name = 'Pipeline Origem' LIMIT 1
    ];
    ClonePipelineController.Preview preview = ClonePipelineController.getPreview(
      source.Id
    );
    Assert.areEqual('Pipeline Origem - Cópia 01', preview.suggestedName);
  }

  @IsTest
  static void respectsEightyCharacterNameLimit() {
    Flosum__Pipeline__c source = new Flosum__Pipeline__c(
      Name = ''.leftPad(80, 'X')
    );
    insert source;
    ClonePipelineController.Preview preview = ClonePipelineController.getPreview(
      source.Id
    );
    Assert.isTrue(preview.suggestedName.length() <= 80);
    Assert.isTrue(preview.suggestedName.endsWith(' - Cópia 01'));
  }

  @IsTest
  static void clonesPipelineStepsAndReferences() {
    Flosum__Pipeline__c source = [
      SELECT Id
      FROM Flosum__Pipeline__c
      WHERE Name = 'Pipeline Origem'
      LIMIT 1
    ];

    Test.startTest();
    ClonePipelineController.CloneResult result = ClonePipelineController.clonePipeline(
      source.Id,
      ' Pipeline Clonado '
    );
    Test.stopTest();

    Assert.areEqual('Pipeline Clonado', result.pipelineName);
    Assert.areEqual(2, result.stepCount);
    List<Flosum__PipelineStep__c> clonedSteps = [
      SELECT
        Id,
        Flosum__Pipeline__c,
        Flosum__Number__c,
        Flosum__Description__c,
        Flosum__Next_Step_Id_On_Pass__c,
        Flosum__Next_Step_Id_On_Fail__c
      FROM Flosum__PipelineStep__c
      WHERE Flosum__Pipeline__c = :result.pipelineId
      ORDER BY Flosum__Number__c
    ];
    Assert.areEqual(2, clonedSteps.size());
    Assert.areEqual('Primeiro passo', clonedSteps[0].Flosum__Description__c);
    Assert.areEqual(
      clonedSteps[1].Id,
      clonedSteps[0].Flosum__Next_Step_Id_On_Pass__c
    );
    Assert.areEqual(
      clonedSteps[1].Id,
      clonedSteps[0].Flosum__Next_Step_Id_On_Fail__c
    );
    Assert.areNotEqual(source.Id, clonedSteps[0].Flosum__Pipeline__c);
  }

  @IsTest
  static void clonesPipelineWithoutSteps() {
    Flosum__Pipeline__c emptySource = new Flosum__Pipeline__c(
      Name = 'Pipeline Vazio'
    );
    insert emptySource;

    Test.startTest();
    ClonePipelineController.CloneResult result = ClonePipelineController.clonePipeline(
      emptySource.Id,
      'Pipeline Vazio Clonado'
    );
    Test.stopTest();

    Assert.areEqual(0, result.stepCount);
    Assert.areEqual(
      0,
      [
        SELECT COUNT()
        FROM Flosum__PipelineStep__c
        WHERE Flosum__Pipeline__c = :result.pipelineId
      ]
    );
  }

  @IsTest
  static void rejectsInvalidInput() {
    Flosum__Pipeline__c source = [
      SELECT Id
      FROM Flosum__Pipeline__c
      WHERE Name = 'Pipeline Origem'
      LIMIT 1
    ];

    assertHandledException(source.Id, '   ');
    assertHandledException(source.Id, ''.leftPad(81, 'X'));
    assertHandledException(UserInfo.getUserId(), 'Nome válido');
  }

  @IsTest
  static void rollsBackAfterParentFailure() {
    Flosum__Pipeline__c source = [
      SELECT Id
      FROM Flosum__Pipeline__c
      WHERE Name = 'Pipeline Origem'
      LIMIT 1
    ];
    Integer pipelinesBefore = [SELECT COUNT() FROM Flosum__Pipeline__c];
    ClonePipelineController.simulateFailureAfterParentInsert = true;

    Test.startTest();
    assertHandledException(source.Id, 'Não deve persistir');
    Test.stopTest();

    Assert.areEqual(pipelinesBefore, [SELECT COUNT() FROM Flosum__Pipeline__c]);
  }

  private static void assertHandledException(Id sourceId, String newName) {
    try {
      ClonePipelineController.clonePipeline(sourceId, newName);
      Assert.fail('Era esperada uma AuraHandledException.');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
  }
}
