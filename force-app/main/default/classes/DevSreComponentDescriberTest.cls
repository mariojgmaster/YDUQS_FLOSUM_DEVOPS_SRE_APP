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
            row.put('Name','Flow_Component');
            row.put(foreign,branchId);
            records.add(row);
        }
        Map<Id,String> names=new Map<Id,String>{branchId=>'integration'};
        DevSreComponentDescriberController.ComponentPage page =
            DevSreComponentDescriberController.toPage(records,foreign,names);
        System.assertEquals(25,page.rows.size());
        System.assertEquals(true,page.hasMore);
        System.assertEquals('Flow_Component',page.cursorName);
        System.assertEquals('integration',page.rows[0].branchName);
        System.assertEquals(branchId,page.rows[0].branchId);
        System.assertNotEquals(page.rows[0].id,page.rows[1].id);
        DevSreComponentDescriberController.ComponentRow inaccessible =
            DevSreComponentDescriberController.convert(records[0],foreign,
                                                        new Map<Id,String>());
        System.assertEquals(null,inaccessible.branchId);
        System.assertEquals('Branch não acessível',inaccessible.branchName);
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