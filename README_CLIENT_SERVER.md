# Client-Server Architecture Guide

This guide explains how to use the new client-server architecture for the Omaha Poker Detection system.

## Overview

The system is now split into two components:

- **🔍 CLIENT** - Runs locally on the machine with poker tables, performs detection
- **🌐 SERVER** - Runs on internet-accessible server, hosts web UI and receives data

## Quick Start

### 1. Set Up Server (Internet-Accessible Machine)

```bash
# Configure server
python -m src.server.config

# Start server
python -m src.server.main
```

The server will be accessible at `http://YOUR_SERVER_IP:5001`

### 2. Set Up Client (Local Machine with Poker Tables)

```bash
# Configure client
python -m src.client.config

# Start client  
python -m src.client.main
```

The client will connect to your server and start sending detection data.

## Detailed Setup

### Server Setup

1. **Configure Server**
   ```bash
   python -m src.server.config
   ```
   This creates `.env.server` with your settings:
   - Server host/port
   - Allowed clients
   - UI display options

2. **Start Server**
   ```bash
   python -m src.server.main
   ```

3. **Access Web UI**
   - Open `http://YOUR_SERVER_IP:5001` in browser
   - View real-time poker data from connected clients

### Client Setup

1. **Configure Client**
   ```bash
   python -m src.client.config
   ```
   This creates `.env.client` with your settings:
   - Server URL to connect to
   - Detection settings
   - Connection parameters

2. **Start Client**
   ```bash
   python -m src.client.main
   ```
   
3. **Verify Connection**
   - Check client logs for successful registration
   - Check server logs for incoming client connection
   - View connected clients at `http://SERVER:5001/api/clients`

## Configuration Files

### Client Configuration (`.env.client`)
```bash
SERVER_URL=http://your-server.com:5001
CLIENT_ID=poker_client_1
DETECTION_INTERVAL=10
DEBUG_MODE=false
COUNTRY=canada
CONNECTION_TIMEOUT=10
RETRY_ATTEMPTS=3
RETRY_DELAY=5
CONNECTOR_TYPE=auto  # 'auto', 'http', or 'websocket'
```

### Server Configuration (`.env.server`)
```bash
PORT=5001
HOST=0.0.0.0
ALLOWED_CLIENTS=*
MAX_CLIENTS=10
SHOW_TABLE_CARDS=true
SHOW_POSITIONS=true
SHOW_MOVES=true
SHOW_SOLVER_LINK=true
```

## Connection Types

The system supports two communication methods:

### **HTTP Connector** (Default fallback)
- Uses REST API calls for communication
- Reliable but slightly higher latency  
- Works with basic HTTP servers
- Automatic retry logic for failed requests

### **WebSocket Connector** (Recommended)
- Real-time bidirectional communication
- Lower latency for game updates
- Automatic reconnection on connection loss
- Requires `python-socketio` package

### **Auto Selection**
- Automatically chooses WebSocket if available
- Falls back to HTTP if WebSocket unavailable
- Recommended for most users (set `CONNECTOR_TYPE=auto`)

### **Testing Connectors**
```bash
# Test both connector types
python test_connectors.py

# Full communication test including connectors
python test_client_server.py
```

## Network Requirements

### Firewall Settings
- **Server**: Open port 5001 (or your chosen port) for incoming connections
- **Client**: Allow outbound HTTP connections to server

### Internet Access
- **Server**: Must be accessible from internet
- **Client**: Must be able to reach server URL

## API Endpoints

### Server Endpoints

#### Web UI
- `GET /` - Main poker detection interface
- `GET /api/config` - UI configuration

#### Client Communication  
- `POST /api/client/register` - Client registration
- `POST /api/client/update` - Game state updates
- `GET /api/clients` - List connected clients

#### WebSocket
- `ws://server:port/socket.io/` - Real-time updates

### Client Communication

The client automatically:
1. Registers with server on startup
2. Sends game updates when poker state changes
3. Handles connection failures with retries

## Troubleshooting

### Connection Issues

**Client cannot connect to server:**
```bash
# Test server connectivity
curl http://your-server:5001/api/clients

# Check client configuration
cat .env.client

# Check server logs for blocked connections
```

**Server not accessible:**
```bash
# Check if server is running
netstat -tlnp | grep 5001

# Check firewall rules
ufw status  # Ubuntu
firewall-cmd --list-all  # CentOS/RHEL
```

### Common Problems

1. **Wrong SERVER_URL in client config**
   - Update `.env.client` with correct server address
   - Use IP address instead of hostname if DNS issues

2. **Firewall blocking connections**
   - Open port 5001 on server machine
   - Allow outbound connections from client machine

3. **Server not accessible from internet**
   - Check router port forwarding
   - Verify server HOST is set to `0.0.0.0`
   - Consider using cloud hosting (AWS, DigitalOcean, etc.)

## Deployment Options

### Local Network
- Server: `HOST=192.168.1.100` (local IP)
- Client: `SERVER_URL=http://192.168.1.100:5001`

### Cloud Hosting
- Deploy server to AWS/DigitalOcean/etc.
- Use public IP or domain name
- Configure security groups/firewall rules

### Docker Deployment
```bash
# Server
docker run -p 5001:5001 -e HOST=0.0.0.0 omaha-server

# Client  
docker run -e SERVER_URL=http://server:5001 omaha-client
```

## Monitoring

### Server Monitoring
```bash
# Check connected clients
curl http://localhost:5001/api/clients

# View server logs
tail -f logs/server.log
```

### Client Monitoring
```bash
# View client logs
tail -f logs/client.log

# Check client status
ps aux | grep main_client
```

## Security Considerations

### Basic Security
- Use HTTPS in production (`https://` URLs)
- Restrict `ALLOWED_CLIENTS` to known client IDs
- Run server behind reverse proxy (nginx)

### Advanced Security
- Implement client authentication tokens
- Use VPN for client-server communication
- Enable CORS restrictions
- Add rate limiting

## Migration from Single Machine

1. **Backup Current Setup**
   ```bash
   cp .env .env.backup
   cp -r resources/ resources_backup/
   ```

2. **Install on Server Machine**
   ```bash
   git clone [repository]
   pip install -r requirements.txt
   python -m src.server.config
   python -m src.server.main
   ```

3. **Configure Client on Original Machine**
   ```bash
   python -m src.client.config
   # Enter your server URL
   python -m src.client.main
   ```

4. **Verify Migration**
   - Check web UI shows same data
   - Verify real-time updates work
   - Test with multiple poker tables

## Support

For issues with the client-server setup:

1. Check logs on both client and server
2. Verify network connectivity
3. Test with simple HTTP requests
4. Check firewall and port settings
5. Review configuration files

The original single-machine setup (`main_web.py`) continues to work for local-only usage.


# Omaha Reader

heroku builds:create --app omaha-reader
heroku logs --tail --app omaha-reader
heroku restart --app omaha-reader
heroku run bash -a omaha-reader

heroku open --app omaha-reader