"""
Test DynamoDB connection and basic operations
"""
import os
import sys
import asyncio
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_dynamodb_connection():
    """Test DynamoDB connection and basic operations"""
    try:
        # Print configuration (without sensitive data)
        logger.info(f"Using DynamoDB endpoint: {settings.DYNAMODB_ENDPOINT}")
        logger.info(f"Using AWS region: {settings.DYNAMODB_REGION}")
        logger.info(f"Using AWS access key: {settings.DYNAMODB_ACCESS_KEY[:4]}...")
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=settings.DYNAMODB_ENDPOINT,
            region_name=settings.DYNAMODB_REGION,
            aws_access_key_id=settings.DYNAMODB_ACCESS_KEY,
            aws_secret_access_key=settings.DYNAMODB_SECRET_KEY
        )
        
        # Test 1: List tables
        logger.info("Testing: List tables")
        try:
            tables = [table.name for table in dynamodb.tables.all()]
            logger.info(f"Available tables: {tables}")
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return False
        
        # Test 2: Create a test table
        test_table_name = "TestTable"
        logger.info(f"Testing: Create table {test_table_name}")
        
        try:
            # First, try to get the caller identity to verify credentials
            sts = boto3.client(
                'sts',
                endpoint_url=settings.DYNAMODB_ENDPOINT.replace('dynamodb', 'sts'),
                aws_access_key_id=settings.DYNAMODB_ACCESS_KEY,
                aws_secret_access_key=settings.DYNAMODB_SECRET_KEY,
                region_name=settings.DYNAMODB_REGION
            )
            identity = sts.get_caller_identity()
            logger.info(f"AWS Identity: {identity}")
            
            # Check if table already exists
            existing_tables = [table.name for table in dynamodb.tables.all()]
            if test_table_name in existing_tables:
                logger.info(f"Table {test_table_name} already exists, deleting it first")
                table = dynamodb.Table(test_table_name)
                table.delete()
                table.wait_until_not_exists()
            
            table = dynamodb.create_table(
                TableName=test_table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Table created successfully")
            
            # Wait for table to be created
            table.wait_until_exists()
            
            # Test 3: Put item
            logger.info("Testing: Put item")
            table.put_item(
                Item={
                    'id': 'test1',
                    'message': 'Hello DynamoDB!'
                }
            )
            logger.info("Item put successfully")
            
            # Test 4: Get item
            logger.info("Testing: Get item")
            response = table.get_item(
                Key={
                    'id': 'test1'
                }
            )
            item = response.get('Item')
            logger.info(f"Retrieved item: {item}")
            
            # Test 5: Delete table
            logger.info("Testing: Delete table")
            table.delete()
            logger.info("Table deleted successfully")
            
            logger.info("All DynamoDB tests passed successfully!")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"DynamoDB error: {error_code} - {error_message}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing DynamoDB connection: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_dynamodb_connection()) 