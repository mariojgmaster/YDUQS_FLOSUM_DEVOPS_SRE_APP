@isTest
private class CompareSecurityCodeTest {
    @isTest
    static void testCompareSecurityCode() {
        // Crie um Contato de teste com um código de segurança
        Contact testContact = new Contact(
            FirstName = 'John',
            LastName = 'Doe',
            ChaveSeguranca__c = '12345'  // Código de segurança para o teste
        );
        insert testContact;

        // Crie objetos de entrada para o método invocável
        CompareSecurityCode.InputParameters input = new CompareSecurityCode.InputParameters();
        input.contactId = testContact.Id;
        input.securityCode = '12345'; // Código de segurança correspondente ao do Contato

        // Chame o método invocável
        CompareSecurityCode.OutputResult result = CompareSecurityCode.compareSecurityCode(new List<CompareSecurityCode.InputParameters>{input})[0];

        // Verifique se o resultado é verdadeiro
        System.assertEquals(true, result.isMatch);
    }
}