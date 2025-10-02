# Contributing to AGC Software

Thank you for your interest in contributing to the Adaptive Gaming Controller project! This document provides guidelines and information for team members and contributors.

## 🎯 Project Mission

We're building accessibility software to help blind users navigate and interact with games through AI-powered voice commands. Every contribution should keep this mission in mind and prioritize accessibility and user experience.

## 🏗️ Development Workflow

### Getting Started

1. **Set up your development environment**:
   ```bash
   git clone <repository-url>
   cd AGC-software
   python scripts/setup_dev.py
   ```

2. **Activate your virtual environment**:
   ```bash
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Configure your environment**:
   - Copy `env.example` to `.env`
   - Add your API keys and configuration

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/component-name-feature`: Individual feature branches
- `hotfix/issue-description`: Critical bug fixes

### Workflow Steps

1. **Create a feature branch**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/voice-input-hotkey-detection
   ```

2. **Make your changes**:
   - Follow the coding standards below
   - Write tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   python scripts/run_tests.py --type all
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(voice_input): add hotkey detection for F1 key"
   ```

5. **Push and create a pull request**:
   ```bash
   git push origin feature/voice-input-hotkey-detection
   ```

## 📝 Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Type hints**: Required for all public functions and methods
- **Docstrings**: Google style for all modules, classes, and functions

### Code Formatting

We use automated formatting tools:

```bash
# Format code
python scripts/run_tests.py --type format

# Check formatting
python scripts/run_tests.py --type format-check
```

### Example Code Style

```python
"""Module for handling voice input processing."""

from typing import Optional, List, Callable
import asyncio
from pathlib import Path

from loguru import logger
from pynput import keyboard


class HotkeyListener:
    """Listens for global hotkey presses to activate voice input."""
    
    def __init__(self, activation_key: str, callback: Callable[[], None]) -> None:
        """Initialize the hotkey listener.
        
        Args:
            activation_key: The key combination to listen for (e.g., 'f1')
            callback: Function to call when hotkey is pressed
            
        Raises:
            ValueError: If activation_key is not supported
        """
        self.activation_key = activation_key
        self.callback = callback
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        
    async def start(self) -> None:
        """Start listening for hotkey presses."""
        logger.info(f"Starting hotkey listener for {self.activation_key}")
        # Implementation here...
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── voice_input/
│   ├── screen_capture/
│   ├── ai_agent/
│   └── voice_response/
├── integration/             # Integration tests between components
└── fixtures/                # Test data and mock files
```

### Writing Tests

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test component interactions
3. **Mock External Services**: Use mocks for AI APIs, audio devices, etc.
4. **Test Coverage**: Aim for 80%+ coverage on new code

### Test Example

```python
"""Tests for hotkey listener functionality."""

import pytest
from unittest.mock import Mock, patch
from voice_input.hotkey_listener import HotkeyListener


class TestHotkeyListener:
    """Test cases for HotkeyListener class."""
    
    def test_init_with_valid_key(self):
        """Test initialization with valid activation key."""
        callback = Mock()
        listener = HotkeyListener("f1", callback)
        
        assert listener.activation_key == "f1"
        assert listener.callback == callback
    
    def test_init_with_invalid_key(self):
        """Test initialization with invalid activation key."""
        callback = Mock()
        
        with pytest.raises(ValueError):
            HotkeyListener("invalid_key", callback)
    
    @patch('voice_input.hotkey_listener.keyboard.GlobalHotKeys')
    async def test_start_listening(self, mock_hotkeys):
        """Test starting the hotkey listener."""
        callback = Mock()
        listener = HotkeyListener("f1", callback)
        
        await listener.start()
        
        mock_hotkeys.assert_called_once()
```

## 📋 Component Responsibilities

### Voice Input Team (1-2 developers)
- **Files**: `src/voice_input/`
- **Responsibilities**: Hotkey detection, speech-to-text, command parsing
- **Key Deliverables**:
  - Global hotkey listener
  - Speech recognition integration
  - Command parsing system
  - Audio input handling

### Screen Capture Team (1-2 developers)
- **Files**: `src/screen_capture/`
- **Responsibilities**: Screenshot capture, game detection, image preprocessing
- **Key Deliverables**:
  - Efficient screenshot capture
  - Game window detection
  - Image preprocessing pipeline
  - Multi-monitor support

### AI Agent Team (2-3 developers)
- **Files**: `src/ai_agent/`
- **Responsibilities**: Image analysis, UI detection, command processing, response generation
- **Key Deliverables**:
  - AI vision integration
  - UI element detection
  - Command-to-action mapping
  - Response generation system

### Voice Response Team (1 developer)
- **Files**: `src/voice_response/`
- **Responsibilities**: Text-to-speech, audio output management
- **Key Deliverables**:
  - TTS integration
  - Audio output management
  - Response queuing system

### Game Integration Team (1-2 developers)
- **Files**: `src/game_integration/`
- **Responsibilities**: Game-specific configurations and optimizations
- **Key Deliverables**:
  - Game detection and configuration
  - UI pattern templates
  - Game-specific optimizations

## 🔄 Code Review Process

### Pull Request Requirements

- [ ] All tests pass
- [ ] Code coverage maintained (80%+)
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Descriptive commit messages
- [ ] PR description explains changes

### Review Checklist

**Functionality**:
- [ ] Code works as intended
- [ ] Edge cases handled
- [ ] Error handling implemented
- [ ] Performance considerations addressed

**Code Quality**:
- [ ] Follows coding standards
- [ ] Well-structured and readable
- [ ] Appropriate comments and docstrings
- [ ] No code duplication

**Testing**:
- [ ] Adequate test coverage
- [ ] Tests are meaningful and comprehensive
- [ ] Integration points tested

**Accessibility**:
- [ ] Changes consider blind user experience
- [ ] Audio feedback is clear and helpful
- [ ] Response times are reasonable

## 🐛 Issue Reporting

### Bug Reports

Use the following template for bug reports:

```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 10, macOS 12.0]
- Python version: [e.g., 3.9.7]
- AGC version: [e.g., 0.1.0]

## Additional Context
Any other relevant information
```

### Feature Requests

```markdown
## Feature Description
Brief description of the proposed feature

## User Story
As a [user type], I want [functionality] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Additional Context
Any mockups, examples, or related issues
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public functions, classes, and modules
- **Type hints**: All function parameters and return values
- **Comments**: Complex logic and business rules
- **README files**: Each component directory

### User Documentation

- **API documentation**: Auto-generated from docstrings
- **User guides**: Step-by-step instructions
- **Architecture docs**: System design and component interactions

## 🚀 Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Release notes prepared
- [ ] Tagged in git

## 💬 Communication

### Team Channels

- **General Discussion**: [Discord/Slack channel]
- **Technical Questions**: GitHub Discussions
- **Bug Reports**: GitHub Issues
- **Feature Requests**: GitHub Issues

### Meeting Schedule

- **Daily Standups**: 9:00 AM (optional for async team)
- **Weekly Planning**: Mondays 2:00 PM
- **Sprint Reviews**: Every 2 weeks
- **Retrospectives**: End of each sprint

## 🎯 Accessibility Guidelines

Remember, we're building for blind users. Consider these principles:

1. **Audio First**: All feedback should be available through audio
2. **Clear Communication**: Use descriptive, unambiguous language
3. **Consistent Patterns**: Maintain consistent interaction patterns
4. **Error Recovery**: Provide clear error messages and recovery options
5. **Performance**: Minimize response times for better user experience

## 📞 Getting Help

- **Technical Issues**: Ask in the team channel or create a GitHub issue
- **Setup Problems**: Check the setup script or ask for help
- **Code Reviews**: Tag team members for specific expertise
- **Architecture Questions**: Discuss in team meetings or with project lead

---

Thank you for contributing to making gaming more accessible! 🎮♿
