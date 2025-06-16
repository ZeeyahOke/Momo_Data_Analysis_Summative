# Momo Transaction Dashboard

A web application for visualizing and analyzing SMS transaction data from mobile money services.

## Features

- Transaction history visualization
- Transaction type filtering
- Date range filtering
- Search functionality
- Transaction statistics and charts
- Detailed transaction view

## Link To Demo Video
- https://vimeo.com/1093534312/60975a0067?ts=0&share=copy

## Prerequisites

- Python 3.8 or higher
- Git Bash (for Windows users)
- An XML file containing your MTN MoMo SMS data

## Project Structure


sms_dashboard/
├── backend/
│   ├── data/
│   │   ├── modified_sms_v2.xml        # Raw SMS data
│   │   └── processed_sms_data.json    # Processed transaction data
│   ├── database/
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   └── transaction.py
│   │   └── init_db.py
│   ├── app.py                         # Flask backend
│   ├── process_sms.py                 # SMS data processor
│   └── setup_db.py                    # Database setup script
└── frontend/
    ├── index.html
    ├── styles.css
    └── script.js


## Setup Instructions

1. Clone the repository:
bash
git clone <repository-url>
cd sms_dashboard


2. Create and activate a virtual environment
bash
# On windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate


3. Install Python dependencies:
bash
cd backend
pip install -r requirements.txt


4. Process the SMS data:
bash
python process_sms.py

This will:
- Read the SMS data from data/modified_sms_v2.xml
- Process and parse the SMS messages
- Save the processed data to data/processed_sms_data.json
- Log any unprocessed messages to data/unprocessed_sms_messages.log

5. Initialize the database:
bash
python setup_db.py

This will:
- Create the database tables
- Seed the transaction types
- Load the processed transactions into the database

## Running the Application

1. Start the Flask backend:
bash
cd backend
python app.py

The backend server will start at http://127.0.0.1:5000

2. In a new terminal, start the frontend server:
bash
cd frontend
python -m http.server 8000

The frontend server will start at http://localhost:8000

3. Open your browser and navigate to http://localhost:8000

## API Endpoints

- GET /api/health - Health check endpoint
- GET /api/transactions - Get all transactions (with optional filters)
- GET /api/transaction-types - Get all transaction types
- GET /api/summary - Get transaction statistics and summary data

## Troubleshooting

1. If you see CORS errors in the browser console:
   - Make sure both frontend and backend servers are running
   - Clear your browser cache and refresh the page
   - Check that you're accessing the frontend via http://localhost:8000

2. If the database is empty or corrupted:
   - Delete the sms_data.db file
   - Run python setup_db.py again to reinitialize the database

3. If you see "No data available" messages:
   - Check that the SMS data was processed correctly
   - Verify that the database was initialized properly
   - Check the browser console for any API errors

## Development

- The frontend is built with vanilla JavaScript and uses Chart.js for visualizations
- The backend is built with Flask and SQLAlchemy
- The database is SQLite for simplicity

## Authors

- Fawziyyah Oke
- Betelhem Feleke Chelebo
- Arsene Kabasinga
- Yvan Nziza Rugamba