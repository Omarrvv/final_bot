# Egypt Tourism Chatbot Troubleshooting Guide

This guide provides solutions for common issues you might encounter when setting up and running the Egypt Tourism Chatbot.

## Backend Issues

### 1. Port Conflicts

**Issue**: Error message about port 5001 already being in use.

**Solution**:
- Check if another process is using port 5001:
  ```bash
  lsof -i :5001
  ```
- Kill the process using the port:
  ```bash
  kill -9 <PID>
  ```
- Alternatively, change the port in `.env` file and update the proxy in `react-frontend/package.json`

### 2. Missing Dependencies

**Issue**: `ModuleNotFoundError` when starting the backend.

**Solution**:
- Ensure your virtual environment is activated:
  ```bash
  source chatbot_env/bin/activate
  ```
- Install all required dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- If specific dependencies fail to install, try installing them individually:
  ```bash
  pip install <package-name>
  ```

### 3. Environment Variables

**Issue**: Backend fails to start due to missing environment variables.

**Solution**:
- Create or update your `.env` file in the project root with the following variables:
  ```
  PORT=5001
  DEBUG=True
  SECRET_KEY=your-secret-key
  LOG_LEVEL=INFO
  ```

## Frontend Issues

### 1. NPM Errors

**Issue**: Errors when running `npm start`.

**Solution**:
- Clear npm cache:
  ```bash
  npm cache clean --force
  ```
- Delete node_modules and reinstall:
  ```bash
  rm -rf node_modules
  npm install
  ```

### 2. Proxy Configuration

**Issue**: Frontend can't connect to backend API.

**Solution**:
- Ensure the proxy in `package.json` matches the backend port:
  ```json
  "proxy": "http://localhost:5001"
  ```
- Restart both frontend and backend servers

### 3. CORS Issues

**Issue**: Browser console shows CORS errors.

**Solution**:
- Ensure Flask-CORS is properly configured in the backend
- Check that the frontend is making requests to the correct URL

## API Communication Issues

### 1. API Endpoints Not Found

**Issue**: 404 errors when making API requests.

**Solution**:
- Confirm the backend is running and the API routes are correctly defined
- Check the browser console for specific error messages
- Verify that the frontend is using the correct API paths

### 2. Authentication Errors

**Issue**: CSRF token errors or authentication failures.

**Solution**:
- Ensure the CSRF token is being properly passed in API requests
- Check that the SecurityMiddleware is correctly configured in the backend

## Database Issues

### 1. Database Connection Errors

**Issue**: Backend fails to connect to the database.

**Solution**:
- Check database connection strings in your `.env` file
- Ensure the database server is running
- Run the database initialization script:
  ```bash
  python init_db.py
  ```

## General Troubleshooting Steps

1. **Check Logs**: Review the logs in the `logs` directory for detailed error messages.

2. **Restart Services**: Sometimes simply restarting the backend and frontend can resolve issues.

3. **Clean Start**: Use the provided `start_chatbot.sh` script for a clean start of both services.

4. **Update Dependencies**: Periodically update your dependencies to get bug fixes and security updates:
   ```bash
   pip install -r requirements.txt --upgrade
   cd react-frontend && npm update
   ```

5. **Development Mode**: Run the backend in debug mode to get more detailed error messages:
   ```
   DEBUG=True
   ```

If you continue to experience issues after trying these solutions, check the project's GitHub issues or create a new issue with detailed information about the problem you're encountering.
