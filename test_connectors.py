#!/usr/bin/env python3
"""
Connector Diagnostic Tool
Tests both HTTP and WebSocket connectors to help choose the best option.
"""

import sys
from loguru import logger
from src.core.client.server_connector import ServerConnectorFactory


def test_connectors(server_url: str):
    """Test both connector types and display results."""
    logger.info("🧪 Testing Server Connectors")
    logger.info("=" * 50)
    logger.info(f"🌐 Server URL: {server_url}")
    logger.info("-" * 50)
    
    # Test both connectors
    results = ServerConnectorFactory.test_both_connectors(server_url)
    
    # Display results
    logger.info("\n📊 Test Results:")
    logger.info("-" * 30)
    
    # HTTP Connector Results
    http_result = results['http']
    http_status = "✅ Available" if http_result['available'] else "❌ Not Available"
    http_connection = "✅ Connected" if http_result['connected'] else "❌ Failed"
    logger.info(f"🔗 HTTP Connector:")
    logger.info(f"   Status: {http_status}")
    logger.info(f"   Connection: {http_connection}")
    if http_result['error']:
        logger.info(f"   Error: {http_result['error']}")
    
    # WebSocket Connector Results
    ws_result = results['websocket']
    ws_status = "✅ Available" if ws_result['available'] else "❌ Not Available"
    ws_connection = "✅ Connected" if ws_result['connected'] else "❌ Failed"
    logger.info(f"🔗 WebSocket Connector:")
    logger.info(f"   Status: {ws_status}")
    logger.info(f"   Connection: {ws_connection}")
    if ws_result['error']:
        logger.info(f"   Error: {ws_result['error']}")
    
    # Recommendations
    logger.info("\n💡 Recommendations:")
    logger.info("-" * 30)
    
    if http_result['connected'] and ws_result['connected']:
        logger.info("✅ Both connectors working - WebSocket recommended for real-time performance")
        logger.info("   Use CONNECTOR_TYPE=websocket in your .env.client file")
    elif http_result['connected'] and not ws_result['connected']:
        logger.info("⚠️  Only HTTP connector working - use HTTP connector")
        logger.info("   Use CONNECTOR_TYPE=http in your .env.client file")
        if not ws_result['available']:
            logger.info("   💡 Install python-socketio for WebSocket support: pip install python-socketio")
    elif not http_result['connected'] and ws_result['connected']:
        logger.info("⚠️  Only WebSocket connector working - use WebSocket connector")
        logger.info("   Use CONNECTOR_TYPE=websocket in your .env.client file")
    else:
        logger.info("❌ Neither connector working - check server status and network connectivity")
        logger.info("   Troubleshooting:")
        logger.info("   - Ensure server is running: python main_server.py")
        logger.info(f"   - Check server URL: {server_url}")
        logger.info("   - Verify network connectivity")
        logger.info("   - Check firewall settings")
    
    # Return overall success
    return http_result['connected'] or ws_result['connected']


def main():
    logger.info("🔌 Omaha Poker Connector Diagnostic Tool")
    logger.info("=" * 50)
    
    # Get server URL
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = input("Enter server URL (default: http://localhost:5001): ").strip()
        if not server_url:
            server_url = "http://localhost:5001"
    
    try:
        # Test connectors
        success = test_connectors(server_url)
        
        if success:
            logger.info("\n🎉 At least one connector is working!")
            logger.info("You can now start the client with: python main_client.py")
        else:
            logger.error("\n❌ No connectors are working - please fix connection issues first")
            sys.exit(1)
            
        # Show auto-selection result
        logger.info("\n🔄 Auto-Selection Test:")
        logger.info("-" * 30)
        try:
            auto_connector = ServerConnectorFactory.create_connector(server_url, 'auto')
            connector_type = "WebSocket" if hasattr(auto_connector, 'connect') else "HTTP"
            logger.info(f"   Auto-selected: {connector_type}")
            auto_connector.close()
        except Exception as e:
            logger.error(f"   Auto-selection failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()