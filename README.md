# Screen Activity Logger & AI Assistant

This program is an AI-powered screen activity logger that captures screenshots at regular intervals, analyzes them using OpenAI/Claude/Your Model, and logs the descriptions. It also allows users to ask questions about their activity log, providing a unique way to track and understand your computer usage.

## Features

- Automatic screenshot capture at customizable intervals, interpreted by vision model of your choice.
- Q&A mode to ask questions about your activity.
- Privacy model support (via LM Studio or Ollama) to gatekeep what gets sent to stronger models, or use all local models.

## Setup

1. Clone this repository
2. Install the required packages: `pip install -r requirements.txt`
3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Use `config.json` to configure your models and other settings.

## Usage

1. Run the program:
   ```
   python main.py 
   ```

2. The program will start capturing screenshots and logging activity.

3. Press Enter at any time to pause capturing and enter inquiry mode.

4. In inquiry mode, you can:
   - Ask questions about your activity
   - Type 'exit' to quit the program
   - Type 'reset' to start a new session
   - Type 'continue' to resume screen capturing

## Note

This program uses your screen content and sends it to OpenAI for analysis. Make sure you're comfortable with this and comply with all relevant privacy policies and regulations.

## License

[MIT License](LICENSE)
