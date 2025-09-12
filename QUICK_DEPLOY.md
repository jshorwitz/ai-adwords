# 🚀 Quick Deploy Guide - Get Your AI AdWords Platform Online in Minutes

## ⚡ Fastest Options (5-10 minutes)

### 🥇 Option 1: Railway (Recommended - Free PostgreSQL)

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "AI AdWords platform ready for deployment"
   git branch -M main
   git remote add origin https://github.com/yourusername/ai-adwords.git
   git push -u origin main
   ```

2. **Deploy on Railway**:
   - Visit [railway.app](https://railway.app) 
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects `railway.toml` and deploys
   - **Add PostgreSQL**: Click "Add Service" → "Database" → "PostgreSQL"

3. **Configure Variables**:
   - Railway auto-generates `DATABASE_URL` and `SECRET_KEY`
   - Add your API keys in Railway dashboard:
     ```
     GOOGLE_ADS_CLIENT_ID=your_client_id
     GOOGLE_ADS_CLIENT_SECRET=your_client_secret
     GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
     ```

4. **🎉 DONE!** Your app is live at `https://your-app.up.railway.app`

### 🥈 Option 2: Render (Free Tier)

1. **Connect GitHub to Render**:
   - Go to [render.com](https://render.com)
   - "New Web Service" → Connect your GitHub repo
   - Render auto-detects `render.yaml`

2. **Database**: Render creates PostgreSQL automatically

3. **Deploy**: Click "Create Web Service" - done!

### 🥉 Option 3: Local Docker (Development)

1. **One Command Deploy**:
   ```bash
   ./deploy.sh local
   ```
   
   This script will:
   - Set up environment file
   - Start PostgreSQL database  
   - Build and run the application
   - Initialize database tables
   - Test the deployment

2. **Access Your App**:
   - Application: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database: localhost:5432

## 🔧 Manual Docker Setup (If script doesn't work)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Generate secret key and edit .env
openssl rand -base64 32  # Use this as SECRET_KEY

# 3. Start services
docker-compose up -d

# 4. Wait for startup and initialize database
sleep 30
docker-compose exec app python -m src.db_init

# 5. Test
curl http://localhost:8000/health
```

## 🌐 Production Deployments

### AWS (Advanced)
- Use ECS with Fargate + RDS PostgreSQL
- See full guide in `DEPLOYMENT_GUIDE.md`

### Google Cloud (Advanced)  
- Use Cloud Run + Cloud SQL PostgreSQL
- Serverless, auto-scaling

### DigitalOcean/Linode (VPS)
- Deploy with Docker on $5/month droplet
- Use managed PostgreSQL database

## ✅ Post-Deployment Checklist

After deploying to any platform:

1. **✅ Verify Health**: Visit `/health` endpoint
2. **✅ Create Admin Account**: 
   ```bash
   curl -X POST https://yourapp.com/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"securepassword123"}'
   ```

3. **✅ Test Agent System**:
   ```bash
   # Login first to get session
   curl -X POST https://yourapp.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"securepassword123"}'
   
   # Test agent (with session cookie)
   curl -X POST https://yourapp.com/agents/run \
     -H "Content-Type: application/json" \
     -H "Cookie: sid=your_session_cookie" \
     -d '{"agent":"budget-optimizer","dry_run":true}'
   ```

4. **✅ Explore API**: Visit `/docs` for interactive API documentation

## 🎯 Next Steps After Deployment

1. **Add Real API Keys**: Update environment variables with actual Google Ads credentials
2. **Disable Mock Mode**: Set `MOCK_REDDIT=false` and `MOCK_TWITTER=false` when ready
3. **Set Up Custom Domain**: Point your domain to the deployed app
4. **Enable SSL**: Most platforms provide free SSL automatically
5. **Configure Alerts**: Set up monitoring for production use

## 🆘 Troubleshooting

**App won't start?**
- Check logs: `docker-compose logs app` (Docker) or platform dashboard
- Verify `DATABASE_URL` is set correctly
- Ensure `SECRET_KEY` is at least 32 characters

**Database connection failed?**
- Wait 30-60 seconds for PostgreSQL to fully start
- Check database credentials in logs
- Verify network connectivity between app and database

**Agent system not working?**
- Check `/agents/health` endpoint
- Verify all agents are registered with `/agents/list`
- Test with dry-run mode first

## 💡 Pro Tips

- **Railway**: Best for beginners, generous free tier, great PostgreSQL
- **Render**: Good free tier, automatic SSL, connects to GitHub seamlessly  
- **Docker**: Best for development, full control, works anywhere
- **Vercel**: Fast for APIs only (serverless limitations for agents)

**Environment Variables Security**:
- Never commit `.env` file to Git
- Use platform secret management (Railway Variables, Render Environment)
- Rotate secrets regularly in production

**Database Backups**:
- Railway/Render: Built-in database backups
- Docker: Set up automated `pg_dump` scripts
- Cloud: Use managed database backup features

---

🎉 **Your AI AdWords platform is now ready for the web!** 

Choose your deployment option and have your ads management platform live in minutes!
