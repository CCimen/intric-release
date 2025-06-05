# Intric Troubleshooting Guide

## TLDR
- **Check Logs**: Use `podman-compose logs <service>` or `journalctl -u <service>` for systemd services
- **Verify Configuration**: Ensure environment variables are set correctly in `env_*` files
- **Database Issues**: Check PostgreSQL with pgvector is running and accessible
- **Network Problems**: Verify services can communicate, check ports 8000 (backend) and 3000 (frontend)
- **Common Fixes**: Most issues stem from missing dependencies, incorrect config, or port conflicts

This guide provides solutions for common issues encountered when deploying, developing, or using the Intric platform.

## Table of Contents
- [Development Environment Issues](#development-environment-issues)
- [Production Deployment Issues](#production-deployment-issues)
- [Container and Orchestration Issues](#container-and-orchestration-issues)
- [SSL and CORS Issues](#ssl-and-cors-issues)
- [Database Issues](#database-issues)
- [Authentication Issues](#authentication-issues)
- [LLM Integration Issues](#llm-integration-issues)
- [Frontend Issues](#frontend-issues)
- [Backend Issues](#backend-issues)
- [Worker Issues](#worker-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)
- [Getting Help](#getting-help)

## Development Environment Issues

### Initial Setup Problems

**Symptoms:**
- Poetry install fails
- pnpm install fails
- Services won't start

**Solutions:**
1. Verify Python version (3.11+):
   ```bash
   python --version
   ```

2. Verify Node.js version (18+) and pnpm:
   ```bash
   node --version
   pnpm --version
   ```

3. Ensure Docker services are running:
   ```bash
   cd backend
   docker compose up -d
   docker compose ps
   ```

4. Check if ports are already in use:
   ```bash
   lsof -i :8000  # Backend
   lsof -i :3000  # Frontend
   lsof -i :5432  # PostgreSQL
   lsof -i :6379  # Redis
   ```

### Missing Environment Variables

**Symptoms:**
- "Missing required configuration" errors
- Services fail to start

**Solutions:**
1. Create environment files from templates:
   ```bash
   # Backend
   cp backend/.env.template backend/.env
   
   # Frontend
   cp frontend/apps/web/.env.example frontend/apps/web/.env
   ```

2. Edit `.env` files and set required values:
   - Backend: `JWT_SECRET`, `POSTGRES_PASSWORD`, LLM API keys
   - Frontend: `JWT_SECRET` (must match backend), `INTRIC_BACKEND_URL`

### Database Initialization Fails

**Symptoms:**
- "Relation does not exist" errors
- Cannot login with default credentials

**Solutions:**
1. Ensure PostgreSQL is running:
   ```bash
   docker compose ps db
   ```

2. Run database initialization:
   ```bash
   cd backend
   poetry run python init_db.py
   ```

3. Check migrations are up to date:
   ```bash
   poetry run alembic upgrade head
   ```

## Production Deployment Issues

### Container Service Failures

**Symptoms:**
- Containers fail to start or restart repeatedly
- "Error starting container" messages
- Services not accessible after deployment

**Solutions:**
1. Check container status and logs:
   ```bash
   sudo podman-compose ps
   sudo podman-compose logs backend    # Check specific service
   sudo podman logs intric-backend-1   # Check by container name
   ```

2. Verify environment files exist and have correct permissions:
   ```bash
   ls -la env_* .env
   # Should show: -rw------- (600) for env_* files
   sudo chmod 600 env_*
   ```

3. Check volume mounts and permissions:
   ```bash
   ls -la data/
   # PostgreSQL directory should be owned by UID 999
   sudo chown -R 999:999 data/postgres
   ```

4. Verify images are pulled:
   ```bash
   sudo podman images | grep intric
   ```

### Systemd Integration Issues

**Symptoms:**
- podman-compose doesn't start on boot
- Services don't auto-restart after reboot

**Solutions:**
1. Create and enable systemd service:
   ```bash
   # Create service file
   sudo tee /etc/systemd/system/intric-production.service << EOF
   [Unit]
   Description=Intric Production Stack
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/opt/intric-production
   ExecStart=/usr/bin/podman-compose up -d
   ExecStop=/usr/bin/podman-compose down
   Restart=on-failure
   RestartSec=30
   User=root
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start
   sudo systemctl daemon-reload
   sudo systemctl enable intric-production
   sudo systemctl start intric-production
   ```

2. Check service status:
   ```bash
   sudo systemctl status intric-production
   sudo journalctl -u intric-production -f
   ```

### Container Networking Issues

**Symptoms:**
- Containers can't communicate with each other
- "Connection refused" between services
- DNS resolution fails inside containers

**Solutions:**
1. Verify container network exists:
   ```bash
   sudo podman network ls
   sudo podman network inspect intric_default
   ```

2. Check container connectivity:
   ```bash
   # From host
   sudo podman exec intric-backend-1 ping db
   sudo podman exec intric-frontend-1 curl http://backend:8000/api/v1/version
   ```

3. Verify DNS resolution:
   ```bash
   sudo podman exec intric-backend-1 nslookup db
   sudo podman exec intric-backend-1 cat /etc/resolv.conf
   ```

4. If using Podman with different user namespaces:
   ```bash
   # Check if running rootless
   podman info | grep rootless
   
   # For rootless issues, may need to use host networking temporarily
   # In compose file: network_mode: host
   ```

## Container and Orchestration Issues

### Docker Image Pull Errors

**Symptoms:**
- `Error response from daemon: pull access denied for intric/backend`
- `repository does not exist or may require 'docker login'`
- Containers fail to start with image not found errors

**Solutions:**
1. Use the correct community images from GitHub Container Registry:
   ```bash
   # Update your .env file with correct image names:
   FRONTEND_IMAGE=ghcr.io/inoolabs/intric-release-frontend
   BACKEND_IMAGE=ghcr.io/inoolabs/intric-release-backend
   
   # These are publicly available - no login required
   ```

2. Test pulling images manually:
   ```bash
   # For Docker
   docker pull ghcr.io/inoolabs/intric-release-backend:latest
   docker pull ghcr.io/inoolabs/intric-release-frontend:latest
   
   # For Podman
   podman pull ghcr.io/inoolabs/intric-release-backend:latest
   podman pull ghcr.io/inoolabs/intric-release-frontend:latest
   ```

3. If you see `intric/backend` or `intric/frontend` in your configuration:
   ```bash
   # Wrong - these images don't exist
   BACKEND_IMAGE=intric/backend
   FRONTEND_IMAGE=intric/frontend
   
   # Currently also wrong - images are private
   BACKEND_IMAGE=ghcr.io/inoolabs/intric-release-backend
   FRONTEND_IMAGE=ghcr.io/inoolabs/intric-release-frontend
   ```

4. **RECOMMENDED: Build your own images from source:**
   ```bash
   git clone https://github.com/inooLabs/intric-community.git
   cd intric-community
   docker build -t intric-backend:latest ./backend
   docker build -t intric-frontend:latest ./frontend
   
   # Update your .env to use local images:
   BACKEND_IMAGE=intric-backend
   FRONTEND_IMAGE=intric-frontend
   ```

### GitHub Container Registry Authorization Errors

**Symptoms:**
- `Error response from daemon: Head "https://ghcr.io/v2/inoolabs/intric-release-backend/manifests/latest": unauthorized`
- `unauthorized: authentication required`

**Cause:**
The pre-built community images are currently set to private in the GitHub Container Registry.

**Solutions:**
1. **Build from source** (recommended):
   See the instructions above for building your own images.

2. **Authenticate with GitHub** (if you have access):
   ```bash
   # Create a Personal Access Token at https://github.com/settings/tokens
   # Make sure it has 'read:packages' scope
   
   # Login to GitHub Container Registry
   echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   
   # Now try pulling again
   docker pull ghcr.io/inoolabs/intric-release-backend:latest
   docker pull ghcr.io/inoolabs/intric-release-frontend:latest
   
   # For Podman users:
   echo YOUR_GITHUB_TOKEN | podman login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

3. **Contact InooLabs**:
   Request that the images be made public or ask for access permissions.

4. **Use Docker Hub or your own registry**:
   After building, push to your own registry:
   ```bash
   # Tag and push to Docker Hub
   docker tag intric-backend:latest yourusername/intric-backend:latest
   docker push yourusername/intric-backend:latest
   
   # Or to a private registry
   docker tag intric-backend:latest your-registry.com/intric-backend:latest
   docker push your-registry.com/intric-backend:latest
   ```

### Podman vs Docker Compatibility

**Symptoms:**
- Commands fail with podman-compose
- Different behavior between Docker and Podman

**Solutions:**
1. Use compatible compose syntax:
   ```yaml
   # Use version 3.8 or lower
   version: '3.8'
   
   # Avoid Docker-specific features like:
   # - init: true (use podman's built-in init)
   # - platform: linux/amd64 (Podman detects automatically)
   ```

2. For socket compatibility:
   ```bash
   # Enable podman socket for Docker compatibility
   sudo systemctl enable --now podman.socket
   
   # Set DOCKER_HOST for tools expecting Docker
   export DOCKER_HOST=unix:///run/podman/podman.sock
   ```

3. Handle user namespace differences:
   ```bash
   # For permission issues
   sudo podman unshare chown -R 999:999 ./data/postgres
   ```

### Resource Limits and Memory Issues

**Symptoms:**
- Containers killed due to OOM
- Slow performance under load
- "Cannot allocate memory" errors

**Solutions:**
1. Set appropriate resource limits in compose file:
   ```yaml
   services:
     backend:
       mem_limit: 2g
       memswap_limit: 2g
       cpus: '2.0'
   ```

2. Monitor resource usage:
   ```bash
   sudo podman stats
   sudo podman system df
   ```

3. Clean up unused resources:
   ```bash
   sudo podman system prune -a --volumes
   ```

## SSL and CORS Issues

### SSL Certificate Problems

**Symptoms:**
- Browser shows "Not Secure" warning
- SSL handshake failures
- Mixed content warnings

**Solutions:**
1. Verify certificate installation:
   ```bash
   # Check certificate validity
   openssl x509 -in /etc/ssl/certs/intric.crt -text -noout
   
   # Test SSL connection
   openssl s_client -connect intric.example.com:443 -servername intric.example.com
   ```

2. For Let's Encrypt with HAProxy:
   ```bash
   # Install certbot
   sudo dnf install certbot
   
   # Get certificate
   sudo certbot certonly --standalone -d intric.example.com \
     --pre-hook "systemctl stop haproxy" \
     --post-hook "systemctl start haproxy"
   
   # Combine for HAProxy
   sudo cat /etc/letsencrypt/live/intric.example.com/fullchain.pem \
           /etc/letsencrypt/live/intric.example.com/privkey.pem \
           > /etc/haproxy/certs/intric.example.com.pem
   ```

3. Auto-renewal setup:
   ```bash
   # Create renewal hook
   sudo tee /etc/letsencrypt/renewal-hooks/post/haproxy.sh << 'EOF'
   #!/bin/bash
   cat /etc/letsencrypt/live/intric.example.com/fullchain.pem \
       /etc/letsencrypt/live/intric.example.com/privkey.pem \
       > /etc/haproxy/certs/intric.example.com.pem
   systemctl reload haproxy
   EOF
   
   sudo chmod +x /etc/letsencrypt/renewal-hooks/post/haproxy.sh
   ```

### CORS and Mixed Content Issues

**Symptoms:**
- "CORS policy" errors in browser console
- API calls blocked by browser
- WebSocket connections fail

**Solutions:**
1. Verify URL configuration:
   ```bash
   # Frontend env_frontend
   grep INTRIC_BACKEND_URL env_frontend        # Should be HTTPS public URL
   grep INTRIC_BACKEND_SERVER_URL env_frontend # Should be internal HTTP URL
   
   # Example:
   # INTRIC_BACKEND_URL=https://intric.example.com
   # INTRIC_BACKEND_SERVER_URL=http://backend:8000
   ```

2. Fix mixed content (HTTP/HTTPS):
   ```bash
   # Ensure all URLs use HTTPS in production
   # Check frontend configuration
   grep -r "http://" frontend/apps/web/src/ | grep -v localhost
   ```

3. Debug CORS headers:
   ```bash
   # Test CORS preflight
   curl -X OPTIONS https://intric.example.com/api/v1/spaces \
     -H "Origin: https://intric.example.com" \
     -H "Access-Control-Request-Method: GET" \
     -v
   ```

### HAProxy SSL Termination Issues

**Symptoms:**
- 502 Bad Gateway with HTTPS
- SSL works but backend communication fails
- WebSocket upgrade fails over HTTPS

**Solutions:**
1. Proper HAProxy SSL configuration:
   ```bash
   # /etc/haproxy/haproxy.cfg
   frontend https-in
       bind *:443 ssl crt /etc/haproxy/certs/
       http-request set-header X-Forwarded-Proto https
       
       # WebSocket detection
       acl is_websocket hdr(Upgrade) -i websocket
       use_backend backend_ws if is_websocket
       
       default_backend backend_http
   
   backend backend_http
       server backend1 127.0.0.1:8000 check
   
   backend backend_ws
       server backend1 127.0.0.1:8000 check
   ```

2. Verify header forwarding:
   ```bash
   # Backend should receive proper headers
   curl -H "X-Forwarded-Proto: https" http://localhost:8000/api/v1/test
   ```

## Database Issues

### PostgreSQL Connection Failures

**Symptoms:**
- "Could not connect to database" errors
- psycopg2.OperationalError

**Solutions:**
1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql-13  # RHEL8
   docker compose ps db                 # Development
   ```

2. Check connection parameters in `.env`:
   ```
   POSTGRES_HOST=localhost  # or actual hostname
   POSTGRES_PORT=5432
   POSTGRES_USER=intric
   POSTGRES_PASSWORD=<your-password>
   POSTGRES_DB=intric
   ```

3. Test connection manually:
   ```bash
   psql -h localhost -p 5432 -U intric -d intric
   ```

### pgvector Extension Issues

**Symptoms:**
- Vector operations fail
- "type vector does not exist" errors

**Solutions:**
1. Verify pgvector is installed:
   ```sql
   \dx vector
   ```

2. Create extension if missing:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. Check vector column exists:
   ```sql
   \d info_blob_chunks
   ```

### Migration Problems

**Symptoms:**
- Database schema out of sync
- "Column does not exist" errors

**Solutions:**
1. Check current migration status:
   ```bash
   cd backend
   poetry run alembic current
   ```

2. Apply pending migrations:
   ```bash
   poetry run alembic upgrade head
   ```

3. If migrations are stuck:
   ```bash
   poetry run alembic stamp head  # Mark as current
   poetry run alembic upgrade head # Apply any new ones
   ```

## Authentication Issues

### JWT Token Problems

**Symptoms:**
- "Invalid token" errors
- 401 Unauthorized responses
- Users logged out unexpectedly

**Solutions:**
1. Verify JWT_SECRET matches between frontend and backend:
   ```bash
   # Backend .env
   grep JWT_SECRET backend/.env
   
   # Frontend .env
   grep JWT_SECRET frontend/apps/web/.env
   ```

2. Check token in browser DevTools:
   - Network tab → Request headers → Authorization
   - Should be: `Bearer <token>`

3. Decode token to check expiry:
   ```bash
   # Use jwt.io or similar tool
   ```

### Login Failures

**Symptoms:**
- Cannot login with credentials
- "Invalid credentials" error

**Solutions:**
1. For development, use default credentials:
   - Email: `user@example.com`
   - Password: `Password1!`

2. Verify user exists in database:
   ```sql
   SELECT email, username FROM users WHERE email = 'user@example.com';
   ```

3. Check password hashing:
   ```bash
   # Backend logs should show bcrypt operations
   docker compose logs backend | grep -i auth
   ```

### API Key Authentication Issues

**Symptoms:**
- API key not working
- "Invalid API key" errors

**Solutions:**
1. Check API key header name in config:
   ```bash
   grep API_KEY_HEADER_NAME backend/.env
   # Default is "example", production should be "X-API-Key"
   ```

2. Verify API key format in request:
   ```bash
   curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/endpoint
   ```

## LLM Integration Issues

### Missing or Invalid API Keys

**Symptoms:**
- "API key not found" errors
- LLM features not working

**Solutions:**
1. Verify at least one LLM provider is configured:
   ```bash
   grep -E "OPENAI_API_KEY|ANTHROPIC_API_KEY" backend/.env
   ```

2. Test API key validity:
   ```bash
   # For OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. Check environment variables are loaded:
   ```bash
   cd backend
   poetry run python -c "import os; print('Keys:', [k for k in os.environ if 'API_KEY' in k])"
   ```

### Model Configuration Issues

**Symptoms:**
- "Model not found" errors
- Wrong model being used

**Solutions:**
1. Check available models in the database:
   ```sql
   SELECT name, model_id, provider FROM completion_models WHERE is_active = true;
   ```

2. Verify model configuration in spaces:
   ```sql
   SELECT s.name, cm.name as model_name 
   FROM spaces s 
   JOIN completion_models cm ON s.completion_model_id = cm.id;
   ```

## Frontend Issues

### Build Failures

**Symptoms:**
- pnpm build fails
- Missing dependencies

**Solutions:**
1. Clean install dependencies:
   ```bash
   cd frontend
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   pnpm run setup
   ```

2. Check Node.js version (should be 18+):
   ```bash
   node --version
   ```

### Cannot Connect to Backend

**Symptoms:**
- API calls fail
- "Network error" in console

**Solutions:**
1. Verify backend URL in frontend config:
   ```bash
   grep INTRIC_BACKEND_URL frontend/apps/web/.env
   # Should be http://localhost:8000 for dev
   ```

2. Check CORS settings if in production
3. Verify backend is accessible:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

### WebSocket Connection Issues

**Symptoms:**
- Real-time updates not working
- WebSocket errors in console

**Solutions:**
1. Check WebSocket endpoint:
   ```javascript
   // Should connect to ws://localhost:8000/ws
   ```

2. Verify no proxy is blocking WebSocket upgrade (if using HAProxy)
3. Check browser console for specific errors
4. Ensure backend WebSocket handlers are properly configured

## Backend Issues

### Import Errors

**Symptoms:**
- ModuleNotFoundError
- ImportError

**Solutions:**
1. Ensure you're in Poetry environment:
   ```bash
   cd backend
   poetry shell
   # or use poetry run prefix
   ```

2. Reinstall dependencies:
   ```bash
   poetry install
   ```

### Gunicorn Worker Timeout

**Symptoms:**
- Worker timeout errors
- 502 errors after 30 seconds

**Solutions:**
1. Increase worker timeout in run.sh:
   ```bash
   --timeout 120  # Increase from default
   ```

2. Check for long-running synchronous operations
3. Consider using background tasks for heavy operations

## Worker Issues

### ARQ Worker Not Processing Jobs

**Symptoms:**
- Tasks stuck in queue
- Background jobs not completing

**Solutions:**
1. Check worker is running:
   ```bash
   ps aux | grep arq
   ```

2. Verify Redis connectivity:
   ```bash
   redis-cli ping
   ```

3. Check job queue:
   ```bash
   redis-cli
   > KEYS arq:*
   > LLEN arq:queue:default
   ```

4. Monitor worker logs:
   ```bash
   journalctl -u intric-worker -f
   ```

### Task Failures

**Symptoms:**
- Jobs marked as failed
- Retry count exceeded

**Solutions:**
1. Check task implementation for errors
2. Verify external dependencies (file paths, API access)
3. Increase task timeout if needed
4. Check worker has necessary permissions

## Performance Issues

### Slow Vector Search

**Symptoms:**
- Search queries timeout
- High CPU usage during search

**Solutions:**
1. Check vector index exists:
   ```sql
   \d info_blob_chunks
   ```

2. Create appropriate index:
   ```sql
   CREATE INDEX ON info_blob_chunks USING ivfflat (embedding vector_cosine_ops);
   ```

3. Tune index parameters:
   ```sql
   ALTER INDEX info_blob_chunks_embedding_idx SET (lists = 100);
   ```

### High Memory Usage

**Symptoms:**
- OOM killer terminates services
- Slow response times

**Solutions:**
1. Check memory usage:
   ```bash
   free -h
   top -o %MEM
   ```

2. Tune PostgreSQL memory:
   ```bash
   # postgresql.conf
   shared_buffers = 1GB
   effective_cache_size = 3GB
   ```

3. Limit Gunicorn workers based on available RAM
4. Configure connection pooling properly

## Common Error Messages

### "SQLSTATE[08006] - connection refused"
- PostgreSQL not running or wrong connection params
- Check POSTGRES_HOST and POSTGRES_PORT

### "TypeError: expected string or bytes-like object"
- Usually indicates None value where string expected
- Check for missing environment variables

### "asyncpg.exceptions.UndefinedColumnError"
- Database schema out of sync
- Run migrations: `poetry run alembic upgrade head`

### "redis.exceptions.ConnectionError"
- Redis not running or wrong host/port
- Check REDIS_HOST and REDIS_PORT

### "413 Request Entity Too Large"
- File upload exceeds limit
- Check UPLOAD_MAX_FILE_SIZE in backend config
- Adjust proxy settings if using HAProxy or other load balancer

## Production Monitoring and Logging

### Log Collection Issues

**Symptoms:**
- Can't find container logs
- Logs not persisted after container restart
- Disk space filling up with logs

**Solutions:**
1. Configure log drivers in compose file:
   ```yaml
   services:
     backend:
       logging:
         driver: "json-file"
         options:
           max-size: "100m"
           max-file: "5"
   ```

2. Centralize logs with journald (Podman):
   ```yaml
   services:
     backend:
       logging:
         driver: "journald"
         options:
           tag: "intric-backend"
   ```

3. View logs:
   ```bash
   # Container logs
   sudo podman-compose logs -f backend --tail 100
   
   # Journald logs (if using journald driver)
   sudo journalctl -u intric-production -f
   sudo journalctl CONTAINER_NAME=intric-backend-1 -f
   ```

### Health Check Failures

**Symptoms:**
- Containers marked as unhealthy
- Load balancer removing backends
- Intermittent service availability

**Solutions:**
1. Add health checks to compose file:
   ```yaml
   services:
     backend:
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/version"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 40s
     
     frontend:
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:3000"]
         interval: 30s
         timeout: 10s
         retries: 3
   ```

2. Monitor health status:
   ```bash
   sudo podman-compose ps
   sudo podman inspect intric-backend-1 | jq '.[0].State.Health'
   ```

### Backup and Restore Issues

**Symptoms:**
- Database backups failing
- Can't restore from backup
- Data loss after updates

**Solutions:**
1. Automated PostgreSQL backups:
   ```bash
   # Create backup script
   sudo tee /opt/intric-production/backup.sh << 'EOF'
   #!/bin/bash
   BACKUP_DIR="/opt/intric-production/backups"
   mkdir -p $BACKUP_DIR
   
   # Database backup
   sudo podman exec intric-db-1 pg_dump -U postgres postgres | \
     gzip > $BACKUP_DIR/intric-$(date +%Y%m%d-%H%M%S).sql.gz
   
   # Keep only last 7 days
   find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
   EOF
   
   sudo chmod +x /opt/intric-production/backup.sh
   
   # Add to crontab
   echo "0 2 * * * /opt/intric-production/backup.sh" | sudo crontab -
   ```

2. Restore from backup:
   ```bash
   # Stop services
   sudo podman-compose stop backend worker
   
   # Restore database
   gunzip -c /opt/intric-production/backups/intric-20240120-020000.sql.gz | \
     sudo podman exec -i intric-db-1 psql -U postgres postgres
   
   # Start services
   sudo podman-compose start backend worker
   ```

## Common Production Scenarios

### Upgrading Intric Version

**Safe upgrade procedure:**
1. Backup everything:
   ```bash
   # Backup database
   sudo /opt/intric-production/backup.sh
   
   # Backup environment files
   sudo tar -czf env-backup-$(date +%Y%m%d).tar.gz env_* .env
   ```

2. Test in staging environment first

3. Pull new images:
   ```bash
   sudo podman-compose pull
   ```

4. Apply database migrations:
   ```bash
   # Check pending migrations
   sudo podman-compose run --rm backend poetry run alembic current
   sudo podman-compose run --rm backend poetry run alembic upgrade head
   ```

5. Restart services:
   ```bash
   sudo podman-compose down
   sudo podman-compose up -d
   ```

### Emergency Recovery

**When everything is broken:**
1. Stop all services:
   ```bash
   sudo podman-compose down
   sudo podman stop $(sudo podman ps -q)
   ```

2. Clean up containers and networks:
   ```bash
   sudo podman system prune -f
   sudo podman network prune -f
   ```

3. Restore from backup:
   ```bash
   # Restore database from latest backup
   # Restore environment files
   # Start fresh
   sudo podman-compose up -d
   ```

### Performance Tuning

**For production workloads:**
1. Database optimization:
   ```sql
   -- Vacuum and analyze
   VACUUM ANALYZE;
   
   -- Check slow queries
   SELECT query, calls, mean_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

2. Container resource tuning:
   ```yaml
   # In compose file
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '4.0'
             memory: 4G
           reservations:
             cpus: '2.0'
             memory: 2G
   ```

3. Frontend optimization:
   ```bash
   # Enable production optimizations
   NODE_ENV=production
   # In env_frontend
   ```

## Getting Help

If you're still experiencing issues:

1. **Check existing resources:**
   - GitHub Issues: https://github.com/inooLabs/intric-community/issues
   - Documentation: `/docs` folder
   - Deployment Guide: [deployment-guide.md](deployment-guide.md)

2. **Collect diagnostic information:**
   ```bash
   # System info
   uname -a
   podman --version
   
   # Container logs
   sudo podman-compose logs --tail 200 > intric-logs.txt
   
   # Service status
   sudo podman-compose ps > intric-status.txt
   
   # Database status
   sudo podman exec intric-db-1 psql -U postgres -c "SELECT version();"
   ```

3. **Report issues with:**
   - Clear description of the problem
   - Steps to reproduce
   - Error messages and logs
   - Environment details (OS, versions)
   - Configuration (sanitized - remove passwords/keys)
   - Deployment method (Podman/Docker, systemd, etc.)

4. **Community support:**
   - GitHub Discussions
   - Create detailed bug reports with logs