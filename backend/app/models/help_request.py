"""
Help Request model
"""
import uuid
import time
import logging
from typing import Dict, List, Optional, Any, ClassVar

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import asyncio

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class HelpRequest:
    """
    HelpRequest model for storing help requests in DynamoDB
    
    Attributes:
        request_id: Unique identifier for the request
        question: The customer's question
        call_id: Reference to the call
        customer_id: Customer identifier
        customer_phone: Customer contact info
        status: "pending", "resolved", or "unresolved"
        timestamp: When the request was created
        answer: Optional answer from supervisor
        resolved_at: Optional timestamp when the request was resolved
    """
    
    # DynamoDB table name
    table_name: ClassVar[str] = "HelpRequests"
    
    # DynamoDB client and table (initialized in init_table class method)
    dynamodb = None
    table = None
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        question: Optional[str] = None,
        call_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        status: Optional[str] = None,
        timestamp: Optional[int] = None,
        answer: Optional[str] = None,
        resolved_at: Optional[int] = None,
        resolvedAt: Optional[int] = None  # Handle both camelCase and snake_case
    ):
        """
        Initialize a help request
        
        Args:
            request_id: Unique identifier for the request
            question: The customer's question
            call_id: Reference to the call
            customer_id: Customer identifier
            customer_phone: Customer contact info
            status: "pending", "resolved", or "unresolved"
            timestamp: When the request was created
            answer: Optional answer from supervisor
            resolved_at: Optional timestamp when the request was resolved
            resolvedAt: Alternative camelCase version of resolved_at
        """
        self.request_id = request_id or str(uuid.uuid4())
        self.question = question
        self.call_id = call_id
        self.customer_id = customer_id
        self.customer_phone = customer_phone
        self.status = status or "pending"
        self.timestamp = timestamp or int(time.time())
        self.answer = answer
        # Use resolvedAt if provided, otherwise use resolved_at
        self.resolved_at = resolvedAt if resolvedAt is not None else resolved_at
        self.timeout_seconds = settings.HELP_REQUEST_TIMEOUT_SECONDS
    
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
            
            # Check if table exists
            existing_tables = [table.name for table in cls.dynamodb.tables.all()]
            
            if cls.table_name not in existing_tables:
                logger.info(f"Creating DynamoDB table: {cls.table_name}")
                
                # Create table with GSI
                cls.table = cls.dynamodb.create_table(
                    TableName=cls.table_name,
                    KeySchema=[
                        {'AttributeName': 'request_id', 'KeyType': 'HASH'}  # Primary key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'request_id', 'AttributeType': 'S'},
                        {'AttributeName': 'status', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'StatusIndex',
                            'KeySchema': [
                                {'AttributeName': 'status', 'KeyType': 'HASH'},
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
                
                # Verify GSI exists
                try:
                    response = cls.table.meta.client.describe_table(TableName=cls.table_name)
                    gsis = response['Table'].get('GlobalSecondaryIndexes', [])
                    status_index = next((gsi for gsi in gsis if gsi['IndexName'] == 'StatusIndex'), None)
                    
                    if not status_index:
                        logger.warning("StatusIndex GSI not found, creating it...")
                        # Use GlobalSecondaryIndexUpdates for updating existing table
                        cls.table.meta.client.update_table(
                            TableName=cls.table_name,
                            AttributeDefinitions=[
                                {'AttributeName': 'request_id', 'AttributeType': 'S'},
                                {'AttributeName': 'status', 'AttributeType': 'S'},
                                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                            ],
                            GlobalSecondaryIndexUpdates=[
                                {
                                    'Create': {
                                        'IndexName': 'StatusIndex',
                                        'KeySchema': [
                                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                                        ],
                                        'Projection': {'ProjectionType': 'ALL'},
                                        'ProvisionedThroughput': {
                                            'ReadCapacityUnits': 5,
                                            'WriteCapacityUnits': 5
                                        }
                                    }
                                }
                            ]
                        )
                        
                        # Wait for the GSI to be created and backfilled
                        logger.info("Waiting for StatusIndex GSI to be created and backfilled...")
                        while True:
                            response = cls.table.meta.client.describe_table(TableName=cls.table_name)
                            gsis = response['Table'].get('GlobalSecondaryIndexes', [])
                            status_index = next((gsi for gsi in gsis if gsi['IndexName'] == 'StatusIndex'), None)
                            
                            if status_index and status_index.get('IndexStatus') == 'ACTIVE':
                                logger.info("StatusIndex GSI is now active")
                                break
                            
                            logger.info("Waiting for StatusIndex GSI to become active...")
                            await asyncio.sleep(5)  # Wait 5 seconds before checking again
                        
                        logger.info("StatusIndex GSI created and backfilled successfully")
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    error_message = e.response['Error']['Message']
                    logger.error(f"Error verifying/creating GSI: {error_code} - {error_message}")
                    return False
                
                logger.info(f"Using existing DynamoDB table: {cls.table_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing DynamoDB table: {e}")
            return False
    
    async def save(self) -> bool:
        """
        Save the help request to DynamoDB
        
        Returns:
            bool: True if successful
        """
        try:
            # Ensure table is initialized
            if not self.table:
                await self.init_table()
            
            # Prepare item for DynamoDB
            item = {
                'request_id': self.request_id,
                'question': self.question,
                'call_id': self.call_id,
                'customer_id': self.customer_id,
                'customer_phone': self.customer_phone,
                'status': self.status,
                'timestamp': self.timestamp
            }
            
            # Add optional fields
            if self.answer:
                item['answer'] = self.answer
            if self.resolved_at:
                item['resolved_at'] = self.resolved_at
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            logger.info(f"Saved help request {self.request_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving help request: {e}")
            return False
    
    @classmethod
    async def get_by_id(cls, request_id: str) -> Optional['HelpRequest']:
        """
        Get a help request by ID
        
        Args:
            request_id: Request identifier
        
        Returns:
            HelpRequest: The help request if found, None otherwise
        """
        try:
            # Ensure table is initialized
            if not cls.table:
                await cls.init_table()
            
            # Get item from DynamoDB
            response = cls.table.get_item(Key={'request_id': request_id})
            item = response.get('Item')
            
            if not item:
                return None
            
            # Convert item to HelpRequest instance
            return cls(**item)
            
        except Exception as e:
            logger.error(f"Error getting help request by ID: {e}")
            return None
    
    @classmethod
    async def get_by_status(cls, status: str, limit: int = 50) -> List['HelpRequest']:
        """
        Get help requests by status
        
        Args:
            status: Status to filter by ("pending", "resolved", "unresolved")
            limit: Maximum number of results
        
        Returns:
            List[HelpRequest]: List of help requests
        """
        try:
            # Ensure table is initialized
            if not cls.table:
                success = await cls.init_table()
                if not success:
                    logger.error("Failed to initialize table")
                    return []
            
            # Query by status using the GSI
            response = cls.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression=Key('status').eq(status),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            # Convert items to HelpRequest instances
            requests = []
            for item in response.get('Items', []):
                requests.append(cls(**item))
            
            return requests
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"DynamoDB error: {error_code} - {error_message}")
            return []
        except Exception as e:
            logger.error(f"Error getting help requests by status: {e}")
            return []
    
    def is_timed_out(self) -> bool:
        """
        Check if the help request has timed out
        
        Returns:
            bool: True if timed out
        """
        current_time = int(time.time())
        return (self.status == "pending" and 
                (current_time - self.timestamp) > self.timeout_seconds)
    
    async def mark_unresolved(self) -> bool:
        """
        Mark the help request as unresolved
        
        Returns:
            bool: True if successful
        """
        self.status = "unresolved"
        return await self.save()
    
    @classmethod
    async def check_timeouts(cls) -> int:
        """
        Check for timed out requests and mark them as unresolved
        
        Returns:
            int: Number of requests that were marked as unresolved
        """
        try:
            # Get all pending requests
            pending_requests = await cls.get_by_status("pending")
            
            # Check each request for timeout
            timed_out_count = 0
            for request in pending_requests:
                if request.is_timed_out():
                    await request.mark_unresolved()
                    timed_out_count += 1
                    logger.info(f"Request {request.request_id} marked as timed out")
            
            return timed_out_count
            
        except Exception as e:
            logger.error(f"Error checking timeouts: {e}")
            return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the help request to a dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = {
            'request_id': self.request_id,
            'question': self.question,
            'call_id': self.call_id,
            'customer_id': self.customer_id,
            'customer_phone': self.customer_phone,
            'status': self.status,
            'timestamp': self.timestamp
        }
        
        if self.answer:
            data['answer'] = self.answer
        
        return data