import xml.etree.ElementTree as ET
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_processing.log'),
        logging.StreamHandler()
    ]
)

class SMSProcessor:
    def __init__(self):
        # Define regex patterns for different transaction types
        self.patterns = {
            "Incoming Money": [
                re.compile(r"You have received (\d+,?\d*\.?\d*) RWF from (.*?)(?: on |\. New balance is|\.)"),
                re.compile(r"Received (\d+,?\d*\.?\d*) RWF from (.*?)\. Your new balance is")
            ],
            "Payments to Code Holders": [
                re.compile(r"You paid (\d+,?\d*\.?\d*) RWF to (.*?)\. New balance is"),
                re.compile(r"Paid (\d+,?\d*\.?\d*) RWF to (.*?)\. Your new balance is")
            ],
            "Transfers to Mobile Numbers": [
                re.compile(r"You have sent (\d+,?\d*\.?\d*) RWF to (.*?)\. Your new balance is"),
                re.compile(r"Sent (\d+,?\d*\.?\d*) RWF to (.*?)\. New balance is")
            ],
            "Bank Deposits": [
                re.compile(r"(\d+,?\d*\.?\d*) RWF has been added to your mobile money account at .*? from (.*?)\. Your NEW BALANCE"),
                re.compile(r"Deposit of (\d+,?\d*\.?\d*) RWF from (.*?)\. Your new balance is")
            ],
            "Airtime Bill Payments": [
                re.compile(r"You have bought airtime worth (\d+,?\d*\.?\d*) RWF for (.*?)\. Your new balance is")
            ],
            "Transactions Initiated by Third Parties": [
                re.compile(r"(\d+,?\d*\.?\d*) RWF has been deducted from your mobile money account by (.*?)\. Your new balance is")
            ],
            "Withdrawals from Agents": [
                re.compile(r"You have withdrawn (\d+,?\d*\.?\d*) RWF from (.*?)\. Your new balance is")
            ]
        }

    def parse_sms_body(self, sms_body: str) -> Dict[str, Any]:
        """
        Parse SMS body and extract transaction details using regex patterns.
        
        Args:
            sms_body (str): The raw SMS message body
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted transaction details
        """
        transaction_data = {
            "type": "Unknown",
            "amount": None,
            "sender": None,
            "receiver": None,
            "balance": None,
            "fee": None,
            "transaction_id": None,
            "status": "Processed"
        }

        try:
            # Extract balance and transaction ID (common patterns)
            balance_match = re.search(r"balance is (\d+,?\d*\.?\d*) RWF", sms_body)
            if balance_match:
                transaction_data["balance"] = float(balance_match.group(1).replace(",", ""))

            fee_match = re.search(r"Fee: (\d+,?\d*\.?\d*) RWF", sms_body)
            if fee_match:
                transaction_data["fee"] = float(fee_match.group(1).replace(",", ""))
            else:
                transaction_data["fee"] = 0.0

            id_match = re.search(r"Ref: (\w+)|ID: (\w+)|TrxID: (\w+)|TransID: (\w+)", sms_body)
            if id_match:
                transaction_data["transaction_id"] = next(filter(None, id_match.groups()), None)

            # Determine transaction type and extract specific details
            for sms_type, regex_list in self.patterns.items():
                for pattern in regex_list:
                    match = pattern.search(sms_body)
                    if match:
                        transaction_data["type"] = sms_type
                        amount_str = match.group(1).replace(",", "")
                        transaction_data["amount"] = float(amount_str)
                        
                        # Determine sender/receiver based on type
                        if sms_type in ["Incoming Money", "Bank Deposits"]:
                            transaction_data["sender"] = match.group(2).strip()
                            transaction_data["receiver"] = "You"
                        elif sms_type in ["Payments to Code Holders", "Transfers to Mobile Numbers", 
                                        "Airtime Bill Payments", "Transactions Initiated by Third Parties", 
                                        "Withdrawals from Agents"]:
                            transaction_data["sender"] = "You"
                            transaction_data["receiver"] = match.group(2).strip()
                        
                        return transaction_data

            # If no specific pattern matched, try to extract amount if present
            if transaction_data["type"] == "Unknown":
                amount_match = re.search(r"(\d+,?\d*\.?\d*) RWF", sms_body)
                if amount_match:
                    transaction_data["amount"] = float(amount_match.group(1).replace(",", ""))
                    transaction_data["status"] = "Partially Processed"
                else:
                    transaction_data["status"] = "Unprocessed"

        except Exception as e:
            logging.error(f"Error processing SMS body: {str(e)}")
            transaction_data["status"] = "Error"
            transaction_data["error_message"] = str(e)

        return transaction_data

    def process_xml_data(self, xml_file_path: str, output_json_path: str, unprocessed_log_path: str) -> Dict[str, int]:
        """
        Process XML file containing SMS messages and extract transaction data.
        
        Args:
            xml_file_path (str): Path to the input XML file
            output_json_path (str): Path to save processed data
            unprocessed_log_path (str): Path to save unprocessed messages
            
        Returns:
            Dict[str, int]: Statistics about the processing results
        """
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            processed_sms_data = []
            unprocessed_messages = []
            error_messages = []

            for sms in root.findall("sms"):
                try:
                    sms_body = sms.get("body")
                    sms_date_ms = int(sms.get("date"))
                    sms_date = datetime.fromtimestamp(sms_date_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    sms_type_raw = sms.get("type")

                    parsed_data = self.parse_sms_body(sms_body)
                    
                    # Add original SMS attributes and clean up
                    transaction = {
                        "raw_body": sms_body,
                        "date": sms_date,
                        "original_type": sms_type_raw,
                        **parsed_data
                    }

                    if parsed_data["status"] == "Unprocessed":
                        unprocessed_messages.append(transaction)
                    elif parsed_data["status"] == "Error":
                        error_messages.append(transaction)
                    else:
                        processed_sms_data.append(transaction)

                except Exception as e:
                    logging.error(f"Error processing SMS element: {str(e)}")
                    error_messages.append({
                        "raw_body": sms_body,
                        "error": str(e)
                    })

            # Save processed data
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(processed_sms_data, f, indent=4, ensure_ascii=False)

            # Save unprocessed messages
            with open(unprocessed_log_path, "w", encoding="utf-8") as f:
                json.dump({
                    "unprocessed": unprocessed_messages,
                    "errors": error_messages
                }, f, indent=4, ensure_ascii=False)

            stats = {
                "processed": len(processed_sms_data),
                "unprocessed": len(unprocessed_messages),
                "errors": len(error_messages)
            }

            logging.info(f"Processing complete. Stats: {stats}")
            return stats

        except Exception as e:
            logging.error(f"Error processing XML file: {str(e)}")
            raise

def main():
    processor = SMSProcessor()
    xml_file = "data/modified_sms_v2.xml"
    output_json = "data/processed_sms_data.json"
    unprocessed_log = "data/unprocessed_sms_messages.log"
    
    try:
        stats = processor.process_xml_data(xml_file, output_json, unprocessed_log)
        print("\nProcessing Summary:")
        print(f"Successfully processed: {stats['processed']} messages")
        print(f"Unprocessed messages: {stats['unprocessed']}")
        print(f"Errors encountered: {stats['errors']}")
        print(f"\nProcessed data saved to: {output_json}")
        print(f"Unprocessed messages logged to: {unprocessed_log}")
    except Exception as e:
        print(f"Error: {str(e)}")
        logging.error(f"Main process error: {str(e)}")

if __name__ == "__main__":
    main() 