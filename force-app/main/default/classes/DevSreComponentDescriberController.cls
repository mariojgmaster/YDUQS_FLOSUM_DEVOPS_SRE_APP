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
        @AuraEnabled public String componentName { get; set; }
        @AuraEnabled public String source { get; set; }
        @AuraEnabled public String sourceDetails { get; set; }
        @AuraEnabled public String version { get; set; }
        @AuraEnabled public Datetime changedOn { get; set; }
        @AuraEnabled public Datetime committedOn { get; set; }
        @AuraEnabled public Id branchId { get; set; }
        @AuraEnabled public String branchName { get; set; }
        @AuraEnabled public String componentType { get; set; }
        @AuraEnabled public Datetime createdAt { get; set; }
    }
    public class ComponentPage {
        @AuraEnabled public List<ComponentRow> rows { get; set; }
        @AuraEnabled public Boolean hasMore { get; set; }
        @AuraEnabled public String cursorName { get; set; }
        @AuraEnabled public Id cursorId { get; set; }
        @AuraEnabled public String identityLevel { get; set; }
    }
    public class ComponentTypeOption {
        @AuraEnabled public String label { get; set; }
        @AuraEnabled public String value { get; set; }
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
    private static String textField(SObject source, String name) {
        Object v = source.get(name);
        return v == null ? null : String.valueOf(v);
    }
    private static void decorate(ComponentRow row, SObject source) {
        row.componentName = textField(source, 'Flosum__Component_Name__c');
        row.source = textField(source, 'Flosum__Source__c');
        row.sourceDetails = textField(source, 'Flosum__Source_Details__c');
        row.version = textField(source, 'Flosum__Version__c');
        row.changedOn = (Datetime)source.get('Flosum__Last_Modified_Date__c');
        row.committedOn = (Datetime)source.get('Flosum__Committed_On__c');
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

    @TestVisible private static String searchQuery(String field, Boolean hasCursor) {
        if (!Pattern.matches('Flosum__[A-Za-z][A-Za-z0-9_]*__c',field))
            throw new AuraHandledException('Relação de Branch inválida.');
        String query = 'SELECT Id, Name, CreatedDate, ' + field +
            ' FROM Flosum__Component__c WHERE Name LIKE :pattern';
        if (hasCursor)
            query += ' AND (Name > :cursorName OR (Name = :cursorName AND Id > :cursorId))';
        return query + ' ORDER BY Name ASC, Id ASC LIMIT 26';
    }
    @TestVisible private static String historyQuery(String field) {
        if (!Pattern.matches('Flosum__[A-Za-z][A-Za-z0-9_]*__c',field))
            throw new AuraHandledException('Relação de histórico inválida.');
        return 'SELECT Id, CreatedDate FROM Flosum__Component_History__c WHERE ' +
            field + ' = :componentId ORDER BY CreatedDate DESC, Id DESC LIMIT 21';
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
            String query = searchQuery(field,cursorId != null);
            List<SObject> records = Database.queryWithBinds(query, binds, AccessLevel.USER_MODE);
            return toPage(records, field, branchNames(records, field));
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException('Não foi possível consultar os componentes Flosum acessíveis.');
        }
    }

    /**
     * Select the unique readable Flosum Component Type picklist by described API name.
     * The DevSreFeat schema inventory confirmed 1 picklist and 1 unrelated reference.
     */
    @TestVisible private static Schema.DescribeFieldResult typeDescribe() {
        List<Schema.DescribeFieldResult> matches = new List<Schema.DescribeFieldResult>();
        for (Schema.SObjectField sf : Flosum__Component__c.SObjectType.getDescribe().fields.getMap().values()) {
            Schema.DescribeFieldResult field = sf.getDescribe();
            String api = field.getName().toLowerCase();
            if (field.getType() == Schema.DisplayType.PICKLIST && field.isAccessible() &&
                api.startsWith('flosum__') && api.contains('component') && api.contains('type') &&
                Pattern.matches('Flosum__[A-Za-z][A-Za-z0-9_]*__c',field.getName()))
                matches.add(field);
        }
        if (matches.size()!=1)
            throw new AuraHandledException('Campo Component Type não disponível ou ambíguo.');
        return matches[0];
    }

    @AuraEnabled(cacheable=true)
    public static List<ComponentTypeOption> getComponentTypes(String searchTerm) {
        if (searchTerm != null && searchTerm.length() > 80)
            throw new AuraHandledException('Pesquisa de tipos limitada a 80 caracteres.');
        String term = String.isBlank(searchTerm) ? '' : searchTerm.trim().toLowerCase();
        List<ComponentTypeOption> output = new List<ComponentTypeOption>();
        for (Schema.PicklistEntry entry : typeDescribe().getPicklistValues()) {
            if (!entry.isActive()) continue;
            if (!entry.getLabel().toLowerCase().contains(term) &&
                !entry.getValue().toLowerCase().contains(term)) continue;
            ComponentTypeOption item = new ComponentTypeOption();
            item.label = entry.getLabel();
            item.value = entry.getValue();
            output.add(item);
            if (output.size() >= 20) break;
        }
        return output;
    }

    @TestVisible private static void validateTypeValue(String candidate) {
        if (candidate == null) return;
        if (candidate.length() > 255) throw new AuraHandledException('Tipo de componente inválido.');
        for (Schema.PicklistEntry entry : typeDescribe().getPicklistValues()) {
            if (entry.isActive() && entry.getValue() == candidate) return;
        }
        throw new AuraHandledException('Selecione um Component Type válido.');
    }

    @TestVisible private static String filteredQuery(String branchField, String typeField,
                Boolean hasName, Boolean hasType, Boolean hasCursor) {
        if (!Pattern.matches('Flosum__[A-Za-z][A-Za-z0-9_]*__c',branchField) ||
            !Pattern.matches('Flosum__[A-Za-z][A-Za-z0-9_]*__c',typeField))
            throw new AuraHandledException('Campo de filtro inválido.');
        String query = 'SELECT Id, Name, CreatedDate, ' + branchField + ', ' + typeField +
            ', Flosum__Component_Name__c, Flosum__Version__c, Flosum__Source__c,' +
            ' Flosum__Source_Details__c, Flosum__Last_Modified_Date__c, Flosum__Committed_On__c' +
            ' FROM Flosum__Component__c';
        List<String> conditions = new List<String>();
        if (hasName) conditions.add('Flosum__Component_Name__c LIKE :pattern');
        if (hasType) conditions.add(typeField + ' = :typeValue');
        if (hasCursor)
            conditions.add('(Name > :cursorName OR (Name = :cursorName AND Id > :cursorId))');
        if (!conditions.isEmpty()) query += ' WHERE ' + String.join(conditions,' AND ');
        return query + ' ORDER BY Name ASC, Id ASC LIMIT 26';
    }

    @AuraEnabled(cacheable=true)
    public static ComponentPage searchFilteredComponents(
        String search, String componentType, String cursorName, Id cursorId
    ) {
        validateCursor(cursorName, cursorId);
        String branchField = componentBranchField();
        String typeField = typeDescribe().getName();
        String pattern = String.isBlank(search) ? null : likeTerm(search);
        String typeValue = String.isBlank(componentType) ? null : componentType;
        validateTypeValue(typeValue);
        try {
            String query = filteredQuery(branchField,typeField,
                pattern!=null,typeValue!=null,cursorId!=null);
            List<SObject> records = Database.queryWithBinds(
                query,
                new Map<String,Object>{
                    'pattern'=>pattern, 'typeValue'=>typeValue,
                    'cursorName'=>cursorName, 'cursorId'=>cursorId
                },
                AccessLevel.USER_MODE
            );
            ComponentPage page = toPage(records, branchField, branchNames(records,branchField));
            for (Integer i=0; i<page.rows.size(); i++) {
                page.rows[i].componentType = (String)records[i].get(typeField);
                decorate(page.rows[i], records[i]);
            }
            return page;
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException('Não foi possível consultar o inventário Flosum acessível.');
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

    @TestVisible private static ComponentDetail buildDetail(
        SObject source, String branchField, Map<Id,String> branchNamesById,
        List<SObject> history, Boolean available
    ) {
        ComponentDetail result = new ComponentDetail();
        result.component = convert(source,branchField,branchNamesById);
        result.histories = available ? toHistories(history) : new List<HistoryRow>();
        result.historiesHasMore = available && history.size() > HISTORY_SIZE;
        result.historyQuality = available ? 'TYPED_LINK_SAMPLE' : 'UNAVAILABLE';
        result.deployEvidenceQuality = 'UNVERIFIED';
        return result;
    }

    /**
     * On-demand read-only ZIP browser. Caller must have Attachment and History
     * access in USER_MODE; no ZIP bytes are cached or written to Salesforce.
     */
    @AuraEnabled
    public static DevSreHistoryArchiveReader.ArchiveView inspectHistoryArchive(
        Id historyId, String entryPath
    ) {
        return DevSreHistoryArchiveReader.inspect(historyId, entryPath);
    }

    @AuraEnabled(cacheable=true)
    public static ComponentDetail describeComponent(Id componentId) {
        if (componentId == null || componentId.getSObjectType() != Flosum__Component__c.SObjectType)
            throw new AuraHandledException('Selecione um componente Flosum válido.');
        String field = componentBranchField();
        String typeField = typeDescribe().getName();
        try {
            List<SObject> records = Database.queryWithBinds(
                'SELECT Id, Name, CreatedDate, ' + field + ', ' + typeField +
                ', Flosum__Component_Name__c, Flosum__Version__c, Flosum__Source__c,' +
                ' Flosum__Source_Details__c, Flosum__Last_Modified_Date__c, Flosum__Committed_On__c' +
                ' FROM Flosum__Component__c WHERE Id = :componentId LIMIT 1',
                new Map<String,Object>{ 'componentId' => componentId },
                AccessLevel.USER_MODE
            );
            if (records.isEmpty())
                throw new AuraHandledException('Componente não encontrado ou sem acesso.');
            Map<Id,String> accessibleBranches = branchNames(records, field);
            if (!Flosum__Component_History__c.SObjectType.getDescribe().isAccessible()) {
                ComponentDetail unavailable = buildDetail(records[0],field,accessibleBranches,
                    new List<SObject>(),false);
                unavailable.component.componentType = (String)records[0].get(typeField);
                decorate(unavailable.component, records[0]);
                return unavailable;
            }
            String historyKey = typedForeignKey(
                Flosum__Component_History__c.SObjectType, Flosum__Component__c.SObjectType
            );
            List<SObject> history = Database.queryWithBinds(
                historyQuery(historyKey),
                new Map<String,Object>{ 'componentId' => componentId },
                AccessLevel.USER_MODE
            );
            ComponentDetail details = buildDetail(records[0],field,accessibleBranches,history,true);
            details.component.componentType = (String)records[0].get(typeField);
            decorate(details.component, records[0]);
            return details;
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException('Não foi possível consultar o histórico Flosum acessível.');
        }
    }

    /**
     * V3.6-B: bounded contextual view of Metadata Logs of this Component's
     * *accessible Branch*. A Branch log does NOT establish Component membership
     * in a deployment. No log-to-component inference or DORA classification.
     */
    public class BranchLogRow {
        @AuraEnabled public Id id { get; set; }
        @AuraEnabled public String processType { get; set; }
        @AuraEnabled public String sourceStatus { get; set; }
        @AuraEnabled public Datetime startedAt { get; set; }
        @AuraEnabled public Datetime completedAt { get; set; }
        @AuraEnabled public Boolean hasOrganisation { get; set; }
        @AuraEnabled public String evidenceCode { get; set; }
        @AuraEnabled public String evidenceLabel { get; set; }
    }

    public class BranchLogContext {
        @AuraEnabled public String sourceQuality { get; set; }
        @AuraEnabled public String branchName { get; set; }
        @AuraEnabled public List<BranchLogRow> rows { get; set; }
        @AuraEnabled public Boolean hasMore { get; set; }
        @AuraEnabled public Boolean componentMembershipVerified { get; set; }
    }

    @TestVisible private static String branchLogQuery() {
        // Static, schema-verified fields from flosum-source-contract.md.
        // Branch is the main typed lookup; Source_Branch is not equivalent.
        return 'SELECT Id, Flosum__Process_Type__c, Flosum__Status__c, ' +
            'Flosum__Job_Completed__c, Flosum__Succeed__c, Flosum__Is_Error__c, ' +
            'Flosum__Start_Date__c, Flosum__Completed_Date__c, Flosum__Organisation__c ' +
            'FROM Flosum__Metadata_Log__c WHERE Flosum__Branch__c = :branchId ' +
            'ORDER BY CreatedDate DESC, Id DESC LIMIT 11';
    }

    @TestVisible private static BranchLogRow summarizeBranchLog(SObject source) {
        BranchLogRow row = new BranchLogRow();
        row.id = (Id)source.get('Id');
        row.processType = textField(source, 'Flosum__Process_Type__c');
        row.sourceStatus = textField(source, 'Flosum__Status__c');
        row.startedAt = (Datetime)source.get('Flosum__Start_Date__c');
        row.completedAt = (Datetime)source.get('Flosum__Completed_Date__c');
        row.hasOrganisation = source.get('Flosum__Organisation__c') != null;
        // Success on a log is only a CANDIDATE, never per-Component deploy proof.
        Boolean eligible = row.processType == 'Deployment' && row.sourceStatus == 'Completed' &&
            source.get('Flosum__Job_Completed__c') == true &&
            source.get('Flosum__Succeed__c') == true &&
            source.get('Flosum__Is_Error__c') == false &&
            row.completedAt != null &&
            (row.startedAt == null || row.startedAt <= row.completedAt) &&
            row.hasOrganisation;
        row.evidenceCode = eligible ? 'BRANCH_DEPLOY_CANDIDATE' : 'NOT_CERTIFIED';
        row.evidenceLabel = eligible ? 'Sucesso registrado no log da Branch' :
            'Operação sem sucesso de deploy certificado';
        return row;
    }

    @AuraEnabled(cacheable=true)
    public static BranchLogContext getBranchLogContext(Id componentId) {
        if (componentId == null || componentId.getSObjectType() != Flosum__Component__c.SObjectType)
            throw new AuraHandledException('Selecione um Component Flosum válido.');
        String branchField = componentBranchField();
        BranchLogContext context = new BranchLogContext();
        context.rows = new List<BranchLogRow>();
        context.hasMore = false;
        context.componentMembershipVerified = false;
        try {
            List<SObject> components = Database.queryWithBinds(
                'SELECT Id, ' + branchField + ' FROM Flosum__Component__c ' +
                'WHERE Id = :componentId LIMIT 1',
                new Map<String,Object>{'componentId' => componentId}, AccessLevel.USER_MODE);
            if (components.isEmpty())
                throw new AuraHandledException('Componente não encontrado ou sem acesso.');
            Id branchId = (Id)components[0].get(branchField);
            if (branchId == null) {
                context.sourceQuality = 'NO_ACCESSIBLE_BRANCH';
                return context;
            }
            // Confirm that the linked Branch is accessible, not merely stored.
            List<Flosum__Branch__c> branches = [
                SELECT Id, Name FROM Flosum__Branch__c WHERE Id = :branchId WITH USER_MODE LIMIT 1
            ];
            if (branches.isEmpty()) {
                context.sourceQuality = 'NO_ACCESSIBLE_BRANCH';
                return context;
            }
            context.branchName = branches[0].Name;
            if (!Flosum__Metadata_Log__c.SObjectType.getDescribe().isAccessible())
                throw new AuraHandledException('Sem permissão de consulta aos Metadata Logs.');
            List<SObject> logs = Database.queryWithBinds(branchLogQuery(),
                new Map<String,Object>{'branchId' => branchId}, AccessLevel.USER_MODE);
            context.hasMore = logs.size() > 10;
            for (Integer i = 0; i < Math.min(10, logs.size()); i++)
                context.rows.add(summarizeBranchLog(logs[i]));
            context.sourceQuality = 'BRANCH_LOG_SAMPLE';
            return context;
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException(
                'Não foi possível consultar os logs da Branch com as permissões atuais.');
        }
    }

}
