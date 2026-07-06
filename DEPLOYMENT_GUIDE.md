# AI Gateway Deployment Guide

Complete guide for deploying the AI Gateway Monitoring Platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [SSL/TLS Configuration](#ssltls-configuration)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Production Checklist](#production-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+

**Recommended (Production)**:
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 100+ GB SSD
- OS: Ubuntu 22.04 LTS

### Software Requirements

```bash
# Docker & Docker Compose
Docker: 24.0+
Docker Compose: 2.20+

# Optional (for manual deployment)
Python: 3.11+
Node.js: 18+
PostgreSQL: 15+
Redis: 7+
Nginx: 1.24+
```

### Domain & DNS

- Registered domain name
- DNS A record pointing to server IP
- Wildcard SSL certificate (recommended)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/Arshkareer/AI_GATEWAY_SYSTEM.git
cd AI_GATEWAY_SYSTEM
```

### 2. Create Production Environment File

```bash
cp backend/.env.example .env.production
```

### 3. Configure Environment Variables

Edit `.env.production` with production values:

```bash
# Application
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-super-secret-key-min-32-characters-long

# Database
POSTGRES_USER=aigateway
POSTGRES_PASSWORD=secure-password-here
POSTGRES_DB=aigateway_prod
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=secure-redis-password
REDIS_HOST=redis
REDIS_PORT=6379

# LLM Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_TLS=True

# Webhooks & Integrations
WEBHOOK_URL=https://your-webhook-url.com/endpoint
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK

# Frontend
REACT_APP_API_URL=https://api.yourdomain.com

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure-grafana-password
```

### 4. Generate Strong Secrets

```bash
# Generate SECRET_KEY (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate passwords
openssl rand -base64 32
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

Install Certbot:

```bash
# Ubuntu/Debian
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
```

Copy certificates:

```bash
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chmod 644 nginx/ssl/*.pem
```

### Option 2: Self-Signed (Development/Testing)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### Option 3: Commercial Certificate

Place your certificate files in `nginx/ssl/`:
- `cert.pem` - Certificate file
- `key.pem` - Private key file

---

## Database Setup

### Initialize Database

```bash
# Start only database first
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for database to be ready
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### Create Initial Admin User

```bash
docker-compose -f docker-compose.prod.yml run --rm backend python -c "
from app.config.database import SessionLocal
from app.services.auth_service import auth_service
from app.models.user import UserRole

db = SessionLocal()
admin = auth_service.create_user(
    db=db,
    username='admin',
    email='admin@yourdomain.com',
    password='secure-admin-password',
    full_name='System Administrator',
    role=UserRole.ADMIN
)
print(f'Admin user created: {admin.username}')
"
```

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U aigateway aigateway_prod | gzip > backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Restore backup
gunzip < backups/backup-YYYYMMDD-HHMMSS.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres psql \
  -U aigateway aigateway_prod
```

---

## Docker Deployment

### 1. Build Images

```bash
# Build all services
docker-compose -f docker-compose.prod.yml build

# Or build specific service
docker-compose -f docker-compose.prod.yml build backend
```

### 2. Start Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 3. Verify Deployment

```bash
# Check health endpoints
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/health

# Check all containers
docker-compose -f docker-compose.prod.yml ps
```

### 4. Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.prod.yml down -v
```

---

## Monitoring Setup

### 1. Access Prometheus

```
URL: http://your-server-ip:9090
Default: No authentication
```

### 2. Access Grafana

```
URL: http://your-server-ip:3001
Username: admin (or GRAFANA_ADMIN_USER)
Password: (from GRAFANA_ADMIN_PASSWORD)
```

### 3. Import Dashboards

1. Log into Grafana
2. Go to Dashboards → Import
3. Upload JSON files from `monitoring/grafana/dashboards/`
4. Select Prometheus as datasource

### 4. Set Up Alerts

Configure alerts in Grafana:

**Budget Alert**:
```promql
rate(aigateway_cost_total[1h]) > 10
```

**High Error Rate**:
```promql
rate(aigateway_errors_total[5m]) / rate(aigateway_requests_total[5m]) > 0.05
```

**High Latency**:
```promql
histogram_quantile(0.95, aigateway_request_duration_seconds) > 5
```

---

## Production Checklist

### Security

- [ ] Changed all default passwords
- [ ] Generated strong SECRET_KEY
- [ ] SSL/TLS certificate installed and valid
- [ ] Firewall configured (allow 80, 443 only)
- [ ] Database not publicly accessible
- [ ] Redis password protection enabled
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Security headers configured

### Performance

- [ ] Database indexes created
- [ ] Redis caching enabled
- [ ] Gzip compression enabled
- [ ] Static asset caching configured
- [ ] Connection pooling configured
- [ ] Worker processes optimized

### Monitoring

- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards configured
- [ ] Alert rules configured
- [ ] Log aggregation setup
- [ ] Health checks passing
- [ ] Backup strategy implemented

### Application

- [ ] Database migrations applied
- [ ] Admin user created
- [ ] Email notifications tested
- [ ] Webhook integrations tested
- [ ] LLM provider keys configured
- [ ] AI services tested

### Documentation

- [ ] Deployment documented
- [ ] Admin credentials secured
- [ ] Runbook created
- [ ] Backup procedures documented
- [ ] Recovery procedures tested

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs servicename

# Check container status
docker ps -a

# Rebuild container
docker-compose -f docker-compose.prod.yml up -d --build servicename
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check connectivity from backend
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.config.database import engine; engine.connect()"

# Check environment variables
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# With password
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a "$REDIS_PASSWORD" ping
```

### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Check certificate expiry
openssl x509 -in nginx/ssl/cert.pem -enddate -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### High Memory Usage

```bash
# Check memory usage by container
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Adjust memory limits in docker-compose.prod.yml
```

### Slow Performance

```bash
# Check database query performance
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U aigateway -d aigateway_prod -c \
  "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"

# Check Redis memory
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory

# Check Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx | grep "request_time"
```

### Email Not Sending

```bash
# Test SMTP connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
import smtplib
from app.config.settings import settings
try:
    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    server.starttls()
    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    print('SMTP connection successful')
    server.quit()
except Exception as e:
    print(f'SMTP connection failed: {e}')
"
```

---

## Scaling

### Horizontal Scaling

Update `docker-compose.prod.yml`:

```yaml
backend:
  deploy:
    replicas: 3
```

### Load Balancing

Configure Nginx upstream:

```nginx
upstream backend {
    least_conn;
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

### Database Replication

Set up PostgreSQL primary-replica:

```yaml
postgres_replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_PRIMARY_HOST: postgres
  # Additional replica configuration
```

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Update Dependencies

```bash
# Backend
docker-compose -f docker-compose.prod.yml run --rm backend pip list --outdated

# Frontend
docker-compose -f docker-compose.prod.yml run --rm frontend npm outdated
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/Arshkareer/AI_GATEWAY_SYSTEM/issues
- Documentation: README.md
- API Docs: https://yourdomain.com/api/v1/docs

---

**Last Updated**: Phase 5 completion
**Version**: 1.0.0
