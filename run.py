"""
Merculy Backend - Application Entry Point
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
