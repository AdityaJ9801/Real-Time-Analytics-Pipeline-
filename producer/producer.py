from kafka import KafkaProducer
from faker import Faker
import json, time, random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()

# Retry logic for Kafka connection
max_retries = 10
retry_count = 0
producer = None

while retry_count < max_retries and producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=3,
            retry_backoff_ms=100
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

products = [fake.uuid4() for _ in range(10)]
users = [fake.uuid4() for _ in range(10)]

logger.info("🚀 Starting event producer...")
event_count = 0

while True:
    try:
        event = {
            "user_id": random.choice(users),
            "product_id": random.choice(products),
            "timestamp": fake.iso8601(),
            "action": random.choice(["view", "click", "purchase"]),
            "location": fake.city()
        }
        producer.send("clickstream", event)
        event_count += 1
        logger.info(f"✅ Event #{event_count} produced: {event['action']} on product {event['product_id'][:8]}")
        time.sleep(1)
    except Exception as e:
        logger.error(f"❌ Error producing event: {e}")
        time.sleep(2)