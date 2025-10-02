# Screen Capture Component

**Team Assignment**: 1-2 developers  
**Estimated Time**: 2-3 weeks  
**Dependencies**: `pillow`, `pyautogui`, `opencv-python`, `mss`

## Overview

The Screen Capture component handles all aspects of capturing and preprocessing screen content:
- Taking screenshots of active games
- Detecting which games are currently running
- Image preprocessing for AI analysis
- Managing capture regions and timing

## Architecture

```
Screen Capture Flow:
Game Detection → Screenshot Capture → Image Processing → AI Agent
```

## Key Files

### `screenshot.py`
- **Purpose**: Capture screenshots efficiently and reliably
- **Key Functions**:
  - `capture()`: Take a screenshot of the active window/screen
  - `capture_region(x, y, width, height)`: Capture specific screen region
  - `save_screenshot(image, path)`: Save screenshot for debugging
- **Integration**: Provides images to AI agent for analysis

### `game_detector.py`
- **Purpose**: Identify running games and active windows
- **Key Functions**:
  - `get_active_game()`: Identify currently active game
  - `is_game_running(game_name)`: Check if specific game is running
  - `get_game_window_info()`: Get window position and size
- **Integration**: Helps optimize capture regions and game-specific processing

### `image_processor.py`
- **Purpose**: Preprocess images for optimal AI analysis
- **Key Functions**:
  - `resize_image(image, max_size)`: Resize for API limits
  - `enhance_contrast(image)`: Improve text readability
  - `crop_ui_elements(image)`: Focus on relevant UI areas
- **Integration**: Prepares images before sending to AI agent

## Implementation Tasks

### Phase 1: Basic Functionality
- [ ] Implement basic screenshot capture using `mss` or `pyautogui`
- [ ] Add game window detection using `psutil` and window APIs
- [ ] Create image preprocessing pipeline
- [ ] Add support for different screen resolutions
- [ ] Implement basic error handling for capture failures

### Phase 2: Enhanced Features
- [ ] Add multi-monitor support
- [ ] Implement smart capture regions based on game type
- [ ] Add image quality optimization
- [ ] Create capture scheduling and caching
- [ ] Add support for different image formats

## API Interface

```python
class ScreenCaptureManager:
    async def capture_screen(self) -> Image
    async def capture_active_window(self) -> Image
    async def detect_active_game(self) -> GameInfo
    def set_capture_region(self, region: CaptureRegion) -> None
    def preprocess_image(self, image: Image) -> Image
```

## Configuration

```python
# Environment variables used by this component
SCREENSHOT_INTERVAL=0.5
IMAGE_QUALITY=85
CAPTURE_REGION_AUTO=true
SUPPORTED_GAMES=all
GAME_DETECTION_METHOD=window_title
```

## Testing Strategy

### Unit Tests
- Test screenshot capture on different screen sizes
- Test game detection with various running applications
- Test image preprocessing with sample images
- Test error handling for permission issues

### Integration Tests
- Test capture with real games running
- Test performance under different system loads
- Test multi-monitor configurations

## Game Detection Methods

### Window Title Detection
- Scan running processes for known game executables
- Match window titles against game database
- Handle different game launchers (Steam, Epic, etc.)

### Process Detection
- Monitor running processes for game executables
- Use process names and paths for identification
- Handle games launched through different methods

## Image Preprocessing Pipeline

1. **Capture**: Raw screenshot from screen/window
2. **Crop**: Remove unnecessary borders or areas
3. **Resize**: Optimize for AI API limits (typically 1024x1024 max)
4. **Enhance**: Improve contrast and text readability
5. **Format**: Convert to appropriate format (PNG/JPEG)

## Performance Considerations

- Use efficient capture methods (`mss` is faster than `pyautogui`)
- Implement capture caching to avoid redundant screenshots
- Optimize image compression for API transmission
- Consider capture frequency vs. system performance

## Error Handling

- Screen capture permissions denied
- Game window not found or minimized
- Multiple monitors with different configurations
- High system load affecting capture performance
- Image processing failures

## Game-Specific Optimizations

### Common Game Types
- **Menu-heavy games**: Focus on UI elements
- **Action games**: Capture HUD and status information
- **Strategy games**: Capture entire screen for context
- **Text-heavy games**: Enhance text readability

### Capture Regions
```python
# Example capture regions for different game types
GAME_REGIONS = {
    "menu_game": {"x": 0, "y": 0, "width": "100%", "height": "100%"},
    "hud_game": {"x": 0, "y": 0, "width": "100%", "height": "20%"},
    "inventory_game": {"x": "75%", "y": "25%", "width": "25%", "height": "50%"}
}
```

## Future Enhancements

- Real-time screen analysis for dynamic capture regions
- Integration with game APIs for enhanced detection
- Support for VR/AR game capture
- Machine learning-based UI element detection
- Capture optimization based on user behavior patterns
