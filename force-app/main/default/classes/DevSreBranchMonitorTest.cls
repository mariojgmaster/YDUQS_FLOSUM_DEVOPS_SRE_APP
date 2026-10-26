@IsTest
private class DevSreBranchMonitorTest {
  @TestSetup
  static void fixtures() {
    Flosum__Branch__c branch = new Flosum__Branch__c(Name='BM-M1-Test-Branch');
    insert branch;
    insert new List<Flosum__Metadata_Log__c>{
      new Flosum__Metadata_Log__c(
        Flosum__Branch__c=branch.Id, Flosum__Process_Type__c='Deployment',
        Flosum__Status__c='Completed', Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=true, Flosum__Is_Error__c=false,
        Flosum__Start_Date__c=System.now().addMinutes(-3),
        Flosum__Completed_Date__c=System.now().addMinutes(-2),
        Flosum__Async_Request_Id__c='BM_M1_DEPLOY'),
      new Flosum__Metadata_Log__c(
        Flosum__Branch__c=branch.Id, Flosum__Process_Type__c='Validate',
        Flosum__Status__c='Completed', Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=false, Flosum__Is_Error__c=true,
        Flosum__Async_Request_Id__c='BM_M1_VALIDATE')
    };
  }
  @IsTest static void paginatesBranchesAndShowsRealDetails() {
    Test.startTest();
    DevSreBranchMonitorController.BranchPage result=
      DevSreBranchMonitorController.listBranches('BM-M1-Test',null,null);
    System.assertEquals(1,result.rows.size());
    System.assertEquals(false,result.hasMore);
    DevSreBranchMonitorController.BranchDetail detail=
      DevSreBranchMonitorController.getBranchDetail(result.rows[0].id);
    Test.stopTest();
    System.assertEquals('BM-M1-Test-Branch',detail.name);
    System.assertEquals(2,detail.recent.size());
    System.assertEquals(false,detail.hasMore);
    System.assertEquals(result.rows[0].id,detail.id);
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
    System.assertEquals(1,summary.activeBranches);
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