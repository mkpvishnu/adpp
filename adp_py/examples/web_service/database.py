"""
@ai-metadata {
    "name": "UserDatabase",
    "domain": "example-web-service",
    "description": "Database layer for the user service",
    "dependencies": [],
    "dataHandling": [
        {
            "dataType": "User data",
            "sensitivity": "high",
            "description": "Stores and retrieves user information from the database",
            "encryption": "at-rest"
        }
    ],
    "performance": [
        {
            "consideration": "Connection pooling",
            "description": "Uses SQLAlchemy's connection pooling to improve performance"
        },
        {
            "consideration": "Query optimization",
            "description": "Queries are optimized with appropriate indexes"
        }
    ]
}
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create the database model
Base = declarative_base()


class UserModel(Base):
    """
    @ai-metadata {
        "description": "SQLAlchemy model for user data",
        "scope_name": "database",
        "dataHandling": [
            {
                "dataType": "User authentication data",
                "sensitivity": "high",
                "description": "Maps to users table in the database"
            }
        ]
    }
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    bio = Column(Text, nullable=True)
    profile_image = Column(String(200), nullable=True)


@dataclass
class User:
    """
    @ai-metadata {
        "description": "Data class for user information",
        "name": "User",
        "dataHandling": [
            {
                "dataType": "User profile data",
                "sensitivity": "high",
                "description": "Represents user data in the application"
            }
        ]
    }
    """
    username: str
    email: str
    password: str
    created_at: datetime
    id: Optional[int] = None
    full_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    
    def to_dict(self, exclude_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user object to dictionary.
        
        Args:
            exclude_sensitive: Whether to exclude sensitive fields like password
        
        Returns:
            Dictionary representation of the user
        """
        result = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if not exclude_sensitive:
            result.update({
                'full_name': self.full_name,
                'bio': self.bio,
                'profile_image': self.profile_image
            })
        
        # Never include password
        
        return result


class UserDatabase:
    """
    @ai-metadata {
        "description": "Database access layer for user operations",
        "name": "UserDatabase",
        "dependencies": [],
        "dataHandling": [
            {
                "dataType": "User credentials",
                "sensitivity": "high",
                "description": "Manages user data persistence"
            }
        ]
    }
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the database connection.
        
        Args:
            connection_string: Database connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        logger.info("Database initialized")
    
    def get_users(self, page: int = 1, limit: int = 10) -> List[User]:
        """
        Get a paginated list of users.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of users per page
        
        Returns:
            List of User objects
        """
        session = self.Session()
        try:
            offset = (page - 1) * limit
            user_models = session.query(UserModel).order_by(UserModel.id).offset(offset).limit(limit).all()
            
            return [self._model_to_user(model) for model in user_models]
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return []
        finally:
            session.close()
    
    def count_users(self) -> int:
        """
        Count the total number of users.
        
        Returns:
            Total number of users
        """
        session = self.Session()
        try:
            return session.query(UserModel).count()
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            return 0
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID to find
        
        Returns:
            User object if found, None otherwise
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
            
            if not user_model:
                return None
            
            return self._model_to_user(user_model)
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: The email to find
        
        Returns:
            User object if found, None otherwise
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter(UserModel.email == email).first()
            
            if not user_model:
                return None
            
            return self._model_to_user(user_model)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: The username to find
        
        Returns:
            User object if found, None otherwise
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter(UserModel.username == username).first()
            
            if not user_model:
                return None
            
            return self._model_to_user(user_model)
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            return None
        finally:
            session.close()
    
    def create_user(self, user: User) -> int:
        """
        Create a new user.
        
        Args:
            user: The user to create
        
        Returns:
            The ID of the created user
        """
        session = self.Session()
        try:
            user_model = UserModel(
                username=user.username,
                email=user.email,
                password=user.password,
                full_name=user.full_name,
                created_at=user.created_at or datetime.utcnow(),
                bio=user.bio,
                profile_image=user.profile_image
            )
            
            session.add(user_model)
            session.commit()
            
            return user_model.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Update a user.
        
        Args:
            user_id: The ID of the user to update
            user_data: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
            
            if not user_model:
                return False
            
            # Update fields
            for key, value in user_data.items():
                if hasattr(user_model, key) and key != 'id':
                    setattr(user_model, key, value)
            
            user_model.updated_at = datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return False
        finally:
            session.close()
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: The ID of the user to delete
        
        Returns:
            True if successful, False otherwise
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
            
            if not user_model:
                return False
            
            session.delete(user_model)
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False
        finally:
            session.close()
    
    def _model_to_user(self, model: UserModel) -> User:
        """
        Convert a SQLAlchemy model to a User object.
        
        Args:
            model: The SQLAlchemy model
        
        Returns:
            User object
        """
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password=model.password,
            full_name=model.full_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            bio=model.bio,
            profile_image=model.profile_image
        ) 