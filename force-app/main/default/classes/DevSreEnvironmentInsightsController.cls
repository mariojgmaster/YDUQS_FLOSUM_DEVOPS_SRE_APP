/** Read-only operational overview of Flosum organisations. No environment mapping writes.
 * Counts are bounded to avoid presenting partial scans as complete totals.
 * Time window refers to metadata log creation; not a certified DORA metric. */
public with sharing class DevSreEnvironmentInsightsController {
  public class LogEntry {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public String processType { get; set; }
    @AuraEnabled public String result { get; set; }
    @AuraEnabled public Datetime completedAt { get; set; }
  }
  public class OrganisationInsight {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public Integer deployments { get; set; }
    @AuraEnabled public Integer validations { get; set; }
    @AuraEnabled public Integer otherOperations { get; set; }
    @AuraEnabled public Integer successes { get; set; }
    @AuraEnabled public Integer failures { get; set; }
    @AuraEnabled public Datetime lastActivity { get; set; }
    @AuraEnabled public List<LogEntry> recent { get; set; }
  }
  public class InsightsPage {
    @AuraEnabled public Boolean complete { get; set; }
    @AuraEnabled public Boolean organizationLimitReached { get; set; }
    @AuraEnabled public Integer organizationCount { get; set; }
    @AuraEnabled public Integer logCount { get; set; }
    @AuraEnabled public Integer deploymentCount { get; set; }
    @AuraEnabled public Integer validationCount { get; set; }
    @AuraEnabled public Integer successCount { get; set; }
    @AuraEnabled public Integer failureCount { get; set; }
    @AuraEnabled public List<OrganisationInsight> organizations { get; set; }
  }
  @AuraEnabled(cacheable=true)
  public static InsightsPage loadOverview(Integer days, Id organizationId) {
    if (days == null) days = 30;
    if (days != 7 && days != 30 && days != 90)
      throw new AuraHandledException('Selecione 7, 30 ou 90 dias.');
    if (organizationId != null && organizationId.getSObjectType() != Flosum__Organisation__c.SObjectType)
      throw new AuraHandledException('Organização Flosum inválida.');
    try {
      Datetime fromUtc = System.now().addDays(-days);
      Map<String, Object> binds = new Map<String, Object>{
        'organizationId' => organizationId, 'fromUtc' => fromUtc
      };
      String orgQuery = 'SELECT Id, Name FROM Flosum__Organisation__c';
      if (organizationId != null) orgQuery += ' WHERE Id = :organizationId';
      orgQuery += ' ORDER BY Name ASC, Id ASC LIMIT 101';
      List<Flosum__Organisation__c> sourceOrgs = Database.queryWithBinds(
        orgQuery, binds, AccessLevel.USER_MODE);
      InsightsPage page = new InsightsPage();
      page.complete = true;
      page.organizationLimitReached = sourceOrgs.size() > 100;
      page.organizations = new List<OrganisationInsight>();
      Map<Id, OrganisationInsight> indexed = new Map<Id, OrganisationInsight>();
      for (Integer i = 0; i < Math.min(sourceOrgs.size(), 100); i++) {
        OrganisationInsight item = new OrganisationInsight();
        item.id = sourceOrgs[i].Id;
        item.name = sourceOrgs[i].Name;
        item.deployments = 0; item.validations = 0; item.otherOperations = 0;
        item.successes = 0; item.failures = 0;
        item.recent = new List<LogEntry>();
        indexed.put(item.id, item);
        page.organizations.add(item);
      }
      page.organizationCount = page.organizations.size();
      page.logCount = 0; page.deploymentCount = 0; page.validationCount = 0;
      page.successCount = 0; page.failureCount = 0;
      if (indexed.isEmpty()) return page;
      Set<Id> ids = indexed.keySet();
      List<Flosum__Metadata_Log__c> logs = [
        SELECT Id, Name, CreatedDate, Flosum__Organisation__c,
               Flosum__Process_Type__c, Flosum__Status__c,
               Flosum__Job_Completed__c, Flosum__Succeed__c, Flosum__Is_Error__c,
               Flosum__Completed_Date__c
        FROM Flosum__Metadata_Log__c
        WHERE Flosum__Organisation__c IN :ids AND CreatedDate >= :fromUtc
        WITH USER_MODE
        ORDER BY CreatedDate DESC, Id DESC LIMIT 2001
      ];
      if (logs.size() > 2000 || page.organizationLimitReached) {
        // Do not publish a misleading subtotal when the source is truncated.
        page.complete = false;
        page.logCount = null; page.deploymentCount = null;
        page.validationCount = null; page.successCount = null; page.failureCount = null;
        page.organizations.clear();
        return page;
      }
      for (Flosum__Metadata_Log__c log : logs) {
        OrganisationInsight item = indexed.get(log.Flosum__Organisation__c);
        if (item == null) continue;
        page.logCount++;
        String type = log.Flosum__Process_Type__c;
        if (type == 'Deployment') {
          item.deployments++; page.deploymentCount++;
        } else if (type == 'Validate') {
          item.validations++; page.validationCount++;
        } else item.otherOperations++;
        String result = 'Não concluído';
        if (log.Flosum__Status__c == 'Did Not Run') result = 'Não executado';
        else if (log.Flosum__Job_Completed__c == true &&
                 log.Flosum__Succeed__c == true && log.Flosum__Is_Error__c != true) {
          result = 'Sucesso'; item.successes++; page.successCount++;
        } else if (log.Flosum__Job_Completed__c == true &&
                   log.Flosum__Succeed__c != true) {
          result = 'Falha'; item.failures++; page.failureCount++;
        } else if (log.Flosum__Job_Completed__c == true &&
                   log.Flosum__Is_Error__c == true) result = 'Parcial';
        if (item.lastActivity == null) item.lastActivity = log.CreatedDate;
        if (item.recent.size() < 5) {
          LogEntry detail = new LogEntry();
          detail.id = log.Id; detail.name = log.Name;
          detail.processType = type; detail.result = result;
          detail.completedAt = log.Flosum__Completed_Date__c;
          item.recent.add(detail);
        }
      }
      return page;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception ex) {
      throw new AuraHandledException('Não foi possível consultar os dados operacionais do Flosum com seu acesso atual.');
    }
  }
}
