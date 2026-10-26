@IsTest
private class DevSreComponentDescriberTest {
    @IsTest static void boundedSearchAndTypedRelationDiscovery() {
        System.assertEquals('%Flow\\_Calc%', DevSreComponentDescriberController.likeTerm('Flow_Calc'));
        try { DevSreComponentDescriberController.likeTerm(' '); System.assert(false); }
        catch (AuraHandledException expected) {}
        try { DevSreComponentDescriberController.likeTerm('a'); System.assert(false); }
        catch (AuraHandledException expected) {}
        try { DevSreComponentDescriberController.likeTerm(
            'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdef'); System.assert(false); }
        catch (AuraHandledException expected) {}
        try { DevSreComponentDescriberController.validateCursor('x',null); System.assert(false); }
        catch (AuraHandledException expected) {}
        try { DevSreComponentDescriberController.validateCursor(
            null,UserInfo.getUserId()); System.assert(false); }
        catch (AuraHandledException expected) {}
        System.assertNotEquals(null,DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component__c.SObjectType,Flosum__Branch__c.SObjectType));
        System.assertNotEquals(null,DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component_History__c.SObjectType,Flosum__Component__c.SObjectType));
    }
    @IsTest static void emptyQueryAndInvalidDetailUseRealObjects() {
        Test.startTest();
        DevSreComponentDescriberController.ComponentPage page =
            DevSreComponentDescriberController.searchComponents('BM_M2_nonexistent_999',null,null);
        Test.stopTest();
        System.assertEquals(0,page.rows.size());
        System.assertEquals(false,page.hasMore);
        System.assertEquals('REGISTERED_NAME_ONLY',page.identityLevel);
        try {
            DevSreComponentDescriberController.describeComponent(UserInfo.getUserId());
            System.assert(false);
        } catch (AuraHandledException expected) {}
        try {
            DevSreComponentDescriberController.searchComponents('Flow', 'Flow', null);
            System.assert(false);
        } catch (AuraHandledException expected) {}
    }
    @IsTest static void paginatedRowsKeepDistinctComponentIdsAndAccessibleBranchesOnly() {
        String cp = Flosum__Component__c.SObjectType.getDescribe().getKeyPrefix();
        String bp = Flosum__Branch__c.SObjectType.getDescribe().getKeyPrefix();
        Id branchId=(Id)(bp+'000000000001');
        String foreign=DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component__c.SObjectType,Flosum__Branch__c.SObjectType);
        List<SObject> records=new List<SObject>();
        for(Integer i=1;i<=26;i++) {
            Flosum__Component__c row = new Flosum__Component__c();
            String suffix=String.valueOf(i).leftPad(12,'0');
            row.put('Id',(Id)(cp+suffix));
            row.put(foreign,branchId);
            records.add(row);
        }
        Map<Id,String> names=new Map<Id,String>{branchId=>'integration'};
        DevSreComponentDescriberController.ComponentPage page =
            DevSreComponentDescriberController.toPage(records,foreign,names);
        System.assertEquals(25,page.rows.size());
        System.assertEquals(true,page.hasMore);
        System.assertEquals(null,page.cursorName);
        System.assertEquals('integration',page.rows[0].branchName);
        System.assertEquals(branchId,page.rows[0].branchId);
        System.assertNotEquals(page.rows[0].id,page.rows[1].id);
        DevSreComponentDescriberController.ComponentRow inaccessible =
            DevSreComponentDescriberController.convert(records[0],foreign,
                                                        new Map<Id,String>());
        System.assertEquals(null,inaccessible.branchId);
        System.assertEquals('Branch não acessível',inaccessible.branchName);
    }
    @IsTest static void detailBuildRetainsVerifiedLinkAndSeparatesUnavailableHistory() {
        String componentPrefix=Flosum__Component__c.SObjectType.getDescribe().getKeyPrefix();
        String branchPrefix=Flosum__Branch__c.SObjectType.getDescribe().getKeyPrefix();
        String historyPrefix=Flosum__Component_History__c.SObjectType.getDescribe().getKeyPrefix();
        Id componentId=(Id)(componentPrefix+'000000000001');
        Id branchId=(Id)(branchPrefix+'000000000001');
        String foreign=DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component__c.SObjectType,Flosum__Branch__c.SObjectType);
        Flosum__Component__c component=new Flosum__Component__c();
        component.put('Id',componentId);
        component.put(foreign,branchId);
        List<SObject> histories=new List<SObject>();
        for(Integer i=1;i<=21;i++) {
            Flosum__Component_History__c history=new Flosum__Component_History__c();
            history.put('Id',(Id)(historyPrefix+String.valueOf(i).leftPad(12,'0')));
            histories.add(history);
        }
        DevSreComponentDescriberController.ComponentDetail detail =
            DevSreComponentDescriberController.buildDetail(component,foreign,
                new Map<Id,String>{branchId=>'SIT'},histories,true);
        System.assertEquals(20,detail.histories.size());
        System.assertEquals(true,detail.historiesHasMore);
        System.assertEquals('TYPED_LINK_SAMPLE',detail.historyQuality);
        System.assertEquals('UNVERIFIED',detail.deployEvidenceQuality);
        System.assertEquals(componentId,detail.component.id);
        System.assertEquals('SIT',detail.component.branchName);

        DevSreComponentDescriberController.ComponentDetail unavailable =
            DevSreComponentDescriberController.buildDetail(component,foreign,
                new Map<Id,String>(),histories,false);
        System.assertEquals('UNAVAILABLE',unavailable.historyQuality);
        System.assertEquals(0,unavailable.histories.size());
        System.assertEquals(false,unavailable.historiesHasMore);
        System.assertEquals(null,unavailable.component.branchId);
    }
    @IsTest static void validMissingComponentAndValidCursorDoNotReturnFakeData() {
        String prefix=Flosum__Component__c.SObjectType.getDescribe().getKeyPrefix();
        Id unavailable=(Id)(prefix+'000000000001');
        Test.startTest();
        DevSreComponentDescriberController.ComponentPage result =
            DevSreComponentDescriberController.searchComponents('BM_M2_nonexistent_999',
                'BM_M2_nonexistent_999',unavailable);
        Test.stopTest();
        System.assertEquals(0,result.rows.size());
        try {
            DevSreComponentDescriberController.describeComponent(unavailable);
            System.assert(false,'An absent component cannot be described');
        } catch(AuraHandledException expected) {}
    }

    @IsTest static void checkedQueriesAndBoundaryExceptions() {
        String branchField=DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component__c.SObjectType,Flosum__Branch__c.SObjectType);
        String historyField=DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component_History__c.SObjectType,Flosum__Component__c.SObjectType);
        String base=DevSreComponentDescriberController.searchQuery(branchField,false);
        String paginated=DevSreComponentDescriberController.searchQuery(branchField,true);
        System.assert(base.contains('ORDER BY Name ASC, Id ASC LIMIT 26'));
        System.assert(!base.contains('Name > :cursorName'));
        System.assert(paginated.contains('Name > :cursorName'));
        System.assert(paginated.contains('Id > :cursorId'));
        System.assert(DevSreComponentDescriberController.historyQuery(historyField).contains(
            'ORDER BY CreatedDate DESC, Id DESC LIMIT 21'));
        for (String candidate : new List<String>{'Name','Bad Field','Flosum__Invalid__r'}) {
            try {
                DevSreComponentDescriberController.searchQuery(candidate,false);
                System.assert(false,'Unexpected search query field');
            } catch(AuraHandledException expected) {}
            try {
                DevSreComponentDescriberController.historyQuery(candidate);
                System.assert(false,'Unexpected history query field');
            } catch(AuraHandledException expected) {}
        }
        try {
            DevSreComponentDescriberController.typedForeignKey(
                Flosum__Component__c.SObjectType,User.SObjectType);
            System.assert(false,'No typed Component to User link expected');
        } catch(AuraHandledException expected) {}
        System.assertEquals('%A\\%B%',DevSreComponentDescriberController.likeTerm('A%B'));
        System.assertEquals('%A\\_B%',DevSreComponentDescriberController.likeTerm('A_B'));
    }
    @IsTest static void emptyAndUnlinkedFixturesDoNotClaimHistory() {
        String fk=DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component__c.SObjectType,Flosum__Branch__c.SObjectType);
        Flosum__Component__c source=new Flosum__Component__c();
        source.put('Id',(Id)(Flosum__Component__c.SObjectType.getDescribe().getKeyPrefix()+'000000000001'));
        DevSreComponentDescriberController.ComponentRow row=
            DevSreComponentDescriberController.convert(source,fk,new Map<Id,String>());
        System.assertEquals('Sem Branch vinculada',row.branchName);
        System.assertEquals(null,row.branchId);
        DevSreComponentDescriberController.ComponentDetail details=
            DevSreComponentDescriberController.buildDetail(source,fk,
                new Map<Id,String>(),new List<SObject>(),true);
        System.assertEquals(false,details.historiesHasMore);
        System.assertEquals(0,details.histories.size());
        System.assertEquals('TYPED_LINK_SAMPLE',details.historyQuality);
        System.assertEquals('UNVERIFIED',details.deployEvidenceQuality);
        DevSreComponentDescriberController.ComponentPage page=
            DevSreComponentDescriberController.toPage(new List<SObject>(),fk,new Map<Id,String>());
        System.assertEquals(false,page.hasMore);
        System.assertEquals(null,page.cursorId);
    }
    @IsTest static void histSampleLimitAndNoFakeVersionOrDeploy() {
        String prefix=Flosum__Component_History__c.SObjectType.getDescribe().getKeyPrefix();
        List<SObject> history=new List<SObject>();
        for(Integer i=1;i<=21;i++) {
            Flosum__Component_History__c entry=new Flosum__Component_History__c();
            entry.put('Id',(Id)(prefix+String.valueOf(i).leftPad(12,'0')));
            history.add(entry);
        }
        List<DevSreComponentDescriberController.HistoryRow> rows =
            DevSreComponentDescriberController.toHistories(history);
        System.assertEquals(20,rows.size());
        System.assertNotEquals(rows[0].id,rows[1].id);
    }

    @IsTest static void componentTypePicklistAndFilteredInventoryContract() {
        Schema.DescribeFieldResult typeField = DevSreComponentDescriberController.typeDescribe();
        System.assertEquals(Schema.DisplayType.PICKLIST, typeField.getType());
        System.assert(typeField.isAccessible());
        String branchField = DevSreComponentDescriberController.typedForeignKey(
            Flosum__Component__c.SObjectType,Flosum__Branch__c.SObjectType);
        String allQuery=DevSreComponentDescriberController.filteredQuery(
            branchField,typeField.getName(),false,false,false);
        System.assert(allQuery.contains('FROM Flosum__Component__c ORDER BY Name'));
        System.assert(!allQuery.contains('WHERE Name LIKE'));
        String combined=DevSreComponentDescriberController.filteredQuery(
            branchField,typeField.getName(),true,true,true);
        System.assert(combined.contains('Flosum__Component_Name__c LIKE :pattern'));
        System.assert(combined.contains('Flosum__Source__c'));
        System.assert(combined.contains('Flosum__Version__c'));
        System.assert(combined.contains(typeField.getName()+' = :typeValue'));
        System.assert(combined.contains('AND (Name > :cursorName'));
        try {
            DevSreComponentDescriberController.filteredQuery('Name',typeField.getName(),
                false,false,false);
            System.assert(false,'Untrusted dynamic field should fail.');
        } catch (AuraHandledException expected) {}
        List<DevSreComponentDescriberController.ComponentTypeOption> opts =
            DevSreComponentDescriberController.getComponentTypes(null);
        System.assert(opts.size() <= 20);
        if (!opts.isEmpty()) {
            DevSreComponentDescriberController.validateTypeValue(opts[0].value);
            List<DevSreComponentDescriberController.ComponentTypeOption> matches =
                DevSreComponentDescriberController.getComponentTypes(opts[0].label);
            System.assert(!matches.isEmpty());
        }
        try {
            DevSreComponentDescriberController.validateTypeValue('not_an_approved_component_type_9999');
            System.assert(false,'Untrusted type should fail');
        } catch (AuraHandledException expected) {}
        try {
            DevSreComponentDescriberController.getComponentTypes(
                'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdef');
            System.assert(false,'Overlong lookup should fail.');
        } catch (AuraHandledException expected) {}
    }
    @IsTest static void userModeUnfilteredAndCombinedSearchRespectAccess() {
        Test.startTest();
        DevSreComponentDescriberController.ComponentPage all =
            DevSreComponentDescriberController.searchFilteredComponents(null,null,null,null);
        DevSreComponentDescriberController.ComponentPage missing =
            DevSreComponentDescriberController.searchFilteredComponents(
                'BM_M2_nonexistent_999',null,null,null);
        Test.stopTest();
        System.assert(all.rows.size() <= 25);
        System.assertEquals('REGISTERED_NAME_ONLY',all.identityLevel);
        System.assertEquals(0,missing.rows.size());
        try {
            DevSreComponentDescriberController.searchFilteredComponents('a',null,null,null);
            System.assert(false,'One-character name invalid');
        } catch (AuraHandledException expected) {}
        try {
            DevSreComponentDescriberController.searchFilteredComponents(
                null,'not_a_picklist_value',null,null);
            System.assert(false,'Unknown type invalid');
        } catch (AuraHandledException expected) {}
    }
}
