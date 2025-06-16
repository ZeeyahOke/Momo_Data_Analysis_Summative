import unittest
from modules.xml_processor import SMSProcessor

class TestSMSProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = SMSProcessor('data/modified_sms_v2.xml')

    def test_load_xml(self):
        """Test XML file loading"""
        self.assertTrue(self.processor.load_xml())

    def test_extract_transaction_details(self):
        """Test transaction details extraction"""
        # Test received transaction
        received_body = "You have received 2000 RWF from Jane Smith. New balance is 15000 RWF. Ref: 12345. Date: 10 May 2024 4:30:58 PM."
        received_details = self.processor.extract_transaction_details(received_body)
        self.assertEqual(received_details['amount'], '2000')
        self.assertEqual(received_details['sender'], 'Jane Smith')
        self.assertEqual(received_details['balance'], '15000')
        self.assertEqual(received_details['reference'], '12345')

        # Test sent transaction
        sent_body = "You sent 500 RWF to John Doe. New balance is 14500 RWF. Ref: 67890. Date: 10 May 2024 4:35:10 PM."
        sent_details = self.processor.extract_transaction_details(sent_body)
        self.assertEqual(sent_details['amount'], '500')
        self.assertEqual(sent_details['receiver'], 'John Doe')
        self.assertEqual(sent_details['balance'], '14500')
        self.assertEqual(sent_details['reference'], '67890')

if __name__ == '__main__':
    unittest.main() 