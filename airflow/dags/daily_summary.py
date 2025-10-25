from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def summarize():
    """
    Summarize daily purchase data from MongoDB and store results.
    """
    try:
        logger.info("🚀 Starting daily summary job...")

        # Connect to MongoDB
        client = MongoClient('mongo', 27017, serverSelectionTimeoutMS=5000)
        db = client.analytics

        # Fetch all events
        events = list(db.events.find())
        logger.info(f"📊 Found {len(events)} total events")

        if not events:
            logger.warning("⚠️ No events found in database")
            return

        # Calculate purchase summary
        purchase_events = [e for e in events if e.get('action') == 'purchase']
        logger.info(f"💰 Found {len(purchase_events)} purchase events")

        summary = Counter([e['product_id'] for e in purchase_events])
        top_purchases = summary.most_common(5)

        # Store summary
        summary_doc = {
            "date": datetime.now(timezone.utc),
            "total_events": len(events),
            "total_purchases": len(purchase_events),
            "top_purchases": [{"product_id": p[0], "count": p[1]} for p in top_purchases],
            "unique_products": len(set(e.get('product_id') for e in events)),
            "unique_users": len(set(e.get('user_id') for e in events))
        }

        db.daily_summary.insert_one(summary_doc)
        logger.info(f"✅ Daily summary stored: {summary_doc}")

    except Exception as e:
        logger.error(f"❌ Error in daily summary job: {e}")
        raise

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='daily_summary',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Daily summary of purchase events from MongoDB'
)

task = PythonOperator(
    task_id='summarize_purchases',
    python_callable=summarize,
    dag=dag
)