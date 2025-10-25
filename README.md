# Real-Time Analytics System for E-Commerce Platform

A complete real-time analytics pipeline that tracks user behavior, product views, and purchase trends for e-commerce platforms.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Real-Time Analytics Pipeline                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Producer (Faker)  ──→  Kafka Topic  ──→  Consumer  ──→  MongoDB │
│  (Simulates Events)    (clickstream)    (Processes)   (Storage)  │
│                                                            │       │
│                                                            ↓       │
│                                                      Dashboard API │
│                                                      (Flask)       │
│                                                            │       │
│                                                            ↓       │
│                                                      Airflow DAG   │
│                                                      (Daily Jobs)  │
│                                                                   │
│  Monitoring Stack:                                               │
│  ├─ Prometheus (Metrics)                                         │
│  ├─ Grafana (Visualization)                                      │
│  └─ MongoDB Exporter (DB Metrics)                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Docker** (v20.10+)
- **Docker Compose** (v1.29+)
- **Git**
- At least 4GB RAM available
- Ports available: 5000, 8081, 9090, 3000, 27017, 9092

## 🚀 Quick Start

### 1. Clone and Navigate to Project

```bash
cd d:\Data_engineering_project
```

### 2. Build and Start All Services

```bash
docker-compose up --build
```

This will:
- Build custom Docker images for producer, consumer, dashboard, and Airflow
- Start Zookeeper and Kafka
- Initialize MongoDB with persistent volume
- Set up PostgreSQL for Airflow
- Initialize Airflow database and create admin user
- Start Airflow webserver and scheduler
- Launch the event producer
- Start the Kafka consumer
- Run the Flask dashboard

### 3. Verify Services Are Running

```bash
docker-compose ps
```

Expected output:
```
NAME                 STATUS
zookeeper           Up (healthy)
kafka               Up (healthy)
mongo               Up (healthy)
postgres            Up
airflow-init        Exited (0)
webserver           Up
scheduler           Up
producer            Up
consumer            Up
dashboard           Up
prometheus          Up
grafana             Up
mongodb_exporter    Up
```

## 📊 Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard API** | http://localhost:5000 | N/A |
| **Airflow UI** | http://localhost:8081 | admin / admin |
| **Prometheus** | http://localhost:9090 | N/A |
| **Grafana** | http://localhost:3000 | admin / admin |
| **MongoDB** | localhost:27017 | N/A |
| **Kafka** | localhost:9092 | N/A |

## 🔍 Dashboard API Endpoints

### Get Dashboard Status
```bash
curl http://localhost:5000/
```

Response:
```json
{
  "status": "✅ Dashboard is running",
  "events_stored": 1250,
  "endpoints": {
    "/top-products": "Get top 5 viewed products",
    "/top-purchases": "Get top 5 purchased products",
    "/stats": "Get overall statistics"
  }
}
```

### Get Top Viewed Products
```bash
curl http://localhost:5000/top-products
```

### Get Top Purchased Products
```bash
curl http://localhost:5000/top-purchases
```

### Get Overall Statistics
```bash
curl http://localhost:5000/stats
```

## 🔄 Data Flow

1. **Producer** generates fake user events (view, click, purchase) every second
2. **Kafka** receives events on `clickstream` topic
3. **Consumer** reads from Kafka and stores events in MongoDB
4. **Dashboard API** queries MongoDB and provides analytics endpoints
5. **Airflow DAG** runs daily to generate purchase summaries
6. **Prometheus** scrapes metrics from MongoDB exporter
7. **Grafana** visualizes metrics from Prometheus

## 📝 Event Schema

Each event contains:
```json
{
  "user_id": "uuid",
  "product_id": "uuid",
  "timestamp": "ISO8601",
  "action": "view|click|purchase",
  "location": "city_name"
}
```

## 🛠️ Airflow DAG

**DAG ID:** `daily_summary`
**Schedule:** Daily at midnight UTC
**Task:** Summarizes purchase events and stores results in MongoDB

### View DAG Status
1. Go to http://localhost:8081
2. Login with admin/admin
3. Find `daily_summary` DAG
4. Check task execution history

## 📈 Monitoring

### Prometheus Targets
- MongoDB Exporter: http://localhost:9090/targets

### Grafana Dashboards
1. Go to http://localhost:3000
2. Login with admin/admin
3. Add Prometheus as data source: http://prometheus:9090
4. Create dashboards for MongoDB metrics

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs producer
docker-compose logs consumer
docker-compose logs scheduler
```

### Kafka Connection Issues
- Ensure Zookeeper is healthy first
- Check Kafka logs: `docker-compose logs kafka`
- Verify network: `docker network ls`

### MongoDB Connection Issues
- Check MongoDB logs: `docker-compose logs mongo`
- Verify volume: `docker volume ls | grep mongo`

### Airflow DAG Not Running
- Check scheduler logs: `docker-compose logs scheduler`
- Verify pymongo is installed: `docker-compose exec scheduler pip list | grep pymongo`
- Check DAG syntax: `docker-compose exec scheduler airflow dags list`

### No Events in Dashboard
- Check producer logs: `docker-compose logs producer`
- Check consumer logs: `docker-compose logs consumer`
- Verify Kafka topic: `docker-compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092`

## 🧹 Cleanup

### Stop All Services
```bash
docker-compose down
```

### Remove All Data (including volumes)
```bash
docker-compose down -v
```

### Remove Custom Images
```bash
docker-compose down --rmi all
```

## 📚 Project Structure

```
.
├── producer/
│   ├── Dockerfile
│   └── producer.py          # Event generator
├── consumer/
│   ├── Dockerfile
│   └── consumer.py          # Kafka consumer
├── dashboard/
│   ├── Dockerfile
│   └── app.py               # Flask API
├── airflow/
│   ├── Dockerfile
│   ├── dags/
│   │   └── daily_summary.py # Daily batch job
│   ├── logs/
│   └── plugins/
├── docker-compose.yml       # Service orchestration
├── prometheus.yml           # Prometheus config
└── README.md               # This file
```

## 🔧 Configuration

### Kafka Settings
- Bootstrap servers: `kafka:9092`
- Topic: `clickstream`
- Partitions: 1
- Replication factor: 1

### MongoDB Settings
- Host: `mongo`
- Port: `27017`
- Database: `analytics`
- Collections: `events`, `daily_summary`

### Airflow Settings
- Executor: LocalExecutor
- Database: PostgreSQL
- DAG folder: `/opt/airflow/dags`

## 📊 Expected Metrics

After running for a few minutes:
- **Events per minute:** ~60 (1 per second)
- **Event types:** ~33% view, ~33% click, ~33% purchase
- **Unique products:** 10
- **Unique users:** 10
- **Locations:** Various cities

## 🎯 Next Steps

1. **Customize Event Generation:** Modify `producer/producer.py` to generate realistic data
2. **Add Grafana Dashboards:** Create visualizations for key metrics
3. **Scale Kafka:** Add more partitions and brokers
4. **Add Real Data:** Connect to actual user event sources
5. **Implement Alerts:** Set up Prometheus alerts for anomalies

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs [service_name]`
2. Verify all services are healthy: `docker-compose ps`
3. Review error messages in service logs
4. Check Docker network: `docker network inspect [network_name]`

## 📄 License

This project is provided as-is for educational purposes.

