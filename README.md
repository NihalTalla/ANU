# Anu Dashboard - Enhanced Personal Assistant

Anu Dashboard is a comprehensive desktop assistant with system monitoring capabilities and a rich set of features.

## Features

### Core Features
- Voice recognition and text-to-speech capabilities
- Interactive dashboard with system monitoring
- Real-time CPU, memory, and disk usage charts
- Process monitoring

### Assistant Features
- Open applications and websites
- Tell time and date
- Answer questions
- Enhanced screenshot capabilities with options
- System information display
- Web search with multiple search engines
- Code generation for multiple programming languages
- Note-taking functionality
- Joke telling with multiple categories
- Weather information lookup
- Simple calculator functionality

## Requirements

- Python 3.8 or higher
- Windows 10 or higher
- Microphone for voice input
- Speakers for voice output
- Required Python packages (see requirements.txt)

## Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the assistant:
```
python anu_dashboard.py
```

Or use the batch file:
```
run_enhanced_dashboard.bat
```

## Voice/Text Commands

- "Hello" - Greet the assistant
- "What time is it" - Get the current time
- "What date is it" - Get the current date
- "Open [application]" - Open an application
- "Take a screenshot" - Capture the screen with options
- "System info" - Get system information
- "Search for [query]" - Perform a web search
- "Generate code" - Open code generation dialog
- "Tell me a joke" - Get a random joke
- "Save a note" - Create and save notes
- "Weather in [location]" - Get weather information
- "Calculate [expression]" - Perform calculations
- "Help" - Show available commands
- "Exit" or "Goodbye" - Close the assistant

## Quick Actions

The dashboard provides quick access buttons for common actions:
- Web Search
- Generate Code
- Take Screenshot
- System Info
- Tell Joke
- Save Notes

## Project Structure

```
anu/
├── anu_dashboard.py       # Main dashboard application
├── data/                  # Database storage
├── logs/                  # Log files
└── requirements.txt       # Project dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.