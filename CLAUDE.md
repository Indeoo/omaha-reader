# CLAUD.md - Omaha Poker Assistant Project

## Project Overview
This is an Omaha Poker assistant that captures poker table screenshots and extracts game state information using OpenCV template matching and OCR (Tesseract). The system runs as a web application with real-time updates via WebSocket.

## Core Architecture

### Main Components
1. **OmahaEngine** - Central orchestration engine
2. **Image Capture Service** - Screenshot capture and change detection
3. **Detection Services** - Template matching for cards, positions, actions
4. **Game State Management** - Tracks game progression and moves
5. **Web API** - Flask + SocketIO for real-time updates

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

### Services
- **OmahaEngine**: Main orchestrator
- **ImageCaptureService**: Screenshot management
- **GameStateService**: Game state tracking
- **MoveReconstructor**: Action history building

### Matchers
- **PlayerCardMatcher**: Detects hero's cards
- **TableCardMatcher**: Detects community cards
- **PlayerPositionMatcher**: Detects positions (BTN, SB, etc.)
- **PlayerActionMatcher**: Detects action buttons

## Testing Approach

### Unit Tests
- Template matching accuracy
- OCR preprocessing validation
- Game state transitions

### Integration Tests
- Full detection pipeline
- WebSocket communication
- Multi-window handling

## Deployment Considerations

### System Requirements
- Windows OS (for window capture)
- Python 3.8+
- Tesseract OCR installed
- Sufficient CPU for real-time processing

### Performance Targets
- Detection cycle: < 1 second
- WebSocket latency: < 100ms
- Memory usage: < 500MB