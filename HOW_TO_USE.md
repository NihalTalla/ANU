# How to Use Anu Dashboard - Enhanced Personal Assistant

## Getting Started

1. **Run Anu Dashboard**: 
   - Double-click on `run_enhanced_dashboard.bat` to start the dashboard assistant.
   - Or run directly with `python anu_dashboard.py` from the command line.

## Interface Overview

The Anu Dashboard has two main sections:

1. **System Monitoring Panel** (Left Side):
   - Real-time CPU usage chart
   - Memory usage chart
   - Disk usage chart
   - Top processes list

2. **Assistant Panel** (Right Side):
   - Text input field
   - Voice control buttons
   - Quick action buttons
   - Conversation log

## Voice and Text Commands

Anu Dashboard responds to both voice and text commands:

### Basic Commands:
- **"Open [application]"** - Opens applications like Chrome, Notepad, etc.
  - Examples: "Open Chrome", "Open Notepad", "Open Calculator"

### Time and Date:
- **"What time is it"** - Tells you the current time
- **"What is today"** or **"What day is it"** - Tells you the current date

### System Information:
- **"System info"** or **"System status"** - Shows detailed system information
- **"Processes"** or **"Running apps"** - Shows top running processes

### Enhanced Features:
- **"Take a screenshot"** - Opens screenshot dialog with options
- **"Search for [query]"** - Performs a web search
- **"Generate code"** or **"Write code"** - Opens code generation dialog
- **"Tell me a joke"** - Tells a random joke
- **"Save a note"** or **"Write down"** - Opens note-taking dialog
- **"Weather in [location]"** - Looks up weather information
- **"Calculate [expression]"** - Performs calculations

### Conversation:
- **"Hello"** or **"Hi"** - Greets you
- **"Help"** - Shows available commands
- **"Goodbye"** or **"Exit"** - Closes the assistant

## Quick Actions

The dashboard provides quick access buttons for common actions:
- **Web Search** - Opens the web search dialog
- **Generate Code** - Opens the code generation dialog
- **Take Screenshot** - Opens the screenshot dialog with options
- **System Info** - Shows detailed system information
- **Tell Joke** - Tells a random joke
- **Save Notes** - Opens the note-taking dialog

## Troubleshooting

If you encounter any issues:

1. **No Voice Output**:
   - Check your speakers/headphones are connected and volume is up
   - Check Windows sound settings

2. **Microphone Issues**:
   - Make sure your microphone is connected and working
   - Check Windows microphone privacy settings
   - Try using the text input instead of voice commands

3. **Application Not Found**:
   - Try using the exact name of the application
   - For custom applications, you may need to edit the `apps` dictionary in the code

## Advanced Usage

### Adding New Applications

To add new applications to Anu's knowledge:

1. Open `anu_dashboard.py` in a text editor
2. Find the `apps` dictionary (around line 50)
3. Add a new entry with the application name and path:
   ```python
   'app_name': r'C:\Path\To\Application.exe',
   ```

### Customizing Code Templates

To add new code templates:

1. Open `anu_dashboard.py` in a text editor
2. Find the `code_templates` dictionary
3. Add new templates to the appropriate language section

## Enjoy Using Anu Dashboard!

Anu Dashboard is designed to make your computer interaction easier through a comprehensive interface with system monitoring and assistant features. Feel free to explore and discover what Anu Dashboard can do for you!