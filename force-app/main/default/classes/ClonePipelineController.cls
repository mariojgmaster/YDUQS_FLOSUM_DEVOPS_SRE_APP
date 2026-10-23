public with sharing class ClonePipelineController {
  private static final String PIPELINE_OBJECT = 'Flosum__Pipeline__c';
  private static final String STEP_OBJECT = 'Flosum__PipelineStep__c';
  private static final String PIPELINE_LOOKUP = 'Flosum__Pipeline__c';
  private static final String NEXT_ON_PASS = 'Flosum__Next_Step_Id_On_Pass__c';
  private static final String NEXT_ON_FAIL = 'Flosum__Next_Step_Id_On_Fail__c';
  private static final Integer MAX_NAME_LENGTH = 80;
  private static final Integer MAX_STEPS = 100;

  @TestVisible
  private static Boolean simulateFailureAfterParentInsert = false;

  public class Preview {
    @AuraEnabled
    public String sourceName { get; set; }
    @AuraEnabled
    public String suggestedName { get; set; }
    @AuraEnabled
    public Integer stepCount { get; set; }
    @AuraEnabled
    public Integer maxNameLength { get; set; }
    @AuraEnabled
    public List<StepPreview> steps { get; set; }
  }

  public class StepPreview {
    @AuraEnabled
    public Decimal stepNumber { get; set; }
    @AuraEnabled
    public String description { get; set; }
    @AuraEnabled
    public String action { get; set; }
  }

  public class CloneResult {
    @AuraEnabled
    public Id pipelineId { get; set; }
    @AuraEnabled
    public String pipelineName { get; set; }
    @AuraEnabled
    public Integer stepCount { get; set; }
  }

  private class ClonePipelineException extends Exception {
  }

  @AuraEnabled
  public static Preview getPreview(Id sourcePipelineId) {
    try {
      validateSourceId(sourcePipelineId);
      validateReadAccess();

      SObject source = queryPipeline(
        sourcePipelineId,
        new Set<String>{ 'Name' }
      );
      Integer stepCount = countSteps(sourcePipelineId);
      ensureSupportedStepCount(stepCount);

      String sourceName = (String) source.get('Name');
      Preview preview = new Preview();
      preview.sourceName = sourceName;
      preview.suggestedName = buildSuggestedName(sourceName);
      preview.stepCount = stepCount;
      preview.maxNameLength = MAX_NAME_LENGTH;
      preview.steps = getStepPreviews(sourcePipelineId);
      return preview;
    } catch (Exception exceptionValue) {
      throw toHandledException(exceptionValue);
    }
  }

  @AuraEnabled
  public static CloneResult clonePipeline(Id sourcePipelineId, String newName) {
    Savepoint savepointValue;
    try {
      validateSourceId(sourcePipelineId);
      String normalizedName = validateName(newName);
      validateReadAccess();
      validateCreateAccess();
      validateRelationshipFieldAccess();

      savepointValue = Database.setSavepoint();

      Set<String> pipelineFields = getCopyableFields(
        PIPELINE_OBJECT,
        new Set<String>{ 'Id', 'OwnerId', 'Name' }
      );
      SObject sourcePipeline = queryPipeline(sourcePipelineId, pipelineFields);
      SObject clonedPipeline = copyRecord(
        sourcePipeline,
        PIPELINE_OBJECT,
        pipelineFields
      );
      clonedPipeline.put('Name', normalizedName);
      insert as user clonedPipeline;

      if (simulateFailureAfterParentInsert) {
        throw new ClonePipelineException('Falha simulada durante a clonagem.');
      }

      Set<String> excludedStepFields = new Set<String>{
        'Id',
        'OwnerId',
        PIPELINE_LOOKUP,
        NEXT_ON_PASS,
        NEXT_ON_FAIL
      };
      Set<String> stepFields = getCopyableFields(
        STEP_OBJECT,
        excludedStepFields
      );
      List<SObject> sourceSteps = querySteps(sourcePipelineId, stepFields);
      ensureSupportedStepCount(sourceSteps.size());

      List<SObject> clonedSteps = new List<SObject>();
      for (SObject sourceStep : sourceSteps) {
        SObject clonedStep = copyRecord(sourceStep, STEP_OBJECT, stepFields);
        clonedStep.put(PIPELINE_LOOKUP, clonedPipeline.Id);
        clonedSteps.add(clonedStep);
      }

      if (!clonedSteps.isEmpty()) {
        insert as user clonedSteps;
        remapStepReferences(sourceSteps, clonedSteps);
      }

      CloneResult result = new CloneResult();
      result.pipelineId = clonedPipeline.Id;
      result.pipelineName = normalizedName;
      result.stepCount = clonedSteps.size();
      return result;
    } catch (Exception exceptionValue) {
      if (savepointValue != null) {
        Database.rollback(savepointValue);
      }
      throw toHandledException(exceptionValue);
    }
  }

  private static void validateSourceId(Id sourcePipelineId) {
    if (
      sourcePipelineId == null ||
      sourcePipelineId.getSObjectType() !=
      Schema.getGlobalDescribe().get(PIPELINE_OBJECT)
    ) {
      throw new ClonePipelineException('O Pipeline de origem é inválido.');
    }
  }

  private static String validateName(String newName) {
    String normalizedName = newName == null ? null : newName.trim();
    if (String.isBlank(normalizedName)) {
      throw new ClonePipelineException('Informe um nome para o novo Pipeline.');
    }
    if (normalizedName.length() > MAX_NAME_LENGTH) {
      throw new ClonePipelineException(
        'O nome do Pipeline deve ter no máximo 80 caracteres.'
      );
    }
    return normalizedName;
  }

  private static void validateReadAccess() {
    if (
      !objectDescribe(PIPELINE_OBJECT).isAccessible() ||
      !objectDescribe(STEP_OBJECT).isAccessible()
    ) {
      throw new ClonePipelineException(
        'Você não possui acesso aos dados necessários para clonar este Pipeline.'
      );
    }
  }

  private static void validateCreateAccess() {
    if (
      !objectDescribe(PIPELINE_OBJECT).isCreateable() ||
      !objectDescribe(STEP_OBJECT).isCreateable()
    ) {
      throw new ClonePipelineException(
        'Você não possui permissão para criar Pipelines e Pipeline Steps.'
      );
    }
  }

  private static void validateRelationshipFieldAccess() {
    Map<String, Schema.SObjectField> fields = fieldsFor(STEP_OBJECT);
    for (
      String fieldName : new List<String>{
        PIPELINE_LOOKUP,
        NEXT_ON_PASS,
        NEXT_ON_FAIL
      }
    ) {
      Schema.DescribeFieldResult fieldDescribe = fields.get(fieldName)
        .getDescribe();
      if (!fieldDescribe.isAccessible() || !fieldDescribe.isCreateable()) {
        throw new ClonePipelineException(
          'Você não possui acesso aos relacionamentos necessários para clonar os Steps.'
        );
      }
    }
  }

  private static Schema.DescribeSObjectResult objectDescribe(
    String objectName
  ) {
    return Schema.getGlobalDescribe().get(objectName).getDescribe();
  }

  private static Map<String, Schema.SObjectField> fieldsFor(String objectName) {
    return objectDescribe(objectName).fields.getMap();
  }

  private static Set<String> getCopyableFields(
    String objectName,
    Set<String> excludedFields
  ) {
    Set<String> result = new Set<String>();
    Set<String> excludedFieldsLowerCase = new Set<String>();
    for (String excludedField : excludedFields) {
      excludedFieldsLowerCase.add(excludedField.toLowerCase());
    }
    for (String fieldName : fieldsFor(objectName).keySet()) {
      Schema.DescribeFieldResult fieldDescribe = fieldsFor(objectName)
        .get(fieldName)
        .getDescribe();
      if (
        !excludedFieldsLowerCase.contains(fieldName.toLowerCase()) &&
        fieldDescribe.isAccessible() &&
        fieldDescribe.isCreateable() &&
        !fieldDescribe.isCalculated()
      ) {
        result.add(fieldName);
      }
    }
    return result;
  }

  private static SObject queryPipeline(
    Id sourcePipelineId,
    Set<String> requestedFields
  ) {
    Set<String> fields = new Set<String>{ 'Id', 'Name' };
    fields.addAll(requestedFields);
    String queryText =
      'SELECT ' +
      String.join(new List<String>(fields), ',') +
      ' FROM ' +
      PIPELINE_OBJECT +
      ' WHERE Id = :sourcePipelineId WITH USER_MODE LIMIT 1';
    List<SObject> records = Database.query(queryText);
    if (records.isEmpty()) {
      throw new ClonePipelineException(
        'O Pipeline de origem não foi encontrado ou não está acessível.'
      );
    }
    return records[0];
  }

  private static Integer countSteps(Id sourcePipelineId) {
    String queryText =
      'SELECT COUNT() FROM ' +
      STEP_OBJECT +
      ' WHERE ' +
      PIPELINE_LOOKUP +
      ' = :sourcePipelineId WITH USER_MODE';
    return Database.countQuery(queryText);
  }

  // Display-only projection: never expose fields the current user cannot read.
  // Missing optional fields are omitted without blocking an otherwise valid clone.
  private static List<StepPreview> getStepPreviews(Id sourcePipelineId) {
    Map<String, Schema.SObjectField> available = fieldsFor(STEP_OBJECT);
    List<String> optionalFields = new List<String>{
      'Flosum__Number__c',
      'Flosum__Description__c',
      'Flosum__Step__c'
    };
    List<String> readableFields = new List<String>();
    for (String fieldName : optionalFields) {
      if (
        available.containsKey(fieldName) &&
        available.get(fieldName).getDescribe().isAccessible()
      ) {
        readableFields.add(fieldName);
      }
    }

    String ordering = readableFields.contains('Flosum__Number__c')
      ? 'Flosum__Number__c NULLS LAST, CreatedDate, Id'
      : 'CreatedDate, Id';
    String queryText =
      'SELECT Id' +
      (readableFields.isEmpty() ? '' : ',' + String.join(readableFields, ',')) +
      ' FROM ' +
      STEP_OBJECT +
      ' WHERE ' +
      PIPELINE_LOOKUP +
      ' = :sourcePipelineId WITH USER_MODE ORDER BY ' +
      ordering +
      ' LIMIT 101';
    List<SObject> rows = Database.query(queryText);
    ensureSupportedStepCount(rows.size());

    List<StepPreview> result = new List<StepPreview>();
    for (SObject row : rows) {
      StepPreview step = new StepPreview();
      step.stepNumber = readableFields.contains('Flosum__Number__c')
        ? (Decimal) row.get('Flosum__Number__c')
        : null;
      step.description = readableFields.contains('Flosum__Description__c')
        ? (String) row.get('Flosum__Description__c')
        : null;
      step.action = readableFields.contains('Flosum__Step__c')
        ? (String) row.get('Flosum__Step__c')
        : null;
      result.add(step);
    }
    return result;
  }

  private static List<SObject> querySteps(
    Id sourcePipelineId,
    Set<String> requestedFields
  ) {
    Set<String> fields = new Set<String>{
      'Id',
      PIPELINE_LOOKUP,
      NEXT_ON_PASS,
      NEXT_ON_FAIL
    };
    fields.addAll(requestedFields);
    String queryText =
      'SELECT ' +
      String.join(new List<String>(fields), ',') +
      ' FROM ' +
      STEP_OBJECT +
      ' WHERE ' +
      PIPELINE_LOOKUP +
      ' = :sourcePipelineId WITH USER_MODE ORDER BY Flosum__Number__c NULLS LAST, CreatedDate, Id LIMIT 101';
    return Database.query(queryText);
  }

  private static SObject copyRecord(
    SObject source,
    String objectName,
    Set<String> fields
  ) {
    SObject target = Schema.getGlobalDescribe().get(objectName).newSObject();
    for (String fieldName : fields) {
      target.put(fieldName, source.get(fieldName));
    }
    return target;
  }

  private static void remapStepReferences(
    List<SObject> sourceSteps,
    List<SObject> clonedSteps
  ) {
    Map<Id, Id> clonedIdBySourceId = new Map<Id, Id>();
    for (Integer index = 0; index < sourceSteps.size(); index++) {
      clonedIdBySourceId.put(sourceSteps[index].Id, clonedSteps[index].Id);
    }

    List<SObject> stepsToUpdate = new List<SObject>();
    for (Integer index = 0; index < sourceSteps.size(); index++) {
      Id sourcePassId = (Id) sourceSteps[index].get(NEXT_ON_PASS);
      Id sourceFailId = (Id) sourceSteps[index].get(NEXT_ON_FAIL);
      Id clonedPassId = clonedIdBySourceId.get(sourcePassId);
      Id clonedFailId = clonedIdBySourceId.get(sourceFailId);
      if (clonedPassId != null || clonedFailId != null) {
        SObject updateRecord = Schema.getGlobalDescribe()
          .get(STEP_OBJECT)
          .newSObject(clonedSteps[index].Id);
        updateRecord.put(NEXT_ON_PASS, clonedPassId);
        updateRecord.put(NEXT_ON_FAIL, clonedFailId);
        stepsToUpdate.add(updateRecord);
      }
    }
    if (!stepsToUpdate.isEmpty()) {
      update as user stepsToUpdate;
    }
  }

  private static void ensureSupportedStepCount(Integer stepCount) {
    if (stepCount > MAX_STEPS) {
      throw new ClonePipelineException(
        'Este Pipeline possui mais de 100 Steps e não pode ser clonado por esta ação.'
      );
    }
  }

  private static String buildSuggestedName(String sourceName) {
    String baseName = String.isBlank(sourceName) ? 'Pipeline' : sourceName.trim();
    // A clone of a clone continues the same numbering sequence.
    Pattern copySuffix = Pattern.compile('(?i) - Cópia(?: [0-9]{1,4})?$');
    Matcher suffixMatcher = copySuffix.matcher(baseName);
    while (suffixMatcher.find()) {
      baseName = baseName.substring(0, suffixMatcher.start()).trim();
      suffixMatcher = copySuffix.matcher(baseName);
    }
    if (String.isBlank(baseName)) {
      baseName = 'Pipeline';
    }

    // Reserve room for " - Cópia 9999", keeping the prefix stable
    // while numbering new generations of the same Pipeline.
    Integer baseLimit = MAX_NAME_LENGTH - ' - Cópia 9999'.length();
    if (baseName.length() > baseLimit) {
      baseName = baseName.substring(0, baseLimit);
    }

    String copyPrefix = baseName + ' - Cópia';
    String nameFilter = baseName.replace('\\', '\\\\')
      .replace('%', '\\%')
      .replace('_', '\\_') + ' - Cópia%';
    String queryText = 'SELECT Name FROM ' + PIPELINE_OBJECT +
      ' WHERE Name LIKE :nameFilter WITH USER_MODE LIMIT 2001';
    List<SObject> existing = Database.query(queryText);
    if (existing.size() > 2000) {
      throw new ClonePipelineException(
        'Existem muitas cópias deste Pipeline. Informe um nome manualmente.'
      );
    }

    Integer highest = 0;
    for (SObject recordValue : existing) {
      String existingName = (String) recordValue.get('Name');
      if (String.isBlank(existingName) ||
          !existingName.toLowerCase().startsWith(copyPrefix.toLowerCase())) {
        continue;
      }
      String numericSuffix = existingName.substring(copyPrefix.length());
      if (numericSuffix == '') {
        highest = Math.max(highest, 1); // Legacy unnumbered clone.
      } else if (Pattern.matches(' [0-9]{1,4}', numericSuffix)) {
        highest = Math.max(
          highest, Integer.valueOf(numericSuffix.trim())
        );
      }
    }

    Integer nextNumber = highest + 1;
    if (nextNumber > 9999) {
      throw new ClonePipelineException(
        'Limite de numeração atingido. Informe um nome manualmente.'
      );
    }
    String ordinal = String.valueOf(nextNumber).leftPad(2, '0');
    return copyPrefix + ' ' + ordinal;
  }

  private static AuraHandledException toHandledException(
    Exception exceptionValue
  ) {
    String safeMessage = exceptionValue instanceof ClonePipelineException
      ? exceptionValue.getMessage()
      : 'Não foi possível clonar o Pipeline. Verifique suas permissões e os dados informados.';
    AuraHandledException handledException = new AuraHandledException(
      safeMessage
    );
    handledException.setMessage(safeMessage);
    return handledException;
  }
}
