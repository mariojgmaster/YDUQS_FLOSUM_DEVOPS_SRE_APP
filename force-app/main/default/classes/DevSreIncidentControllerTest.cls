@IsTest
private class DevSreIncidentControllerTest {
  @TestSetup
  static void createRecords() {
    List<DevSre_Incident__c> incidents = new List<DevSre_Incident__c>{
      new DevSre_Incident__c(
        Title__c = 'Erro de serviço Alpha',
        ServiceKey__c = 'Serviço Alpha',
        Severity__c = 'SEV2',
        Status__c = 'Open',
        Source__c = 'Manual'
      ),
      new DevSre_Incident__c(
        Title__c = 'Instabilidade Beta',
        ServiceKey__c = 'Serviço Beta',
        Severity__c = 'SEV3',
        Status__c = 'Investigating',
        Source__c = 'Manual'
      )
    };
    insert incidents;
    insert new List<DevSre_RecoveryAction__c>{
      new DevSre_RecoveryAction__c(
        Incident__c = incidents[0].Id,
        ActionType__c = 'Mitigation',
        Status__c = 'Planned'
      ),
      new DevSre_RecoveryAction__c(
        Incident__c = incidents[0].Id,
        ActionType__c = 'Rollback',
        Status__c = 'Running'
      )
    };
  }

  @IsTest
  static void listsRealIncidentsWithSearch() {
    Test.startTest();
    DevSreIncidentController.IncidentPage allRows =
      DevSreIncidentController.listIncidents('');
    DevSreIncidentController.IncidentPage found =
      DevSreIncidentController.listIncidents('Alpha');
    Test.stopTest();
    Assert.areEqual(2, allRows.incidents.size());
    Assert.isFalse(allRows.hasMore);
    Assert.areEqual(1, found.incidents.size());
    Assert.areEqual('Erro de serviço Alpha', found.incidents[0].title);
    Assert.areEqual('Manual', [
      SELECT Source__c FROM DevSre_Incident__c WHERE Id = :found.incidents[0].id
    ].Source__c);
    Assert.areEqual('Pending', found.incidents[0].causeReviewStatus);
  }

  @IsTest
  static void listsOnlySelectedIncidentsActions() {
    DevSre_Incident__c first = [
      SELECT Id FROM DevSre_Incident__c WHERE Title__c = 'Erro de serviço Alpha' LIMIT 1
    ];
    DevSre_Incident__c second = [
      SELECT Id FROM DevSre_Incident__c WHERE Title__c = 'Instabilidade Beta' LIMIT 1
    ];
    Test.startTest();
    DevSreIncidentController.RecoveryPage firstActions =
      DevSreIncidentController.listRecoveryActions(first.Id);
    DevSreIncidentController.RecoveryPage secondActions =
      DevSreIncidentController.listRecoveryActions(second.Id);
    Test.stopTest();
    Assert.areEqual(2, firstActions.actions.size());
    Assert.isFalse(firstActions.hasMore);
    Assert.areEqual(0, secondActions.actions.size());
  }

  @IsTest
  static void rejectsOtherObjectIdAndLongSearch() {
    try {
      DevSreIncidentController.listRecoveryActions(UserInfo.getUserId());
      Assert.fail('Id de usuário não pode ser consultado como incidente');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
    try {
      DevSreIncidentController.listIncidents('A'.leftPad(81, 'A'));
      Assert.fail('Pesquisa maior que 80 deve ser rejeitada');
    } catch (AuraHandledException expected) {
      Assert.isNotNull(expected);
    }
  }

  @IsTest
  static void validatesRestorationTimeline() {
    DevSre_Incident__c first = [
      SELECT Id FROM DevSre_Incident__c WHERE Title__c = 'Erro de serviço Alpha' LIMIT 1
    ];
    first.Status__c = 'Restored';
    first.ImpactStartedAt__c = System.now();
    first.RestoredAt__c = first.ImpactStartedAt__c.addMinutes(-5);
    Database.SaveResult invalid = Database.update(first, false);
    Assert.isFalse(invalid.isSuccess(), 'Não aceitar restauração anterior ao impacto');
  }
  @IsTest
  static void refusesPrematureDeploymentCausality() {
    DevSre_Incident__c incident = [
      SELECT Id, CauseType__c, CauseReviewStatus__c
      FROM DevSre_Incident__c
      WHERE Title__c = 'Erro de serviço Alpha'
      LIMIT 1
    ];
    incident.CauseType__c = 'DeploymentRelated';
    incident.CauseReviewStatus__c = 'Confirmed';
    incident.CauseJustification__c = 'Sem comprovacao de vinculo real do Flosum';
    Database.SaveResult result = Database.update(incident, false);
    Assert.isFalse(result.isSuccess(), 'Nao confirmar deployment sem evidencias verificadas.');
  }
}
