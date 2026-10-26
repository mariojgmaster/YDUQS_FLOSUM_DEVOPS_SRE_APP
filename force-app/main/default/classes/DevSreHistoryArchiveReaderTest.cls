@IsTest
private class DevSreHistoryArchiveReaderTest {
    private static Blob syntheticArchive() {
        Compression.ZipWriter writer = new Compression.ZipWriter();
        writer.addEntry('classes/Example.cls', Blob.valueOf('public class Example {}'));
        writer.addEntry('objects/Test.object-meta.xml', Blob.valueOf('<xml>value</xml>'));
        writer.addEntry('images/icon.png', Blob.valueOf('not a supported preview'));
        return writer.getArchive();
    }

    @IsTest static void listsAllowedEntryPathsWithoutRelyingOnArchiveOrder() {
        DevSreHistoryArchiveReader.ArchiveView manifestView =
            DevSreHistoryArchiveReader.parseArchive(syntheticArchive(), null);
        Map<String, DevSreHistoryArchiveReader.EntryRow> entries =
            new Map<String, DevSreHistoryArchiveReader.EntryRow>();
        for (DevSreHistoryArchiveReader.EntryRow row : manifestView.entries) {
            entries.put(row.path, row);
        }
        System.assert(entries.containsKey('classes/Example.cls'));
        System.assert(entries.containsKey('objects/Test.object-meta.xml'));
        System.assert(entries.containsKey('images/icon.png'));
        System.assertEquals(null, manifestView.text);
        System.assertEquals(false, entries.get('images/icon.png').previewable);
    }

    @IsTest static void previewsSelectedApexSourceAsPlainText() {
        DevSreHistoryArchiveReader.ArchiveView preview =
            DevSreHistoryArchiveReader.parseArchive(
                syntheticArchive(), 'classes/Example.cls');
        System.assertEquals('classes/Example.cls', preview.selectedPath);
        System.assertEquals('public class Example {}', preview.text);
    }

    @IsTest static void rejectsBinaryAndAbsentTextSelections() {
        Blob zip = syntheticArchive();
        try {
            DevSreHistoryArchiveReader.parseArchive(zip, 'images/icon.png');
            System.assert(false, 'Binary preview not allowed');
        } catch (AuraHandledException expected) {}
        try {
            DevSreHistoryArchiveReader.parseArchive(zip, 'no-such-file.cls');
            System.assert(false, 'Missing entry not allowed');
        } catch (AuraHandledException expected) {}
    }

    @IsTest static void validatesPathAndRejectsUnauthorizedHistoryIdentifiers() {
        System.assert(!DevSreHistoryArchiveReader.isTextPath('../secrets.cls'));
        System.assert(!DevSreHistoryArchiveReader.isTextPath('/absolute.cls'));
        System.assert(!DevSreHistoryArchiveReader.isTextPath('secret.key'));
        System.assert(DevSreHistoryArchiveReader.isTextPath('src/classes/Test.cls'));
        try {
            DevSreHistoryArchiveReader.inspect(UserInfo.getUserId(), null);
            System.assert(false, 'Only typed Flosum histories may be read');
        } catch (AuraHandledException expected) {}
        try {
            DevSreHistoryArchiveReader.parseArchive(Blob.valueOf('not a zip'), null);
            System.assert(false, 'Invalid archive should fail');
        } catch (AuraHandledException expected) {}
    }
}
