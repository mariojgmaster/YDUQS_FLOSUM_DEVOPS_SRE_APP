/**
 * SPEC-006 G2: read-only lookup by Flosum Component.Name and typed Branch relation.
 * Name is NOT asserted to be metadata FullName; History link is NOT a revision
 * or evidence that this component was deployed. No DML, no content access.
 */
public with sharing class DevSreComponentDescriberController {
    private static final Integer PAGE_SIZE = 25;
    private static final Integer HISTORY_SIZE = 20;

    public class ComponentRow {
        @AuraEnabled public Id id { get; set; }
        @AuraEnabled public String name { get; set; }
        @AuraEnabled public Id branchId { get; set; }
        @AuraEnabled public String branchName { get; set; }
        @AuraEnabled public Datetime createdAt { get; set; }
    }
    public class ComponentPage {
        @AuraEnabled public List<ComponentRow> rows { get; set; }
        @AuraEnabled public Boolean hasMore { get; set; }
        @AuraEnabled public String cursorName { get; set; }
        @AuraEnabled public Id cursorId { get; set; }
        @AuraEnabled public String identityLevel { get; set; }
    }
    public class HistoryRow {
        @AuraEnabled public Id id { get; set; }
        @AuraEnabled public Datetime createdAt { get; set; }
    }
    public class ComponentDetail {
        @AuraEnabled public ComponentRow component { get; set; }
        @AuraEnabled public List<HistoryRow> histories { get; set; }
        @AuraEnabled public Boolean historiesHasMore { get; set; }
        @AuraEnabled public String historyQuality { get; set; }
        @AuraEnabled public String deployEvidenceQuality { get; set; }
    }

    @TestVisible private static String likeTerm(String search) {
        if (String.isBlank(search) || search.trim().length() < 2)
            throw new AuraHandledException('Informe pelo menos 2 caracteres do nome do componente.');
        String term = search.trim();
        if (term.length() > 80)
            throw new AuraHandledException('Busca limitada a 80 caracteres.');
        return '%' + term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%';
    }
    @TestVisible private static void validateCursor(String name, Id recordId) {
        if ((name == null) != (recordId == null) ||
            (recordId != null && recordId.getSObjectType() != Flosum__Component__c.SObjectType) ||
            (name != null && name.length() > 255))
            throw new AuraHandledException('Cursor de componentes inválido.');
    }
    @TestVisible private static String typedForeignKey(
        Schema.SObjectType source, Schema.SObjectType target
    ) {
        List<String> matches = new List<String>();
        for (Schema.SObjectField sf : source.getDescribe().fields.getMap().values()) {
            Schema.DescribeFieldResult f = sf.getDescribe();
            if (f.getType() != Schema.DisplayType.REFERENCE || !f.isAccessible()) continue;
            if (f.getReferenceTo().contains(target) &&
                Pattern.matches('Flosum__[A-Za-z][A-Za-z0-9_]*__c', f.getName()))
                matches.add(f.getName());
        }
        if (matches.size() != 1)
            throw new AuraHandledException('Relação Flosum não disponível ou ambígua.');
        return matches[0];
    }
    private static String componentBranchField() {
        if (!Flosum__Component__c.SObjectType.getDescribe().isAccessible() ||
            !Flosum__Branch__c.SObjectType.getDescribe().isAccessible() ||
            !Flosum__Component__c.Name.getDescribe().isAccessible())
            throw new AuraHandledException('Acesso de leitura ao componente Flosum indisponível.');
        return typedForeignKey(Flosum__Component__c.SObjectType, Flosum__Branch__c.SObjectType);
    }
    private static Map<Id,String> branchNames(List<SObject> records, String branchField) {
        Set<Id> branchIds = new Set<Id>();
        for (SObject rec : records) {
            Id ref = (Id) rec.get(branchField);
            if (ref != null) branchIds.add(ref);
        }
        Map<Id,String> output = new Map<Id,String>();
        if (branchIds.isEmpty()) return output;
        for (Flosum__Branch__c branch : [
            SELECT Id, Name FROM Flosum__Branch__c WHERE Id IN :branchIds WITH USER_MODE
        ]) output.put(branch.Id, branch.Name);
        return output;
    }
    @TestVisible private static ComponentRow convert(SObject source, String branchField,
                                                      Map<Id,String> names) {
        ComponentRow row = new ComponentRow();
        row.id = (Id)source.get('Id');
        row.name = (String)source.get('Name');
        Id candidate = (Id)source.get(branchField);
        row.branchId = candidate != null && names.containsKey(candidate) ? candidate : null;
        row.branchName = candidate == null ? 'Sem Branch vinculada' :
            (row.branchId == null ? 'Branch não acessível' : names.get(candidate));
        row.createdAt = (Datetime)source.get('CreatedDate');
        return row;
    }
    @TestVisible private static ComponentPage toPage(List<SObject> data, String branchField,
                                                       Map<Id,String> names) {
        ComponentPage page = new ComponentPage();
        page.rows = new List<ComponentRow>();
        page.identityLevel = 'REGISTERED_NAME_ONLY';
        page.hasMore = data.size() > PAGE_SIZE;
        for (Integer i = 0; i < Math.min(PAGE_SIZE, data.size()); i++) {
            ComponentRow row = convert(data[i], branchField, names);
            page.rows.add(row);
            page.cursorId = row.id;
            page.cursorName = row.name;
        }
        return page;
    }

    @AuraEnabled(cacheable=true)
    public static ComponentPage searchComponents(String search, String cursorName, Id cursorId) {
        String pattern = likeTerm(search);
        validateCursor(cursorName, cursorId);
        String field = componentBranchField();
        try {
            Map<String,Object> binds = new Map<String,Object>{
                'pattern' => pattern, 'cursorName' => cursorName, 'cursorId' => cursorId
            };
            String query = 'SELECT Id, Name, CreatedDate, ' + field +
                ' FROM Flosum__Component__c WHERE Name LIKE :pattern';
            if (cursorId != null)
                query += ' AND (Name > :cursorName OR (Name = :cursorName AND Id > :cursorId))';
            query += ' ORDER BY Name ASC, Id ASC LIMIT 26';
            List<SObject> records = Database.queryWithBinds(query, binds, AccessLevel.USER_MODE);
            return toPage(records, field, branchNames(records, field));
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException('Não foi possível consultar os componentes Flosum acessíveis.');
        }
    }

    @TestVisible private static List<HistoryRow> toHistories(List<SObject> history) {
        List<HistoryRow> rows = new List<HistoryRow>();
        for (Integer i = 0; i < Math.min(HISTORY_SIZE, history.size()); i++) {
            HistoryRow row = new HistoryRow();
            row.id = (Id)history[i].get('Id');
            row.createdAt = (Datetime)history[i].get('CreatedDate');
            rows.add(row);
        }
        return rows;
    }

    @AuraEnabled(cacheable=true)
    public static ComponentDetail describeComponent(Id componentId) {
        if (componentId == null || componentId.getSObjectType() != Flosum__Component__c.SObjectType)
            throw new AuraHandledException('Selecione um componente Flosum válido.');
        String field = componentBranchField();
        try {
            List<SObject> records = Database.queryWithBinds(
                'SELECT Id, Name, CreatedDate, ' + field +
                ' FROM Flosum__Component__c WHERE Id = :componentId LIMIT 1',
                new Map<String,Object>{ 'componentId' => componentId },
                AccessLevel.USER_MODE
            );
            if (records.isEmpty())
                throw new AuraHandledException('Componente não encontrado ou sem acesso.');
            ComponentDetail detail = new ComponentDetail();
            detail.component = convert(records[0], field, branchNames(records, field));
            detail.histories = new List<HistoryRow>();
            detail.historiesHasMore = false;
            detail.historyQuality = 'UNAVAILABLE';
            detail.deployEvidenceQuality = 'UNVERIFIED';
            if (!Flosum__Component_History__c.SObjectType.getDescribe().isAccessible())
                return detail;
            String historyKey = typedForeignKey(
                Flosum__Component_History__c.SObjectType, Flosum__Component__c.SObjectType
            );
            List<SObject> history = Database.queryWithBinds(
                'SELECT Id, CreatedDate FROM Flosum__Component_History__c WHERE ' +
                historyKey + ' = :componentId ORDER BY CreatedDate DESC, Id DESC LIMIT 21',
                new Map<String,Object>{ 'componentId' => componentId },
                AccessLevel.USER_MODE
            );
            detail.historiesHasMore = history.size() > HISTORY_SIZE;
            detail.histories = toHistories(history);
            detail.historyQuality = 'TYPED_LINK_SAMPLE';
            return detail;
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException('Não foi possível consultar o histórico Flosum acessível.');
        }
    }
}
