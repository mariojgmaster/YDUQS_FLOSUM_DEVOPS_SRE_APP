@IsTest
public class GeradorSenhaInicialTest {

    @IsTest
    static void testGenerateRandomStringsNumeric() {
        // Setup
        GeradorSenhaInicial.Request request = new GeradorSenhaInicial.Request();
        request.quantidadeDigitos = 8;
        request.apenasNumerico = true;
        
        List<GeradorSenhaInicial.Request> requests = new List<GeradorSenhaInicial.Request>{request};

        // Test
        Test.startTest();
        List<String> randomStrings = GeradorSenhaInicial.generateRandomStrings(requests);
        Test.stopTest();
        
        // Assert
        System.assertEquals(1, randomStrings.size());
        String generatedString = randomStrings[0];
        System.assertEquals(8, generatedString.length());
        System.assert(Pattern.matches('^[0-9]{8}$', generatedString), 'String is not numeric');
    }
    
    @IsTest
    static void testGenerateRandomStringsAlphanumeric() {
        // Setup
        GeradorSenhaInicial.Request request = new GeradorSenhaInicial.Request();
        request.quantidadeDigitos = 8;
        request.apenasNumerico = false;
        
        List<GeradorSenhaInicial.Request> requests = new List<GeradorSenhaInicial.Request>{request};

        // Test
        Test.startTest();
        List<String> randomStrings = GeradorSenhaInicial.generateRandomStrings(requests);
        Test.stopTest();
        
        // Assert
        System.assertEquals(1, randomStrings.size());
        String generatedString = randomStrings[0];
        System.assertEquals(8, generatedString.length());
        System.assert(Pattern.matches('^[A-Za-z0-9]{8}$', generatedString), 'String is not alphanumeric');
    }
}