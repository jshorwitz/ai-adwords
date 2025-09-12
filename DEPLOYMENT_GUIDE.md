# 🚀 AI AdWords Platform - Deployment Guide

Multiple deployment options from easiest to most advanced.

## 🏃‍♂️ Quick Start Options (Recommended)

### Option 1: Railway (Easiest - 5 minutes)

Railway provides free PostgreSQL and automatic deployments from GitHub.

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial AI AdWords platform"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Visit [railway.app](https://railway.app)
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Add PostgreSQL service
   - Click "Deploy"

3. **Configure Environment**:
   ```bash
   # Railway will auto-generate DATABASE_URL and SECRET_KEY
   # Add your API keys in Railway dashboard:
   GOOGLE_ADS_CLIENT_ID=your_client_id
   GOOGLE_ADS_CLIENT_SECRET=your_client_secret
   GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
   ```

4. **Access Your App**:
   - Railway provides a public URL like `https://ai-adwords-production.up.railway.app`
   - Visit the URL to see your platform running!

### Option 2: Render (Free Tier Available)

1. **Fork/Push to GitHub**
2. **Connect Render**:
   - Go to [render.com](https://render.com)
   - "New Web Service" → Connect GitHub
   - Render auto-detects `render.yaml`

3. **Database Setup**:
   - Render creates PostgreSQL automatically
   - Environment variables auto-configured

4. **Deploy**:
   - Automatic deployments on git push
   - Free tier available with some limitations

### Option 3: Vercel (Serverless)

⚠️ **Note**: Vercel is serverless, so agent scheduling won't work. Best for API-only usage.

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel --prod
   ```

3. **Add Database**:
   - Use external PostgreSQL (Neon, Supabase, etc.)
   - Configure `DATABASE_URL` in Vercel dashboard

## 🐳 Docker Deployment (Local/VPS)

### Local Development

1. **Start with Docker Compose**:
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env
   
   # Start services
   docker-compose up -d
   ```

2. **Access Application**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Database: localhost:5432

3. **View Logs**:
   ```bash
   docker-compose logs -f app
   ```

### Production VPS (DigitalOcean, Linode, AWS EC2)

1. **Server Setup**:
   ```bash
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Deploy Application**:
   ```bash
   git clone https://github.com/yourusername/ai-adwords.git
   cd ai-adwords
   
   # Production environment
   cp .env.example .env
   # Edit .env with production values
   
   # Start in production mode
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Setup Reverse Proxy (Nginx)**:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **SSL with Certbot**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

## ☁️ Cloud Platform Deployments

### AWS (Comprehensive Setup)

1. **ECS with Fargate**:
   ```bash
   # Build and push to ECR
   aws ecr create-repository --repository-name ai-adwords
   
   docker build -t ai-adwords .
   docker tag ai-adwords:latest your-account.dkr.ecr.region.amazonaws.com/ai-adwords:latest
   docker push your-account.dkr.ecr.region.amazonaws.com/ai-adwords:latest
   ```

2. **RDS PostgreSQL**:
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier ai-adwords-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --engine-version 15.4 \
     --allocated-storage 20 \
     --db-name ai_adwords \
     --master-username ads_user \
     --master-user-password SecurePassword123
   ```

3. **ECS Service**:
   - Create ECS cluster
   - Define task definition with environment variables
   - Create service with load balancer

### Google Cloud Platform

1. **Cloud Run (Recommended)**:
   ```bash
   # Build and deploy
   gcloud run deploy ai-adwords \
     --image gcr.io/your-project/ai-adwords \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000
   ```

2. **Cloud SQL PostgreSQL**:
   ```bash
   gcloud sql instances create ai-adwords-db \
     --database-version=POSTGRES_15 \
     --cpu=1 \
     --memory=3840MB \
     --region=us-central1
   ```

### Azure Container Instances

1. **Build and Push**:
   ```bash
   az acr create --resource-group myResourceGroup --name aiadwords --sku Basic
   az acr build --registry aiadwords --image ai-adwords .
   ```

2. **Deploy Container**:
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name ai-adwords-app \
     --image aiadwords.azurecr.io/ai-adwords \
     --cpu 1 --memory 2 \
     --ports 8000 \
     --environment-variables DATABASE_URL="your-connection-string"
   ```

## 🔧 Production Configuration

### Environment Variables Checklist

**Required**:
- ✅ `DATABASE_URL` - PostgreSQL connection string
- ✅ `SECRET_KEY` - 32+ character secret key
- ✅ `JWT_SECRET_KEY` - JWT signing key

**Google Ads Integration**:
- ✅ `GOOGLE_ADS_CLIENT_ID`
- ✅ `GOOGLE_ADS_CLIENT_SECRET`
- ✅ `GOOGLE_ADS_DEVELOPER_TOKEN`
- ✅ `GOOGLE_ADS_CUSTOMER_ID`

**Security Settings**:
- ✅ `SECURE_COOKIES=true`
- ✅ `HTTPS_ONLY=true`
- ✅ `CORS_ORIGINS=https://yourdomain.com`

### Database Migration

```bash
# Initialize database with tables and seed data
poetry run python -m src.db_init

# Or with Docker
docker-compose exec app python -m src.db_init
```

### SSL Certificate Setup

**Let's Encrypt (Free)**:
```bash
# With Nginx
sudo certbot --nginx -d yourdomain.com

# With Apache
sudo certbot --apache -d yourdomain.com

# Manual/DNS challenge
sudo certbot certonly --manual --preferred-challenges dns -d yourdomain.com
```

**Custom Certificate**:
- Purchase SSL certificate
- Configure in reverse proxy (Nginx/Apache/CloudFlare)

### Domain Setup

1. **Purchase Domain** (Namecheap, GoDaddy, Google Domains)

2. **Configure DNS**:
   ```
   A record: @ → your-server-ip
   A record: www → your-server-ip
   ```

3. **CloudFlare (Recommended)**:
   - Free SSL, CDN, DDoS protection
   - Point DNS to CloudFlare
   - Configure origin rules

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Application health
curl https://yourdomain.com/health

# Agent system health
curl https://yourdomain.com/agents/health
```

### Log Management

**Centralized Logging**:
```bash
# With Docker
docker-compose logs -f

# With systemd
journalctl -u ai-adwords -f

# External: Datadog, New Relic, CloudWatch
```

### Backup Strategy

**Database Backups**:
```bash
# Daily automated backup
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Cloud storage
aws s3 cp backup-$(date +%Y%m%d).sql s3://your-backup-bucket/
```

**Application Backups**:
- Git repository (code)
- Environment variables (secure storage)
- SSL certificates
- Configuration files

## 🚨 Troubleshooting

### Common Issues

**Database Connection Failed**:
```bash
# Check connection
psql $DATABASE_URL

# Check firewall rules
telnet your-db-host 5432
```

**Agent Execution Errors**:
```bash
# Check agent logs
curl https://yourdomain.com/agents/status

# Run manual test
curl -X POST https://yourdomain.com/agents/run \
  -H "Content-Type: application/json" \
  -d '{"agent":"budget-optimizer","dry_run":true}'
```

**Authentication Issues**:
```bash
# Check session cookies
curl -v https://yourdomain.com/auth/me

# Test login
curl -X POST https://yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### Performance Optimization

**Database Optimization**:
```sql
-- Create indexes for common queries
CREATE INDEX idx_ad_metrics_platform_date ON ad_metrics(platform, date);
CREATE INDEX idx_agent_runs_agent_started ON agent_runs(agent, started_at);
```

**Application Scaling**:
- Use connection pooling
- Enable Redis caching
- Implement rate limiting
- Configure load balancer

## 🎉 Post-Deployment Checklist

- [ ] ✅ Application loads at your domain
- [ ] ✅ Database connected and tables created
- [ ] ✅ Admin user can sign up and login
- [ ] ✅ Agent system functional (test with dry-run)
- [ ] ✅ API endpoints working (/docs accessible)
- [ ] ✅ SSL certificate installed and valid
- [ ] ✅ Environment variables properly set
- [ ] ✅ Logs are being written and accessible
- [ ] ✅ Health checks returning 200 OK
- [ ] ✅ Backup strategy implemented
- [ ] ✅ Monitoring alerts configured

## 📞 Support & Next Steps

### Get Help
- Check application logs first
- Use `/health` and `/agents/health` endpoints
- Review this deployment guide
- Check platform-specific documentation

### Next Steps After Deployment
1. **Create Admin Account**: Visit `/auth/signup`
2. **Configure Google Ads**: Add real API credentials
3. **Test Agent System**: Run agents in dry-run mode
4. **Set Up Monitoring**: Configure alerts and dashboards
5. **Customize for Your Needs**: Add specific campaigns and optimization rules

🎉 **Congratulations! Your AI AdWords platform is now live on the web!**
