from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db, Transaction, TransactionType
from sqlalchemy import func, case
from datetime import datetime
from contextlib import contextmanager

app = Flask(__name__)

# Configure CORS to be more permissive for development
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Accept"],
         "supports_credentials": True,
         "expose_headers": ["Content-Type", "Accept"]
     }},
     supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API is running'}), 200

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    with get_db_session() as db:
        # Get filter parameters from request arguments
        transaction_type = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search_term = request.args.get('search')

        # Base query
        query = db.query(
            Transaction,
            TransactionType.name.label('type_name')
        ).join(
            TransactionType,
            Transaction.type_id == TransactionType.id
        )

        # Apply filters
        if transaction_type and transaction_type != 'all':
            query = query.filter(TransactionType.name == transaction_type)
        
        if start_date:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d'))
            
        if end_date:
            query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d'))
            
        if search_term:
            search_like = f'%{search_term}%'
            query = query.filter(
                (Transaction.raw_body.ilike(search_like)) |
                (Transaction.sender.ilike(search_like)) |
                (Transaction.receiver.ilike(search_like))
            )

        # Order by date descending
        query = query.order_by(Transaction.date.desc())
        
        # Execute query and format results
        transactions = query.all()
        result = []
        for transaction, type_name in transactions:
            transaction_dict = {
                'id': transaction.id,
                'transaction_id': transaction.transaction_id,
                'type_name': type_name,
                'date': transaction.date.isoformat(),
                'amount': float(transaction.amount),
                'fee': float(transaction.fee) if transaction.fee else None,
                'balance': float(transaction.balance) if transaction.balance else None,
                'sender': transaction.sender,
                'receiver': transaction.receiver,
                'raw_body': transaction.raw_body,
                'status': transaction.status
            }
            result.append(transaction_dict)

        return jsonify(result)

@app.route('/api/summary', methods=['GET'])
def get_summary():
    with get_db_session() as db:
        # Overall statistics
        overall_stats = db.query(
            func.count(Transaction.id).label('total_transactions'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount'),
            func.sum(Transaction.fee).label('total_fees')
        ).first()

        # Transactions by type
        transactions_by_type = db.query(
            TransactionType.name,
            func.count(Transaction.id).label('count')
        ).join(
            Transaction,
            Transaction.type_id == TransactionType.id
        ).group_by(
            TransactionType.name
        ).order_by(
            func.count(Transaction.id).desc()
        ).all()

        # Monthly transaction volume
        monthly_volume = db.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total_amount')
        ).group_by(
            func.strftime('%Y-%m', Transaction.date)
        ).order_by(
            func.strftime('%Y-%m', Transaction.date)
        ).all()

        # Payments vs. Deposits
        payments_deposits = db.query(
            case(
                (TransactionType.name.in_(['Incoming Money', 'Bank Deposits']), 'Deposits'),
                else_='Payments'
            ).label('category'),
            func.sum(Transaction.amount).label('total_amount')
        ).join(
            TransactionType,
            Transaction.type_id == TransactionType.id
        ).group_by(
            'category'
        ).all()

        summary_data = {
            'total_stats': {
                'total_transactions': overall_stats.total_transactions,
                'total_amount': float(overall_stats.total_amount) if overall_stats.total_amount else 0,
                'avg_amount': float(overall_stats.avg_amount) if overall_stats.avg_amount else 0,
                'total_fees': float(overall_stats.total_fees) if overall_stats.total_fees else 0
            },
            'transactions_by_type': [
                {'name': name, 'count': count}
                for name, count in transactions_by_type
            ],
            'monthly_volume': [
                {'month': month, 'total_amount': float(total_amount)}
                for month, total_amount in monthly_volume
            ],
            'payments_deposits': [
                {'category': category, 'total_amount': float(total_amount)}
                for category, total_amount in payments_deposits
            ]
        }
        
        return jsonify(summary_data)

@app.route('/api/transaction-types', methods=['GET'])
def get_transaction_types():
    with get_db_session() as db:
        transaction_types = db.query(TransactionType).all()
        return jsonify([{
            'id': t.id,
            'name': t.name
        } for t in transaction_types])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)