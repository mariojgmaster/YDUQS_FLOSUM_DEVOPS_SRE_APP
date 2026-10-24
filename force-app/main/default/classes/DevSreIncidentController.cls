/**
 * Consultas somente leitura para a fila operacional de incidentes.
 * Nenhuma informação aqui atesta causalidade com um deployment ou certifica métricas DORA.
 */
public with sharing class DevSreIncidentController {
  private static final Integer MAX_ROWS = 50;
  private static final Integer MAX_ACTIONS = 100;

  public class IncidentSummary {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String number { get; set; }
    @AuraEnabled public String title { get; set; }
    @AuraEnabled public String serviceKey { get; set; }
    @AuraEnabled public String severity { get; set; }
    @AuraEnabled public String status { get; set; }
    @AuraEnabled public DateTime impactStartedAt { get; set; }
    @AuraEnabled public DateTime restoredAt { get; set; }
    @AuraEnabled public String causeReviewStatus { get; set; }
  }

  public class IncidentPage {
    @AuraEnabled public List<IncidentSummary> incidents { get; set; }
    @AuraEnabled public Boolean hasMore { get; set; }
  }

  public class RecoverySummary {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String number { get; set; }
    @AuraEnabled public String actionType { get; set; }
    @AuraEnabled public String status { get; set; }
    @AuraEnabled public DateTime startedAt { get; set; }
    @AuraEnabled public DateTime completedAt { get; set; }
  }

  public class RecoveryPage {
    @AuraEnabled public List<RecoverySummary> actions { get; set; }
    @AuraEnabled public Boolean hasMore { get; set; }
  }

  @AuraEnabled
  public static IncidentPage listIncidents(String searchTerm) {
    try {
      requireAccess('DevSre_Incident__c', new List<String>{
        'Name', 'Title__c', 'ServiceKey__c', 'Severity__c', 'Status__c',
        'ImpactStartedAt__c', 'RestoredAt__c', 'CauseReviewStatus__c'
      });
      String term = searchTerm == null ? '' : searchTerm.trim();
      if (term.length() > 80) {
        throw new AuraHandledException('A pesquisa permite até 80 caracteres.');
      }
      Integer rowLimit = MAX_ROWS + 1;
      List<DevSre_Incident__c> records;
      if (String.isBlank(term)) {
        records = [
          SELECT Id, Name, Title__c, ServiceKey__c, Severity__c,
            Status__c, ImpactStartedAt__c, RestoredAt__c, CauseReviewStatus__c
          FROM DevSre_Incident__c
          WITH USER_MODE
          ORDER BY CreatedDate DESC, Id DESC
          LIMIT :rowLimit
        ];
      } else {
        String pattern = '%' + term + '%';
        records = [
          SELECT Id, Name, Title__c, ServiceKey__c, Severity__c,
            Status__c, ImpactStartedAt__c, RestoredAt__c, CauseReviewStatus__c
          FROM DevSre_Incident__c
          WHERE Title__c LIKE :pattern OR Name LIKE :pattern
          WITH USER_MODE
          ORDER BY CreatedDate DESC, Id DESC
          LIMIT :rowLimit
        ];
      }
      IncidentPage page = new IncidentPage();
      page.incidents = new List<IncidentSummary>();
      page.hasMore = records.size() > MAX_ROWS;
      for (Integer i = 0; i < records.size() && i < MAX_ROWS; i++) {
        DevSre_Incident__c recordValue = records[i];
        IncidentSummary row = new IncidentSummary();
        row.id = recordValue.Id;
        row.number = recordValue.Name;
        row.title = recordValue.Title__c;
        row.serviceKey = recordValue.ServiceKey__c;
        row.severity = recordValue.Severity__c;
        row.status = recordValue.Status__c;
        row.impactStartedAt = recordValue.ImpactStartedAt__c;
        row.restoredAt = recordValue.RestoredAt__c;
        row.causeReviewStatus = recordValue.CauseReviewStatus__c;
        page.incidents.add(row);
      }
      return page;
    } catch (AuraHandledException expected) {
      throw expected;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível consultar incidentes com seu acesso atual.');
    }
  }

  @AuraEnabled
  public static RecoveryPage listRecoveryActions(Id incidentId) {
    try {
      requireAccess('DevSre_Incident__c', new List<String>{ 'Name' });
      requireAccess('DevSre_RecoveryAction__c', new List<String>{
        'Name', 'Incident__c', 'ActionType__c', 'Status__c',
        'StartedAt__c', 'CompletedAt__c'
      });
      if (incidentId == null ||
          incidentId.getSObjectType() != Schema.getGlobalDescribe().get('DevSre_Incident__c')) {
        throw new AuraHandledException('Incidente inválido ou indisponível.');
      }
      List<DevSre_Incident__c> parents = [
        SELECT Id FROM DevSre_Incident__c
        WHERE Id = :incidentId WITH USER_MODE LIMIT 1
      ];
      if (parents.isEmpty()) {
        throw new AuraHandledException('Incidente inválido ou indisponível.');
      }
      Integer rowLimit = MAX_ACTIONS + 1;
      List<DevSre_RecoveryAction__c> records = [
        SELECT Id, Name, ActionType__c, Status__c, StartedAt__c, CompletedAt__c
        FROM DevSre_RecoveryAction__c
        WHERE Incident__c = :incidentId
        WITH USER_MODE
        ORDER BY CreatedDate DESC, Id DESC
        LIMIT :rowLimit
      ];
      RecoveryPage page = new RecoveryPage();
      page.actions = new List<RecoverySummary>();
      page.hasMore = records.size() > MAX_ACTIONS;
      for (Integer i = 0; i < records.size() && i < MAX_ACTIONS; i++) {
        DevSre_RecoveryAction__c recordValue = records[i];
        RecoverySummary row = new RecoverySummary();
        row.id = recordValue.Id;
        row.number = recordValue.Name;
        row.actionType = recordValue.ActionType__c;
        row.status = recordValue.Status__c;
        row.startedAt = recordValue.StartedAt__c;
        row.completedAt = recordValue.CompletedAt__c;
        page.actions.add(row);
      }
      return page;
    } catch (AuraHandledException expected) {
      throw expected;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível consultar as ações deste incidente.');
    }
  }

  private static void requireAccess(String objectName, List<String> fieldNames) {
    Schema.SObjectType typeValue = Schema.getGlobalDescribe().get(objectName);
    if (typeValue == null || !typeValue.getDescribe().isAccessible()) {
      throw new AuraHandledException('Você não possui permissão para consultar estes registros.');
    }
    Map<String, Schema.SObjectField> fields = typeValue.getDescribe().fields.getMap();
    for (String fieldName : fieldNames) {
      if (!fields.containsKey(fieldName) || !fields.get(fieldName).getDescribe().isAccessible()) {
        throw new AuraHandledException('Você não possui permissão para consultar estes campos.');
      }
    }
  }
}
