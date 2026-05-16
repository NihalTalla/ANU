import speech_recognition as sr
import pyttsx3
import threading
import time
import os
import datetime
import random
import traceback
import queue
import importlib.util
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import sys
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")
import webbrowser
import requests
import json
import pyautogui
import pyjokes
import re

class AnuDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Anu OS Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f5f5")
        
        # Flag to track if GUI is ready
        self.gui_ready = False
        self.log_queue = queue.Queue()
        
        # Set up the GUI
        self.setup_gui()
        self.gui_ready = True
        
        # Initialize speech recognition
        self.log("Setting up speech recognition...")
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize text-to-speech
        self.log("Setting up text-to-speech...")
        self.setup_voice()

        # Detect whether microphone input is usable on this machine.
        self.setup_microphone_support()
        
        # Speech queue for thread safety
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        
        # Schedule speech thread to start after the main loop starts
        # This is done via root.after in the main() function
        
        self.is_listening = False
        self.listening_thread = None
        
        # Common applications
        self.apps = {
            'brave': r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Brave.lnk',
            'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'explorer': 'explorer.exe',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe'
        }
        
        # Special Windows apps that need to be launched with the 'start' command
        self.windows_apps = {
            'camera': 'microsoft.windows.camera:',
            'photos': 'ms-photos:',
            'weather': 'msnweather:',
            'settings': 'ms-settings:',
            'maps': 'bingmaps:',
            'mail': 'outlookmail:',
            'calendar': 'outlookcal:',
            'clock': 'ms-clock:',
            'alarms': 'ms-clock:',
            'store': 'ms-windows-store:'
        }
        
        # Initialize system monitoring data
        self.cpu_data = []
        self.memory_data = []
        self.disk_data = []
        self.time_data = []
        
        # Code templates for code generation
        self.code_templates = {
            'python': {
                'hello_world': 'print("Hello, World!")',
                'function': 'def function_name(parameters):\n    """Docstring for function."""\n    # Function body\n    return result',
                'class': 'class ClassName:\n    """Docstring for class."""\n    \n    def __init__(self, parameters):\n        """Initialize the class."""\n        # Initialization code\n        pass\n    \n    def method_name(self, parameters):\n        """Docstring for method."""\n        # Method body\n        return result',
                'if_statement': 'if condition:\n    # Code to execute if condition is True\n    pass\nelse:\n    # Code to execute if condition is False\n    pass',
                'for_loop': 'for item in iterable:\n    # Code to execute for each item\n    pass',
                'while_loop': 'while condition:\n    # Code to execute while condition is True\n    pass',
                'try_except': 'try:\n    # Code that might raise an exception\n    pass\nexcept Exception as e:\n    # Code to handle the exception\n    print(f"An error occurred: {e}")',
                'file_read': 'with open("filename.txt", "r") as file:\n    content = file.read()\n    print(content)',
                'file_write': 'with open("filename.txt", "w") as file:\n    file.write("Content to write")',
                'list_comprehension': '[expression for item in iterable if condition]',
                'dictionary_comprehension': '{key: value for item in iterable if condition}',
                'lambda': 'lambda parameters: expression'
            },
            'html': {
                'basic': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Page Title</title>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>\n<body>\n    <h1>Hello, World!</h1>\n    <p>This is a paragraph.</p>\n</body>\n</html>',
                'form': '<form action="/action_page.php" method="post">\n    <label for="fname">First name:</label><br>\n    <input type="text" id="fname" name="fname"><br>\n    <label for="lname">Last name:</label><br>\n    <input type="text" id="lname" name="lname"><br><br>\n    <input type="submit" value="Submit">\n</form>',
                'table': '<table>\n    <tr>\n        <th>Header 1</th>\n        <th>Header 2</th>\n    </tr>\n    <tr>\n        <td>Row 1, Cell 1</td>\n        <td>Row 1, Cell 2</td>\n    </tr>\n    <tr>\n        <td>Row 2, Cell 1</td>\n        <td>Row 2, Cell 2</td>\n    </tr>\n</table>'
            },
            'javascript': {
                'function': 'function functionName(parameters) {\n    // Function body\n    return result;\n}',
                'arrow_function': 'const functionName = (parameters) => {\n    // Function body\n    return result;\n};',
                'class': 'class ClassName {\n    constructor(parameters) {\n        // Initialization code\n    }\n    \n    methodName(parameters) {\n        // Method body\n        return result;\n    }\n}',
                'if_statement': 'if (condition) {\n    // Code to execute if condition is true\n} else {\n    // Code to execute if condition is false\n}',
                'for_loop': 'for (let i = 0; i < array.length; i++) {\n    // Code to execute for each iteration\n}',
                'for_of': 'for (const item of iterable) {\n    // Code to execute for each item\n}',
                'for_in': 'for (const key in object) {\n    // Code to execute for each key\n}',
                'while_loop': 'while (condition) {\n    // Code to execute while condition is true\n}',
                'try_catch': 'try {\n    // Code that might throw an exception\n} catch (error) {\n    // Code to handle the exception\n    console.error(error);\n}',
                'promise': 'const promise = new Promise((resolve, reject) => {\n    // Asynchronous code\n    if (success) {\n        resolve(result);\n    } else {\n        reject(error);\n    }\n});'
            },
            'css': {
                'basic': 'body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 0;\n    background-color: #f0f0f0;\n}\n\nh1 {\n    color: #333;\n    text-align: center;\n}\n\np {\n    font-size: 16px;\n    line-height: 1.5;\n    color: #666;\n}',
                'flexbox': '.container {\n    display: flex;\n    flex-direction: row;\n    justify-content: space-between;\n    align-items: center;\n    flex-wrap: wrap;\n}\n\n.item {\n    flex: 1;\n    margin: 10px;\n    padding: 20px;\n    background-color: #fff;\n    border-radius: 5px;\n    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);\n}',
                'grid': '.container {\n    display: grid;\n    grid-template-columns: repeat(3, 1fr);\n    grid-gap: 20px;\n}\n\n.item {\n    padding: 20px;\n    background-color: #fff;\n    border-radius: 5px;\n    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);\n}'
            }
        }
        
        # Joke categories
        self.joke_categories = ['neutral', 'chuck', 'all', 'programming']
        
        # Start system monitoring
        self.update_system_info()
        
        self.log("Anu dashboard initialized successfully!")
        
        # Welcome message
        welcome_message = "Hello! I'm Anu, your enhanced personal OS assistant with comprehensive system monitoring, code generation, web search, and more. I'm ready to help you."
        self.speak(welcome_message)

    def setup_gui(self):
        """Set up the GUI components"""
        # Configure ttk style
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5')
        self.style.configure('TButton', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'), foreground='#2c3e50')
        self.style.configure('Subheader.TLabel', font=('Segoe UI', 14), foreground='#34495e')
        self.style.configure('Dashboard.TFrame', background='#ffffff', relief='raised')
        
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel (system monitoring)
        left_panel = ttk.Frame(main_container, style='Dashboard.TFrame')
        main_container.add(left_panel, weight=1)
        
        # Right panel (assistant interaction)
        right_panel = ttk.Frame(main_container, style='Dashboard.TFrame')
        main_container.add(right_panel, weight=1)
        
        # Set up left panel (system monitoring)
        self.setup_system_panel(left_panel)
        
        # Set up right panel (assistant interaction)
        self.setup_assistant_panel(right_panel)

    def setup_system_panel(self, parent):
        """Set up the system monitoring panel"""
        # Header
        header_label = ttk.Label(
            parent, 
            text="System Monitoring", 
            style='Header.TLabel',
            padding=(0, 10)
        )
        header_label.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # System info frame
        system_frame = ttk.LabelFrame(parent, text="System Information", padding=10)
        system_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Grid for system info
        for i in range(3):
            system_frame.columnconfigure(i, weight=1)
        
        # CPU usage
        ttk.Label(system_frame, text="CPU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cpu_label = ttk.Label(system_frame, text="0%")
        self.cpu_label.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Memory usage
        ttk.Label(system_frame, text="Memory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.memory_label = ttk.Label(system_frame, text="0%")
        self.memory_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Disk usage
        ttk.Label(system_frame, text="Disk:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.disk_label = ttk.Label(system_frame, text="0%")
        self.disk_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Battery status
        ttk.Label(system_frame, text="Battery:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.battery_label = ttk.Label(system_frame, text="N/A")
        self.battery_label.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Process count
        ttk.Label(system_frame, text="Processes:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.process_label = ttk.Label(system_frame, text="0")
        self.process_label.grid(row=1, column=3, sticky=tk.W, pady=5)
        
        # Uptime
        ttk.Label(system_frame, text="Uptime:").grid(row=2, column=2, sticky=tk.W, pady=5)
        self.uptime_label = ttk.Label(system_frame, text="0:00:00")
        self.uptime_label.grid(row=2, column=3, sticky=tk.W, pady=5)
        
        # Charts frame
        charts_frame = ttk.LabelFrame(parent, text="Resource Usage", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Create figure for charts
        self.fig = plt.figure(figsize=(6, 8))
        
        # CPU chart
        self.ax1 = self.fig.add_subplot(311)
        self.ax1.set_title('CPU Usage (%)')
        self.ax1.set_ylim(0, 100)
        self.ax1.grid(True)
        self.cpu_line, = self.ax1.plot([], [], 'r-', label='CPU')
        self.ax1.legend()
        
        # Memory chart
        self.ax2 = self.fig.add_subplot(312)
        self.ax2.set_title('Memory Usage (%)')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True)
        self.memory_line, = self.ax2.plot([], [], 'b-', label='Memory')
        self.ax2.legend()
        
        # Disk chart
        self.ax3 = self.fig.add_subplot(313)
        self.ax3.set_title('Disk Usage (%)')
        self.ax3.set_ylim(0, 100)
        self.ax3.grid(True)
        self.disk_line, = self.ax3.plot([], [], 'g-', label='Disk')
        self.ax3.legend()
        
        self.fig.tight_layout()
        
        # Add the plot to the GUI
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
        
        # Running processes frame
        processes_frame = ttk.LabelFrame(parent, text="Top Processes", padding=10)
        processes_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        # Process list
        columns = ('name', 'pid', 'cpu', 'memory')
        self.process_tree = ttk.Treeview(processes_frame, columns=columns, show='headings', height=5)
        
        # Define headings
        self.process_tree.heading('name', text='Process Name')
        self.process_tree.heading('pid', text='PID')
        self.process_tree.heading('cpu', text='CPU %')
        self.process_tree.heading('memory', text='Memory %')
        
        # Define columns
        self.process_tree.column('name', width=150)
        self.process_tree.column('pid', width=50)
        self.process_tree.column('cpu', width=70)
        self.process_tree.column('memory', width=70)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(processes_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_assistant_panel(self, parent):
        """Set up the assistant interaction panel"""
        # Header
        header_label = ttk.Label(
            parent, 
            text="Anu Assistant", 
            style='Header.TLabel',
            padding=(0, 10)
        )
        header_label.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # Status frame
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            font=('Segoe UI', 10, 'italic')
        )
        status_label.pack(side=tk.LEFT)
        
        # Output text area
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#ffffff',
            height=15
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Text entry
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame,
            textvariable=self.input_var,
            font=('Segoe UI', 11)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind('<Return>', self.send_command)
        
        # Send button
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_command
        )
        send_button.pack(side=tk.RIGHT)
        
        # Control buttons frame
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        
        # Voice button
        self.voice_button = ttk.Button(
            control_frame, 
            text="Start Listening", 
            command=self.toggle_listening
        )
        self.voice_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_button = ttk.Button(
            control_frame, 
            text="Clear Log", 
            command=self.clear_log
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Test voice button
        test_voice_button = ttk.Button(
            control_frame, 
            text="Test Voice", 
            command=lambda: self.speak("Voice test successful")
        )
        test_voice_button.pack(side=tk.LEFT)
        
        # Exit button
        exit_button = ttk.Button(
            control_frame, 
            text="Exit", 
            command=self.exit_app
        )
        exit_button.pack(side=tk.RIGHT)
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Quick action buttons
        actions = [
            ("Open Browser", lambda: self.open_application("chrome")),
            ("Open Explorer", lambda: self.open_application("explorer")),
            ("Take Screenshot", self.take_screenshot),
            ("System Info", self.show_system_info),
            ("Web Search", self.web_search_dialog),
            ("Generate Code", self.code_generation_dialog),
            ("Tell Joke", self.tell_joke),
            ("Save Notes", self.save_notes)
        ]
        
        # Create action buttons
        for i, (text, command) in enumerate(actions):
            btn = ttk.Button(actions_frame, text=text, command=command)
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Configure grid
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

    def log(self, message, message_type="INFO"):
        """Add a message to the log with timestamp (thread-safe)"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{message_type}] {message}\n"
        
        # Print to console for debugging
        print(log_message.strip())
        
        # If GUI is not ready, queue the message or skip
        if not self.gui_ready or not hasattr(self, 'output_text'):
            return
        
        # Schedule the update on the main thread using root.after
        def update_gui():
            try:
                self.output_text.config(state=tk.NORMAL)
                
                # Apply different colors based on message type
                if message_type == "ERROR":
                    self.output_text.insert(tk.END, log_message, "error")
                    self.output_text.tag_configure("error", foreground="red")
                elif message_type == "USER":
                    self.output_text.insert(tk.END, log_message, "user")
                    self.output_text.tag_configure("user", foreground="blue")
                elif message_type == "ANU":
                    self.output_text.insert(tk.END, log_message, "anu")
                    self.output_text.tag_configure("anu", foreground="green")
                else:
                    self.output_text.insert(tk.END, log_message)
                
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
            except tk.TclError:
                # Window might have been closed
                pass
        
        # Use root.after to ensure update happens on main thread
        try:
            self.root.after(0, update_gui)
        except tk.TclError:
            # Window might have been closed
            pass

    def set_status(self, status):
        """Set status (thread-safe)"""
        if not self.gui_ready or not hasattr(self, 'status_var'):
            return
        
        def update_gui():
            try:
                self.status_var.set(status)
            except tk.TclError:
                pass
        
        try:
            self.root.after(0, update_gui)
        except tk.TclError:
            pass

    def clear_log(self):
        """Clear the log text area"""
        if not self.gui_ready or not hasattr(self, 'output_text'):
            return
        
        def update_gui():
            try:
                self.output_text.config(state=tk.NORMAL)
                self.output_text.delete(1.0, tk.END)
                self.output_text.config(state=tk.DISABLED)
            except tk.TclError:
                pass
        
        try:
            self.root.after(0, update_gui)
            self.log("Log cleared")
        except tk.TclError:
            pass

    def setup_voice(self):
        """Set up the text-to-speech engine"""
        try:
            # List available voices
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            
            self.log(f"Found {len(voices)} voices")
            
            # Try to find Zira (female voice)
            voice_found = False
            for voice in voices:
                if "zira" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    self.log(f"Selected voice: {voice.name}")
                    voice_found = True
                    break
            
            # If Zira not found, try any female voice
            if not voice_found:
                for voice in voices:
                    if any(indicator in voice.name.lower() for indicator in ['female', 'hazel', 'woman']):
                        self.engine.setProperty('voice', voice.id)
                        self.log(f"Selected voice: {voice.name}")
                        voice_found = True
                        break
            
            # If no female voice found, use the first available voice
            if not voice_found and voices:
                self.engine.setProperty('voice', voices[0].id)
                self.log(f"Selected default voice: {voices[0].name}")
            
            # Set voice properties
            self.engine.setProperty('rate', 175)  # Normal speaking rate
            self.engine.setProperty('volume', 1.0)  # Maximum volume
            
            # Test the voice
            self.log("Testing voice...")
            self.engine.say("Anu voice system initialized")
            self.engine.runAndWait()
            self.log("Voice test completed")
            
            return True
        except Exception as e:
            self.log(f"Error setting up voice: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            return False

    def setup_microphone_support(self):
        """Detect whether microphone input is available."""
        self.microphone_available = False

        try:
            if importlib.util.find_spec("pyaudio") is not None:
                self.microphone_available = True
                try:
                    microphone_count = len(sr.Microphone.list_microphone_names())
                    self.log(f"Microphone support available ({microphone_count} input devices detected)")
                except Exception:
                    self.log("Microphone support available")
            else:
                raise ModuleNotFoundError("No module named 'pyaudio'")
        except Exception as e:
            self.log(
                f"Microphone input disabled: PyAudio is not available ({e}). "
                "Voice listening will be disabled; text commands still work.",
                "WARNING"
            )

        try:
            if not self.microphone_available and hasattr(self, "voice_button"):
                self.voice_button.config(text="Voice Unavailable", state=tk.DISABLED)
        except Exception:
            pass

    def _get_microphone_indices(self):
        """Return a list of valid microphone device indices."""
        indices = []

        try:
            audio = pyaudio.PyAudio()
            try:
                try:
                    default_input = audio.get_default_input_device_info()
                    default_index = int(default_input.get("index"))
                    indices.append(default_index)
                except Exception:
                    pass

                for index in range(audio.get_device_count()):
                    try:
                        info = audio.get_device_info_by_index(index)
                        if info.get("maxInputChannels", 0) > 0 and index not in indices:
                            indices.append(index)
                    except Exception:
                        continue
            finally:
                audio.terminate()
        except Exception as e:
            self.log(f"Unable to enumerate microphones: {e}", "WARNING")

        return indices

    def start_speech_worker(self):
        """Start the speech worker thread (call after main loop starts)"""
        if self.speech_thread is None:
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()

    def _speech_worker(self):
        """Worker thread for handling speech"""
        self.log("Speech worker thread started")
        
        # Create a dedicated engine for the speech worker
        try:
            worker_engine = pyttsx3.init()
            voices = worker_engine.getProperty('voices')
            
            # Try to find Zira
            for voice in voices:
                if "zira" in voice.name.lower():
                    worker_engine.setProperty('voice', voice.id)
                    break
            
            worker_engine.setProperty('rate', 175)
            worker_engine.setProperty('volume', 1.0)
            
            self.log("Speech worker engine initialized")
        except Exception as e:
            self.log(f"Error initializing speech worker engine: {e}", "ERROR")
            worker_engine = None
        
        while True:
            try:
                # Get text from queue
                text = self.speech_queue.get()
                
                if text is None:  # Signal to exit
                    break
                
                self.set_status("Speaking...")
                
                # Try to speak using the worker engine
                if worker_engine is not None:
                    try:
                        worker_engine.say(text)
                        worker_engine.runAndWait()
                    except Exception as e:
                        self.log(f"Error in speech worker: {e}", "ERROR")
                        # Try to reinitialize the engine
                        try:
                            worker_engine = pyttsx3.init()
                            voices = worker_engine.getProperty('voices')
                            for voice in voices:
                                if "zira" in voice.name.lower():
                                    worker_engine.setProperty('voice', voice.id)
                                    break
                            worker_engine.setProperty('rate', 175)
                            worker_engine.setProperty('volume', 1.0)
                        except:
                            worker_engine = None
                
                # If worker engine failed, try direct speech
                if worker_engine is None:
                    try:
                        direct_engine = pyttsx3.init()
                        direct_engine.say(text)
                        direct_engine.runAndWait()
                    except Exception as direct_error:
                        self.log(f"Error in direct speech: {direct_error}", "ERROR")
                
                # Mark task as done
                self.speech_queue.task_done()
                
                # Update status based on listening state
                if self.is_listening:
                    self.set_status("Listening...")
                else:
                    self.set_status("Ready")
                
            except Exception as e:
                self.log(f"Error in speech worker: {e}", "ERROR")
                self.set_status("Speech Error")
                time.sleep(0.5)

    def speak(self, text):
        """Add text to speech queue"""
        self.log(f"Anu: {text}", "ANU")
        
        try:
            # Add to queue
            self.speech_queue.put(text)
            
            # If queue is backing up, try direct speech
            if self.speech_queue.qsize() > 2:
                self.log("Speech queue is backing up. Trying direct speech...", "INFO")
                try:
                    direct_engine = pyttsx3.init()
                    direct_engine.say(text)
                    direct_engine.runAndWait()
                except Exception as e:
                    self.log(f"Error in direct speech: {e}", "ERROR")
        except Exception as e:
            self.log(f"Error queueing speech: {e}", "ERROR")
            
            # Try direct speech as fallback
            try:
                direct_engine = pyttsx3.init()
                direct_engine.say(text)
                direct_engine.runAndWait()
            except Exception as direct_error:
                self.log(f"Error in direct speech fallback: {direct_error}", "ERROR")

    def toggle_listening(self):
        """Toggle listening on/off"""
        if not getattr(self, "microphone_available", False):
            self.log(
                "Voice listening is unavailable because PyAudio could not be loaded. "
                "Use the text input instead.",
                "WARNING"
            )
            self.status_var.set("Voice unavailable")
            return

        if self.is_listening:
            self.is_listening = False
            self.voice_button.config(text="Start Listening")
            self.status_var.set("Ready")
            self.log("Listening paused")
        else:
            self.is_listening = True
            self.voice_button.config(text="Stop Listening")
            self.status_var.set("Listening...")
            self.log("Listening started")
            self.start_listening()

    def start_listening(self):
        """Start the listening thread"""
        if not getattr(self, "microphone_available", False):
            return

        if self.listening_thread is None or not self.listening_thread.is_alive():
            self.listening_thread = threading.Thread(target=self.listening_loop, daemon=True)
            self.listening_thread.start()

    def listening_loop(self):
        """Continuous listening loop in a separate thread"""
        while self.is_listening:
            self.status_var.set("Listening...")
            command = self.listen()
            if command:
                self.process_command(command)
            time.sleep(0.1)
        
        self.status_var.set("Ready")

    def listen(self):
        """Listen for a single command"""
        if not getattr(self, "microphone_available", False):
            return None

        self.status_var.set("Listening...")
        
        # Try only valid microphone indices to avoid noisy failures on systems
        # that do not expose some of the hard-coded device ids.
        mic_indices = self._get_microphone_indices()
        if not mic_indices:
            self.log("No valid input microphones were found.", "ERROR")
            return None
        
        for mic_index in mic_indices:
            try:
                with sr.Microphone(device_index=mic_index) as source:
                    self.log(f"Listening with microphone index {mic_index}...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                    try:
                        self.log("Recognizing speech...")
                        text = self.recognizer.recognize_google(audio)
                        self.log(f"User said: {text}", "USER")
                        return text.lower()
                    except sr.UnknownValueError:
                        self.log("Could not understand audio")
                    except sr.RequestError as e:
                        self.log(f"Could not request results; {e}", "ERROR")
                    
                    # If we got here without returning, this microphone didn't work
                    continue
            except Exception as e:
                self.log(f"Error with microphone {mic_index}: {e}", "ERROR")
                continue
        
        # If we get here, all microphones failed
        return None

    def send_command(self, event=None):
        """Process a text command from the input field"""
        command = self.input_var.get().strip()
        if command:
            self.log(f"User typed: {command}", "USER")
            self.input_var.set("")  # Clear the input field
            self.process_command(command)

    def process_command(self, command):
        """Process a voice command"""
        if not command:
            return
        
        command = command.lower()
        
        # Exit commands
        if any(exit_cmd in command for exit_cmd in ["exit", "quit", "goodbye", "bye"]):
            self.speak("Goodbye! Have a nice day.")
            self.exit_app()
            return
        
        # Open application commands
        if "open" in command:
            app_name = command.replace("open", "").strip()
            self.open_application(app_name)
            return
        
        # Time commands
        if "time" in command:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
            return
        
        # Date commands
        if "date" in command:
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speak(f"Today is {current_date}")
            return
        
        # System info commands
        if any(info_cmd in command for info_cmd in ["system info", "system status", "computer status"]):
            self.show_system_info()
            return
        
        # Process commands
        if any(proc_cmd in command for proc_cmd in ["processes", "running apps", "top processes"]):
            self.speak("Here are the top processes running on your system.")
            return
        
        # Screenshot command
        if "screenshot" in command:
            self.take_screenshot()
            return
        
        # Web search commands
        if any(search_cmd in command for search_cmd in ["search", "google", "look up", "find"]):
            search_query = command
            for term in ["search", "google", "look up", "find", "for"]:
                search_query = search_query.replace(term, "").strip()
            
            if search_query:
                self.log(f"Searching for: {search_query}")
                self.speak(f"Searching for {search_query}")
                webbrowser.open(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
            else:
                self.web_search_dialog()
            return
        
        # Code generation commands
        if any(code_cmd in command for code_cmd in ["code", "generate code", "write code", "programming"]):
            self.code_generation_dialog()
            return
        
        # Joke commands
        if any(joke_cmd in command for joke_cmd in ["joke", "funny", "make me laugh"]):
            self.tell_joke()
            return
        
        # Notes commands
        if any(notes_cmd in command for notes_cmd in ["note", "notes", "save note", "write down"]):
            self.save_notes()
            return
        
        # Weather commands (simplified)
        if "weather" in command:
            location = command.replace("weather", "").replace("in", "").strip()
            if not location:
                location = "current location"
            
            self.speak(f"Let me check the weather in {location}")
            webbrowser.open(f"https://www.google.com/search?q=weather+in+{location.replace(' ', '+')}")
            return
        
        # Calculator commands
        if any(calc_cmd in command for calc_cmd in ["calculate", "calculator", "compute", "math"]):
            # Extract the calculation part
            calc_query = command
            for term in ["calculate", "calculator", "compute", "math", "what is"]:
                calc_query = calc_query.replace(term, "").strip()
            
            if calc_query:
                try:
                    # Very simple and unsafe eval for demo purposes
                    # In a real app, you'd use a safer method to evaluate expressions
                    result = eval(calc_query)
                    self.speak(f"The result of {calc_query} is {result}")
                except:
                    self.speak(f"I couldn't calculate {calc_query}. Let me open the calculator for you.")
                    self.open_application("calculator")
            else:
                self.open_application("calculator")
            return
        
        # Greeting commands
        if any(greeting in command for greeting in ["hello", "hi", "hey"]):
            responses = [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Hey! I'm listening. What do you need?"
            ]
            self.speak(random.choice(responses))
            return
        
        # Help command
        if "help" in command:
            help_text = """
I can help you with many tasks, including:
- Opening applications ("open chrome")
- Telling the time and date ("what time is it")
- System monitoring and information ("system info")
- Taking screenshots ("take a screenshot")
- Web searches ("search for cats")
- Generating code ("generate python code")
- Telling jokes ("tell me a joke")
- Saving notes ("save a note")
- Weather information ("weather in New York")
- Simple calculations ("calculate 2 plus 2")
            """
            self.speak("Here are some things I can help you with.")
            self.log(help_text, "INFO")
            return
        
        # Default response
        self.speak("I'm not sure how to help with that yet. Try asking for help to see what I can do.")

    def open_application(self, app_name):
        """Open an application"""
        app_name = app_name.lower().strip()
        self.log(f"Attempting to open: {app_name}")
        
        # First check for special Windows apps
        for windows_app, uri in self.windows_apps.items():
            if windows_app in app_name:
                try:
                    self.log(f"Opening Windows app: {windows_app} with URI: {uri}")
                    # Use the start command with the URI
                    os.system(f"start {uri}")
                    self.speak(f"Opening {windows_app} for you.")
                    return
                except Exception as e:
                    self.log(f"Error opening Windows app {windows_app}: {e}", "ERROR")
        
        # Check if app is in our common apps dictionary
        for common_app, path in self.apps.items():
            if common_app in app_name:
                try:
                    self.log(f"Opening {common_app} at path: {path}")
                    os.startfile(path)
                    self.speak(f"Opening {common_app} for you.")
                    return
                except Exception as e:
                    self.log(f"Error opening {common_app}: {e}", "ERROR")
        
        # Try to open directly
        try:
            self.log(f"Trying to open {app_name} directly")
            os.system(f"start {app_name}")
            self.speak(f"I've tried to open {app_name} for you.")
        except Exception as e:
            self.log(f"Error opening {app_name}: {e}", "ERROR")
            self.speak(f"I'm sorry, I couldn't open {app_name}.")

    def take_screenshot(self):
        """Take a screenshot and save it to the specified directory"""
        try:
            # Create screenshots directory if it doesn't exist
            screenshots_dir = r"C:\Users\talla\OneDrive\Pictures\Screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Take a full screenshot
            self.speak("Taking screenshot")
            screenshot = pyautogui.screenshot()
            
            # Save the screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
            screenshot.save(screenshot_path)
            
            self.log(f"Screenshot saved to: {screenshot_path}")
            self.speak(f"Screenshot saved to Screenshots folder")
            
        except ImportError:
            self.log("pyautogui module not found. Please install it with 'pip install pyautogui'", "ERROR")
            self.speak("I'm sorry, I can't take screenshots without the pyautogui module.")
        except Exception as e:
            self.log(f"Error taking screenshot: {e}", "ERROR")
            self.speak("I'm sorry, there was an error taking the screenshot")
    
    def web_search_dialog(self):
        """Open a dialog for web search"""
        search_dialog = tk.Toplevel(self.root)
        search_dialog.title("Web Search")
        search_dialog.geometry("500x400")
        search_dialog.transient(self.root)
        search_dialog.grab_set()
        
        # Search frame
        search_frame = ttk.Frame(search_dialog, padding=10)
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search Query:").pack(anchor=tk.W, pady=(0, 5))
        
        # Search entry and button
        entry_frame = ttk.Frame(search_frame)
        entry_frame.pack(fill=tk.X)
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(entry_frame, textvariable=search_var, width=50)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        search_entry.focus_set()
        
        # Search engines
        engine_var = tk.StringVar(value="google")
        engines_frame = ttk.Frame(search_frame)
        engines_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(engines_frame, text="Search Engine:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(engines_frame, text="Google", variable=engine_var, value="google").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(engines_frame, text="Bing", variable=engine_var, value="bing").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(engines_frame, text="DuckDuckGo", variable=engine_var, value="duckduckgo").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(engines_frame, text="YouTube", variable=engine_var, value="youtube").pack(side=tk.LEFT, padx=5)
        
        # Results area
        ttk.Label(search_dialog, text="Search Results:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        results_frame = ttk.Frame(search_dialog, padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=10)
        results_text.pack(fill=tk.BOTH, expand=True)
        results_text.config(state=tk.DISABLED)
        
        def perform_search():
            query = search_var.get().strip()
            if not query:
                return
            
            engine = engine_var.get()
            
            # Update results area
            results_text.config(state=tk.NORMAL)
            results_text.delete(1.0, tk.END)
            results_text.insert(tk.END, f"Searching for: {query} using {engine.capitalize()}...\n\n")
            results_text.config(state=tk.DISABLED)
            
            # Perform search
            try:
                # Open in browser
                if engine == "google":
                    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                elif engine == "bing":
                    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
                elif engine == "duckduckgo":
                    url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
                elif engine == "youtube":
                    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                
                webbrowser.open(url)
                
                # Try to get some results programmatically (simplified)
                try:
                    # This is a simplified example - in a real app, you'd use proper APIs
                    if engine in ["google", "bing"]:
                        # Use a search API or web scraping (simplified here)
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        response = requests.get(url, headers=headers, timeout=5)
                        
                        # Extract some text (this is very simplified)
                        if response.status_code == 200:
                            # Just extract some text for demonstration
                            text = response.text
                            # Remove HTML tags (very simplified)
                            text = re.sub(r'<.*?>', '', text)
                            # Get a sample
                            sample = ' '.join(text.split()[:100])
                            
                            results_text.config(state=tk.NORMAL)
                            results_text.insert(tk.END, f"Search completed. Browser opened with results.\n\n")
                            results_text.insert(tk.END, f"Sample of results (text only):\n{sample}...\n")
                            results_text.config(state=tk.DISABLED)
                    else:
                        results_text.config(state=tk.NORMAL)
                        results_text.insert(tk.END, f"Search completed. Browser opened with results.\n")
                        results_text.config(state=tk.DISABLED)
                
                except Exception as e:
                    results_text.config(state=tk.NORMAL)
                    results_text.insert(tk.END, f"Browser opened with search results.\n")
                    results_text.insert(tk.END, f"Note: Could not fetch preview results: {str(e)}\n")
                    results_text.config(state=tk.DISABLED)
                
                self.log(f"Performed web search for: {query} using {engine}")
                self.speak(f"I've searched for {query} using {engine}")
                
            except Exception as e:
                results_text.config(state=tk.NORMAL)
                results_text.insert(tk.END, f"Error performing search: {str(e)}\n")
                results_text.config(state=tk.DISABLED)
                
                self.log(f"Error performing web search: {e}", "ERROR")
                self.speak("I'm sorry, I couldn't perform the web search")
        
        # Search button
        search_button = ttk.Button(entry_frame, text="Search", command=perform_search)
        search_button.pack(side=tk.RIGHT)
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda event: perform_search())
        
        # Buttons at bottom
        button_frame = ttk.Frame(search_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Close", command=search_dialog.destroy).pack(side=tk.RIGHT)
    
    def code_generation_dialog(self):
        """Open a dialog for code generation"""
        code_dialog = tk.Toplevel(self.root)
        code_dialog.title("Code Generation")
        code_dialog.geometry("800x600")
        code_dialog.transient(self.root)
        code_dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(code_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Language selection
        language_frame = ttk.Frame(main_frame)
        language_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(language_frame, text="Programming Language:").pack(side=tk.LEFT, padx=(0, 10))
        
        language_var = tk.StringVar(value="python")
        languages = ["python", "javascript", "html", "css"]
        language_combo = ttk.Combobox(language_frame, textvariable=language_var, values=languages, state="readonly")
        language_combo.pack(side=tk.LEFT)
        
        # Template selection
        template_frame = ttk.Frame(main_frame)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(template_frame, text="Code Template:").pack(side=tk.LEFT, padx=(0, 10))
        
        template_var = tk.StringVar()
        template_combo = ttk.Combobox(template_frame, textvariable=template_var, width=40, state="readonly")
        template_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Update templates when language changes
        def update_templates(*args):
            language = language_var.get()
            templates = list(self.code_templates.get(language, {}).keys())
            template_combo['values'] = templates
            if templates:
                template_combo.current(0)
                update_code_preview()
        
        language_var.trace_add("write", update_templates)
        
        # Code preview
        ttk.Label(main_frame, text="Code Preview:").pack(anchor=tk.W)
        
        code_frame = ttk.Frame(main_frame)
        code_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.NONE, font=('Consolas', 11))
        code_text.pack(fill=tk.BOTH, expand=True)
        
        # Update code preview when template changes
        def update_code_preview(*args):
            language = language_var.get()
            template = template_var.get()
            
            code_text.delete(1.0, tk.END)
            
            if template and language in self.code_templates and template in self.code_templates[language]:
                code = self.code_templates[language][template]
                code_text.insert(tk.END, code)
        
        template_var.trace_add("write", update_code_preview)
        
        # Custom code input
        custom_frame = ttk.LabelFrame(main_frame, text="Custom Code Description")
        custom_frame.pack(fill=tk.X, pady=(0, 10))
        
        custom_text = scrolledtext.ScrolledText(custom_frame, wrap=tk.WORD, height=4)
        custom_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Generate custom code
        def generate_custom_code():
            description = custom_text.get(1.0, tk.END).strip()
            language = language_var.get()
            
            if not description:
                messagebox.showwarning("Input Required", "Please enter a description of the code you want to generate.")
                return
            
            # Here you would typically call an AI service to generate code
            # For this example, we'll just provide a simple response based on the description
            
            code_text.delete(1.0, tk.END)
            
            # Simple pattern matching for demonstration
            if language == "python":
                if "file" in description.lower():
                    code_text.insert(tk.END, "# Code to handle files\n\ndef read_file(filename):\n    with open(filename, 'r') as f:\n        return f.read()\n\ndef write_file(filename, content):\n    with open(filename, 'w') as f:\n        f.write(content)\n\n# Example usage\nfilename = 'example.txt'\ncontent = read_file(filename)\nprint(f'File content: {content}')\n")
                elif "web" in description.lower() or "http" in description.lower():
                    code_text.insert(tk.END, "# Code for web requests\nimport requests\n\ndef fetch_webpage(url):\n    response = requests.get(url)\n    if response.status_code == 200:\n        return response.text\n    else:\n        return f'Error: {response.status_code}'\n\n# Example usage\nurl = 'https://example.com'\nhtml = fetch_webpage(url)\nprint(f'Webpage content length: {len(html)}')\n")
                else:
                    code_text.insert(tk.END, f"# Generated code based on: {description}\n\ndef main():\n    print('Implementing: {description}')\n    # TODO: Implement the functionality\n    pass\n\nif __name__ == '__main__':\n    main()\n")
            elif language == "javascript":
                if "web" in description.lower() or "http" in description.lower():
                    code_text.insert(tk.END, "// Code for web requests\nasync function fetchWebpage(url) {\n    try {\n        const response = await fetch(url);\n        if (response.ok) {\n            return await response.text();\n        } else {\n            return `Error: ${response.status}`;\n        }\n    } catch (error) {\n        return `Error: ${error.message}`;\n    }\n}\n\n// Example usage\nfetchWebpage('https://example.com')\n    .then(html => console.log(`Webpage content length: ${html.length}`))\n    .catch(error => console.error(error));\n")
                else:
                    code_text.insert(tk.END, f"// Generated code based on: {description}\n\nfunction main() {{\n    console.log('Implementing: {description}');\n    // TODO: Implement the functionality\n}}\n\nmain();\n")
            elif language == "html":
                html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{0}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
        }}
    </style>
</head>
<body>
    <h1>{0}</h1>
    <p>This is a generated HTML page based on your description.</p>
    <div id="content">
        <!-- Content goes here -->
    </div>
    <script>
        // JavaScript can be added here
        console.log('Page loaded');
    </script>
</body>
</html>
"""
                code_text.insert(tk.END, html_template.format(description))
            
            self.log(f"Generated custom code for: {description}")
            self.speak(f"I've generated some {language} code based on your description")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        generate_button = ttk.Button(button_frame, text="Generate Custom Code", command=generate_custom_code)
        generate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        copy_button = ttk.Button(button_frame, text="Copy to Clipboard", 
                                command=lambda: [self.root.clipboard_clear(), 
                                                self.root.clipboard_append(code_text.get(1.0, tk.END)),
                                                self.log("Code copied to clipboard")])
        copy_button.pack(side=tk.LEFT, padx=(0, 10))
        
        save_button = ttk.Button(button_frame, text="Save to File", 
                                command=lambda: self.save_code_to_file(language_var.get(), code_text.get(1.0, tk.END)))
        save_button.pack(side=tk.LEFT)
        
        close_button = ttk.Button(button_frame, text="Close", command=code_dialog.destroy)
        close_button.pack(side=tk.RIGHT)
        
        # Initialize templates
        update_templates()
    
    def save_code_to_file(self, language, code):
        """Save generated code to a file"""
        # Determine file extension
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "html": ".html",
            "css": ".css"
        }
        extension = extensions.get(language, ".txt")
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[
                (f"{language.capitalize()} files", f"*{extension}"),
                ("All files", "*.*")
            ],
            title="Save Code"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(code)
                self.log(f"Code saved to: {file_path}")
                self.speak("Code has been saved to file")
            except Exception as e:
                self.log(f"Error saving code: {e}", "ERROR")
                self.speak("I'm sorry, I couldn't save the code to file")
    
    def save_notes(self):
        """Save notes to a file"""
        notes_dialog = tk.Toplevel(self.root)
        notes_dialog.title("Save Notes")
        notes_dialog.geometry("600x500")
        notes_dialog.transient(self.root)
        notes_dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(notes_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Title:").pack(side=tk.LEFT, padx=(0, 5))
        
        title_var = tk.StringVar()
        title_entry = ttk.Entry(title_frame, textvariable=title_var, width=50)
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        title_entry.focus_set()
        
        # Notes content
        ttk.Label(main_frame, text="Notes:").pack(anchor=tk.W)
        
        notes_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15)
        notes_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Save function
        def save_notes_to_file():
            title = title_var.get().strip()
            content = notes_text.get(1.0, tk.END).strip()
            
            if not title:
                messagebox.showwarning("Input Required", "Please enter a title for your notes.")
                return
            
            if not content:
                messagebox.showwarning("Input Required", "Please enter some content for your notes.")
                return
            
            # Create notes directory if it doesn't exist
            notes_dir = os.path.join(os.path.expanduser("~"), "Documents", "Anu_Notes")
            os.makedirs(notes_dir, exist_ok=True)
            
            # Generate filename from title
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.txt"
            file_path = os.path.join(notes_dir, filename)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"Title: {title}\n")
                    file.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    file.write(f"{'-' * 40}\n\n")
                    file.write(content)
                
                self.log(f"Notes saved to: {file_path}")
                self.speak("Your notes have been saved")
                notes_dialog.destroy()
            except Exception as e:
                self.log(f"Error saving notes: {e}", "ERROR")
                self.speak("I'm sorry, I couldn't save your notes")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="Save", command=save_notes_to_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=notes_dialog.destroy).pack(side=tk.RIGHT)
    
    def tell_joke(self):
        """Tell a joke with improved functionality"""
        try:
            # Create a joke dialog
            joke_dialog = tk.Toplevel(self.root)
            joke_dialog.title("Anu Jokes")
            joke_dialog.geometry("500x400")
            joke_dialog.transient(self.root)
            joke_dialog.grab_set()
            
            # Main frame
            main_frame = ttk.Frame(joke_dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Joke category selection
            category_frame = ttk.Frame(main_frame)
            category_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(category_frame, text="Joke Category:").pack(side=tk.LEFT, padx=(0, 10))
            
            category_var = tk.StringVar(value="neutral")
            for category in self.joke_categories:
                ttk.Radiobutton(category_frame, text=category.capitalize(), 
                               variable=category_var, value=category).pack(side=tk.LEFT, padx=5)
            
            # Joke display area
            joke_frame = ttk.LabelFrame(main_frame, text="Joke")
            joke_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            joke_text = scrolledtext.ScrolledText(joke_frame, wrap=tk.WORD, height=10, font=('Segoe UI', 11))
            joke_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            joke_text.config(state=tk.DISABLED)
            
            # Get joke function
            def get_joke():
                category = category_var.get()
                
                try:
                    # Get joke from pyjokes or API
                    if category in ["programming", "neutral"]:
                        # Use pyjokes for programming jokes
                        joke = pyjokes.get_joke(category=category)
                    elif category == "chuck":
                        # Use Chuck Norris API
                        response = requests.get("https://api.chucknorris.io/jokes/random")
                        if response.status_code == 200:
                            joke = response.json()["value"]
                        else:
                            joke = "I couldn't fetch a Chuck Norris joke. Even APIs are afraid of him."
                    else:
                        # Use JokeAPI for other categories
                        response = requests.get(f"https://v2.jokeapi.dev/joke/Any?safe-mode")
                        if response.status_code == 200:
                            data = response.json()
                            if "joke" in data:
                                joke = data["joke"]
                            elif "setup" in data and "delivery" in data:
                                joke = f"{data['setup']}\n\n{data['delivery']}"
                            else:
                                joke = "I couldn't understand the joke format."
                        else:
                            joke = "I couldn't fetch a joke right now."
                    
                    # Display joke
                    joke_text.config(state=tk.NORMAL)
                    joke_text.delete(1.0, tk.END)
                    joke_text.insert(tk.END, joke)
                    joke_text.config(state=tk.DISABLED)
                    
                    # Speak joke
                    self.speak(joke)
                    
                except Exception as e:
                    joke_text.config(state=tk.NORMAL)
                    joke_text.delete(1.0, tk.END)
                    joke_text.insert(tk.END, f"Error getting joke: {str(e)}")
                    joke_text.config(state=tk.DISABLED)
                    
                    self.log(f"Error getting joke: {e}", "ERROR")
                    self.speak("I'm sorry, I couldn't tell a joke right now")
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X)
            
            ttk.Button(button_frame, text="Tell Me a Joke", command=get_joke).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Close", command=joke_dialog.destroy).pack(side=tk.RIGHT)
            
            # Get a joke immediately
            get_joke()
            
        except ImportError:
            self.log("pyjokes module not found. Please install it with 'pip install pyjokes'", "ERROR")
            self.speak("I'm sorry, I need the pyjokes module to tell jokes. Please install it with pip install pyjokes.")
        except Exception as e:
            self.log(f"Error setting up joke dialog: {e}", "ERROR")
            self.speak("I'm sorry, I couldn't tell a joke right now.")
    
    def show_system_info(self):
        """Show detailed system information"""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Format information
            info = f"""
System Information:
------------------
CPU Usage: {cpu_percent}%
Memory: {memory.percent}% used ({self.format_bytes(memory.used)} of {self.format_bytes(memory.total)})
Disk: {disk.percent}% used ({self.format_bytes(disk.used)} of {self.format_bytes(disk.total)})
Processes: {len(psutil.pids())}
Boot Time: {datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Display in a messagebox
            messagebox.showinfo("System Information", info)
            
            # Speak summary
            self.speak(f"Your system is currently using {cpu_percent} percent CPU and {memory.percent} percent memory.")
        except Exception as e:
            self.log(f"Error showing system info: {e}", "ERROR")
            self.speak("I'm sorry, I couldn't retrieve system information.")

    def format_bytes(self, bytes):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
        return f"{bytes:.2f} PB"

    def update_system_info(self):
        """Update system information display"""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update labels
            self.cpu_label.config(text=f"{cpu_percent}%")
            self.memory_label.config(text=f"{memory.percent}%")
            self.disk_label.config(text=f"{disk.percent}%")
            
            # Get battery information if available
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    status = "Charging" if battery.power_plugged else "Discharging"
                    self.battery_label.config(text=f"{battery.percent}% ({status})")
                else:
                    self.battery_label.config(text="N/A")
            
            # Update process count
            process_count = len(psutil.pids())
            self.process_label.config(text=str(process_count))
            
            # Update uptime
            boot_time = psutil.boot_time()
            uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.config(text=f"{hours}:{minutes:02d}:{seconds:02d}")
            
            # Update data for charts
            self.cpu_data.append(cpu_percent)
            self.memory_data.append(memory.percent)
            self.disk_data.append(disk.percent)
            self.time_data.append(datetime.datetime.now())
            
            # Keep only last 60 data points
            if len(self.cpu_data) > 60:
                self.cpu_data.pop(0)
                self.memory_data.pop(0)
                self.disk_data.pop(0)
                self.time_data.pop(0)
            
            # Update charts
            x_range = range(len(self.cpu_data))
            self.cpu_line.set_data(x_range, self.cpu_data)
            self.memory_line.set_data(x_range, self.memory_data)
            self.disk_line.set_data(x_range, self.disk_data)
            
            # Update x-axis limits
            for ax in [self.ax1, self.ax2, self.ax3]:
                ax.set_xlim(0, max(59, len(self.cpu_data) - 1))
            
            # Redraw the canvas
            self.canvas.draw_idle()
            
            # Update process list
            self.update_process_list()
            
            # Schedule next update
            self.root.after(2000, self.update_system_info)
        
        except Exception as e:
            self.log(f"Error updating system info: {e}", "ERROR")
            # Try again after a delay
            self.root.after(5000, self.update_system_info)

    def update_process_list(self):
        """Update the list of top processes"""
        try:
            # Clear current items
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            
            # Get process information
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Display top processes
            for i, proc in enumerate(processes[:10]):  # Show top 10
                self.process_tree.insert('', 'end', values=(
                    proc['name'],
                    proc['pid'],
                    f"{proc['cpu_percent']:.1f}%",
                    f"{proc['memory_percent']:.1f}%"
                ))
        
        except Exception as e:
            self.log(f"Error updating process list: {e}", "ERROR")

    def exit_app(self):
        """Exit the application"""
        self.log("Exiting application...")
        self.is_listening = False
        
        # Signal speech worker to exit
        self.speech_queue.put(None)
        
        # Wait for threads to finish
        if self.speech_thread.is_alive():
            self.speech_thread.join(timeout=1)
        
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=1)
        
        self.root.quit()

def main():
    root = tk.Tk()
    app = AnuDashboard(root)
    # Schedule speech worker to start after the main loop starts
    root.after(100, app.start_speech_worker)
    root.mainloop()

if __name__ == "__main__":
    main()