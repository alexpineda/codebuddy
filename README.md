# AI-Powered Screen Activity Logger

This program is an AI-powered screen activity logger that captures screenshots at regular intervals, analyzes them using OpenAI's GPT-4 Vision model, and logs the descriptions. It also allows users to ask questions about their activity log, providing a unique way to track and understand your computer usage.

## Features

- Automatic screenshot capture at customizable intervals
- AI-powered analysis of screenshots using GPT-4 Vision
- Activity logging with timestamps
- Interactive inquiry mode to ask questions about your activity
- Option to clear the log and reset

## Requirements

- Python 3.7+
- OpenAI API key
- Required Python packages (install via `pip install -r requirements.txt`):
  - openai
  - python-dotenv
  - Pillow

## Setup

1. Clone this repository
2. Install the required packages: `pip install -r requirements.txt`
3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Run the program:
   ```
   python screen_capture_logger.py [interval]
   ```
   Where `[interval]` is an optional argument to set the capture interval in seconds (default is 15 seconds).

2. The program will start capturing screenshots and logging activity.

3. Press Enter at any time to pause capturing and enter inquiry mode.

4. In inquiry mode, you can:
   - Ask questions about your activity
   - Type 'exit' to quit the program
   - Type 'reset' to clear the log
   - Type 'continue' to resume screen capturing

## Note

This program uses your screen content and sends it to OpenAI for analysis. Make sure you're comfortable with this and comply with all relevant privacy policies and regulations.

## License

[MIT License](LICENSE)
