from setuptools import setup, find_packages

setup(
    name="sms-dashboard-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask==3.0.0",
        "Flask-CORS==4.0.0",
        "python-dotenv==1.0.0",
        "SQLAlchemy==1.4.54",
        "Werkzeug==3.0.1",
        "pytest==7.4.3",
        "black==23.11.0",
        "flake8==6.1.0"
    ],
    python_requires=">=3.8",
) 