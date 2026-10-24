/**
 * Consulta somente leitura de configurações de Pipeline Flosum.
 * NÃO representa execuções, deployments nem métricas DORA.
 */
public with sharing class DevSrePipelineMonitorController {
  private static final String PIPELINE_OBJECT = 'Flosum__Pipeline__c';
  private static final String STEP_OBJECT = 'Flosum__PipelineStep__c';
  private static final String PARENT_FIELD = 'Flosum__Pipeline__c';
  private static final Integer PIPELINE_PAGE_SIZE = 50;
  private static final Integer STEP_PAGE_SIZE = 100;
  private static final Integer MAX_SEARCH_LENGTH = 80;

  public class PipelineSummary {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
  }

  public class PipelinePage {
    @AuraEnabled public List<PipelineSummary> pipelines { get; set; }
    @AuraEnabled public Boolean hasMore { get; set; }
  }

  public class StepRow {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public Decimal stepNumber { get; set; }
    @AuraEnabled public String description { get; set; }
    @AuraEnabled public String action { get; set; }
    @AuraEnabled public Id nextOnPass { get; set; }
    @AuraEnabled public Id nextOnFail { get; set; }
  }

  public class PipelineDetail {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public List<StepRow> steps { get; set; }
    @AuraEnabled public Boolean hasMore { get; set; }
    @AuraEnabled public Boolean canReadNumber { get; set; }
    @AuraEnabled public Boolean canReadDescription { get; set; }
    @AuraEnabled public Boolean canReadAction { get; set; }
    @AuraEnabled public Boolean canReadPass { get; set; }
    @AuraEnabled public Boolean canReadFail { get; set; }
  }

  @AuraEnabled
  public static PipelinePage listPipelines(String searchTerm) {
    try {
      requirePipelineRead();
      String term = searchTerm == null ? '' : searchTerm.trim();
      if (term.length() > MAX_SEARCH_LENGTH) {
        throw new AuraHandledException('A pesquisa permite até 80 caracteres.');
      }

      Integer queryLimit = PIPELINE_PAGE_SIZE + 1;
      List<Flosum__Pipeline__c> records;
      if (String.isBlank(term)) {
        records = [
          SELECT Id, Name
          FROM Flosum__Pipeline__c
          WITH USER_MODE
          ORDER BY Name, Id
          LIMIT :queryLimit
        ];
      } else {
        String namePattern = '%' + term + '%';
        records = [
          SELECT Id, Name
          FROM Flosum__Pipeline__c
          WHERE Name LIKE :namePattern
          WITH USER_MODE
          ORDER BY Name, Id
          LIMIT :queryLimit
        ];
      }

      PipelinePage page = new PipelinePage();
      page.pipelines = new List<PipelineSummary>();
      page.hasMore = records.size() > PIPELINE_PAGE_SIZE;
      for (Integer i = 0; i < records.size() && i < PIPELINE_PAGE_SIZE; i++) {
        PipelineSummary row = new PipelineSummary();
        row.id = records[i].Id;
        row.name = records[i].Name;
        page.pipelines.add(row);
      }
      return page;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível consultar os Pipelines. Tente novamente.');
    }
  }

  @AuraEnabled
  public static PipelineDetail getPipelineDetail(Id pipelineId) {
    try {
      requirePipelineRead();
      requireStepRead();
      if (pipelineId == null || pipelineId.getSObjectType() != Schema.getGlobalDescribe().get(PIPELINE_OBJECT)) {
        throw new AuraHandledException('Pipeline inválido ou indisponível.');
      }

      List<Flosum__Pipeline__c> parents = [
        SELECT Id, Name
        FROM Flosum__Pipeline__c
        WHERE Id = :pipelineId
        WITH USER_MODE
        LIMIT 1
      ];
      if (parents.isEmpty()) {
        throw new AuraHandledException('Pipeline inválido ou indisponível.');
      }

      Map<String, Schema.SObjectField> fields = Schema.getGlobalDescribe().get(STEP_OBJECT).getDescribe().fields.getMap();
      List<String> optionalFields = new List<String>{
        'Flosum__Number__c',
        'Flosum__Description__c',
        'Flosum__Step__c',
        'Flosum__Next_Step_Id_On_Pass__c',
        'Flosum__Next_Step_Id_On_Fail__c'
      };
      List<String> selectedFields = new List<String>{ 'Id' };
      Set<String> readableFields = new Set<String>();
      for (String fieldName : optionalFields) {
        if (fields.containsKey(fieldName) && fields.get(fieldName).getDescribe().isAccessible()) {
          readableFields.add(fieldName);
          selectedFields.add(fieldName);
        }
      }
      String orderBy = readableFields.contains('Flosum__Number__c')
        ? 'Flosum__Number__c NULLS LAST, Id'
        : 'Id';
      Integer queryLimit = STEP_PAGE_SIZE + 1;
      String queryText =
        'SELECT ' + String.join(selectedFields, ',') +
        ' FROM ' + STEP_OBJECT +
        ' WHERE ' + PARENT_FIELD + ' = :pipelineId' +
        ' WITH USER_MODE ORDER BY ' + orderBy +
        ' LIMIT :queryLimit';
      List<SObject> records = Database.query(queryText);

      PipelineDetail result = new PipelineDetail();
      result.id = parents[0].Id;
      result.name = parents[0].Name;
      result.steps = new List<StepRow>();
      result.hasMore = records.size() > STEP_PAGE_SIZE;
      result.canReadNumber = readableFields.contains('Flosum__Number__c');
      result.canReadDescription = readableFields.contains('Flosum__Description__c');
      result.canReadAction = readableFields.contains('Flosum__Step__c');
      result.canReadPass = readableFields.contains('Flosum__Next_Step_Id_On_Pass__c');
      result.canReadFail = readableFields.contains('Flosum__Next_Step_Id_On_Fail__c');

      for (Integer i = 0; i < records.size() && i < STEP_PAGE_SIZE; i++) {
        SObject recordValue = records[i];
        StepRow row = new StepRow();
        row.id = (Id) recordValue.get('Id');
        row.stepNumber = result.canReadNumber ? (Decimal) recordValue.get('Flosum__Number__c') : null;
        row.description = result.canReadDescription ? (String) recordValue.get('Flosum__Description__c') : null;
        row.action = result.canReadAction ? (String) recordValue.get('Flosum__Step__c') : null;
        row.nextOnPass = result.canReadPass ? (Id) recordValue.get('Flosum__Next_Step_Id_On_Pass__c') : null;
        row.nextOnFail = result.canReadFail ? (Id) recordValue.get('Flosum__Next_Step_Id_On_Fail__c') : null;
        result.steps.add(row);
      }
      return result;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível carregar a estrutura do Pipeline.');
    }
  }

  private static void requirePipelineRead() {
    Schema.SObjectType obj = Schema.getGlobalDescribe().get(PIPELINE_OBJECT);
    if (obj == null || !obj.getDescribe().isAccessible()
      || !obj.getDescribe().fields.getMap().get('Name').getDescribe().isAccessible()) {
      throw new AuraHandledException('Você não possui acesso aos Pipelines.');
    }
  }

  private static void requireStepRead() {
    Schema.SObjectType obj = Schema.getGlobalDescribe().get(STEP_OBJECT);
    if (obj == null || !obj.getDescribe().isAccessible()) {
      throw new AuraHandledException('Você não possui acesso aos Pipeline Steps.');
    }
    Map<String, Schema.SObjectField> fields = obj.getDescribe().fields.getMap();
    if (!fields.containsKey(PARENT_FIELD) || !fields.get(PARENT_FIELD).getDescribe().isAccessible()) {
      throw new AuraHandledException('Você não possui acesso aos relacionamentos dos Steps.');
    }
  }
}
