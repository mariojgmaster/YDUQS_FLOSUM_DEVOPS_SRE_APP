@IsTest
private class DevSreEnvironmentInsightsTest {
  @IsTest static void readsOperationalSignalsWithoutEnvironmentMappings() {
    Flosum__Organisation__c org = new Flosum__Organisation__c(Name='Insights Org');
    insert org;
    insert new List<Flosum__Metadata_Log__c>{
      new Flosum__Metadata_Log__c(
        Flosum__Organisation__c=org.Id, Flosum__Process_Type__c='Deployment',
        Flosum__Status__c='Completed', Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=true, Flosum__Is_Error__c=false,
        Flosum__Async_Request_Id__c='INSIGHTS_1'),
      new Flosum__Metadata_Log__c(
        Flosum__Organisation__c=org.Id, Flosum__Process_Type__c='Validate',
        Flosum__Status__c='Completed', Flosum__Job_Completed__c=true,
        Flosum__Succeed__c=false, Flosum__Is_Error__c=true,
        Flosum__Async_Request_Id__c='INSIGHTS_2')
    };
    Test.startTest();
    DevSreEnvironmentController.InsightsPage data =
      DevSreEnvironmentController.loadOverview(30, org.Id);
    Test.stopTest();
    System.assertEquals(true, data.complete);
    System.assertEquals(1, data.organizationCount);
    System.assertEquals(1, data.deploymentCount);
    System.assertEquals(1, data.validationCount);
    System.assertEquals(1, data.successCount);
    System.assertEquals(1, data.failureCount);
    System.assertEquals(2, data.organizations[0].recent.size());
  }
  @IsTest static void rejectsBadFilterAndWrongReferenceType() {
    try { DevSreEnvironmentController.loadOverview(45, null);
      System.assert(false); } catch (AuraHandledException ex) { System.assertNotEquals(null,ex); }
    try { DevSreEnvironmentController.loadOverview(30, UserInfo.getUserId());
      System.assert(false); } catch (AuraHandledException ex) { System.assertNotEquals(null,ex); }
  }
}
