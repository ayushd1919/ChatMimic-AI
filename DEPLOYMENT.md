# Deployment Guide for Render

This guide will help you deploy ChatMimic AI to Render.com for free online hosting.

## Branch Structure

- **`local`**: For local development with debug mode enabled
- **`deployment`**: Production-ready code optimized for Render hosting

## Prerequisites

1. A [Render](https://render.com) account (free)
2. Your GitHub repository with the `deployment` branch pushed

## Deployment Steps

### Step 1: Create a New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `https://github.com/ayushd1919/ChatMimic-AI`

### Step 2: Configure the Web Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `chatmimic-ai` (or any name you prefer) |
| **Region** | Choose closest to you (e.g., Singapore, Oregon) |
| **Branch** | `deployment` |
| **Root Directory** | (leave empty) |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` |

### Step 3: Add Environment Variables

Click **"Advanced"** and add these environment variables:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `FLASK_ENV` | `production` |

### Step 4: Deploy!

1. Click **"Create Web Service"**
2. Render will automatically:
   - Pull code from the `deployment` branch
   - Install dependencies from `requirements.txt`
   - Start the app using gunicorn
3. Wait for deployment to complete (usually 2-5 minutes)

### Step 5: Access Your App

Once deployed, Render will provide you with a URL like:
```
https://chatmimic-ai-xxxx.onrender.com
```

Your ChatMimic AI is now live!

## Important Notes

### Free Tier Limitations

- **Spin down after inactivity**: Free instances sleep after 15 minutes of inactivity
- **First request delay**: When sleeping, the first request may take 30-50 seconds
- **750 hours/month**: Free tier includes 750 hours of runtime per month

### File Persistence

**⚠️ WARNING**: Render's free tier has **ephemeral storage**. This means:
- User-uploaded chats and configs will be **deleted** when the instance restarts
- Files are lost during deployments or auto-restarts
- Not suitable for long-term data storage

**Recommendations**:
1. **For Production**: Upgrade to a paid plan with persistent disk
2. **For Testing**: Use the free tier and expect data loss
3. **Alternative**: Integrate cloud storage (AWS S3, Google Cloud Storage)

### Making Updates

To update your deployed app:

1. Switch to deployment branch locally:
   ```bash
   git checkout deployment
   ```

2. Make your changes

3. Commit and push:
   ```bash
   git add .
   git commit -m "Update: your message"
   git push origin deployment
   ```

4. Render will automatically detect the push and redeploy!

## Troubleshooting

### Build Fails
- Check that `requirements.txt` has all dependencies
- Verify Python version compatibility
- Check build logs in Render dashboard

### App Won't Start
- Verify `gunicorn` is in `requirements.txt`
- Check start command is `gunicorn app:app`
- Review application logs in Render dashboard

### App Returns 502 Error
- Ensure app binds to `0.0.0.0` and uses `PORT` environment variable
- Check app logs for Python errors

### File Upload Issues
- Remember: Free tier = ephemeral storage
- Files will be lost on restart
- Consider upgrading or using cloud storage

## Environment Differences

### Local Branch (Development)
- Debug mode: **ON**
- Port: **5000** (fixed)
- Server: Flask development server
- Storage: Persistent local files

### Deployment Branch (Production)
- Debug mode: **OFF**
- Port: Dynamic (from `PORT` env var)
- Server: **Gunicorn** (production-grade)
- Storage: Ephemeral (files cleared on restart)

## Monitoring

- **Logs**: Access real-time logs in Render dashboard
- **Metrics**: View CPU, memory usage in dashboard
- **Health Check**: Render automatically pings your app to keep it alive

## Cost

- **Free Tier**: $0/month
  - 750 hours of runtime
  - Spins down after 15 min inactivity
  - Shared CPU/RAM
  - Ephemeral storage

- **Starter Tier**: $7/month
  - Always on (no spin down)
  - Dedicated resources
  - Persistent disk available (+$1/GB/month)

## Next Steps

1. ✅ Deploy the app
2. 🧪 Test functionality
3. 📊 Monitor logs and performance
4. 💾 Consider storage solution for production use
5. 🚀 Share your deployed app!

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com/)
- Check logs in Render dashboard for errors

---

**Happy Deploying! 🚀**
