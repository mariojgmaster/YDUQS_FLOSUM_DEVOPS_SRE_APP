public with sharing class DevSreEnvironmentController {
  public class OrganizationOption {
    @AuraEnabled
    public Id value { get; set; }
    @AuraEnabled
    public String label { get; set; }
  }
  public class OrganizationPage {
    @AuraEnabled
    public List<OrganizationOption> options { get; set; }
    @AuraEnabled
    public Boolean hasMore { get; set; }
    @AuraEnabled
    public Boolean canManage { get; set; }
  }
  public class MappingRow {
    @AuraEnabled
    public Id id { get; set; }
    @AuraEnabled
    public Id organizationId { get; set; }
    @AuraEnabled
    public String organizationName { get; set; }
    @AuraEnabled
    public String environmentClass { get; set; }
    @AuraEnabled
    public Datetime validFrom { get; set; }
    @AuraEnabled
    public Datetime validTo { get; set; }
    @AuraEnabled
    public String reason { get; set; }
  }

  @AuraEnabled
  public static OrganizationPage searchOrganizations(String searchTerm) {
    try {
      String term = searchTerm == null ? '' : searchTerm.trim();
      if (term.length() > 80)
        throw new AuraHandledException('A pesquisa permite até 80 caracteres.');
      String pattern = '%' + term.replace('%', '\\%').replace('_', '\\_') + '%';
      List<Flosum__Organisation__c> source = [
        SELECT Id, Name
        FROM Flosum__Organisation__c
        WHERE Name LIKE :pattern
        WITH USER_MODE
        ORDER BY Name, Id
        LIMIT 51
      ];
      OrganizationPage result = new OrganizationPage();
      result.options = new List<OrganizationOption>();
      result.hasMore = source.size() > 50;
      result.canManage = FeatureManagement.checkPermission(
        'DevSre_ManageEnvironments'
      );
      for (Integer i = 0; i < Math.min(50, source.size()); i++) {
        OrganizationOption option = new OrganizationOption();
        option.value = source[i].Id;
        option.label = source[i].Name;
        result.options.add(option);
      }
      return result;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível consultar organizações com seu acesso atual.'
      );
    }
  }

  @AuraEnabled
  public static List<MappingRow> listMappings(Id organizationId) {
    try {
      validOrganization(organizationId);
      String queryText = 'SELECT Id, Organization__c, Organization__r.Name, EnvironmentClass__c, ValidFrom__c, ValidTo__c, Reason__c FROM DevSre_EnvironmentMapping__c';
      if (organizationId != null)
        queryText += ' WHERE Organization__c = :organizationId';
      queryText += ' ORDER BY ValidFrom__c DESC, Id DESC LIMIT 2001';
      List<DevSre_EnvironmentMapping__c> source = Database.queryWithBinds(
        queryText,
        new Map<String, Object>{ 'organizationId' => organizationId },
        AccessLevel.USER_MODE
      );
      if (source.size() > 2000)
        throw new AuraHandledException(
          'Há muitas vigências. Selecione uma organização.'
        );
      List<MappingRow> result = new List<MappingRow>();
      for (DevSre_EnvironmentMapping__c item : source) {
        MappingRow row = new MappingRow();
        row.id = item.Id;
        row.organizationId = item.Organization__c;
        row.organizationName = item.Organization__r.Name;
        row.environmentClass = item.EnvironmentClass__c;
        row.validFrom = item.ValidFrom__c;
        row.validTo = item.ValidTo__c;
        row.reason = item.Reason__c;
        result.add(row);
      }
      return result;
    } catch (AuraHandledException known) {
      throw known;
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível consultar as vigências com seu acesso atual.'
      );
    }
  }

  @AuraEnabled
  public static Id saveMapping(
    Id mappingId,
    Id organizationId,
    String environmentClass,
    Datetime validFrom,
    Datetime validTo,
    String reason
  ) {
    if (!FeatureManagement.checkPermission('DevSre_ManageEnvironments'))
      throw new AuraHandledException(
        'Você não possui permissão para gerenciar ambientes.'
      );
    if (String.isBlank(reason) || reason.trim().length() > 255)
      throw new AuraHandledException(
        'Informe uma justificativa com até 255 caracteres.'
      );
    try {
      validOrganization(organizationId);
      if (organizationId == null)
        throw new AuraHandledException('Selecione uma organização.');
      List<Flosum__Organisation__c> visible = [
        SELECT Id
        FROM Flosum__Organisation__c
        WHERE Id = :organizationId
        WITH USER_MODE
        LIMIT 1
      ];
      if (visible.isEmpty())
        throw new AuraHandledException('Organização inválida ou indisponível.');
      DevSre_EnvironmentMapping__c recordValue;
      if (mappingId == null) {
        recordValue = new DevSre_EnvironmentMapping__c(
          Organization__c = organizationId,
          EnvironmentClass__c = environmentClass,
          ValidFrom__c = validFrom,
          ValidTo__c = validTo,
          Reason__c = reason.trim()
        );
        Database.insert(recordValue, AccessLevel.USER_MODE);
      } else {
        if (
          mappingId.getSObjectType() != DevSre_EnvironmentMapping__c.SObjectType
        )
          throw new AuraHandledException('Vigência inválida.');
        List<DevSre_EnvironmentMapping__c> previous = [
          SELECT Id, Organization__c, EnvironmentClass__c, ValidFrom__c
          FROM DevSre_EnvironmentMapping__c
          WHERE Id = :mappingId
          WITH USER_MODE
          LIMIT 1
        ];
        if (
          previous.isEmpty() ||
          previous[0].Organization__c != organizationId ||
          previous[0].EnvironmentClass__c != environmentClass ||
          previous[0].ValidFrom__c != validFrom
        ) {
          throw new AuraHandledException(
            'A identidade da vigência não pode ser alterada.'
          );
        }
        recordValue = new DevSre_EnvironmentMapping__c(
          Id = mappingId,
          ValidTo__c = validTo,
          Reason__c = reason.trim()
        );
        Database.update(recordValue, AccessLevel.USER_MODE);
      }
      return recordValue.Id;
    } catch (AuraHandledException known) {
      throw known;
    } catch (DmlException invalid) {
      throw new AuraHandledException(
        'Não foi possível salvar. Verifique permissões, campos obrigatórios, período e sobreposição de vigências.'
      );
    } catch (Exception unexpected) {
      throw new AuraHandledException(
        'Não foi possível salvar a configuração com seu acesso atual.'
      );
    }
  }

  private static void validOrganization(Id value) {
    if (
      value != null &&
      value.getSObjectType() != Flosum__Organisation__c.SObjectType
    )
      throw new AuraHandledException('Organização inválida.');
  }
}
