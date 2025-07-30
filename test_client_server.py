#!/usr/bin/env python3
"""
Test script for client-server communication.
This script tests the basic functionality without requiring actual poker detection.
"""

import json
import time
import requests
from datetime import datetime
from loguru import logger

from src.core.shared.message_protocol import (
    GameUpdateMessage, 
    ClientRegistrationMessage,
    GameDataSerializer
)
from src.core.client.server_connector import ServerConnectorFactory


def test_server_connection(server_url: str) -> bool:
    """Test if server is reachable."""
    try:
        response = requests.get(f"{server_url}/api/clients", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Server is reachable: {server_url}")
            return True
        else:
            logger.error(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot reach server: {str(e)}")
        return False


def test_client_registration(server_url: str, client_id: str) -> bool:
    """Test client registration."""
    try:
        registration_data = {
            'type': 'client_register',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{server_url}/api/client/register",
            json=registration_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                logger.info(f"✅ Client registration successful: {client_id}")
                return True
            else:
                logger.error(f"❌ Registration failed: {result.get('message')}")
                return False
        else:
            logger.error(f"❌ Registration HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        return False


def test_game_update(server_url: str, client_id: str) -> bool:
    """Test sending game update."""
    try:
        # Create test game data
        test_game_data = {
            'player_cards': [
                {'template_name': 'AS', 'match_score': 0.98, 'position': None, 'name': 'AS'},
                {'template_name': 'KH', 'match_score': 0.96, 'position': None, 'name': 'KH'}
            ],
            'table_cards': [
                {'template_name': 'QD', 'match_score': 0.95, 'position': None, 'name': 'QD'},
                {'template_name': 'JC', 'match_score': 0.93, 'position': None, 'name': 'JC'},
                {'template_name': 'TS', 'match_score': 0.91, 'position': None, 'name': 'TS'}
            ],
            'positions': {
                '1': {'template_name': 'BTN', 'match_score': 0.99, 'position': None, 'name': 'BTN'}
            },
            'moves': [],
            'street': 'flop',
            'solver_link': None
        }
        
        game_update_data = {
            'type': 'game_update',
            'client_id': client_id,
            'window_name': 'test_poker_table',
            'timestamp': datetime.now().isoformat(),
            'game_data': test_game_data
        }
        
        response = requests.post(
            f"{server_url}/api/client/update",
            json=game_update_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                logger.info("✅ Game update successful")
                return True
            else:
                logger.error(f"❌ Game update failed: {result.get('message')}")
                return False
        else:
            logger.error(f"❌ Game update HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Game update error: {str(e)}")
        return False


def test_web_ui(server_url: str) -> bool:
    """Test web UI accessibility."""
    try:
        response = requests.get(server_url, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Web UI is accessible")
            return True
        else:
            logger.error(f"❌ Web UI returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Web UI error: {str(e)}")
        return False


def test_config_endpoint(server_url: str) -> bool:
    """Test configuration endpoint."""
    try:
        response = requests.get(f"{server_url}/api/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            logger.info(f"✅ Config endpoint working: {config}")
            return True
        else:
            logger.error(f"❌ Config endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Config endpoint error: {str(e)}")
        return False


def test_connector_selection(server_url: str) -> bool:
    """Test connector auto-selection and factory."""
    try:
        logger.info("🔗 Testing connector factory...")
        
        # Test both connector types if available
        results = ServerConnectorFactory.test_both_connectors(server_url)
        
        http_working = results['http']['connected']
        ws_working = results['websocket']['connected']
        
        logger.info(f"   HTTP connector: {'✅ Working' if http_working else '❌ Failed'}")
        logger.info(f"   WebSocket connector: {'✅ Working' if ws_working else '❌ Failed'}")
        
        if http_working or ws_working:
            # Test auto-selection
            auto_connector = ServerConnectorFactory.create_connector(server_url, 'auto')
            if auto_connector:
                connector_type = "WebSocket" if hasattr(auto_connector, 'connect') else "HTTP"
                logger.info(f"   Auto-selected: {connector_type}")
                auto_connector.close()
                return True
            else:
                logger.error("   Auto-selection failed")
                return False
        else:
            logger.error("   No connectors working")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connector selection error: {str(e)}")
        return False


def main():
    logger.info("🧪 Testing Client-Server Communication")
    logger.info("=" * 50)
    
    # Configuration
    server_url = input("Enter server URL (default: http://localhost:5001): ").strip()
    if not server_url:
        server_url = "http://localhost:5001"
    
    client_id = f"test_client_{int(time.time())}"
    
    logger.info(f"🌐 Testing server: {server_url}")
    logger.info(f"🆔 Test client ID: {client_id}")
    logger.info("-" * 50)
    
    # Run tests
    tests = [
        ("Server Connection", lambda: test_server_connection(server_url)),
        ("Client Registration", lambda: test_client_registration(server_url, client_id)),
        ("Game Update", lambda: test_game_update(server_url, client_id)),
        ("Web UI Access", lambda: test_web_ui(server_url)),
        ("Config Endpoint", lambda: test_config_endpoint(server_url)),
        ("Connector Selection", lambda: test_connector_selection(server_url)),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running test: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                logger.error(f"❌ Test failed: {test_name}")
        except Exception as e:
            logger.error(f"❌ Test error in {test_name}: {str(e)}")
    
    # Results
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Client-server communication is working.")
        logger.info(f"🌍 Web UI: {server_url}")
        logger.info(f"📡 API: {server_url}/api/clients")
    else:
        logger.error("❌ Some tests failed. Check server status and configuration.")
        
        if passed == 0:
            logger.error("💡 Troubleshooting tips:")
            logger.error("   - Make sure server is running: python main_server.py")
            logger.error(f"   - Check server URL: {server_url}")
            logger.error("   - Verify network connectivity")
            logger.error("   - Check firewall settings")


if __name__ == "__main__":
    main()