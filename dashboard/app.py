from flask import Flask, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging
import time

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# MongoDB Connection with Retry Logic
# ---------------------------------------------------------
max_retries = 10
retry_count = 0
client = None
db = None

while retry_count < max_retries and client is None:
    try:
        client = MongoClient("mongo", 27017, serverSelectionTimeoutMS=5000)
        db = client.analytics
        client.server_info()
        logger.info("✅ Connected to MongoDB successfully")
    except Exception as e:
        retry_count += 1
        logger.warning(f"⚠️ MongoDB connection attempt {retry_count}/{max_retries} failed: {e}")
        time.sleep(2)
else:
    if not client:
        logger.error("❌ Failed to connect to MongoDB after max retries")

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def get_events():
    """Fetch all events from MongoDB."""
    return list(db.events.find())

def safe_jsonify(data, status=200):
    return jsonify(data), status

def group_by(events, key):
    result = defaultdict(list)
    for e in events:
        if key in e:
            result[e[key]].append(e)
    return result


# ---------------------------------------------------------
# Root Route
# ---------------------------------------------------------
@app.route('/')
def home():
    if db is None:
        return safe_jsonify({"status": "❌ MongoDB not connected"}, 500)

    try:
        count = db.events.count_documents({})
        return safe_jsonify({
            "status": "✅ Dashboard API Running",
            "events_stored": count,
            "endpoints": {
                "/stats": "Get overall statistics and breakdowns",
                "/top-products": "Top viewed products",
                "/top-purchases": "Top purchased products",
                "/trend-daily": "7-day activity trend",
                "/user-insights": "Active and new user metrics",
                "/category-insights": "Category-level engagement"
            }
        })
    except Exception as e:
        logger.error(f"Error fetching home stats: {e}")
        return safe_jsonify({"error": str(e)}, 500)


# ---------------------------------------------------------
# Overall Statistics
# ---------------------------------------------------------
@app.route('/stats')
def stats():
    if db is None:
        return safe_jsonify({"error": "MongoDB not connected"}, 500)

    try:
        events = get_events()
        actions = Counter([e.get("action") for e in events])
        locations = Counter([e.get("location") for e in events if e.get("location")])
        devices = Counter([e.get("device_type") for e in events if e.get("device_type")])

        data = {
            "total_events": len(events),
            "actions": dict(actions),
            "unique_users": len(set(e.get("user_id") for e in events if e.get("user_id"))),
            "unique_products": len(set(e.get("product_id") for e in events if e.get("product_id"))),
            "top_locations": dict(locations.most_common(5)),
            "device_distribution": dict(devices.most_common(5)),
            "conversion_rate": round(actions.get("purchase", 0) / max(actions.get("view", 1), 1), 3),
        }
        return safe_jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return safe_jsonify({"error": str(e)}, 500)


# ---------------------------------------------------------
# Top Products
# ---------------------------------------------------------
@app.route('/top-products')
def top_products():
    if db is None:
        return safe_jsonify({"error": "MongoDB not connected"}, 500)

    try:
        events = get_events()
        views = Counter([e.get("product_id") for e in events if e.get("action") == "view"])
        avg_session_time = defaultdict(list)

        for e in events:
            if e.get("action") == "view" and "session_duration" in e:
                avg_session_time[e["product_id"]].append(e["session_duration"])

        top = [
            {
                "product_id": pid,
                "views": count,
                "avg_session_time": round(sum(avg_session_time[pid]) / len(avg_session_time[pid]), 2)
                if avg_session_time[pid] else 0
            }
            for pid, count in views.most_common(5)
        ]
        return safe_jsonify({"top_viewed_products": top})
    except Exception as e:
        logger.error(f"Error fetching top products: {e}")
        return safe_jsonify({"error": str(e)}, 500)


# ---------------------------------------------------------
# Top Purchases
# ---------------------------------------------------------
@app.route('/top-purchases')
def top_purchases():
    if db is None:
        return safe_jsonify({"error": "MongoDB not connected"}, 500)

    try:
        events = get_events()
        purchases = Counter([e.get("product_id") for e in events if e.get("action") == "purchase"])
        revenues = defaultdict(float)

        for e in events:
            if e.get("action") == "purchase":
                revenues[e["product_id"]] += e.get("price", 0.0)

        top = [
            {
                "product_id": pid,
                "purchases": count,
                "total_revenue": round(revenues[pid], 2)
            }
            for pid, count in purchases.most_common(5)
        ]
        return safe_jsonify({"top_purchased_products": top})
    except Exception as e:
        logger.error(f"Error fetching top purchases: {e}")
        return safe_jsonify({"error": str(e)}, 500)

@app.route('/top-users')
def top_users():
    try:
        events = get_events()
        user_activity = Counter([e.get("user_id") for e in events if e.get("user_id")])

        top = [
            {"user_id": uid, "events": count}
            for uid, count in user_activity.most_common(10)
        ]
        return safe_jsonify({"top_users": top})
    except Exception as e:
        return safe_jsonify({"error": str(e)}, 500)

@app.route('/category-device')
def category_device():
    try:
        events = get_events()
        result = defaultdict(lambda: defaultdict(int))

        for e in events:
            cat = e.get("category")
            dev = e.get("device_type")
            if cat and dev:
                result[cat][dev] += 1

        heatmap = [
            {"category": c, "device": d, "count": count}
            for c, devs in result.items()
            for d, count in devs.items()
        ]
        return safe_jsonify({"heatmap": heatmap})
    except Exception as e:
        return safe_jsonify({"error": str(e)}, 500)


# ---------------------------------------------------------
# User Insights
# ---------------------------------------------------------
@app.route('/user-insights')
def user_insights():
    if db is None:
        return safe_jsonify({"error": "MongoDB not connected"}, 500)

    try:
        events = get_events()
        user_activity = Counter([e.get("user_id") for e in events if e.get("user_id")])
        active_users = sum(1 for c in user_activity.values() if c > 5)
        new_users = len([e for e in events if e.get("action") == "signup"])

        return safe_jsonify({
            "total_users": len(user_activity),
            "active_users": active_users,
            "new_users": new_users,
            "avg_actions_per_user": round(sum(user_activity.values()) / max(len(user_activity), 1), 2)
        })
    except Exception as e:
        logger.error(f"Error fetching user insights: {e}")
        return safe_jsonify({"error": str(e)}, 500)


# ---------------------------------------------------------
# Category Insights
# ---------------------------------------------------------
@app.route('/category-insights')
def category_insights():
    if db is None:
        return safe_jsonify({"error": "MongoDB not connected"}, 500)

    try:
        events = get_events()
        category_views = Counter([e.get("category") for e in events if e.get("action") == "view" and e.get("category")])
        category_purchases = Counter([e.get("category") for e in events if e.get("action") == "purchase" and e.get("category")])

        top_categories = []
        for cat, views in category_views.most_common(5):
            purchases = category_purchases.get(cat, 0)
            conversion_rate = round(purchases / views, 3) if views else 0
            top_categories.append({
                "category": cat,
                "views": views,
                "purchases": purchases,
                "conversion_rate": conversion_rate
            })

        return safe_jsonify({"category_insights": top_categories})
    except Exception as e:
        logger.error(f"Error fetching category insights: {e}")
        return safe_jsonify({"error": str(e)}, 500)


# ---------------------------------------------------------
# Run Server
# ---------------------------------------------------------
if __name__ == "__main__":
    logger.info("🚀 Starting Flask Analytics API Server...")
    app.run(host="0.0.0.0", port=5000, debug=False)
