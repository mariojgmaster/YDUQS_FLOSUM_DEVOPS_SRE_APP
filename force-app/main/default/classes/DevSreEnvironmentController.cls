public with sharing class DevSreEnvironmentController {
  public class OrganizationOption {
    @AuraEnabled
    public Id value { get; set; }
    @AuraEnabled
    public String label { get; set; }
  }
  public class OrganizationPage {
    @AuraEnabled
    public List<OrganizationOption> options { get; set; }
    @AuraEnabled
    public Boolean hasMore { get; set; }
    @AuraEnabled
    public Boolean canManage { get; set; }
  }
  public class MappingRow {
    @AuraEnabled
    public Id id { get; set; }
    @AuraEnabled
    public Id organizationId { get; set; }
    @AuraEnabled
    public String organizationName { get; set; }
    @AuraEnabled
    public String environmentClass { get; set; }
    @AuraEnabled
    public Datetime validFrom { get; set; }
    @AuraEnabled
    public Datetime validTo { get; set; }
    @AuraEnabled
    public String reason { get; set; }
  }

  @AuraEnabled
  public static OrganizationPage searchOrganizations(String searchTerm) {
    try {
      String term = searchTerm == null ? '' : searchTerm.trim();
      if (term.length() > 80)
        throw new AuraHandledException('A pesquisa permite até 80 caracteres.');
      String pattern = '%' + term.replace('%', '\\%').replace('_', '\\_') + '%';
      List<Flosum__Organisation__c> source = [
        SELECT Id, Name
        FROM Flosum__Organisation__c
        WHERE Name LIKE :pattern
        WITH USER_MODE
        ORDER BY Name, Id
        LIMIT 51
      ];
      OrganizationPage result = new OrganizationPage();
      result.options = new List<OrganizationOption>();
      result.hasMore = source.size() > 50;
      result.canManage = FeatureManagement.checkPermission(
        'DevSre_ManageEnvironments'
      );
      for (Integer i = 0; i < Math.min(50, source.size()); i++) {
        OrganizationOption option = new OrganizationOption();
        option.value = source[i].Id;
        option.label = source[i].Name;
        result.options.add(option);
      }
      return result;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível consultar organizações com seu acesso atual.'
      );
    }
  }

  @AuraEnabled
  public static List<MappingRow> listMappings(Id organizationId) {
    try {
      validOrganization(organizationId);
      String queryText = 'SELECT Id, Organization__c, Organization__r.Name, EnvironmentClass__c, ValidFrom__c, ValidTo__c, Reason__c FROM DevSre_EnvironmentMapping__c';
      if (organizationId != null)
        queryText += ' WHERE Organization__c = :organizationId';
      queryText += ' ORDER BY ValidFrom__c DESC, Id DESC LIMIT 2001';
      List<DevSre_EnvironmentMapping__c> source = Database.queryWithBinds(
        queryText,
        new Map<String, Object>{ 'organizationId' => organizationId },
        AccessLevel.USER_MODE
      );
      if (source.size() > 2000)
        throw new AuraHandledException(
          'Há muitas vigências. Selecione uma organização.'
        );
      List<MappingRow> result = new List<MappingRow>();
      for (DevSre_EnvironmentMapping__c item : source) {
        MappingRow row = new MappingRow();
        row.id = item.Id;
        row.organizationId = item.Organization__c;
        row.organizationName = item.Organization__r.Name;
        row.environmentClass = item.EnvironmentClass__c;
        row.validFrom = item.ValidFrom__c;
        row.validTo = item.ValidTo__c;
        row.reason = item.Reason__c;
        result.add(row);
      }
      return result;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível consultar as vigências com seu acesso atual.'
      );
    }
  }

  @AuraEnabled
  public static Id saveMapping(
    Id mappingId,
    Id organizationId,
    String environmentClass,
    Datetime validFrom,
    Datetime validTo,
    String reason
  ) {
    if (!FeatureManagement.checkPermission('DevSre_ManageEnvironments'))
      throw new AuraHandledException(
        'Você não possui permissão para gerenciar ambientes.'
      );
    if (String.isBlank(reason) || reason.trim().length() > 255)
      throw new AuraHandledException(
        'Informe uma justificativa com até 255 caracteres.'
      );
    try {
      validOrganization(organizationId);
      if (organizationId == null)
        throw new AuraHandledException('Selecione uma organização.');
      List<Flosum__Organisation__c> visible = [
        SELECT Id
        FROM Flosum__Organisation__c
        WHERE Id = :organizationId
        WITH USER_MODE
        LIMIT 1
      ];
      if (visible.isEmpty())
        throw new AuraHandledException('Organização inválida ou indisponível.');
      DevSre_EnvironmentMapping__c recordValue;
      if (mappingId == null) {
        recordValue = new DevSre_EnvironmentMapping__c(
          Organization__c = organizationId,
          EnvironmentClass__c = environmentClass,
          ValidFrom__c = validFrom,
          ValidTo__c = validTo,
          Reason__c = reason.trim()
        );
        Database.insert(recordValue, AccessLevel.USER_MODE);
      } else {
        if (
          mappingId.getSObjectType() != DevSre_EnvironmentMapping__c.SObjectType
        )
          throw new AuraHandledException('Vigência inválida.');
        List<DevSre_EnvironmentMapping__c> previous = [
          SELECT Id, Organization__c, EnvironmentClass__c, ValidFrom__c
          FROM DevSre_EnvironmentMapping__c
          WHERE Id = :mappingId
          WITH USER_MODE
          LIMIT 1
        ];
        if (
          previous.isEmpty() ||
          previous[0].Organization__c != organizationId ||
          previous[0].EnvironmentClass__c != environmentClass ||
          previous[0].ValidFrom__c != validFrom
        ) {
          throw new AuraHandledException(
            'A identidade da vigência não pode ser alterada.'
          );
        }
        recordValue = new DevSre_EnvironmentMapping__c(
          Id = mappingId,
          ValidTo__c = validTo,
          Reason__c = reason.trim()
        );
        Database.update(recordValue, AccessLevel.USER_MODE);
      }
      return recordValue.Id;
    } catch (AuraHandledException known) {
      throw known;
    } catch (DmlException invalid) {
      throw new AuraHandledException(
        'Não foi possível salvar. Verifique permissões, campos obrigatórios, período e sobreposição de vigências.'
      );
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível salvar a configuração com seu acesso atual.'
      );
    }
  }

  private static void validOrganization(Id value) {
    if (
      value != null &&
      value.getSObjectType() != Flosum__Organisation__c.SObjectType
    )
      throw new AuraHandledException('Organização inválida.');
  }

  // Operational, read-only Flosum organisation insights (legacy mapping remains isolated).
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
