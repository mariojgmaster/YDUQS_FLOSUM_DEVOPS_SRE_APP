/**
 * SPEC-006 V3.2.1 - bounded read-only viewer for Flosum Component History classic Attachments.
 * A history and its parent Attachment must both be visible in USER_MODE to the caller.
 * Never logs/reports the ZIP bytes, path inventory or text in public Actions.
 */
public with sharing class DevSreHistoryArchiveReader {
    @TestVisible private static final Integer MAX_ZIP_BYTES=6291456;
    @TestVisible private static final Integer MAX_TEXT_BYTES=6291456;
    @TestVisible private static final Integer MAX_ENTRIES=200;

    public class EntryRow {
        @AuraEnabled public String path { get; set; }
        @AuraEnabled public Long size { get; set; }
        @AuraEnabled public Boolean previewable { get; set; }
    }
    public class ArchiveView {
        @AuraEnabled public String attachmentName { get; set; }
        @AuraEnabled public Id attachmentId { get; set; }
        @AuraEnabled public List<EntryRow> entries { get; set; }
        @AuraEnabled public String selectedPath { get; set; }
        @AuraEnabled public String text { get; set; }
        @AuraEnabled public Integer matchingArchives { get; set; }
    }

    @TestVisible private static Boolean isTextPath(String path) {
        if (String.isBlank(path) || path.length()>240 ||
            path.startsWith('/') || path.contains('..') ||
            path.contains('\\') || path.contains(':') ||
            path.endsWith('/')) return false;
        String lower=path.toLowerCase();
        for (String ext : new List<String>{
            '.xml','.cls','.trigger','.json','.js','.ts','.html','.css','.txt',
            '.md','.page','.component','.flow','.object','.profile',
            '.permissionset','.layout','.app','.tab','.labels','.svg','.yml','.yaml'
        }) if(lower.endsWith(ext)) return true;
        return false;
    }
    @TestVisible private static Boolean previewAllowed(Compression.ZipEntry entry) {
        if (!isTextPath(entry.getName())) return false;
        Long size=entry.getUncompressedSize();
        Long compressed=entry.getCompressedSize();
        if (size==null || size<0 || size>MAX_TEXT_BYTES ||
            compressed==null || compressed<0) return false;
        if (size>0 && (compressed==0 || size>compressed*200)) return false;
        return true;
    }
    @TestVisible private static ArchiveView parseArchive(Blob zip, String selected) {
        if (zip==null || zip.size()>MAX_ZIP_BYTES)
            throw new AuraHandledException('Arquivo ZIP excede o limite seguro.');
        ArchiveView result=new ArchiveView();
        result.entries=new List<EntryRow>();
        result.matchingArchives=1;
        Compression.ZipReader reader;
        try {
            reader=new Compression.ZipReader(zip);
            List<Compression.ZipEntry> zipEntries=reader.getEntries();
            if (zipEntries.size()>MAX_ENTRIES)
                throw new AuraHandledException('ZIP possui entradas demais para exibição.');
            Boolean selectedFound=selected==null;
            Boolean selectedPermitted=false;
            for (Compression.ZipEntry entry : zipEntries) {
                EntryRow row=new EntryRow();
                row.path=entry.getName();
                row.size=entry.getUncompressedSize();
                row.previewable=previewAllowed(entry);
                result.entries.add(row);
                if (selected!=null && selected==row.path) {
                    selectedFound=true;
                    selectedPermitted=row.previewable;
                }
            }
            if (!selectedFound || !selectedPermitted && selected!=null)
                throw new AuraHandledException('Arquivo indisponível para pré-visualização.');
            if(selected!=null) {
                // The governor heap is shared with ZIP bytes, decompressed data,
                // and serialized text. Fail safely before extraction when possible.
                Long expectedSize;
                for (Compression.ZipEntry entry : zipEntries) {
                    if (entry.getName()==selected) { expectedSize=entry.getUncompressedSize(); break; }
                }
                if (expectedSize==null || expectedSize>MAX_TEXT_BYTES)
                    throw new AuraHandledException('Arquivo excede 6 MiB de texto.');
                if (Limits.getLimitHeapSize()-Limits.getHeapSize() < expectedSize*2+131072)
                    throw new AuraHandledException('Arquivo dentro do limite de 6 MiB, mas sem heap Apex suficiente para abrir. Use o download original do Flosum.');
                Blob bytes=reader.extract(selected);
                if(bytes==null || bytes.size()>MAX_TEXT_BYTES)
                    throw new AuraHandledException('Conteúdo excede o limite de visualização.');
                result.selectedPath=selected;
                result.text=bytes.toString();
            }
            return result;
        } catch (AuraHandledException known) {
            throw known;
        } catch (Exception error) {
            throw new AuraHandledException('ZIP inválido, corrompido ou não suportado.');
        }
    }

    public static ArchiveView inspect(Id historyId, String entryPath) {
        if (historyId==null || historyId.getSObjectType()!=Flosum__Component_History__c.SObjectType)
            throw new AuraHandledException('Histórico inválido.');
        if(!Flosum__Component_History__c.SObjectType.getDescribe().isAccessible() ||
            !Attachment.SObjectType.getDescribe().isAccessible() ||
            !Attachment.Body.getDescribe().isAccessible())
            throw new AuraHandledException('Acesso de leitura ao histórico ou anexo indisponível.');
        List<SObject> history=Database.queryWithBinds(
            'SELECT Id FROM Flosum__Component_History__c WHERE Id = :historyId LIMIT 1',
            new Map<String,Object>{'historyId'=>historyId},AccessLevel.USER_MODE);
        if(history.isEmpty()) throw new AuraHandledException('Histórico não encontrado ou sem acesso.');
        // First query metadata only: never load up to eleven 6-MiB Bodies at once.
        List<SObject> raw=Database.queryWithBinds(
            'SELECT Id, ParentId, Name, BodyLength, ContentType FROM Attachment' +
            ' WHERE ParentId = :historyId AND BodyLength <= :maxBytes' +
            ' ORDER BY CreatedDate DESC LIMIT 11',
            new Map<String,Object>{'historyId'=>historyId,'maxBytes'=>MAX_ZIP_BYTES},
            AccessLevel.USER_MODE);
        ZipSelection selected=selectZipMetadata(raw);
        if(selected.index<0)
            throw new AuraHandledException('Nenhum ZIP acessível e dentro do limite neste histórico.');
        Id chosenId=((Attachment)raw[selected.index]).Id;
        // Read only ONE authorized attachment body in the current user's context.
        List<SObject> bodies=Database.queryWithBinds(
            'SELECT Id, ParentId, Name, BodyLength, ContentType, Body FROM Attachment' +
            ' WHERE Id = :chosenId AND ParentId = :historyId AND BodyLength <= :maxBytes LIMIT 1',
            new Map<String,Object>{
                'chosenId'=>chosenId,'historyId'=>historyId,'maxBytes'=>MAX_ZIP_BYTES
            }, AccessLevel.USER_MODE);
        if(bodies.isEmpty()) throw new AuraHandledException('Anexo não disponível para leitura.');
        ArchiveView view=inspectSelectedAttachments(bodies,entryPath);
        view.matchingArchives=selected.count;
        return view;
    }

    @TestVisible private class ZipSelection {
        public Integer index=-1;
        public Integer count=0;
    }
    // Pure metadata selection: can be unit-tested without managed Flosum DML.
    @TestVisible private static ZipSelection selectZipMetadata(List<SObject> raw) {
        ZipSelection selected=new ZipSelection();
        for(Integer i=0;i<raw.size();i++) {
            Attachment item=(Attachment)raw[i];
            String mime=item.ContentType==null?'':item.ContentType.toLowerCase();
            if(!mime.contains('zip') && !mime.contains('compressed')) continue;
            selected.count++;
            if(selected.index<0) selected.index=i;
        }
        return selected;
    }

    // Separate the pure archive-selection policy from the USER_MODE query.
    // Tests can exercise this path without inserting managed Flosum records.
    @TestVisible private static ArchiveView inspectSelectedAttachments(
        List<SObject> raw, String entryPath
    ) {
        Attachment first;
        Integer matching=0;
        for(SObject rec : raw) {
            Attachment a=(Attachment)rec;
            String type=a.ContentType==null ? '' : a.ContentType.toLowerCase();
            if(!type.contains('zip') && !type.contains('compressed')) continue;
            matching++;
            if(first==null) first=a;
        }
        if(first==null)
            throw new AuraHandledException('Nenhum ZIP acessível e dentro do limite neste histórico.');
        ArchiveView view=parseArchive(first.Body,entryPath);
        view.attachmentId=first.Id;
        view.attachmentName=first.Name;
        view.matchingArchives=matching;
        return view;
    }
}
