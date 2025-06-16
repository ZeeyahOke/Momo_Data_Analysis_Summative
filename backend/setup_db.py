import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, TransactionType
from database.init_db import seed_transaction_types, load_transactions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_database():
    """Set up the database from scratch"""
    # Create engine and session
    engine = create_engine('sqlite:///sms_data.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Drop all tables and recreate them
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        logging.info("Database tables recreated successfully")

        # Seed transaction types
        seed_transaction_types(db)
        logging.info("Transaction types seeded successfully")

        # Load transactions
        load_transactions(db, 'data/processed_sms_data.json')
        logging.info("Transactions loaded successfully")

    except Exception as e:
        logging.error(f"Error setting up database: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_database() 