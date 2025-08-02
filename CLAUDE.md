# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Omaha Poker Assistant Project

## Project Overview
This is an Omaha Poker assistant that captures poker table screenshots and extracts game state information using OpenCV template matching and OCR (Tesseract). The system runs as a web application with real-time updates via WebSocket.

## Core Architecture

The system uses a **client-server architecture** for maximum flexibility:

### Client Components (Local Detection)
1. **DetectionClient** - Local detection orchestrator
2. **Image Capture Service** - Screenshot capture and change detection  
3. **Detection Services** - Template matching for cards, positions, actions
4. **Server Connector** - HTTP/WebSocket communication to server

### Server Components (Web Interface)
1. **ServerWebApi** - Flask + SocketIO web interface
2. **Game Data Receiver** - Receives client detection data
3. **Server Game State** - Manages aggregated game states
4. **Real-time Broadcasting** - WebSocket updates to web clients

### Key Technologies
- **OpenCV** - Template matching for card/button detection
- **Tesseract OCR** - Reading bid amounts
- **Flask + SocketIO** - Real-time web interface
- **APScheduler** - Periodic screenshot capture

## Important Technical Details

### Screen Dimensions
- Every poker table screen is **784x584** pixels
- This is critical for coordinate calculations

### Template Matching Configuration
```python
# Player Cards
DEFAULT_SEARCH_REGION = (0.2, 0.5, 0.8, 0.95)  # Search bottom half
DEFAULT_MATCH_THRESHOLD = 0.955

# Table Cards  
DEFAULT_MATCH_THRESHOLD = 0.955
# Searches entire image for community cards

# Position Detection
DEFAULT_MATCH_THRESHOLD = 0.99  # Higher threshold for UI elements

# Action Buttons (Fold, Call, Raise)
DEFAULT_SEARCH_REGION = (0.376, 0.768, 0.95, 0.910)  # Bottom action area
```

### Player Positions Coordinates
```python
PLAYER_POSITIONS = {
    1: {'x': 300, 'y': 375, 'w': 40, 'h': 40},  # Bottom center (hero)
    2: {'x': 35, 'y': 330, 'w': 40, 'h': 40},   # Left side
    3: {'x': 35, 'y': 173, 'w': 40, 'h': 40},   # Top left
    4: {'x': 297, 'y': 120, 'w': 40, 'h': 40},  # Top center
    5: {'x': 562, 'y': 168, 'w': 40, 'h': 40},  # Top right
    6: {'x': 565, 'y': 332, 'w': 40, 'h': 40}   # Right side
}
```

### Bid Detection Coordinates
```python
BIDS_POSITIONS = {
    1: (388, 334, 45, 15),
    2: (200, 310, 40, 15),
    3: (185, 212, 45, 15),
    4: (450, 165, 45, 15),
    5: (572, 207, 40, 25),
    6: (562, 310, 45, 20),
}
```

### Action Button Coordinates
- **Fold**: x=310, y=460, w=50, h=30
- Other buttons are to the right of fold

## OCR Configuration for Bids

### Tesseract Settings
```python
# 1. Convert to grayscale
# 2. Invert colors (white text on black)
# 3. Apply binary threshold
# 4. Upscale 4x for better dot recognition
# 5. Dilate to connect decimal points

config = (
    "--psm 7 --oem 3 "
    "-c tessedit_char_whitelist=0123456789. "
    "-c load_system_dawg=0 -c load_freq_dawg=0"
)
```

## Game State Tracking

### Street Detection
Based on community card count:
- **0 cards**: Preflop
- **3 cards**: Flop
- **4 cards**: Turn
- **5 cards**: River

### Move Reconstruction
The system tracks player actions by:
1. Detecting bid changes between states
2. Identifying action types (fold, call, raise, check)
3. Maintaining move history per street

### New Game Detection
A new game is detected when:
- Player cards change
- Player positions change

## Template Organization

Templates are organized by country and category:
```
resources/templates/{country}/
├── player_cards/    # Player card templates
├── table_cards/     # Community card templates
├── positions/       # Position markers (BTN, SB, BB, etc.)
└── actions/         # Action buttons (Fold, Call, Raise)
```

## Web Interface Features

### Real-time Updates
- WebSocket connection for instant updates
- Visual highlights for changed elements
- Copy-to-clipboard functionality for card combinations

### Display Sections
1. **Player Cards** - Hero's hole cards
2. **Table Cards** - Community cards with street indicator
3. **Positions** - Player positions (BTN, SB, BB, etc.)
4. **Move History** - Actions per street
5. **Solver Link** - FlopHero integration (BETA)

### Configuration Options
```python
SHOW_TABLE_CARDS = True
SHOW_POSITIONS = True
SHOW_MOVES = True
SHOW_SOLVER_LINK = True
```

## Debug Mode

### Debug Folder Structure
When `DEBUG_MODE=true`, the system loads images from:
```
src/test/tables/test_move/
```

### Image Naming Convention
- Format: `{number}_{description}.png`
- Example: `02_unknown__2_50__5_Pot_Limit_Omaha.png`
- Result images: `{original_name}_result.png`

## Performance Optimizations

### Parallel Processing
- Template matching uses ThreadPoolExecutor
- Default max_workers = 4
- Parallel detection for all card templates

### Change Detection
- Image hashing to detect changes
- Only processes changed windows
- Removes closed windows from state

### Resource Management
- Careful cleanup of Windows GDI resources
- Fallback capture methods for problematic windows

## Common Issues and Solutions

### Template Matching
- Ensure templates match exact card appearance
- Higher threshold (0.99) for UI elements
- Lower threshold (0.955) for cards

### OCR Accuracy
- Proper preprocessing is critical
- 4x upscaling improves decimal point detection
- Whitelist only necessary characters

### Window Capture
- Primary method: PrintWindow API
- Fallback: Screen region capture
- Handle DPI awareness for Windows

## Future Enhancements

### Planned Features
- Multi-table support improvements
- Advanced move analysis
- Hand history export
- GTO solver integration

### Known Limitations
- Fixed screen resolution (784x584)
- Country-specific templates required
- Manual template creation needed

## Environment Variables

```bash
PORT=5001
WAIT_TIME=10
DEBUG_MODE=true
COUNTRY=canada
SHOW_TABLE_CARDS=true
SHOW_POSITIONS=true
SHOW_MOVES=true
SHOW_SOLVER_LINK=true
```

## Key Classes and Their Responsibilities

### Core Domain
- **CapturedWindow**: Represents a screenshot with metadata
- **ReadedCard**: Detected card with position and confidence
- **Game**: Current game state with history
- **Street**: Poker street enumeration

### Client Services
- **DetectionClient**: Client-side detection orchestrator
- **ImageCaptureService**: Screenshot management
- **GameStateService**: Game state tracking
- **ServerConnector**: HTTP/WebSocket communication with server

### Server Services  
- **ServerWebApi**: Web interface and API endpoints
- **GameDataReceiver**: Processes incoming client data
- **ServerGameState**: Server-side game state management

### Matchers
- **PlayerCardMatcher**: Detects hero's cards
- **TableCardMatcher**: Detects community cards
- **PlayerPositionMatcher**: Detects positions (BTN, SB, etc.)
- **PlayerActionMatcher**: Detects action buttons

## Development Commands

### Running the Application

#### Server (Internet-accessible machine):
```bash
# Configure server settings
python -m src.server.config

# Start server (hosts web UI and receives client data)
python -m src.server.main

# Server will be accessible at http://localhost:5001 by default
```

#### Client (Local machine with poker tables):
```bash
# Configure client settings  
python -m src.client.config

# Start detection client (sends data to server)
python -m src.client.main

# Client will connect to server and start detection
```

#### Single Machine Setup:
```bash
# Run both server and client on same machine
# Terminal 1: Start server
python -m src.server.main

# Terminal 2: Start client (connects to localhost)
python -m src.client.main
```

### Running Tests
```bash
# Run individual test modules using Python module syntax
python -m src.test.service.moves_test
python -m src.test.service.action_service_test
python -m src.test.detect_bids_test
python -m src.test.tesseract_test

# Run unittest-based tests
python -m unittest src.test.service.action_service_test.TestActionService.test_action_service

# Note: Tests are currently standalone scripts, not using unittest framework consistently
# Tests require being run from the project root directory
```

### Installing Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Note: Tesseract OCR must be installed separately on the system
# Windows: Download from GitHub releases
# macOS: brew install tesseract
# Linux: apt-get install tesseract-ocr
```

### Environment Configuration
Create a `.env` file or set environment variables:
```bash
PORT=5001                    # Web server port
WAIT_TIME=10                # Detection interval in seconds
DEBUG_MODE=true             # Use test images from src/test/tables/test_move/
COUNTRY=canada              # Template set (canada/usa)
SHOW_TABLE_CARDS=true       # Display community cards
SHOW_POSITIONS=true         # Display player positions
SHOW_MOVES=true             # Display move history
SHOW_SOLVER_LINK=true       # Show FlopHero integration link
```

## Architecture Overview

### Core Data Flow
**Client Side (Detection):**
1. **ImageCaptureService** → Captures poker table screenshots (784x584 resolution)
2. **PokerGameProcessor** → Orchestrates detection pipeline
3. **TemplateMatchService** → Detects cards using OpenCV template matching
4. **DetectUtils** → Detects positions and actions
5. **DetectionClient** → Aggregates detection data and sends to server

**Server Side (Web Interface):**
6. **GameDataReceiver** → Receives detection data from clients
7. **ServerGameState** → Manages aggregated game states
8. **ServerWebApi** → Serves real-time updates via WebSocket to web clients

### Key Service Dependencies
**Client Dependencies:**
- **DetectionClient** depends on ImageCaptureService, GameStateService, PokerGameProcessor, ServerConnector
- **PokerGameProcessor** depends on GameStateService, TemplateMatchService, DetectUtils
- **ServerConnector** provides HTTP/WebSocket communication to server

**Server Dependencies:**
- **ServerWebApi** depends on GameDataReceiver and serves Flask + SocketIO
- **GameDataReceiver** depends on ServerGameState for state management

### Template System Architecture
Templates are organized by country (canada/usa) and detection type:
- `player_cards/` - Hero's hole cards (52 card templates)
- `table_cards/` - Community cards (52 card templates)  
- `positions/` - Position indicators (BTN, SB, BB, EP, MP, CO)
- `actions/` - Action buttons (fold, check templates)
- `moves/` - Move detection templates (call, check, fold, raise)

### Critical Coordinates (Fixed 784x584 Resolution)
```python
# Player positions for 6-max tables
PLAYER_POSITIONS = {
    1: (300, 375, 40, 40),  # Hero (bottom center)
    2: (35, 330, 40, 40),   # Left
    3: (35, 173, 40, 40),   # Top left  
    4: (297, 120, 40, 40),  # Top center
    5: (562, 168, 40, 40),  # Top right
    6: (565, 332, 40, 40)   # Right
}

# Bid detection regions per position
BIDS_POSITIONS = {
    1: (388, 334, 45, 15),
    2: (200, 310, 40, 15),
    3: (185, 212, 45, 15),
    4: (450, 165, 45, 15),
    5: (572, 207, 40, 25),
    6: (562, 310, 45, 20)
}
```

## Testing Strategy

### Test Structure
- Tests are located in `src/test/` directory
- Test images are in `src/test/resources/`
- Debug mode uses images from `src/test/tables/test_move/`

### Running Specific Tests
```bash
# Test move grouping by street
python -m src.test.service.moves_test

# Test action detection
python -m src.test.service.action_service_test

# Test OCR bid detection  
python -m src.test.detect_bids_test

# Test Tesseract configuration
python -m src.test.tesseract_test
```

### Debug Mode Operation
When `DEBUG_MODE=true`, the system reads static images instead of live screenshots:
- Images loaded from `src/test/tables/test_move/`
- Naming convention: `{number}_{description}.png`
- Results saved as `{original_name}_result.png`

## Common Development Tasks

### Adding New Card Templates
1. Place card images in `resources/templates/{country}/player_cards/` or `table_cards/`
2. Use naming convention: `{rank}{suit}.png` (e.g., `AS.png`, `KH.png`)
3. Test detection accuracy with new templates

### Modifying Detection Regions
1. Update coordinates in `src/core/utils/detect_utils.py`
2. Adjust search regions in template matching services
3. Test with debug images to verify accuracy

### Debugging Detection Issues
1. Enable `DEBUG_MODE=true` and `save_result_images=True`
2. Check generated result images for detection overlays
3. Review detection files (`.txt`) for confidence scores
4. Adjust template thresholds if needed

## System Requirements & Deployment

### Required Dependencies
- Python 3.8+ 
- OpenCV (opencv-python)
- Tesseract OCR (system installation required)
- Flask + SocketIO for web interface
- APScheduler for background tasks

### Platform Considerations
- Primarily designed for Windows (window capture APIs)
- Screenshot capture may need adaptation for macOS/Linux
- Fixed 784x584 resolution assumption throughout codebase

## Important Instructions for Claude Code

### Code Editing Guidelines
- Always prefer editing existing files rather than creating new ones
- Only create files when absolutely necessary for the requested functionality
- Follow existing code patterns and architecture when making changes
- Preserve existing functionality when adding new features

### Working with moves_by_street.py
This module contains poker action grouping logic that may need improvements:
- Street transition logic has known issues with betting round detection
- Position order inconsistency between functions (EP vs UTG)
- Complex nested logic that's difficult to maintain
- Missing integration with actual game state (table cards for street detection)

### Template Management
- All templates must match exact pixel appearance of poker client
- Use higher thresholds (0.99) for UI elements, lower (0.955) for cards
- Templates are country-specific (canada/usa folders)
- Test template changes thoroughly with debug mode images

### OCR and Detection
- Tesseract preprocessing is critical for bid detection accuracy
- 4x upscaling and proper image inversion improve decimal recognition
- Coordinate systems assume fixed 784x584 poker table resolution
- Change detection uses image hashing to optimize performance

### Project State and Limitations
- No formal linting or formatting tools configured (no black, flake8, etc.)
- Tests are mixed between standalone scripts and unittest framework
- No automated CI/CD pipeline or build system
- Manual template creation required for new poker sites/themes
- Windows-centric design may need platform adaptations

## Memory

### Poker Rule Awareness
- Use Omaha Poker rules