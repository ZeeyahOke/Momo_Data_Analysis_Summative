import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
import re

class SMSProcessor:
    def __init__(self, xml_file_path: str):
        """Initialize the SMS processor with the path to the XML file."""
        self.xml_file_path = xml_file_path
        self.tree = None
        self.root = None

    def load_xml(self) -> bool:
        """Load and parse the XML file."""
        try:
            self.tree = ET.parse(self.xml_file_path)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            print(f"Error loading XML file: {str(e)}")
            return False

    def extract_transaction_details(self, body: str) -> Dict[str, Any]:
        """Extract transaction details from SMS body using regex patterns."""
        # Common patterns for MTN MoMo transactions
        patterns = {
            'amount': r'(\d+(?:,\d+)*)\s*RWF',
            'sender': r'received\s+(\d+(?:,\d+)*)\s*RWF\s+from\s+([^.]+)',
            'receiver': r'sent\s+(\d+(?:,\d+)*)\s*RWF\s+to\s+([^.]+)',
            'balance': r'New balance is\s+(\d+(?:,\d+)*)\s*RWF',
            'reference': r'Ref:\s*(\d+)',
            'date': r'Date:\s*([^.]+)'
        }

        details = {}
        
        # Extract amount
        amount_match = re.search(patterns['amount'], body)
        if amount_match:
            details['amount'] = amount_match.group(1).replace(',', '')

        # Extract sender/receiver based on transaction type
        if 'received' in body.lower():
            sender_match = re.search(patterns['sender'], body)
            if sender_match:
                details['sender'] = sender_match.group(2).strip()
        elif 'sent' in body.lower():
            receiver_match = re.search(patterns['receiver'], body)
            if receiver_match:
                details['receiver'] = receiver_match.group(2).strip()

        # Extract balance
        balance_match = re.search(patterns['balance'], body)
        if balance_match:
            details['balance'] = balance_match.group(1).replace(',', '')

        # Extract reference number
        ref_match = re.search(patterns['reference'], body)
        if ref_match:
            details['reference'] = ref_match.group(1)

        # Extract transaction date
        date_match = re.search(patterns['date'], body)
        if date_match:
            details['transaction_date'] = date_match.group(1).strip()

        return details

    def process_sms(self, sms_element: ET.Element) -> Dict[str, Any]:
        """Process a single SMS element and extract relevant information."""
        sms_data = {
            'protocol': sms_element.get('protocol'),
            'address': sms_element.get('address'),
            'date': sms_element.get('date'),
            'type': sms_element.get('type'),
            'body': sms_element.get('body'),
            'readable_date': sms_element.get('readable_date'),
            'contact_name': sms_element.get('contact_name')
        }

        # Extract transaction details from the SMS body
        transaction_details = self.extract_transaction_details(sms_data['body'])
        sms_data.update(transaction_details)

        return sms_data

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """Process all SMS messages and return a list of transactions."""
        if not self.root:
            if not self.load_xml():
                return []

        transactions = []
        for sms in self.root.findall('sms'):
            transaction = self.process_sms(sms)
            if transaction.get('amount'):  # Only include messages with transaction details
                transactions.append(transaction)

        return transactions

    def get_transaction_stats(self) -> Dict[str, Any]:
        """Calculate basic statistics from the transactions."""
        transactions = self.get_all_transactions()
        
        if not transactions:
            return {
                'total_transactions': 0,
                'total_amount': 0,
                'average_amount': 0
            }

        total_amount = sum(float(t.get('amount', 0)) for t in transactions)
        
        return {
            'total_transactions': len(transactions),
            'total_amount': total_amount,
            'average_amount': total_amount / len(transactions) if transactions else 0
        } 