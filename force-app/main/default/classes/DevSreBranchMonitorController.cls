/**
 * SPEC-006 M1: readonly, source-backed Branch directory and operational activity.
 * Metadata Log activity is NOT a DORA metric or proof of component deployment.
 */
public with sharing class DevSreBranchMonitorController {
  private static final Integer PAGE_SIZE = 30;
  private static final Integer SUMMARY_LIMIT = 500;

  public class BranchRow {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public Datetime modifiedAt { get; set; }
  }
  public class BranchPage {
    @AuraEnabled public List<BranchRow> rows { get; set; }
    @AuraEnabled public Boolean hasMore { get; set; }
    @AuraEnabled public String cursorName { get; set; }
    @AuraEnabled public Id cursorId { get; set; }
  }
  public class ActivityRow {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public Id branchId { get; set; }
    @AuraEnabled public String branchName { get; set; }
    @AuraEnabled public String processType { get; set; }
    @AuraEnabled public String outcome { get; set; }
    @AuraEnabled public Datetime startedAt { get; set; }
    @AuraEnabled public Datetime completedAt { get; set; }
    @AuraEnabled public Datetime createdAt { get; set; }
    @AuraEnabled public Decimal durationSeconds { get; set; }
  }
  public class Overview {
    @AuraEnabled public Boolean complete { get; set; }
    @AuraEnabled public Integer operations { get; set; }
    @AuraEnabled public Integer deployments { get; set; }
    @AuraEnabled public Integer validations { get; set; }
    @AuraEnabled public Integer activeBranches { get; set; }
    @AuraEnabled public Integer succeeded { get; set; }
    @AuraEnabled public Integer failed { get; set; }
    @AuraEnabled public List<ActivityRow> recent { get; set; }
  }
  public class BranchDetail {
    @AuraEnabled public Id id { get; set; }
    @AuraEnabled public String name { get; set; }
    @AuraEnabled public Datetime modifiedAt { get; set; }
    @AuraEnabled public List<ActivityRow> recent { get; set; }
    @AuraEnabled public Boolean hasMore { get; set; }
  }

  private static void requireRead() {
    if (!Schema.sObjectType.Flosum__Branch__c.isAccessible() ||
        !Schema.sObjectType.Flosum__Metadata_Log__c.isAccessible()) {
      throw new AuraHandledException('Permissão de leitura do Flosum indisponível.');
    }
  }
  private static void checkBranch(Id branchId) {
    if (branchId == null || branchId.getSObjectType() != Flosum__Branch__c.SObjectType)
      throw new AuraHandledException('Selecione uma Branch Flosum válida.');
  }
  @TestVisible private static String wildcard(String search) {
    String term = String.isBlank(search) ? '' : search.trim();
    if (term.length() > 80) throw new AuraHandledException('Busca limitada a 80 caracteres.');
    return '%' + term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%';
  }

  @AuraEnabled(cacheable=true)
  public static BranchPage listBranches(String search, String cursorName, Id cursorId) {
    requireRead();
    if ((cursorName == null) != (cursorId == null))
      throw new AuraHandledException('Cursor de paginação incompleto.');
    if (cursorName != null && cursorId.getSObjectType() != Flosum__Branch__c.SObjectType)
      throw new AuraHandledException('Cursor inválido.');
    if (cursorName != null && cursorName.length() > 255)
      throw new AuraHandledException('Cursor inválido.');
    String pattern = wildcard(search);
    try {
      Map<String,Object> binds = new Map<String,Object>{
        'pattern' => pattern, 'cursorName' => cursorName, 'cursorId' => cursorId
      };
      String soql = 'SELECT Id, Name, LastModifiedDate FROM Flosum__Branch__c WHERE Name LIKE :pattern';
      if (cursorId != null) soql += ' AND (Name > :cursorName OR (Name = :cursorName AND Id > :cursorId))';
      soql += ' ORDER BY Name ASC, Id ASC LIMIT 31';
      List<Flosum__Branch__c> data = Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
      BranchPage result = new BranchPage();
      result.rows = new List<BranchRow>();
      result.hasMore = data.size() > PAGE_SIZE;
      for (Integer i=0; i<Math.min(data.size(),PAGE_SIZE); i++) {
        Flosum__Branch__c source = data[i];
        BranchRow row = new BranchRow();
        row.id=source.Id; row.name=source.Name; row.modifiedAt=source.LastModifiedDate;
        result.rows.add(row);
        result.cursorName=row.name;
        result.cursorId=row.id;
      }
      return result;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível consultar as Branches acessíveis.');
    }
  }

  @TestVisible private static String resultFor(Flosum__Metadata_Log__c log) {
    if (log.Flosum__Status__c == 'Did Not Run') return 'Não executado';
    if (log.Flosum__Job_Completed__c != true) return 'Em andamento / desconhecido';
    if (log.Flosum__Succeed__c == true && log.Flosum__Is_Error__c != true)
      return 'Sucesso';
    if (log.Flosum__Is_Error__c == true && log.Flosum__Succeed__c == true)
      return 'Parcial';
    return log.Flosum__Succeed__c == false ? 'Falha' : 'Indeterminado';
  }
  private static ActivityRow toActivity(Flosum__Metadata_Log__c src, Map<Id,String> names) {
    ActivityRow row = new ActivityRow();
    row.id=src.Id; row.name=src.Name; row.branchId=src.Flosum__Branch__c;
    row.branchName=names.containsKey(row.branchId) ? names.get(row.branchId) : 'Branch não acessível';
    row.processType=String.isBlank(src.Flosum__Process_Type__c) ? 'Não informado' : src.Flosum__Process_Type__c;
    row.outcome=resultFor(src);
    row.startedAt=src.Flosum__Start_Date__c;
    row.completedAt=src.Flosum__Completed_Date__c;
    row.createdAt=src.CreatedDate;
    if (row.startedAt != null && row.completedAt != null && row.completedAt >= row.startedAt)
      row.durationSeconds=(row.completedAt.getTime()-row.startedAt.getTime())/1000.0;
    return row;
  }
  private static Map<Id,String> namesFor(List<Flosum__Metadata_Log__c> logs) {
    Set<Id> ids=new Set<Id>();
    for (Flosum__Metadata_Log__c log : logs)
      if (log.Flosum__Branch__c != null) ids.add(log.Flosum__Branch__c);
    Map<Id,String> names=new Map<Id,String>();
    if (!ids.isEmpty()) for (Flosum__Branch__c b : [
      SELECT Id, Name FROM Flosum__Branch__c WHERE Id IN :ids WITH USER_MODE
    ]) names.put(b.Id,b.Name);
    return names;
  }
  @AuraEnabled(cacheable=true)
  public static Overview getOverview(Integer days) {
    requireRead();
    if (days == null) days=30;
    if (days!=7 && days!=30 && days!=90)
      throw new AuraHandledException('Selecione 7, 30 ou 90 dias.');
    Datetime fromUtc=System.now().addDays(-days);
    try {
      List<Flosum__Metadata_Log__c> logs=[
        SELECT Id, Name, CreatedDate, Flosum__Branch__c,
               Flosum__Process_Type__c, Flosum__Status__c,
               Flosum__Job_Completed__c, Flosum__Succeed__c, Flosum__Is_Error__c,
               Flosum__Start_Date__c, Flosum__Completed_Date__c
        FROM Flosum__Metadata_Log__c WHERE CreatedDate>=:fromUtc
        WITH USER_MODE ORDER BY CreatedDate DESC, Id DESC LIMIT 501
      ];
      Overview page=new Overview();
      page.complete=logs.size()<=SUMMARY_LIMIT;
      page.recent=new List<ActivityRow>();
      List<Flosum__Metadata_Log__c> preview=new List<Flosum__Metadata_Log__c>();
      for (Integer i=0;i<Math.min(logs.size(),8);i++) preview.add(logs[i]);
      Map<Id,String> branchNames=namesFor(preview);
      for (Integer i=0;i<Math.min(logs.size(),8);i++)
        page.recent.add(toActivity(logs[i],branchNames));
      if (!page.complete) return page;
      page.operations=logs.size(); page.deployments=0; page.validations=0;
      page.succeeded=0; page.failed=0;
      Set<Id> touched=new Set<Id>();
      for (Flosum__Metadata_Log__c log : logs) {
        if (log.Flosum__Process_Type__c=='Deployment') page.deployments++;
        if (log.Flosum__Process_Type__c=='Validate') page.validations++;
        String outcome=resultFor(log);
        if (outcome=='Sucesso') page.succeeded++;
        if (outcome=='Falha') page.failed++;
        if (log.Flosum__Branch__c!=null) touched.add(log.Flosum__Branch__c);
      }
      page.activeBranches=touched.size();
      return page;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível consultar a atividade das Branches.');
    }
  }

  @AuraEnabled(cacheable=true)
  public static BranchDetail getBranchDetail(Id branchId) {
    checkBranch(branchId);
    requireRead();
    try {
      List<Flosum__Branch__c> branches=[
        SELECT Id, Name, LastModifiedDate FROM Flosum__Branch__c
        WHERE Id=:branchId WITH USER_MODE LIMIT 1
      ];
      if (branches.isEmpty())
        throw new AuraHandledException('Branch não encontrada ou sem acesso.');
      Datetime fromUtc=System.now().addDays(-90);
      List<Flosum__Metadata_Log__c> logs=[
        SELECT Id, Name, CreatedDate, Flosum__Branch__c,
               Flosum__Process_Type__c, Flosum__Status__c,
               Flosum__Job_Completed__c, Flosum__Succeed__c, Flosum__Is_Error__c,
               Flosum__Start_Date__c, Flosum__Completed_Date__c
        FROM Flosum__Metadata_Log__c
        WHERE Flosum__Branch__c=:branchId AND CreatedDate>=:fromUtc
        WITH USER_MODE ORDER BY CreatedDate DESC, Id DESC LIMIT 51
      ];
      BranchDetail detail=new BranchDetail();
      detail.id=branches[0].Id; detail.name=branches[0].Name;
      detail.modifiedAt=branches[0].LastModifiedDate;
      detail.recent=new List<ActivityRow>();
      detail.hasMore=logs.size()>50;
      Map<Id,String> names=new Map<Id,String>{branchId=>detail.name};
      for (Integer i=0;i<Math.min(logs.size(),50);i++)
        detail.recent.add(toActivity(logs[i], names));
      return detail;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException('Não foi possível consultar os detalhes desta Branch.');
    }
  }
}
