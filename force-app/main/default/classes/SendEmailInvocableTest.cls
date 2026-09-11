@IsTest
public class SendEmailInvocableTest {

    @IsTest
    static void testSendEmail() {
        // Prepare test data
        List<String> emailAddresses = new List<String>{'test1@example.com', 'test2@example.com'};
        String subject = 'Test Subject';
        String htmlBody = '<h1>Test Email Body</h1>';

        // Create an EmailRequest instance with test data
        SendEmailInvocable.EmailRequest emailRequest = new SendEmailInvocable.EmailRequest();
        emailRequest.subject = subject;
        emailRequest.htmlBody = htmlBody;
        emailRequest.emailAddresses = emailAddresses;

        // Add the EmailRequest instance to a list
        List<SendEmailInvocable.EmailRequest> emailRequests = new List<SendEmailInvocable.EmailRequest>{ emailRequest };

        // Call the invocable method
        Test.startTest();
        SendEmailInvocable.sendEmail(emailRequests);
        Test.stopTest();

        // Verify that no exceptions were thrown
        System.assert(true, 'No exceptions were thrown during email send process');
    }
}