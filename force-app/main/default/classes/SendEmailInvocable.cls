public with sharing class SendEmailInvocable {

    // Define a nested class to hold the input parameters for the invocable method
    public class EmailRequest {
        @InvocableVariable(required=true)
        public String subject;

        @InvocableVariable(required=true)
        public String htmlBody;

        @InvocableVariable(required=true)
        public List<String> emailAddresses;
    }

    // Define the invocable method
    @InvocableMethod(label='Send Email' description='Send an email to a list of addresses')
    public static void sendEmail(List<EmailRequest> emailRequests) {
        List<Messaging.SingleEmailMessage> emails = new List<Messaging.SingleEmailMessage>();

        for (EmailRequest request : emailRequests) {
            // Create a new email message
            Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();

            // Set the subject, body, and recipients
            email.setSubject(request.subject);
            email.setHtmlBody(request.htmlBody);
            email.setToAddresses(request.emailAddresses);

            // Add the email to the list
            emails.add(email);
        }

        // Send the emails
        if (!emails.isEmpty()) {
            Messaging.sendEmail(emails);
        }
    }
}