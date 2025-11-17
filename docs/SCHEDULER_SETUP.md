# Quick Scheduler Setup Guide

Get the NewsAgent scheduler running in 3 steps:

## Step 1: Setup Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit with your API keys
nano .env
# OR
vim .env
```

### Minimum Configuration

At least one API key is required. Edit `.env` and add:

```env
# Option A: Use BOCHA (recommended for testing)
BOCHA_API_KEY=your_actual_api_key

# Option B: Use XUNFEI
XUNFEI_APPID=your_appid
XUNFEI_APIKey=your_key

# Option C: Use any other agent (HUNYUAN, QIANFAN, META, TWITTER)
HUNYUAN_API_KEY=your_api_key
```

## Step 2: Verify Configuration

```bash
# Check configuration status
python -m examples.scheduler --show-env

# Check environment variables
python -m examples.scheduler --show-env-vars

# Expected output for --show-env:
# Ready Agents: 1/6  (if only BOCHA configured)
# Ready Agents: 6/6  (if all agents configured)
```

## Step 3: Run Scheduler

```bash
python -m examples.scheduler
```

The scheduler will:
1. Display initialization report
2. Show all settings and agent status
3. Launch interactive menu

## Usage Examples

### View Configuration
```bash
python -m examples.scheduler --show-env
```

### View Environment Variables Detail
```bash
python -m examples.scheduler --show-env-vars
```

### Use Different .env File
```bash
python -m examples.scheduler --env .env.production
```

### Use Different Database
```bash
python -m examples.scheduler --db /data/prod.db
```

## Getting API Keys

### BOCHA (Recommended for Testing)
1. Visit https://open.bochaai.com/
2. Sign up and get API key
3. Add to `.env`: `BOCHA_API_KEY=your_key`

### XUNFEI
1. Visit https://www.xfyun.cn/
2. Create account and get credentials
3. Add to `.env`:
   ```env
   XUNFEI_APPID=your_appid
   XUNFEI_APISecret=your_secret
   XUNFEI_APIKey=your_key
   ```

### HUNYUAN (Tencent)
1. Visit https://cloud.tencent.com/
2. Get API credentials
3. Add to `.env`:
   ```env
   HUNYUAN_API_KEY=your_key
   HUNYUAN_SECRET_ID=your_id
   HUNYUAN_SECRET_KEY=your_secret_key
   ```

### QIANFAN (Baidu)
1. Visit https://cloud.baidu.com/doc/AppBuilder/
2. Get API key
3. Add to `.env`: `QIANFAN_API_KEY=your_key`

### META (MetaSo)
1. Visit https://metaso.cn/search-api/playground
2. Get API key
3. Add to `.env`: `META_API_KEY=your_key`

### TWITTER
1. Visit https://developer.x.com/
2. Create app and get bearer token
3. Add to `.env`: `TWITTER_BEARER_TOKEN=your_token`

## Troubleshooting

### "No agents configured" Error
```
❌ No agents configured! At least one agent needs an API key.
```

**Solution**: Edit `.env` and add at least one API key from the list above.

### "Database directory not writable" Warning
```
❌ Database directory not writable
```

**Solution**:
- Check directory permissions
- Or change database path in `.env`: `DATABASE_PATH=/new/path/db.db`

### Environment Variables Not Loading
```
BOCHA_API_KEY: ✗ NOT SET
```

**Solution**:
1. Verify `.env` file exists: `ls -la .env`
2. Check file format (KEY=VALUE, one per line)
3. No quotes or spaces around values
4. No leading # for uncommented lines

### Module Import Errors
```
ModuleNotFoundError: No module named 'dotenv'
```

**Solution**:
```bash
pip install python-dotenv
# Or reinstall requirements
pip install -r requirements.txt
```

## Configuration Files

### `.env` File Structure
```env
# XUNFEI Configuration
XUNFEI_APPID=your_value
XUNFEI_APISecret=your_value
XUNFEI_APIKey=your_value
XUNFEI_APIPassword=your_value

# Tencent Hunyuan Configuration
HUNYUAN_SECRET_ID=your_value
HUNYUAN_SECRET_KEY=your_value
HUNYUAN_API_KEY=your_value

# BOCHA Web Search API
BOCHA_API_KEY=your_value

# Baidu Qianfan AppBuilder
QIANFAN_API_KEY=your_value

# MetaSo Search API
META_API_KEY=your_value

# Twitter/X API
TWITTER_BEARER_TOKEN=your_value

# Database Configuration
DATABASE_PATH=newsagent.db
LOG_LEVEL=INFO
LOG_FILE=newsagent.log

# Scheduler Configuration
DEFAULT_TIME_RANGE=7
DEFAULT_MAX_RESULTS=10

# Proxy (optional)
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
```

## Running Scheduler with Settings

### Python Code
```python
from src.scheduler import Scheduler
from src.scheduler.scheduler_settings import initialize_scheduler_settings

# Initialize settings from .env
settings = initialize_scheduler_settings(env_file=".env")

# Run scheduler
scheduler = Scheduler(settings=settings)
scheduler.run()
```

### Command Line
```bash
# Standard run
python -m examples.scheduler

# With initialization report
python -m examples.scheduler

# Check settings without running
python -m examples.scheduler --show-env

# Check environment variables
python -m examples.scheduler --show-env-vars
```

## Security Best Practices

1. **Never Commit .env**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Protect .env File**
   ```bash
   # Restrict permissions
   chmod 600 .env
   ```

3. **Use Different Keys for Different Environments**
   ```bash
   .env.dev         # Development
   .env.staging     # Staging
   .env.production  # Production
   ```

4. **Rotate Keys Regularly**
   - Update API keys in provider dashboards
   - Update `.env` file
   - Restart scheduler

5. **Share Securely**
   - Never email API keys
   - Use secure vaults for team sharing
   - Document key rotation procedures

## Next Steps

After setup:

1. **Run Scheduler**
   ```bash
   python -m examples.scheduler
   ```

2. **Explore Results**
   - Use "Explore Recent Research" action
   - Browse your query history
   - View agent responses

3. **Submit Queries**
   - Use "Submit Query" action
   - Follow step-by-step guide
   - Review templates before execution

4. **Export Results**
   - Use "Export Results" action
   - Choose JSON or Markdown format
   - Share with team

## Additional Resources

- [SCHEDULER.md](docs/SCHEDULER.md) - Complete scheduler user guide
- [SCHEDULER_SETTINGS.md](docs/SCHEDULER_SETTINGS.md) - Detailed settings reference
- [README.md](README.md) - Project overview
- [.env.example](.env.example) - Environment variable template

---

**Version**: 1.0
**Status**: Production-Ready
**Last Updated**: November 17, 2024
