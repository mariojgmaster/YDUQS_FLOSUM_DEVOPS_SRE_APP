public with sharing class GeradorSenhaInicial {

    public class Request {
        @InvocableVariable
        public Integer quantidadeDigitos;
        
        @InvocableVariable
        public Boolean apenasNumerico;
    }

    @InvocableMethod
    public static List<String> generateRandomStrings(List<Request> requests) {
        List<String> randomStrings = new List<String>();
        String numericChars = '0123456789';
        String allChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

        for (Request request : requests) {
            String chars = request.apenasNumerico ? numericChars : allChars;
            Integer charsLength = chars.length();
            String randomString = '';
            
            for (Integer i = 0; i < request.quantidadeDigitos; i++) {
                Integer randomIndex = Math.mod(Math.abs(Crypto.getRandomInteger()), charsLength);
                randomString += chars.substring(randomIndex, randomIndex + 1);
            }
            
            randomStrings.add(randomString);
        }
        return randomStrings;
    }
}