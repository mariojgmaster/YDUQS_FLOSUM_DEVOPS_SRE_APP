trigger DevSreEnvironmentMapping on DevSre_EnvironmentMapping__c(
  before insert,
  before update,
  before delete
) {
  DevSreEnvironmentGuard.validate(
    Trigger.isDelete ? Trigger.old : Trigger.new,
    Trigger.isUpdate ? Trigger.oldMap : null,
    Trigger.isDelete
  );
}
