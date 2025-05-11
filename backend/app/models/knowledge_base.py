"""
Knowledge Base model
"""
import uuid
import time
import logging
from typing import Dict, List, Optional, Any, ClassVar

import boto3
from boto3.dynamodb.conditions import Key, Attr

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class KnowledgeBase:
    """
    KnowledgeBase model for storing learned answers in DynamoDB
    
    Attributes:
        question_id: Unique identifier for the knowledge entry
        question: The customer's question
        answer: The supervisor's answer
        created_at: When the knowledge was added
        source_request_id: Reference to original help request
        confidence: Confidence score for the answer
    """
    
    # DynamoDB table name
    table_name: ClassVar[str] = "KnowledgeBase"
    
    # DynamoDB client and table (initialized in init_table class method)
    dynamodb = None
    table = None
    
    def __init__(self, question_id: Optional[str] = None, question: Optional[str] = None,
                 answer: Optional[str] = None, created_at: Optional[int] = None,
                 source_request_id: Optional[str] = None, confidence: Optional[float] = None):
        """
        Initialize a knowledge base entry
        
        Args:
            question_id: Unique identifier for the knowledge entry
            question: The customer's question
            answer: The supervisor's answer
            created_at: When the knowledge was added
            source_request_id: Reference to original help request
            confidence: Confidence score for the answer
        """
        self.question_id = question_id or str(uuid.uuid4())
        self.question = question
        self.answer = answer
        self.created_at = created_at or int(time.time())
        self.source_request_id = source_request_id
        self.confidence = confidence or 1.0  # Default high confidence for supervisor-provided answers
    
    @classmethod
    async def init_table(cls) -> bool:
        """
        Initialize the DynamoDB table
        
        Returns:
            bool: True if successful
        """
        try:
            if cls.dynamodb is None:
                # Initialize DynamoDB client
                cls.dynamodb = boto3.resource(
                    'dynamodb',
                    endpoint_url=settings.DYNAMODB_ENDPOINT,
                    region_name=settings.DYNAMODB_REGION,
                    aws_access_key_id=settings.DYNAMODB_ACCESS_KEY,
                    aws_secret_access_key=settings.DYNAMODB_SECRET_KEY
                )
                
                # Check if table exists, create if not
                existing_tables = [table.name for table in cls.dynamodb.tables.all()]
                
                if cls.table_name not in existing_tables:
                    logger.info(f"Creating DynamoDB table: {cls.table_name}")
                    
                    cls.table = cls.dynamodb.create_table(
                        TableName=cls.table_name,
                        KeySchema=[
                            {'AttributeName': 'question_id', 'KeyType': 'HASH'}  # Primary key
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'question_id', 'AttributeType': 'S'}
                        ],
                        ProvisionedThroughput={
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    )
                    
                    # Wait for table to be created
                    cls.table.wait_until_exists()
                    logger.info(f"DynamoDB table {cls.table_name} created successfully")
                else:
                    cls.table = cls.dynamodb.Table(cls.table_name)
                    logger.info(f"Using existing DynamoDB table: {cls.table_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing DynamoDB table: {e}")
            return False
    
    async def save(self) -> bool:
        """
        Save the knowledge base entry to DynamoDB
        
        Returns:
            bool: True if successful
        """
        try:
            # Ensure table is initialized
            if not self.table:
                await self.init_table()
            
            # Prepare item for DynamoDB
            item = {
                'question_id': self.question_id,
                'question': self.question,
                'answer': self.answer,
                'created_at': self.created_at,
                'confidence': float(self.confidence)  # Ensure it's a float for DynamoDB
            }
            
            # Add optional fields
            if self.source_request_id:
                item['source_request_id'] = self.source_request_id
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            logger.info(f"Saved knowledge base entry {self.question_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving knowledge base entry: {e}")
            return False
    
    @classmethod
    async def get_by_id(cls, question_id: str) -> Optional['KnowledgeBase']:
        """
        Get a knowledge base entry by ID
        
        Args:
            question_id: Question identifier
        
        Returns:
            KnowledgeBase: The knowledge base entry if found, None otherwise
        """
        try:
            # Ensure table is initialized
            if not cls.table:
                await cls.init_table()
            
            # Get item from DynamoDB
            response = cls.table.get_item(Key={'question_id': question_id})
            item = response.get('Item')
            
            if not item:
                return None
            
            # Convert item to KnowledgeBase instance
            return cls(**item)
            
        except Exception as e:
            logger.error(f"Error getting knowledge base entry by ID: {e}")
            return None
    
    @classmethod
    async def get_all(cls, limit: int = 100) -> List['KnowledgeBase']:
        """
        Get all knowledge base entries
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List[KnowledgeBase]: List of knowledge base entries
        """
        try:
            # Ensure table is initialized
            if not cls.table:
                await cls.init_table()
            
            # Scan the table (note: scanning can be expensive for large tables)
            response = cls.table.scan(Limit=limit)
            
            # Convert items to KnowledgeBase instances
            entries = []
            for item in response.get('Items', []):
                entries.append(cls(**item))
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting all knowledge base entries: {e}")
            return []
    
    @classmethod
    async def find_similar(cls, question: str, threshold: float = 0.7) -> List['KnowledgeBase']:
        """
        Find similar questions in the knowledge base
        
        In production, this would use vector embeddings or more sophisticated matching
        For simplicity, this does basic string matching
        
        Args:
            question: Question to search for
            threshold: Similarity threshold
        
        Returns:
            List[KnowledgeBase]: List of matching knowledge base entries
        """
        try:
            # Get all entries (in production, this would use a vector database)
            all_entries = await cls.get_all()
            
            # Simplified similarity check - in production this would be more sophisticated
            matches = []
            question_lower = question.lower()
            
            for entry in all_entries:
                entry_question_lower = entry.question.lower()
                
                # Very simple similarity: check if words overlap
                question_words = set(question_lower.split())
                entry_words = set(entry_question_lower.split())
                
                # Calculate similarity
                if len(question_words) > 0:
                    intersection = question_words.intersection(entry_words)
                    similarity = len(intersection) / len(question_words)
                    
                    if similarity >= threshold:
                        matches.append(entry)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding similar questions: {e}")
            return []
    
    async def update(self, answer: Optional[str] = None, confidence: Optional[float] = None) -> bool:
        """
        Update the knowledge base entry
        
        Args:
            answer: New answer
            confidence: New confidence score
        
        Returns:
            bool: True if successful
        """
        try:
            # Ensure table is initialized
            if not self.table:
                await self.init_table()
            
            # Prepare update expression
            update_expression = "SET "
            expression_attribute_values = {}
            
            if answer:
                update_expression += "answer = :answer, "
                expression_attribute_values[':answer'] = answer
                self.answer = answer
            
            if confidence is not None:
                update_expression += "confidence = :confidence, "
                expression_attribute_values[':confidence'] = float(confidence)
                self.confidence = confidence
            
            # Remove trailing comma and space
            update_expression = update_expression[:-2]
            
            # Update in DynamoDB
            if expression_attribute_values:
                self.table.update_item(
                    Key={'question_id': self.question_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
                logger.info(f"Updated knowledge base entry {self.question_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating knowledge base entry: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the knowledge base entry to a dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = {
            'question_id': self.question_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at,
            'confidence': self.confidence
        }
        
        if self.source_request_id:
            data['source_request_id'] = self.source_request_id
        
        return data