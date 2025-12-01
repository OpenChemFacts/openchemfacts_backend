# Pre-Deployment Quick Reference

Quick checklist and commands before deploying to production.

## Quick Checklist

```bash
# 1. Run automated pre-deployment checks
./scripts/pre_deploy_check.sh  # Linux/macOS
scripts\pre_deploy_check.bat   # Windows

# 2. If all checks pass, proceed with deployment
git add .
git commit -m "Your descriptive commit message"
git push origin main          # Optional: backup to origin
git push scalingo main         # Deploy to production

# 3. Verify deployment
scalingo status
scalingo logs --lines 50
curl https://your-app.scalingo.io/health
```

## Manual Checks (if script not available)

```bash
# Run tests
./scripts/run_tests.sh

# Check Git status
git status

# Verify syntax
python -m py_compile app/*.py

# Check required files
ls Procfile requirements.txt app/main.py

# Verify Scalingo remote
git remote -v
```

## Common Issues

### Tests Fail
```bash
# Run tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
```

### Build Fails on Scalingo
```bash
# Check build logs
scalingo logs --type build

# Verify Procfile
cat Procfile

# Check requirements.txt
cat requirements.txt
```

### Application Crashes
```bash
# View recent logs
scalingo logs --lines 200

# Filter errors
scalingo logs --filter "error OR exception"

# Check environment variables
scalingo env

# Restart application
scalingo restart
```

## Best Practices

1. ✅ Always run pre-deployment checks
2. ✅ Test locally before deploying
3. ✅ Use descriptive commit messages
4. ✅ Deploy small, incremental changes
5. ✅ Monitor logs after deployment
6. ✅ Have a rollback plan

## Full Documentation

For detailed information, see:
- **Documentation/13_Pre_Deploiement_Production.md** - Complete pre-deployment guide
- **Documentation/06_Deploiement_Scalingo.md** - Deployment guide
- **Documentation/08_Tests_API.md** - Testing guide

