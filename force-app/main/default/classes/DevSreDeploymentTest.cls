@IsTest
private class DevSreDeploymentTest {
  private static Datetime at(Integer day) {
    return Datetime.newInstanceGmt(2026, 1, day, 0, 0, 0);
  }
  private static User grant() {
    Id actor = UserInfo.getUserId();
    System.runAs(new User(Id = actor)) {
      Id permissionId = [
        SELECT Id
        FROM PermissionSet
        WHERE Name = 'DevSreEnvironment_Manager'
        WITH SYSTEM_MODE
        LIMIT 1
      ]
      .Id;
      if (
        [
          SELECT COUNT()
          FROM PermissionSetAssignment
          WHERE AssigneeId = :actor AND PermissionSetId = :permissionId
          WITH SYSTEM_MODE
        ] == 0
      ) {
        Database.insert(
          new PermissionSetAssignment(
            AssigneeId = actor,
            PermissionSetId = permissionId
          ),
          AccessLevel.SYSTEM_MODE
        );
      }
    }
    return new User(Id = actor);
  }
  @TestSetup
  static void fixtures() {
    Flosum__Organisation__c org = new Flosum__Organisation__c(
      Name = 'SPEC004 Adapter'
    );
    Database.insert(org, AccessLevel.SYSTEM_MODE);
    List<Flosum__Metadata_Log__c> logs = new List<Flosum__Metadata_Log__c>();
    for (Integer i = 0; i < 55; i++) {
      logs.add(
        new Flosum__Metadata_Log__c(
          Flosum__Organisation__c = org.Id,
          Flosum__Process_Type__c = i == 54 ? 'Validate' : 'Deployment',
          Flosum__Status__c = 'Completed',
          Flosum__Job_Completed__c = true,
          Flosum__Succeed__c = i != 53,
          Flosum__Is_Error__c = false,
          Flosum__Start_Date__c = at(2),
          Flosum__Completed_Date__c = at(2).addSeconds(10),
          Flosum__Async_Request_Id__c = 'SPEC004_' + i
        )
      );
    }
    Database.insert(logs, AccessLevel.SYSTEM_MODE);
  }
  @IsTest
  static void listsRealLogsWithPagingFiltersAndSourceIdentity() {
    System.runAs(grant()) {
      Id org = [SELECT Id FROM Flosum__Organisation__c WITH SYSTEM_MODE LIMIT 1]
      .Id;
      DevSreEnvironmentController.saveMapping(
        null,
        org,
        'PROD',
        at(1),
        null,
        'Mapping'
      );
      DevSreDeploymentController.DeploymentPage first = DevSreDeploymentController.listDeployments(
        at(1),
        at(3),
        org,
        null,
        'PROD',
        null,
        null,
        null
      );
      Assert.areEqual(50, first.rows.size());
      Assert.isTrue(first.hasMore);
      Set<Id> ids = new Set<Id>();
      for (DevSreDeploymentController.DeploymentRow row : first.rows)
        ids.add(row.id);
      DevSreDeploymentController.DeploymentPage next = DevSreDeploymentController.listDeployments(
        at(1),
        at(3),
        org,
        null,
        'PROD',
        null,
        first.cursorCreated,
        first.cursorId
      );
      Assert.areEqual(4, next.rows.size());
      Assert.isFalse(next.hasMore);
      Set<String> correlations = new Set<String>();
      for (DevSreDeploymentController.DeploymentRow row : first.rows)
        correlations.add(row.correlationKey);
      for (DevSreDeploymentController.DeploymentRow row : next.rows) {
        Assert.isFalse(ids.contains(row.id));
        Assert.isFalse(correlations.contains(row.correlationKey));
        correlations.add(row.correlationKey);
      }
      Assert.areEqual(54, correlations.size());
      Assert.isFalse(first.correlationIncomplete);
      DevSreDeploymentController.DeploymentPage failed = DevSreDeploymentController.listDeployments(
        at(1),
        at(3),
        org,
        null,
        null,
        'Failed',
        null,
        null
      );
      Assert.areEqual(1, failed.rows.size());
      Assert.areEqual('Failed', failed.rows[0].outcome);
      Assert.areEqual(
        0,
        DevSreDeploymentController.listDeployments(
            at(1),
            at(3),
            org,
            null,
            'UAT',
            null,
            null,
            null
          )
          .rows.size()
      );
    }
  }
  private static Flosum__Metadata_Log__c event() {
    return new Flosum__Metadata_Log__c(
      Flosum__Status__c = 'Completed',
      Flosum__Job_Completed__c = true,
      Flosum__Succeed__c = true,
      Flosum__Is_Error__c = false,
      Flosum__Start_Date__c = at(1),
      Flosum__Completed_Date__c = at(2)
    );
  }
  @IsTest
  static void usesPrimitiveFlagsAndValidatesClock() {
    Flosum__Metadata_Log__c item = event();
    List<DevSre_EnvironmentMapping__c> none = new List<DevSre_EnvironmentMapping__c>();
    DevSreDeploymentController.DeploymentRow result = DevSreDeploymentController.evaluate(
      item,
      none
    );
    Assert.areEqual('Success', result.outcome);
    Assert.areEqual('UNKNOWN', result.environmentClass);
    Assert.areEqual(86400, result.durationSeconds);
    item.Flosum__Succeed__c = false;
    Assert.areEqual(
      'Failed',
      DevSreDeploymentController.evaluate(item, none).outcome
    );
    item.Flosum__Succeed__c = true;
    item.Flosum__Is_Error__c = true;
    Assert.areEqual(
      'Partial',
      DevSreDeploymentController.evaluate(item, none).outcome
    );
    item.Flosum__Status__c = 'Did Not Run';
    Assert.areEqual(
      'NotRun',
      DevSreDeploymentController.evaluate(item, none).outcome
    );
    item.Flosum__Status__c = 'In Progress';
    item.Flosum__Job_Completed__c = false;
    Assert.areEqual(
      'Pending',
      DevSreDeploymentController.evaluate(item, none).outcome
    );
    item.Flosum__Completed_Date__c = at(1).addSeconds(-1);
    result = DevSreDeploymentController.evaluate(item, none);
    Assert.isNull(result.durationSeconds);
    Assert.isTrue(result.quality.contains('anterior'));
    item.Flosum__Completed_Date__c = null;
    Assert.isTrue(
      DevSreDeploymentController.evaluate(item, none)
        .quality.contains('Sem data de conclusão')
    );
  }
  @IsTest
  static void resolvesBoundariesAndRejectsAmbiguity() {
    Id org = [SELECT Id FROM Flosum__Organisation__c WITH SYSTEM_MODE LIMIT 1]
    .Id;
    Flosum__Metadata_Log__c item = event();
    item.Flosum__Organisation__c = org;
    List<DevSre_EnvironmentMapping__c> mappings = new List<DevSre_EnvironmentMapping__c>{
      new DevSre_EnvironmentMapping__c(
        Organization__c = org,
        EnvironmentClass__c = 'UAT',
        ValidFrom__c = at(1),
        ValidTo__c = at(2)
      ),
      new DevSre_EnvironmentMapping__c(
        Organization__c = org,
        EnvironmentClass__c = 'PROD',
        ValidFrom__c = at(2)
      )
    };
    Assert.areEqual(
      'PROD',
      DevSreDeploymentController.evaluate(item, mappings).environmentClass
    );
    mappings.add(
      new DevSre_EnvironmentMapping__c(
        Organization__c = org,
        EnvironmentClass__c = 'DEV',
        ValidFrom__c = at(1)
      )
    );
    Assert.areEqual(
      'AMBIGUOUS',
      DevSreDeploymentController.evaluate(item, mappings).environmentClass
    );
  }
  @IsTest
  static void rejectsInvalidQueries() {
    try {
      DevSreDeploymentController.listDeployments(
        at(3),
        at(1),
        null,
        null,
        null,
        null,
        null,
        null
      );
      Assert.fail('Period');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
    try {
      DevSreDeploymentController.listDeployments(
        at(1),
        at(2),
        UserInfo.getUserId(),
        null,
        null,
        null,
        null,
        null
      );
      Assert.fail('Org');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
    try {
      DevSreDeploymentController.listDeployments(
        at(1),
        at(2),
        null,
        null,
        'injection',
        null,
        null,
        null
      );
      Assert.fail('Class');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
    try {
      DevSreDeploymentController.listDeployments(
        at(1),
        at(2),
        null,
        null,
        null,
        null,
        at(1),
        null
      );
      Assert.fail('Cursor');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
  }
  @IsTest
  static void summarizesFullScopeBeyondFirstPageAndRespectsEnvironment() {
    System.runAs(grant()) {
      Id org = [SELECT Id FROM Flosum__Organisation__c WITH SYSTEM_MODE LIMIT 1]
      .Id;
      DevSreEnvironmentController.saveMapping(
        null,
        org,
        'PROD',
        at(1),
        null,
        'Monitor'
      );
      DevSreDeploymentController.MonitorSummary summary = DevSreDeploymentController.getMonitorSummary(
        at(1),
        at(3),
        org,
        'PROD',
        null
      );
      Assert.isTrue(summary.complete);
      Assert.areEqual(
        54,
        summary.total,
        'Includes 50 first-page and four further logs, excludes Validate'
      );
      Assert.areEqual(53, summary.succeeded);
      Assert.areEqual(1, summary.failed);
      Assert.areEqual(0, summary.pending);
      Assert.areEqual(98.1, summary.successRate);
      summary = DevSreDeploymentController.getMonitorSummary(
        at(1),
        at(3),
        org,
        'UAT',
        null
      );
      Assert.areEqual(0, summary.total);
      Assert.isNull(
        summary.successRate,
        'An empty denominator is not 0% success'
      );
    }
  }
  @IsTest
  static void searchesMonitorOnServerWithLiteralWildcardsAndOutcomeFilter() {
    System.runAs(grant()) {
      Flosum__Metadata_Log__c log = [
        SELECT Name
        FROM Flosum__Metadata_Log__c
        WHERE Flosum__Process_Type__c = 'Deployment'
        WITH SYSTEM_MODE
        LIMIT 1
      ];
      DevSreDeploymentController.DeploymentPage page = DevSreDeploymentController.listMonitorDeployments(
        at(1),
        at(3),
        null,
        null,
        null,
        log.Name,
        null,
        null
      );
      Assert.isTrue(page.rows.size() > 0);
      for (DevSreDeploymentController.DeploymentRow row : page.rows)
        Assert.isTrue(row.name.contains(log.Name));
      Assert.areEqual(
        0,
        DevSreDeploymentController.listMonitorDeployments(
            at(1),
            at(3),
            null,
            null,
            null,
            '%_',
            null,
            null
          )
          .rows.size(),
        'Wildcards are literal search text'
      );
      Assert.areEqual(
        1,
        DevSreDeploymentController.listMonitorDeployments(
            at(1),
            at(3),
            null,
            null,
            'Failed',
            null,
            null,
            null
          )
          .rows.size()
      );
      String tooLong = 'x';
      for (Integer i = 0; i < 7; i++)
        tooLong += tooLong;
      try {
        DevSreDeploymentController.getMonitorSummary(
          at(1),
          at(3),
          null,
          null,
          tooLong
        );
        Assert.fail('Oversized search');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
    }
  }
  @IsTest
  static void neverReportsPartialCountsAsCompleteSummary() {
    System.runAs(grant()) {
      DevSreDeploymentController.monitorLimit = 10;
      DevSreDeploymentController.MonitorSummary summary = DevSreDeploymentController.getMonitorSummary(
        at(1),
        at(3),
        null,
        null,
        null
      );
      Assert.isFalse(summary.complete);
      Assert.isNull(summary.total);
      Assert.isNull(summary.succeeded);
      Assert.isNull(summary.successRate);
    }
  }
}
