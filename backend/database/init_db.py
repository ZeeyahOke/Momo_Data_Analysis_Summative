import logging
from sqlalchemy.orm import Session
from .models import Base, engine, TransactionType, Transaction
from datetime import datetime
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_default_transaction_types():
    """Return a list of default transaction types"""
    return [
        "Incoming Money",
        "Payments to Code Holders",
        "Transfers to Mobile Numbers",
        "Bank Deposits",
        "Airtime Bill Payments",
        "Transactions Initiated by Third Parties",
        "Withdrawals from Agents",
        "Unknown"
    ]

def init_db():
    """Initialize the database and create tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise

def seed_transaction_types(db: Session):
    """Seed the transaction types table with default values"""
    try:
        # Check if transaction types already exist
        existing_types = db.query(TransactionType).count()
        if existing_types > 0:
            logging.info("Transaction types already exist in the database")
            return

        # Add default transaction types
        for type_name in get_default_transaction_types():
            transaction_type = TransactionType(name=type_name)
            db.add(transaction_type)

        # Commit the changes
        db.commit()
        logging.info(f"Successfully added {len(get_default_transaction_types())} transaction types")

    except Exception as e:
        db.rollback()
        logging.error(f"Error seeding transaction types: {str(e)}")
        raise

def load_transactions(db: Session, json_file_path: str):
    """Load transactions from JSON file into the database"""
    try:
        # Verify file exists
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Processed data file not found at: {json_file_path}")

        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            transactions_data = json.load(f)

        # Get transaction type mapping
        type_mapping = {t.name: t.id for t in db.query(TransactionType).all()}

        # Process each transaction
        for tx_data in transactions_data:
            try:
                # Validate required fields
                required_fields = ['transaction_id', 'type', 'date', 'amount', 'raw_body', 'status']
                missing_fields = [field for field in required_fields if field not in tx_data]
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                # Convert date string to datetime object
                try:
                    tx_date = datetime.strptime(tx_data['date'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError(f"Invalid date format: {tx_data['date']}")

                # Validate transaction type
                if tx_data['type'] not in type_mapping:
                    raise ValueError(f"Invalid transaction type: {tx_data['type']}")

                # Validate numeric fields
                try:
                    amount = float(tx_data['amount'])
                    fee = float(tx_data['fee']) if tx_data.get('fee') else 0.0
                    balance = float(tx_data['balance']) if tx_data.get('balance') else None
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid numeric value in transaction {tx_data['transaction_id']}")

                # Create transaction record
                transaction = Transaction(
                    transaction_id=tx_data['transaction_id'],
                    type_id=type_mapping[tx_data['type']],
                    date=tx_date,
                    amount=amount,
                    fee=fee,
                    balance=balance,
                    sender=tx_data.get('sender'),
                    receiver=tx_data.get('receiver'),
                    raw_body=tx_data['raw_body'],
                    status=tx_data['status']
                )
                db.add(transaction)

            except ValueError as e:
                logging.error(f"Error processing transaction: {str(e)}")
                raise  # Re-raise the ValueError to be caught by the caller

        # Commit all transactions
        db.commit()
        logging.info(f"Successfully loaded {len(transactions_data)} transactions")

    except Exception as e:
        db.rollback()
        logging.error(f"Error loading transactions: {str(e)}")
        raise

def initialize_database(json_file_path: str = 'data/processed_sms_data.json'):
    """Initialize the database and load all data"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Initialize database
        init_db()
        
        # Seed transaction types
        seed_transaction_types(db)
        
        # Load transactions
        load_transactions(db, json_file_path)
        
        logging.info("Database initialization completed successfully")
    
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database() 