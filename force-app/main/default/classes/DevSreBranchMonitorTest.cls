@IsTest
private class DevSreBranchMonitorTest {
  @TestSetup
  static void fixtures() {
    insert new List<Flosum__Metadata_Log__c>{
      new Flosum__Metadata_Log__c(
        Flosum__Process_Type__c='Deployment',
        Flosum__Status__c='Completed', Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=true, Flosum__Is_Error__c=false,
        Flosum__Start_Date__c=System.now().addMinutes(-3),
        Flosum__Completed_Date__c=System.now().addMinutes(-2),
        Flosum__Async_Request_Id__c='BM_M1_DEPLOY'),
      new Flosum__Metadata_Log__c(
        Flosum__Process_Type__c='Validate',
        Flosum__Status__c='Completed', Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=false, Flosum__Is_Error__c=true,
        Flosum__Async_Request_Id__c='BM_M1_VALIDATE')
    };
  }
  @IsTest static void emptyDirectoryAndSafeCursor() {
    Test.startTest();
    DevSreBranchMonitorController.BranchPage page =
      DevSreBranchMonitorController.listBranches('BM-M1-Test',null,null);
    Test.stopTest();
    System.assertEquals(0,page.rows.size());
    System.assertEquals(false,page.hasMore);
    System.assertEquals(null,page.cursorId);
  }
  @IsTest static void aggregatesOnlySupportedOperationsAndRealActivity() {
    Test.startTest();
    DevSreBranchMonitorController.Overview summary =
      DevSreBranchMonitorController.getOverview(30);
    Test.stopTest();
    System.assertEquals(true,summary.complete);
    System.assertEquals(2,summary.operations);
    System.assertEquals(1,summary.deployments);
    System.assertEquals(1,summary.validations);
    System.assertEquals(1,summary.succeeded);
    System.assertEquals(1,summary.failed);
    System.assertEquals(0,summary.activeBranches);
    System.assertEquals(2,summary.recent.size());
  }
  @IsTest static void rejectsInvalidPeriodsSearchAndRelationships() {
    try {
      DevSreBranchMonitorController.getOverview(28);
      System.assert(false,'Bad period must be rejected');
    } catch(AuraHandledException expected) {}
    try {
      DevSreBranchMonitorController.listBranches(
        'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcd',
        null,null);
      System.assert(false,'Long search must be rejected');
    } catch(AuraHandledException expected) {}
    try {
      DevSreBranchMonitorController.getBranchDetail(UserInfo.getUserId());
      System.assert(false,'Wrong object ID must be rejected');
    } catch(AuraHandledException expected) {}
    try {
      DevSreBranchMonitorController.listBranches(null,'abc',null);
      System.assert(false,'Half cursor must be rejected');
    } catch(AuraHandledException expected) {}
  }
  @IsTest static void buildsPaginatedRowsAndBranchDetailsWithoutManagedDml() {
    String prefix=Flosum__Branch__c.SObjectType.getDescribe().getKeyPrefix();
    Id branchId=(Id)(prefix+'000000000001');
    String jsonValue='{"attributes":{"type":"Flosum__Branch__c"},"Id":"'+
      String.valueOf(branchId)+'","Name":"feature/CRM"}';
    Flosum__Branch__c source=(Flosum__Branch__c)JSON.deserialize(jsonValue,Flosum__Branch__c.class);
    List<Flosum__Branch__c> many=new List<Flosum__Branch__c>();
    for(Integer i=0;i<31;i++) many.add(source);
    DevSreBranchMonitorController.BranchPage page=
      DevSreBranchMonitorController.toBranchPage(many);
    System.assertEquals(30,page.rows.size());
    System.assertEquals(true,page.hasMore);
    System.assertEquals(branchId,page.cursorId);

    List<Flosum__Metadata_Log__c> logs=new List<Flosum__Metadata_Log__c>();
    for(Integer i=0;i<51;i++) {
      logs.add(new Flosum__Metadata_Log__c(
        Flosum__Branch__c=branchId, Flosum__Process_Type__c='Deployment',
        Flosum__Status__c='Completed',Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=true,Flosum__Is_Error__c=false,
        Flosum__Start_Date__c=System.now().addMinutes(-3),
        Flosum__Completed_Date__c=System.now().addMinutes(-1)
      ));
    }
    DevSreBranchMonitorController.BranchDetail detail=
      DevSreBranchMonitorController.toDetail(source,logs);
    System.assertEquals(50,detail.recent.size());
    System.assertEquals(true,detail.hasMore);
    System.assertEquals('feature/CRM',detail.name);
    System.assertEquals('feature/CRM',detail.recent[0].branchName);
    System.assertEquals(120,detail.recent[0].durationSeconds);
  }
  @IsTest static void omitsPartialCountsAfterSourceBoundAndHandlesUnknownOutcomes() {
    List<Flosum__Metadata_Log__c> many=new List<Flosum__Metadata_Log__c>();
    for(Integer i=0;i<501;i++) {
      many.add(new Flosum__Metadata_Log__c(
        Flosum__Process_Type__c='Other',
        Flosum__Status__c='Completed',Flosum__Job_Completed__c=false
      ));
    }
    DevSreBranchMonitorController.Overview result=
      DevSreBranchMonitorController.toOverview(many);
    System.assertEquals(false,result.complete);
    System.assertEquals(null,result.operations);
    System.assertEquals(8,result.recent.size());
    System.assertEquals('Em andamento / desconhecido',result.recent[0].outcome);
    Flosum__Metadata_Log__c partial=new Flosum__Metadata_Log__c(
      Flosum__Process_Type__c='Validate',Flosum__Status__c='Completed',
      Flosum__Job_Completed__c=true, Flosum__Succeed__c=true,
      Flosum__Is_Error__c=true);
    System.assertEquals('Parcial',DevSreBranchMonitorController.resultFor(partial));
    Flosum__Metadata_Log__c other=new Flosum__Metadata_Log__c(
      Flosum__Job_Completed__c=true,Flosum__Succeed__c=null);
    System.assertEquals('Indeterminado',DevSreBranchMonitorController.resultFor(other));
  }
  @IsTest static void validatesPagingAndRejectsUnseenBranch() {
    String prefix=Flosum__Branch__c.SObjectType.getDescribe().getKeyPrefix();
    Id branchId=(Id)(prefix+'000000000001');
    DevSreBranchMonitorController.BranchPage result=
      DevSreBranchMonitorController.listBranches(null,'some name',branchId);
    System.assertEquals(0,result.rows.size());
    try {
      DevSreBranchMonitorController.getBranchDetail(branchId);
      System.assert(false,'Unseen Branch must be rejected');
    } catch (AuraHandledException expected) {}
    System.assertEquals('%CRM\\%%',DevSreBranchMonitorController.wildcard('CRM%'));
  }

  @IsTest static void doesNotCallAValidationADeployment() {
    Flosum__Metadata_Log__c item=new Flosum__Metadata_Log__c(
      Flosum__Process_Type__c='Validate', Flosum__Status__c='Did Not Run',
      Flosum__Job_Completed__c=false, Flosum__Succeed__c=false
    );
    System.assertEquals('Não executado',DevSreBranchMonitorController.resultFor(item));
    item.Flosum__Status__c='Completed';
    item.Flosum__Job_Completed__c=true;
    item.Flosum__Succeed__c=false;
    item.Flosum__Is_Error__c=true;
    System.assertEquals('Falha',DevSreBranchMonitorController.resultFor(item));
  }
}