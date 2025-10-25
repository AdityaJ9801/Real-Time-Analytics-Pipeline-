"""
Prometheus Metrics Exporter for E-Commerce Analytics
Reads data from MongoDB and exposes it as Prometheus metrics
"""

from prometheus_client import start_http_server, Gauge, Counter
from pymongo import MongoClient
import time
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus Metrics
total_events = Gauge('analytics_total_events', 'Total number of events')
unique_users = Gauge('analytics_unique_users', 'Number of unique users')
unique_products = Gauge('analytics_unique_products', 'Number of unique products')

# Action metrics
view_count = Gauge('analytics_action_view', 'Total view events')
click_count = Gauge('analytics_action_click', 'Total click events')
purchase_count = Gauge('analytics_action_purchase', 'Total purchase events')

# Location metrics
location_purchases = Gauge('analytics_location_purchases', 'Purchases by location', ['location'])

# Product metrics
product_views = Gauge('analytics_product_views', 'Views by product', ['product_id'])
product_purchases = Gauge('analytics_product_purchases', 'Purchases by product', ['product_id'])

# Connect to MongoDB
max_retries = 10
retry_count = 0
mongo = None

while retry_count < max_retries and mongo is None:
    try:
        mongo = MongoClient('mongo', 27017, serverSelectionTimeoutMS=5000)
        mongo.server_info()
        logger.info("✅ Connected to MongoDB successfully")
    except Exception as e:
        retry_count += 1
        logger.warning(f"⚠️ MongoDB connection attempt {retry_count}/{max_retries} failed: {e}")
        if retry_count < max_retries:
            time.sleep(2)
        else:
            logger.error("❌ Failed to connect to MongoDB after max retries")
            raise

db = mongo.analytics
collection = db.events

def update_metrics():
    """Update all metrics from MongoDB"""
    try:
        # Total events
        total = collection.count_documents({})
        total_events.set(total)
        
        # Unique users and products
        unique_user_count = len(collection.distinct('user_id'))
        unique_product_count = len(collection.distinct('product_id'))
        unique_users.set(unique_user_count)
        unique_products.set(unique_product_count)
        
        # Action counts
        views = collection.count_documents({'action': 'view'})
        clicks = collection.count_documents({'action': 'click'})
        purchases = collection.count_documents({'action': 'purchase'})
        
        view_count.set(views)
        click_count.set(clicks)
        purchase_count.set(purchases)
        
        # Location purchases
        location_stats = collection.aggregate([
            {'$match': {'action': 'purchase'}},
            {'$group': {'_id': '$location', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        for stat in location_stats:
            location_purchases.labels(location=stat['_id']).set(stat['count'])
        
        # Product views and purchases
        product_view_stats = collection.aggregate([
            {'$match': {'action': 'view'}},
            {'$group': {'_id': '$product_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        
        for stat in product_view_stats:
            product_views.labels(product_id=stat['_id'][:8]).set(stat['count'])
        
        product_purchase_stats = collection.aggregate([
            {'$match': {'action': 'purchase'}},
            {'$group': {'_id': '$product_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        
        for stat in product_purchase_stats:
            product_purchases.labels(product_id=stat['_id'][:8]).set(stat['count'])
        
        logger.info(f"✅ Metrics updated: {total} events, {unique_user_count} users, {unique_product_count} products")
        
    except Exception as e:
        logger.error(f"❌ Error updating metrics: {e}")

# Start Prometheus HTTP server
start_http_server(8000)
logger.info("🚀 Prometheus metrics exporter started on port 8000")

# Update metrics every 10 seconds
while True:
    try:
        update_metrics()
        time.sleep(10)
    except Exception as e:
        logger.error(f"❌ Error in metrics loop: {e}")
        time.sleep(10)

