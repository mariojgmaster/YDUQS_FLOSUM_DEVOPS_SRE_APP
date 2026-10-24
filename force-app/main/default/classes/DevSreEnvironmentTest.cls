@IsTest
private class DevSreEnvironmentTest {
  private static User manager() {
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
    Database.insert(
      new Flosum__Organisation__c(Name = 'SPEC004 Organização'),
      AccessLevel.SYSTEM_MODE
    );
  }
  private static Id orgId() {
    return [SELECT Id FROM Flosum__Organisation__c WITH SYSTEM_MODE LIMIT 1].Id;
  }
  private static Datetime instant(Integer day) {
    return Datetime.newInstanceGmt(2026, 1, day, 0, 0, 0);
  }

  @IsTest
  static void createsAdjacentIntervalsAndClosesOpenInterval() {
    User actor = manager();
    System.runAs(actor) {
      Id org = orgId();
      Id first = DevSreEnvironmentController.saveMapping(
        null,
        org,
        'UAT',
        instant(1),
        instant(2),
        'Classificação inicial'
      );
      Id second = DevSreEnvironmentController.saveMapping(
        null,
        org,
        'PROD',
        instant(2),
        null,
        'Promoção do ambiente'
      );
      Assert.isNotNull(first);
      Assert.isNotNull(second);
      DevSreEnvironmentController.saveMapping(
        second,
        org,
        'PROD',
        instant(2),
        instant(3),
        'Encerramento'
      );
      Assert.areEqual(2, DevSreEnvironmentController.listMappings(org).size());
      Assert.isTrue(
        DevSreEnvironmentController.searchOrganizations('SPEC004').canManage
      );
    }
  }
  @IsTest
  static void preventsOverlapAndInvalidIntervalsInBulk() {
    User actor = manager();
    System.runAs(actor) {
      Id org = orgId();
      List<DevSre_EnvironmentMapping__c> rows = new List<DevSre_EnvironmentMapping__c>{
        new DevSre_EnvironmentMapping__c(
          Organization__c = org,
          EnvironmentClass__c = 'PROD',
          ValidFrom__c = instant(1),
          ValidTo__c = instant(3),
          Reason__c = 'A'
        ),
        new DevSre_EnvironmentMapping__c(
          Organization__c = org,
          EnvironmentClass__c = 'UAT',
          ValidFrom__c = instant(2),
          Reason__c = 'B'
        )
      };
      Database.SaveResult[] results = Database.insert(
        rows,
        false,
        AccessLevel.USER_MODE
      );
      Assert.isFalse(results[0].isSuccess());
      Assert.isFalse(results[1].isSuccess());
      DevSreEnvironmentController.saveMapping(
        null,
        org,
        'DEV',
        instant(1),
        instant(2),
        'C'
      );
      try {
        DevSreEnvironmentController.saveMapping(
          null,
          org,
          'SIT',
          instant(1),
          instant(3),
          'D'
        );
        Assert.fail('Overlap');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
      try {
        DevSreEnvironmentController.saveMapping(
          null,
          org,
          'SIT',
          instant(3),
          instant(2),
          'E'
        );
        Assert.fail('Invalid clock');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
    }
  }
  @IsTest
  static void identityDeletionAndReopeningAreForbidden() {
    User actor = manager();
    System.runAs(actor) {
      Id org = orgId();
      Id mapping = DevSreEnvironmentController.saveMapping(
        null,
        org,
        'DEV',
        instant(1),
        instant(2),
        'Inicial'
      );
      try {
        DevSreEnvironmentController.saveMapping(
          mapping,
          org,
          'PROD',
          instant(1),
          instant(2),
          'Mudança'
        );
        Assert.fail('Identity');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
      Database.SaveResult result = Database.update(
        new DevSre_EnvironmentMapping__c(Id = mapping, ValidTo__c = null),
        false,
        AccessLevel.SYSTEM_MODE
      );
      Assert.isFalse(result.isSuccess());
      Database.DeleteResult deleted = Database.delete(
        new DevSre_EnvironmentMapping__c(Id = mapping),
        false,
        AccessLevel.SYSTEM_MODE
      );
      Assert.isFalse(deleted.isSuccess());
      Database.SaveResult changed = Database.update(
        new DevSre_EnvironmentMapping__c(
          Id = mapping,
          ValidFrom__c = instant(2)
        ),
        false,
        AccessLevel.SYSTEM_MODE
      );
      Assert.isFalse(changed.isSuccess());
    }
  }
  @IsTest
  static void rejectsUnprivilegedActorAndMalformedOrganization() {
    // A new standard-profile actor has neither source FLS nor app permissions.
    User actor = new User(
      Alias = 'spec004',
      Email = 'spec004@example.invalid',
      EmailEncodingKey = 'UTF-8',
      LastName = 'SPEC004',
      LanguageLocaleKey = 'en_US',
      LocaleSidKey = 'en_US',
      TimeZoneSidKey = 'GMT',
      ProfileId = UserInfo.getProfileId(),
      Username = 'spec004.' +
        String.valueOf(Datetime.now().getTime()) +
        '.' +
        UserInfo.getOrganizationId() +
        '@example.invalid'
    );
    Database.insert(actor, AccessLevel.SYSTEM_MODE);
    System.runAs(actor) {
      try {
        DevSreEnvironmentController.saveMapping(
          null,
          orgId(),
          'PROD',
          instant(1),
          null,
          'Negado'
        );
        Assert.fail('Permission');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
      Database.SaveResult direct = Database.insert(
        new DevSre_EnvironmentMapping__c(
          Organization__c = orgId(),
          EnvironmentClass__c = 'PROD',
          ValidFrom__c = instant(1),
          Reason__c = 'API'
        ),
        false,
        AccessLevel.SYSTEM_MODE
      );
      Assert.isFalse(direct.isSuccess());
      try {
        DevSreEnvironmentController.listMappings(UserInfo.getUserId());
        Assert.fail('Wrong object');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
    }
  }
  @IsTest
  static void invalidInputsDoNotLeakData() {
    System.runAs(manager()) {
      try {
        DevSreEnvironmentController.searchOrganizations('x'.repeat(81));
        Assert.fail('Length');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
      try {
        DevSreEnvironmentController.saveMapping(
          null,
          orgId(),
          'PROD',
          instant(1),
          null,
          ''
        );
        Assert.fail('Reason');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
      try {
        DevSreEnvironmentController.saveMapping(
          null,
          UserInfo.getUserId(),
          'PROD',
          instant(1),
          null,
          'Reason'
        );
        Assert.fail('Source');
      } catch (AuraHandledException expected) {
        Assert.isNotNull(expected);
      }
    }
  }
}
