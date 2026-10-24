/** Internal integrity boundary. SYSTEM_MODE is required to detect all overlaps,
 * even when the actor cannot see another mapping. No data leaves this handler. */
public without sharing class DevSreEnvironmentGuard {
  public static void validate(
    List<DevSre_EnvironmentMapping__c> incoming,
    Map<Id, DevSre_EnvironmentMapping__c> oldRows,
    Boolean deleting
  ) {
    Boolean allowed = FeatureManagement.checkPermission(
      'DevSre_ManageEnvironments'
    );
    Set<Id> orgIds = new Set<Id>();
    Set<Id> changedIds = new Set<Id>();
    for (DevSre_EnvironmentMapping__c row : incoming) {
      if (!allowed || deleting) {
        row.addError(
          deleting
            ? 'Não é permitido excluir vigências. Encerre o período.'
            : 'Você não possui permissão para gerenciar ambientes.'
        );
        continue;
      }
      if (
        row.Organization__c == null ||
        row.ValidFrom__c == null ||
        String.isBlank(row.Reason__c) ||
        !new Set<String>{ 'PROD', 'UAT', 'SIT', 'DEV' }
          .contains(row.EnvironmentClass__c)
      ) {
        row.addError('Informe organização, ambiente, início e justificativa.');
      }
      if (
        row.ValidTo__c != null &&
        row.ValidFrom__c != null &&
        row.ValidTo__c <= row.ValidFrom__c
      ) {
        row.addError('O fim da vigência deve ser posterior ao início.');
      }
      if (oldRows != null) {
        DevSre_EnvironmentMapping__c previous = oldRows.get(row.Id);
        if (
          previous.Organization__c != row.Organization__c ||
          previous.EnvironmentClass__c != row.EnvironmentClass__c ||
          previous.ValidFrom__c != row.ValidFrom__c
        ) {
          row.addError(
            'Preserve a organização, o ambiente e o início. Encerre a vigência e crie outro período.'
          );
        }
        // A closed interval cannot be reopened or extended over time.
        if (
          previous.ValidTo__c != null &&
          (row.ValidTo__c == null ||
          row.ValidTo__c > previous.ValidTo__c)
        ) {
          row.addError(
            'Uma vigência encerrada não pode ser reaberta ou ampliada.'
          );
        }
      }
      orgIds.add(row.Organization__c);
      if (row.Id != null)
        changedIds.add(row.Id);
    }
    if (!allowed || deleting || orgIds.isEmpty())
      return;
    // Lock parent identity to serialize concurrent inserts for the same org.
    // This SELECT does not modify any managed-package record.
    List<Flosum__Organisation__c> locks = [
      SELECT Id
      FROM Flosum__Organisation__c
      WHERE Id IN :orgIds
      WITH SYSTEM_MODE
      FOR UPDATE
    ];
    List<DevSre_EnvironmentMapping__c> existing = [
      SELECT Id, Organization__c, ValidFrom__c, ValidTo__c
      FROM DevSre_EnvironmentMapping__c
      WHERE Organization__c IN :orgIds AND Id NOT IN :changedIds
      WITH SYSTEM_MODE
      LIMIT 5001
    ];
    if (existing.size() > 5000) {
      for (DevSre_EnvironmentMapping__c row : incoming)
        row.addError('Limite de vigências para validação excedido.');
      return;
    }
    for (Integer i = 0; i < incoming.size(); i++) {
      DevSre_EnvironmentMapping__c row = incoming[i];
      for (DevSre_EnvironmentMapping__c other : existing) {
        if (overlaps(row, other))
          row.addError(
            'Já existe uma vigência sobreposta para esta organização.'
          );
      }
      for (Integer j = 0; j < i; j++) {
        if (overlaps(row, incoming[j])) {
          row.addError('As vigências informadas se sobrepõem.');
          incoming[j].addError('As vigências informadas se sobrepõem.');
        }
      }
    }
  }

  @TestVisible
  private static Boolean overlaps(
    DevSre_EnvironmentMapping__c a,
    DevSre_EnvironmentMapping__c b
  ) {
    return a.Organization__c == b.Organization__c &&
      a.ValidFrom__c != null &&
      b.ValidFrom__c != null &&
      (a.ValidTo__c == null ||
      b.ValidFrom__c < a.ValidTo__c) &&
      (b.ValidTo__c == null ||
      a.ValidFrom__c < b.ValidTo__c);
  }
}
