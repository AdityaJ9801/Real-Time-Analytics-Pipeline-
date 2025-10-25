from flask import Flask, jsonify
from pymongo import MongoClient
from collections import Counter
from flask_cors import CORS
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Retry logic for MongoDB connection
max_retries = 10
retry_count = 0
client = None
db = None

while retry_count < max_retries and client is None:
    try:
        client = MongoClient('mongo', 27017, serverSelectionTimeoutMS=5000)
        db = client.analytics
        client.server_info()  # Trigger connection check
        logger.info("✅ Connected to MongoDB successfully")
    except Exception as e:
        retry_count += 1
        logger.warning(f"⚠️ MongoDB connection attempt {retry_count}/{max_retries} failed: {e}")
        if retry_count < max_retries:
            time.sleep(2)
        else:
            logger.error("❌ Failed to connect to MongoDB after max retries")

@app.route('/')
def home():
    if db is not None:
        try:
            event_count = db.events.count_documents({})
            return jsonify({
                "status": "✅ Dashboard is running",
                "events_stored": event_count,
                "endpoints": {
                    "/top-products": "Get top 5 viewed products",
                    "/top-purchases": "Get top 5 purchased products",
                    "/stats": "Get overall statistics"
                }
            })
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return jsonify({"status": "⚠️ Dashboard running but error fetching stats", "error": str(e)}), 500
    else:
        return jsonify({"status": "❌ MongoDB not connected"}), 500

@app.route('/top-products')
def top_products():
    if db is None:
        return jsonify({"error": "MongoDB not connected"}), 500

    try:
        events = list(db.events.find())
        counter = Counter([e.get('product_id') for e in events if e.get('action') == 'view'])
        top_5 = counter.most_common(5)
        return jsonify({
            "top_viewed_products": [{"product_id": p[0], "views": p[1]} for p in top_5],
            "total_events": len(events)
        })
    except Exception as e:
        logger.error(f"Error fetching top products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/top-purchases')
def top_purchases():
    if db is None:
        return jsonify({"error": "MongoDB not connected"}), 500

    try:
        events = list(db.events.find())
        counter = Counter([e.get('product_id') for e in events if e.get('action') == 'purchase'])
        top_5 = counter.most_common(5)
        return jsonify({
            "top_purchased_products": [{"product_id": p[0], "purchases": p[1]} for p in top_5],
            "total_events": len(events)
        })
    except Exception as e:
        logger.error(f"Error fetching top purchases: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats')
def stats():
    if db is None:
        return jsonify({"error": "MongoDB not connected"}), 500

    try:
        events = list(db.events.find())
        actions = Counter([e.get('action') for e in events])
        locations = Counter([e.get('location') for e in events])

        return jsonify({
            "total_events": len(events),
            "actions": dict(actions),
            "top_locations": dict(locations.most_common(5)),
            "unique_products": len(set(e.get('product_id') for e in events)),
            "unique_users": len(set(e.get('user_id') for e in events))
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Flask dashboard...")
    app.run(host='0.0.0.0', port=5000, debug=False)