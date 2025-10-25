from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry logic for Kafka connection
max_retries = 10
retry_count = 0
consumer = None

while retry_count < max_retries and consumer is None:
    try:
        consumer = KafkaConsumer(
            'clickstream',
            bootstrap_servers='kafka:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='analytics-consumer',
            session_timeout_ms=30000
        )
        logger.info("✅ Connected to Kafka successfully")
    except Exception as e:
        retry_count += 1
        logger.warning(f"⚠️ Kafka connection attempt {retry_count}/{max_retries} failed: {e}")
        if retry_count < max_retries:
            time.sleep(2)
        else:
            logger.error("❌ Failed to connect to Kafka after max retries")
            raise

# Retry logic for MongoDB connection
mongo_retry_count = 0
mongo = None

while mongo_retry_count < max_retries and mongo is None:
    try:
        mongo = MongoClient('mongo', 27017, serverSelectionTimeoutMS=5000)
        mongo.server_info()  # Trigger connection check
        logger.info("✅ Connected to MongoDB successfully")
    except Exception as e:
        mongo_retry_count += 1
        logger.warning(f"⚠️ MongoDB connection attempt {mongo_retry_count}/{max_retries} failed: {e}")
        if mongo_retry_count < max_retries:
            time.sleep(2)
        else:
            logger.error("❌ Failed to connect to MongoDB after max retries")
            raise

db = mongo.analytics
collection = db.events

logger.info("🚀 Starting Kafka consumer...")
message_count = 0

for msg in consumer:
    try:
        collection.insert_one(msg.value)
        message_count += 1
        logger.info(f"✅ Message #{message_count} consumed and stored: {msg.value['action']} on product {msg.value['product_id'][:8]}")
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}")