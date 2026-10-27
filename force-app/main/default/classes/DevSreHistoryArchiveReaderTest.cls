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

    @IsTest static void selectsAccessibleMimeZipWithoutFileExtension() {
        Attachment ignored = new Attachment(
            Name='text attachment', ContentType='text/plain', Body=Blob.valueOf('text'));
        Attachment accepted = new Attachment(
            Name='ApexClass', ContentType='application/zip', Body=syntheticArchive());
        Attachment second = new Attachment(
            Name='Other', ContentType='application/x-zip-compressed', Body=syntheticArchive());
        DevSreHistoryArchiveReader.ArchiveView view =
            DevSreHistoryArchiveReader.inspectSelectedAttachments(
                new List<SObject>{ignored, accepted, second}, null);
        System.assertEquals('ApexClass', view.attachmentName);
        System.assertEquals(2, view.matchingArchives);
        System.assert(view.entries.size() > 0);
        System.assertEquals(null, view.text);
    }
    @IsTest static void previewsOnlyRequestedContentAndRejectsMissingMimeZip() {
        Attachment raw = new Attachment(
            Name='ApexClass', ContentType='application/zip', Body=syntheticArchive());
        DevSreHistoryArchiveReader.ArchiveView view =
            DevSreHistoryArchiveReader.inspectSelectedAttachments(
                new List<SObject>{raw}, 'classes/Example.cls');
        System.assertEquals('public class Example {}', view.text);
        try {
            DevSreHistoryArchiveReader.inspectSelectedAttachments(
                new List<SObject>{new Attachment(
                    Name='OnlyText', ContentType='text/plain', Body=Blob.valueOf('hello'))},
                null);
            System.assert(false, 'Only ZIP MIME attachments are allowed');
        } catch (AuraHandledException expected) {}
    }
    @IsTest static void rejectsMissingArchiveAndInvalidEntryPaths() {
        try {
            DevSreHistoryArchiveReader.inspectSelectedAttachments(new List<SObject>(),null);
            System.assert(false, 'Missing archive must fail');
        } catch (AuraHandledException expected) {}
        try {
            DevSreHistoryArchiveReader.parseArchive(null,null);
            System.assert(false, 'Null archive must fail');
        } catch (AuraHandledException expected) {}
        for (String path : new List<String>{'', 'folder/', 'C:disk.cls',
            'folder\\escape.cls', '../../secret.xml', 'file.exe'}) {
            System.assertEquals(false, DevSreHistoryArchiveReader.isTextPath(path));
        }
    }
    @IsTest static void permitsTextLargerThanTheFormer64KiBLimit() {
        List<String> lines=new List<String>();
        for(Integer i=0;i<11000;i++) lines.add(String.valueOf(i).leftPad(6,'0'));
        String large=String.join(lines,'\n');
        System.assert(large.length()>65536);
        Compression.ZipWriter writer=new Compression.ZipWriter();
        writer.addEntry('classes/Large.cls', Blob.valueOf(large));
        Blob zipped=writer.getArchive();
        DevSreHistoryArchiveReader.ArchiveView view=
            DevSreHistoryArchiveReader.parseArchive(zipped,'classes/Large.cls');
        System.assertEquals(large,view.text);
        System.assertEquals(6291456,DevSreHistoryArchiveReader.MAX_TEXT_BYTES);
        System.assertEquals(6291456,DevSreHistoryArchiveReader.MAX_ZIP_BYTES);
        System.assertEquals(1,view.entries.size());
        System.assertEquals(true,view.entries[0].previewable);
    }

}
