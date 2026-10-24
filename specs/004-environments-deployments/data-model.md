# Dados

DevSre_EnvironmentMapping__c: Name autonumber ENV-{000000}; Organization__c Lookup(Flosum__Organisation__c), EnvironmentClass__c picklist PROD/UAT/SIT/DEV, ValidFrom__c obrigatório DateTime, ValidTo__c opcional DateTime, Reason__c Text(255) obrigatório. FHT nos cinco campos; CreatedBy/CreatedDate/LastModifiedBy/LastModifiedDate nativos.

Lookup não é portátil entre orgs; mapear cada ambiente localmente após implantação. Sem seed com IDs reais. Histórico é o recurso nativo de Field History Tracking, sujeito à retenção padrão da plataforma; sem promessa de retenção indefinida.

Metadata Log permanece fonte autoritativa. Relógios: Completed_Date para conclusão, Start_Date para início. Deployment_Date é fórmula de criação e não serve como fim. LastModifiedDate não define duração.
