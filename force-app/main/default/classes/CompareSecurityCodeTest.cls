@isTest
private class CompareSecurityCodeTest {
    @isTest
    static void testCompareSecurityCode() {
        // A criação aciona o Flow que gera/atualiza a chave de segurança.
        Contact testContact = new Contact(
            FirstName = 'John',
            LastName = 'Doe',
            Email = 'contato.teste@example.com',
            ChaveSeguranca__c = '12345'
        );
        insert testContact;

        // Reconsultar o valor persistido após a execução síncrona dos Flows.
        // Não utilizar a chave inicial fixa, pois a automação pode substituí-la.
        Contact savedContact = [
            SELECT ChaveSeguranca__c
            FROM Contact
            WHERE Id = :testContact.Id
            LIMIT 1
        ];
        System.assert(
            String.isNotBlank(savedContact.ChaveSeguranca__c),
            'A chave de segurança do contato deve estar preenchida após a criação.'
        );

        CompareSecurityCode.InputParameters validInput =
            new CompareSecurityCode.InputParameters();
        validInput.contactId = testContact.Id;
        validInput.securityCode = savedContact.ChaveSeguranca__c;

        CompareSecurityCode.InputParameters invalidInput =
            new CompareSecurityCode.InputParameters();
        invalidInput.contactId = testContact.Id;
        invalidInput.securityCode = savedContact.ChaveSeguranca__c + '_invalid';

        List<CompareSecurityCode.OutputResult> results =
            CompareSecurityCode.compareSecurityCode(
                new List<CompareSecurityCode.InputParameters>{
                    validInput,
                    invalidInput
                }
            );

        System.assertEquals(2, results.size(), 'A comparação deve retornar dois resultados.');
        System.assertEquals(true, results[0].isMatch, 'A chave persistida deve ser aceita.');
        System.assertEquals(false, results[1].isMatch, 'Uma chave diferente deve ser rejeitada.');
    }
}
