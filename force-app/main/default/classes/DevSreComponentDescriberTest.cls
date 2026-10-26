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
}