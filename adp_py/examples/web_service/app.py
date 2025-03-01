"""
@ai-metadata {
    "domain": "example-web-service",
    "name": "UserService",
    "description": "A sample web service demonstrating ADP metadata usage",
    "serviceBoundary": {
        "service": "UserService",
        "teamOwner": "Auth Team",
        "onCallRotation": "team-auth-oncall",
        "serviceType": "REST API"
    },
    "dependencies": ["database.py", "auth_client.py"],
    "techDebt": [
        {
            "issue": "Error handling needs improvement",
            "priority": "medium",
            "description": "Current error handling is basic. Should add more detailed error responses and logging."
        }
    ],
    "performance": [
        {
            "consideration": "Database connection pooling",
            "description": "Uses connection pooling to minimize database connection overhead."
        }
    ],
    "dataHandling": [
        {
            "dataType": "User PII",
            "sensitivity": "high",
            "description": "Contains personally identifiable information that must be handled according to privacy policies.",
            "encryption": "at-rest and in-transit"
        }
    ]
}
"""

from flask import Flask, request, jsonify
import os
import jwt
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional, Union

from adp_py.examples.web_service.database import UserDatabase, User
from adp_py.examples.web_service.auth_client import AuthClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'development-secret-key')
DB_CONNECTION = os.environ.get('DB_CONNECTION', 'sqlite:///users.db')
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001')

# Initialize components
user_db = UserDatabase(DB_CONNECTION)
auth_client = AuthClient(AUTH_SERVICE_URL)


@app.route('/health', methods=['GET'])
def health_check():
    """
    @ai-metadata {
        "description": "Health check endpoint for the service",
        "name": "health_check",
        "dataHandling": [
            {
                "dataType": "System health",
                "sensitivity": "low",
                "description": "Basic system health information"
            }
        ]
    }
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/users', methods=['GET'])
def get_users():
    """
    @ai-metadata {
        "description": "Retrieves a list of users with pagination",
        "name": "get_users",
        "dataHandling": [
            {
                "dataType": "User list",
                "sensitivity": "medium",
                "description": "Returns minimal user data (id, username, email)",
                "filtering": "Personal details are excluded"
            }
        ],
        "performance": [
            {
                "consideration": "Database query optimization",
                "description": "Uses pagination and limited fields to optimize query performance"
            }
        ]
    }
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        users = user_db.get_users(page=page, limit=limit)
        
        return jsonify({
            'users': [user.to_dict(exclude_sensitive=True) for user in users],
            'page': page,
            'limit': limit,
            'total': user_db.count_users()
        })
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    """
    @ai-metadata {
        "description": "Retrieves a single user by ID",
        "name": "get_user",
        "dataHandling": [
            {
                "dataType": "User details",
                "sensitivity": "high",
                "description": "Returns complete user profile data"
            }
        ]
    }
    """
    try:
        user = user_db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()})
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500


@app.route('/users', methods=['POST'])
def create_user():
    """
    @ai-metadata {
        "description": "Creates a new user",
        "name": "create_user",
        "dataHandling": [
            {
                "dataType": "User registration data",
                "sensitivity": "high",
                "description": "Processes and stores new user data",
                "validation": "Input validation is performed"
            }
        ],
        "techDebt": [
            {
                "issue": "Password complexity validation",
                "priority": "high",
                "description": "Need to implement better password complexity rules"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        if user_db.get_user_by_email(data['email']):
            return jsonify({'error': 'User with this email already exists'}), 409
        
        if user_db.get_user_by_username(data['username']):
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create the user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=auth_client.hash_password(data['password']),
            created_at=datetime.now()
        )
        
        user_id = user_db.create_user(new_user)
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500


@app.route('/login', methods=['POST'])
def login():
    """
    @ai-metadata {
        "description": "Authenticates a user and provides a JWT token",
        "name": "login",
        "dataHandling": [
            {
                "dataType": "Authentication credentials",
                "sensitivity": "high",
                "description": "Processes login credentials and returns authentication token",
                "security": "Passwords are never returned or logged"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Get the user
        user = user_db.get_user_by_email(data['email'])
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not auth_client.verify_password(data['password'], user.password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = generate_token(user)
        
        return jsonify({
            'token': token,
            'user_id': user.id,
            'username': user.username
        })
    
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


def generate_token(user: User) -> str:
    """
    @ai-metadata {
        "description": "Generates a JWT token for authenticated users",
        "name": "generate_token",
        "dataHandling": [
            {
                "dataType": "Authentication token",
                "sensitivity": "high",
                "description": "Creates secure token containing user identity"
            }
        ]
    }
    """
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 