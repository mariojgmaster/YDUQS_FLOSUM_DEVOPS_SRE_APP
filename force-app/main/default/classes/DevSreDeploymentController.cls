/** Read-only source adapter. No aggregate here is a certified DORA metric. */
public with sharing class DevSreDeploymentController {
  public class DeploymentRow {
    @AuraEnabled
    public Id id { get; set; }
    @AuraEnabled
    public String name { get; set; }
    @AuraEnabled
    public Id organizationId { get; set; }
    @AuraEnabled
    public String organizationName { get; set; }
    @AuraEnabled
    public Id branchId { get; set; }
    @AuraEnabled
    public String branchName { get; set; }
    @AuraEnabled
    public String environmentClass { get; set; }
    @AuraEnabled
    public String outcome { get; set; }
    @AuraEnabled
    public Datetime startedAt { get; set; }
    @AuraEnabled
    public Datetime completedAt { get; set; }
    @AuraEnabled
    public Datetime createdAt { get; set; }
    @AuraEnabled
    public Decimal durationSeconds { get; set; }
    @AuraEnabled
    public String quality { get; set; }
    @AuraEnabled
    public String correlationKey { get; set; }
  }
  public class DeploymentPage {
    @AuraEnabled
    public List<DeploymentRow> rows { get; set; }
    @AuraEnabled
    public Boolean hasMore { get; set; }
    @AuraEnabled
    public Datetime cursorCreated { get; set; }
    @AuraEnabled
    public Id cursorId { get; set; }
    @AuraEnabled
    public Integer inspectedRows { get; set; }
    @AuraEnabled
    public Boolean correlationIncomplete { get; set; }
  }

  @AuraEnabled
  public static DeploymentPage listDeployments(
    Datetime fromUtc,
    Datetime toUtc,
    Id organizationId,
    Id branchId,
    String environmentClass,
    String outcome,
    Datetime cursorCreated,
    Id cursorId
  ) {
    validateFilters(
      fromUtc,
      toUtc,
      organizationId,
      branchId,
      environmentClass,
      outcome,
      cursorCreated,
      cursorId
    );
    try {
      Map<String, Object> binds = new Map<String, Object>{
        'fromUtc' => fromUtc,
        'toUtc' => toUtc,
        'organizationId' => organizationId,
        'branchId' => branchId,
        'cursorCreated' => cursorCreated,
        'cursorId' => cursorId
      };
      String queryText =
        'SELECT Id, Name, CreatedDate, Flosum__Organisation__c, Flosum__Organisation__r.Name, ' +
        'Flosum__Branch__c, Flosum__Branch__r.Name, Flosum__Process_Type__c, Flosum__Status__c, ' +
        'Flosum__Job_Completed__c, Flosum__Succeed__c, Flosum__Is_Error__c, Flosum__Start_Date__c, ' +
        'Flosum__Completed_Date__c, Flosum__Async_Request_Id__c, Flosum__Parent_Log__c ' +
        'FROM Flosum__Metadata_Log__c WHERE Flosum__Process_Type__c = \'Deployment\' AND (' +
        '(Flosum__Completed_Date__c >= :fromUtc AND Flosum__Completed_Date__c < :toUtc) OR ' +
        '(Flosum__Completed_Date__c = null AND Flosum__Start_Date__c >= :fromUtc AND Flosum__Start_Date__c < :toUtc) OR ' +
        '(Flosum__Completed_Date__c = null AND Flosum__Start_Date__c = null AND CreatedDate >= :fromUtc AND CreatedDate < :toUtc))';
      if (organizationId != null)
        queryText += ' AND Flosum__Organisation__c = :organizationId';
      if (branchId != null)
        queryText += ' AND Flosum__Branch__c = :branchId';
      if (cursorId != null)
        queryText += ' AND (CreatedDate < :cursorCreated OR (CreatedDate = :cursorCreated AND Id < :cursorId))';
      queryText += ' ORDER BY CreatedDate DESC, Id DESC LIMIT 201';
      List<Flosum__Metadata_Log__c> source = Database.queryWithBinds(
        queryText,
        binds,
        AccessLevel.USER_MODE
      );
      Set<Id> orgIds = new Set<Id>();
      Set<String> requestIds = new Set<String>();
      for (Flosum__Metadata_Log__c item : source) {
        if (item.Flosum__Organisation__c != null)
          orgIds.add(item.Flosum__Organisation__c);
        if (!String.isBlank(item.Flosum__Async_Request_Id__c))
          requestIds.add(item.Flosum__Async_Request_Id__c);
      }
      List<DevSre_EnvironmentMapping__c> mappings = [
        SELECT
          Id,
          Organization__c,
          EnvironmentClass__c,
          ValidFrom__c,
          ValidTo__c
        FROM DevSre_EnvironmentMapping__c
        WHERE
          Organization__c IN :orgIds
          AND ValidFrom__c < :toUtc
          AND (ValidTo__c = NULL
          OR ValidTo__c > :fromUtc)
        WITH USER_MODE
        LIMIT 2001
      ];
      if (mappings.size() > 2000)
        throw new AuraHandledException(
          'Há muitas vigências. Refine a organização ou o período.'
        );
      // Repeated requests outside the requested period/page must also be signalled.
      List<Flosum__Metadata_Log__c> related = new List<Flosum__Metadata_Log__c>();
      if (!requestIds.isEmpty() && !orgIds.isEmpty()) {
        related = [
          SELECT Id, Flosum__Organisation__c, Flosum__Async_Request_Id__c
          FROM Flosum__Metadata_Log__c
          WHERE
            Flosum__Process_Type__c = 'Deployment'
            AND Flosum__Organisation__c IN :orgIds
            AND Flosum__Async_Request_Id__c IN :requestIds
          WITH USER_MODE
          LIMIT 501
        ];
      }
      Map<String, Integer> counts = new Map<String, Integer>();
      for (Flosum__Metadata_Log__c item : related) {
        String key = correlation(item);
        counts.put(key, (counts.containsKey(key) ? counts.get(key) : 0) + 1);
      }
      DeploymentPage page = new DeploymentPage();
      page.rows = new List<DeploymentRow>();
      page.hasMore = false;
      page.inspectedRows = 0;
      page.correlationIncomplete = related.size() > 500;
      for (Integer i = 0; i < Math.min(source.size(), 200); i++) {
        Flosum__Metadata_Log__c item = source[i];
        page.cursorCreated = item.CreatedDate;
        page.cursorId = item.Id;
        page.inspectedRows++;
        DeploymentRow row = evaluate(item, mappings);
        if (
          counts.containsKey(row.correlationKey) &&
          counts.get(row.correlationKey) > 1
        )
          row.quality += ' Requisição repetida: revisar correlação.';
        if (page.correlationIncomplete)
          row.quality += ' Verificação de duplicidade incompleta.';
        if (
          (String.isBlank(environmentClass) ||
          row.environmentClass == environmentClass) &&
          (String.isBlank(outcome) || row.outcome == outcome)
        )
          page.rows.add(row);
        if (page.rows.size() == 50) {
          page.hasMore = i + 1 < source.size();
          break;
        }
      }
      if (page.rows.size() < 50)
        page.hasMore = source.size() > 200;
      return page;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível consultar deployments com seu acesso atual.'
      );
    }
  }

  @TestVisible
  private static DeploymentRow evaluate(
    Flosum__Metadata_Log__c item,
    List<DevSre_EnvironmentMapping__c> mappings
  ) {
    DeploymentRow row = new DeploymentRow();
    row.id = item.Id;
    row.name = item.Name;
    row.createdAt = item.CreatedDate;
    row.organizationId = item.Flosum__Organisation__c;
    row.branchId = item.Flosum__Branch__c;
    row.organizationName = item.Flosum__Organisation__r == null
      ? null
      : item.Flosum__Organisation__r.Name;
    row.branchName = item.Flosum__Branch__r == null
      ? null
      : item.Flosum__Branch__r.Name;
    row.startedAt = item.Flosum__Start_Date__c;
    row.completedAt = item.Flosum__Completed_Date__c;
    row.environmentClass = 'UNKNOWN';
    row.quality = '';
    if (item.Flosum__Status__c == 'Did Not Run')
      row.outcome = 'NotRun';
    else if (item.Flosum__Job_Completed__c != true)
      row.outcome = 'Pending';
    else if (
      item.Flosum__Succeed__c == true &&
      item.Flosum__Is_Error__c == true
    )
      row.outcome = 'Partial';
    else if (
      item.Flosum__Status__c == 'Completed' &&
      item.Flosum__Succeed__c == true &&
      item.Flosum__Is_Error__c != true
    )
      row.outcome = 'Success';
    else if (item.Flosum__Succeed__c != true)
      row.outcome = 'Failed';
    else
      row.outcome = 'Unknown';
    Boolean validClock =
      row.completedAt != null &&
      (row.startedAt == null ||
      row.startedAt <= row.completedAt);
    if (row.completedAt == null)
      row.quality += 'Sem data de conclusão.';
    if (row.startedAt == null)
      row.quality += ' Sem data de início.';
    if (!validClock && row.completedAt != null)
      row.quality += ' Conclusão anterior ao início.';
    if (validClock && row.startedAt != null)
      row.durationSeconds =
        Decimal.valueOf(
          String.valueOf(row.completedAt.getTime() - row.startedAt.getTime())
        ) / 1000;
    Integer matches = 0;
    if (validClock && row.organizationId != null) {
      for (DevSre_EnvironmentMapping__c mapping : mappings) {
        if (
          mapping.Organization__c == row.organizationId &&
          mapping.ValidFrom__c <= row.completedAt &&
          (mapping.ValidTo__c == null ||
          row.completedAt < mapping.ValidTo__c)
        ) {
          matches++;
          row.environmentClass = mapping.EnvironmentClass__c;
        }
      }
    }
    if (matches == 0) {
      row.environmentClass = 'UNKNOWN';
      row.quality += ' Ambiente não identificado para a conclusão.';
    }
    if (matches > 1) {
      row.environmentClass = 'AMBIGUOUS';
      row.quality += ' Vigências ambíguas.';
    }
    if (item.Flosum__Parent_Log__c != null)
      row.quality += ' Log filho: revisar correlação.';
    if (String.isBlank(item.Flosum__Async_Request_Id__c))
      row.quality += ' Sem ID de requisição; identidade pelo log.';
    row.correlationKey = correlation(item);
    if (String.isBlank(row.quality))
      row.quality = 'Campos operacionais completos; cobertura DORA não certificada.';
    return row;
  }

  private static String correlation(Flosum__Metadata_Log__c item) {
    return String.valueOf(item.Flosum__Organisation__c) +
      ':' +
      (String.isBlank(item.Flosum__Async_Request_Id__c)
        ? String.valueOf(item.Id)
        : item.Flosum__Async_Request_Id__c);
  }
  private static void validateFilters(
    Datetime startAt,
    Datetime endAt,
    Id organizationId,
    Id branchId,
    String environmentClass,
    String outcome,
    Datetime cursorCreated,
    Id cursorId
  ) {
    if (
      startAt == null ||
      endAt == null ||
      endAt <= startAt ||
      endAt > startAt.addDays(366)
    )
      throw new AuraHandledException(
        'Informe um período UTC válido de até 366 dias.'
      );
    if (
      organizationId != null &&
      organizationId.getSObjectType() != Flosum__Organisation__c.SObjectType
    )
      throw new AuraHandledException('Organização inválida.');
    if (
      branchId != null &&
      branchId.getSObjectType() != Flosum__Branch__c.SObjectType
    )
      throw new AuraHandledException('Branch inválida.');
    if (
      !String.isBlank(environmentClass) &&
      !new Set<String>{ 'PROD', 'UAT', 'SIT', 'DEV', 'UNKNOWN', 'AMBIGUOUS' }
        .contains(environmentClass)
    )
      throw new AuraHandledException('Ambiente inválido.');
    if (
      !String.isBlank(outcome) &&
      !new Set<String>{
          'Success',
          'Failed',
          'Partial',
          'NotRun',
          'Pending',
          'Unknown'
        }
        .contains(outcome)
    )
      throw new AuraHandledException('Resultado inválido.');
    if (
      (cursorId == null) != (cursorCreated == null) ||
      (cursorId != null &&
      cursorId.getSObjectType() != Flosum__Metadata_Log__c.SObjectType)
    )
      throw new AuraHandledException('Cursor inválido.');
  }
}
