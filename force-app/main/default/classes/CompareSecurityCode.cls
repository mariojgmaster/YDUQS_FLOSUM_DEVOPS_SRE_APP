public with sharing class CompareSecurityCode {
    public class InputParameters {
        @InvocableVariable(required=true)
        public Id contactId;
        @InvocableVariable(required=true)
        public String securityCode;
    }
    
    public class OutputResult {
        @InvocableVariable
        public Boolean isMatch;
    }

    @InvocableMethod(label='Compare Security Code')
    public static List<OutputResult> compareSecurityCode(List<InputParameters> inputList) {
        List<OutputResult> results = new List<OutputResult>();
        
        for (InputParameters input : inputList) {
            OutputResult result = new OutputResult();
            result.isMatch = false; // Default to false in case of no match
            
            // Query the Contact and compare the security code
            Contact contact = [SELECT Id, ChaveSeguranca__c FROM Contact WHERE Id = :input.contactId LIMIT 1];
            
            if (contact != null && contact.ChaveSeguranca__c != null) {
                result.isMatch = input.securityCode == contact.ChaveSeguranca__c;
            }
            
            results.add(result);
        }
        
        return results;
    }
}