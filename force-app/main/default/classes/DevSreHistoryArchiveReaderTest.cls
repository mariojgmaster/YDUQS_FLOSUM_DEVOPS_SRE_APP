@IsTest
private class DevSreHistoryArchiveReaderTest {
    @IsTest static void archivesEnumerateTextOnlyAndExtractSelectedFile() {
        Compression.ZipWriter writer=new Compression.ZipWriter();
        writer.addEntry('classes/Example.cls',Blob.valueOf('public class Example {}'));
        writer.addEntry('objects/Test.object-meta.xml',Blob.valueOf('<xml>value</xml>'));
        writer.addEntry('images/icon.png',Blob.valueOf('not a supported preview'));
        Blob zip=writer.getArchive();
        Test.startTest();
        DevSreHistoryArchiveReader.ArchiveView list=
            DevSreHistoryArchiveReader.parseArchive(zip,null);
        DevSreHistoryArchiveReader.ArchiveView preview=
            DevSreHistoryArchiveReader.parseArchive(zip,'classes/Example.cls');
        Test.stopTest();
        System.assertEquals(3,list.entries.size());
        System.assertEquals(null,list.text);
        System.assertEquals(true,list.entries[0].previewable);
        System.assertEquals(false,list.entries[2].previewable);
        System.assertEquals('public class Example {}',preview.text);
        System.assertEquals('classes/Example.cls',preview.selectedPath);
        try {
            DevSreHistoryArchiveReader.parseArchive(zip,'images/icon.png');
            System.assert(false,'Binary preview not allowed');
        } catch(AuraHandledException expected) {}
        try {
            DevSreHistoryArchiveReader.parseArchive(zip,'no-such-file.cls');
            System.assert(false,'Missing entry');
        } catch(AuraHandledException expected) {}
    }
    @IsTest static void validatesPathAndRejectsUnauthorizedHistoryIdentifiers() {
        System.assert(!DevSreHistoryArchiveReader.isTextPath('../secrets.cls'));
        System.assert(!DevSreHistoryArchiveReader.isTextPath('/absolute.cls'));
        System.assert(!DevSreHistoryArchiveReader.isTextPath('secret.key'));
        System.assert(DevSreHistoryArchiveReader.isTextPath('src/classes/Test.cls'));
        try {
            DevSreHistoryArchiveReader.inspect(UserInfo.getUserId(),null);
            System.assert(false,'Only typed Flosum histories may be read');
        } catch(AuraHandledException expected) {}
        try {
            DevSreHistoryArchiveReader.parseArchive(Blob.valueOf('not a zip'),null);
            System.assert(false,'Invalid archive should fail');
        } catch(AuraHandledException expected) {}
    }
}
