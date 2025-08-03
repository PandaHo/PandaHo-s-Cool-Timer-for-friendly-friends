# PandaHo's Cool Timer for Nice Dudes
A feature-rich desktop timer and notes application built with Python and Tkinter. This isn't just a timer; it's a powerful companion for managing tasks, tracking goals, and staying focused.

<img width="475" height="417" alt="Screenshot_12" src="https://github.com/user-attachments/assets/dc92b82f-4587-4aa2-9399-74f8ede33c5f" />

✨ Key Features

This application is packed with features designed to be both powerful and easy to use:

    Multi-Timer Support: Manage up to 8 independent timers simultaneously. Each timer saves its own duration, title, notes, and running state.

    Persistent State: Close the app and re-launch it later—your running and paused timers will be exactly where you left them!

    Integrated Notes System: Attach notes to any timer! The notes library is a powerful tool for task management:

        Rich Text Editor: Style your notes with Bold, Italics, <u>Underline</u>, different font families, sizes, and custom colors.

        Multiple Completion Types: Create simple text notes, interactive Checkboxes, or track progress with Digital Counters (e.g., [5/10]).

    Customizable Alarms:

        Set custom primary and secondary alarm sounds (.mp3, .wav, .ogg).

        Choose how many times the alarm should loop (or set it to infinite!).

    "Presents" System: Save and load entire sets of 8 timers as .ini file templates. Perfect for switching between different workflows (e.g., "Work Timers" vs. "Hobby Timers").

    Polished Custom UI.

    Cross-Platform: Built with standard libraries, making it compatible with Windows, macOS, and Linux.

🚀 Installation & Usage (For Users)

Getting the app running is easy. No installation needed!

    Go to the Releases Page on this GitHub repository.

    Under the latest release, download the application matching your OS.

    Save it to a clean folder and just launch it.

💻 For Developers

Interested in running the code yourself or contributing? Here’s how to get started.
Prerequisites

    Python 3.8+

    Git

Building from Source

Clone the repository:
git clone https://github.com/YourUsername/YourRepoName.git
cd YourRepoName

    




Create a virtual environment (recommended):

      
# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

    





Install the dependencies:

      
pip install -r requirements.txt

    





Run the application:

      
python timer.py

    



    
    

Compiling to an Executable

To create your own standalone .exe file, use the provided PyInstaller command. For a clean build, it's best to delete the build/ and dist/ folders first.

      
# Ensure you are in the project's root directory
pyinstaller --onefile --windowed --icon="timer_icon.ico" --hidden-import=_cffi_backend --add-data "timer_icon.ico;." --add-data "alarmA.ogg;." --add-data "alarmB.mp3;." timer.py

    





📜 License

This project is released under the MIT License. See the LICENSE file for full details. You are free to use, modify, and distribute this software.

Copyright:

alarmA.ogg is from https://pixabay.com/sound-effects/hq-rooster-crowing-247597/
alarmB.mp3 is from https://pixabay.com/sound-effects/alarm-clock-90867/
The stopwatch image from UI is mathimatically created in code.
