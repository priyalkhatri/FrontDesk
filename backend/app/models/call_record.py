"""
Call Record model
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

class CallRecord:
    """
    CallRecord model for storing call information in DynamoDB
    
    Attributes:
        call_id: Unique identifier for the call
        customer_id: Customer identifier
        customer_phone: Customer phone number
        timestamp: When the call started
        duration: Call duration in seconds
        transcript: List of conversation entries
        status: "in_progress" or "completed"
        direction: "inbound" or "outbound"
    """
    
    # DynamoDB table name
    table_name: ClassVar[str] = "CallRecords"
    
    # DynamoDB client and table (initialized in init_table class method)
    dynamodb = None
    table = None
    
    def __init__(self, call_id: Optional[str] = None, customer_id: Optional[str] = None,
                 customer_phone: Optional[str] = None, timestamp: Optional[int] = None,
                 duration: Optional[int] = None, transcript: Optional[List[dict]] = None,
                 status: Optional[str] = None, direction: Optional[str] = None):
        """
        Initialize a call record
        
        Args:
            call_id: Unique identifier for the call
            customer_id: Customer identifier
            customer_phone: Customer phone number
            timestamp: When the call started
            duration: Call duration in seconds
            transcript: List of conversation entries
            status: "in_progress" or "completed"
            direction: "inbound" or "outbound"
        """
        self.call_id = call_id or str(uuid.uuid4())
        self.customer_id = customer_id
        self.customer_phone = customer_phone
        self.timestamp = timestamp or int(time.time())
        self.duration = duration
        self.transcript = transcript or []
        self.status = status or "in_progress"
        self.direction = direction or "inbound"
    
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
                            {'AttributeName': 'call_id', 'KeyType': 'HASH'}  # Primary key
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'call_id', 'AttributeType': 'S'},
                            {'AttributeName': 'customer_id', 'AttributeType': 'S'},
                            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'CustomerIndex',
                                'KeySchema': [
                                    {'AttributeName': 'customer_id', 'KeyType': 'HASH'},
                                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'},
                                'ProvisionedThroughput': {
                                    'ReadCapacityUnits': 5,
                                    'WriteCapacityUnits': 5
                                }
                            }
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
        Save the call record to DynamoDB
        
        Returns:
            bool: True if successful
        """
        try:
            # Ensure table is initialized
            if not self.table:
                await self.init_table()
            
            # Prepare item for DynamoDB
            item = {
                'call_id': self.call_id,
                'customer_id': self.customer_id,
                'customer_phone': self.customer_phone,
                'timestamp': self.timestamp,
                'status': self.status,
                'direction': self.direction
            }
            
            # Add optional fields
            if self.duration is not None:
                item['duration'] = self.duration
            
            if self.transcript:
                item['transcript'] = self.transcript
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            logger.info(f"Saved call record {self.call_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving call record: {e}")
            return False
    
    @classmethod
    async def get_by_id(cls, call_id: str) -> Optional['CallRecord']:
        """
        Get a call record by ID
        
        Args:
            call_id: Call identifier
        
        Returns:
            CallRecord: The call record if found, None otherwise
        """
        try:
            # Ensure table is initialized
            if not cls.table:
                await cls.init_table()
            
            # Get item from DynamoDB
            response = cls.table.get_item(Key={'call_id': call_id})
            item = response.get('Item')
            
            if not item:
                return None
            
            # Convert item to CallRecord instance
            return cls(**item)
            
        except Exception as e:
            logger.error(f"Error getting call record by ID: {e}")
            return None
    
    async def add_transcript_entry(self, speaker: str, text: str) -> bool:
        """
        Add a new entry to the call transcript
        
        Args:
            speaker: Speaker identifier ("customer" or "ai")
            text: Text of the utterance
        
        Returns:
            bool: True if successful
        """
        try:
            # Add to local transcript
            entry = {
                'timestamp': int(time.time()),
                'speaker': speaker,
                'text': text
            }
            
            self.transcript.append(entry)
            
            # Update in DynamoDB
            if not self.table:
                await self.init_table()
            
            self.table.update_item(
                Key={'call_id': self.call_id},
                UpdateExpression="SET transcript = :transcript",
                ExpressionAttributeValues={':transcript': self.transcript}
            )
            
            logger.debug(f"Added transcript entry to call {self.call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding transcript entry: {e}")
            return False
    
    async def complete_call(self, duration: int) -> bool:
        """
        Mark a call as completed
        
        Args:
            duration: Call duration in seconds
        
        Returns:
            bool: True if successful
        """
        try:
            # Update local state
            self.status = "completed"
            self.duration = duration
            
            # Update in DynamoDB
            if not self.table:
                await self.init_table()
            
            self.table.update_item(
                Key={'call_id': self.call_id},
                UpdateExpression="SET #status = :status, duration = :duration",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': self.status,
                    ':duration': self.duration
                }
            )
            
            logger.info(f"Completed call {self.call_id}, duration: {duration} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error completing call: {e}")
            return False
    
    @classmethod
    async def get_by_customer(cls, customer_id: str, limit: int = 20) -> List['CallRecord']:
        """
        Get all calls for a specific customer
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of results
        
        Returns:
            List[CallRecord]: List of call records
        """
        try:
            # Ensure table is initialized
            if not cls.table:
                await cls.init_table()
            
            # Query by customer using the GSI
            response = cls.table.query(
                IndexName='CustomerIndex',
                KeyConditionExpression=Key('customer_id').eq(customer_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            # Convert items to CallRecord instances
            calls = []
            for item in response.get('Items', []):
                calls.append(cls(**item))
            
            return calls
            
        except Exception as e:
            logger.error(f"Error getting calls by customer: {e}")
            return []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the call record to a dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = {
            'call_id': self.call_id,
            'customer_id': self.customer_id,
            'customer_phone': self.customer_phone,
            'timestamp': self.timestamp,
            'status': self.status,
            'direction': self.direction
        }
        
        if self.duration is not None:
            data['duration'] = self.duration
        
        if self.transcript:
            data['transcript'] = self.transcript
        
        return data