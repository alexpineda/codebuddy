import sys
import time
import pyautogui
import io
import threading
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64

# Load environment variables from .env file
load_dotenv()

# Set default interval in seconds
DEFAULT_CAPTURE_INTERVAL = 5

# Get capture interval from command line argument or use default
if len(sys.argv) > 1:
    try:
        CAPTURE_INTERVAL = float(sys.argv[1])
    except ValueError:
        print(f"Invalid interval provided. Using default: {DEFAULT_CAPTURE_INTERVAL} seconds")
        CAPTURE_INTERVAL = DEFAULT_CAPTURE_INTERVAL
else:
    print(f"No interval provided. Using default: {DEFAULT_CAPTURE_INTERVAL} seconds")
    CAPTURE_INTERVAL = DEFAULT_CAPTURE_INTERVAL

# Remove this line
# OPENAI_API_KEY = "your_openai_api_key"

# Replace with this
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add these constants at the top of the file with other constants
SCREENSHOT_DIR = "screenshots"
screenshot_counter = 0

TRACE_LOG_FILE = "./trace_log.txt"

def capture_screen():
    global screenshot_counter
    
    # Create screenshots directory if it doesn't exist
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Capture the screenshot
    screenshot = pyautogui.screenshot()
    
    # Save screenshot to file
    filename = f"{SCREENSHOT_DIR}/screenshot_{screenshot_counter:04d}.png"
    screenshot.save(filename)
    screenshot_counter += 1

    return
    
    # Convert screenshot to base64
    img_byte_array = io.BytesIO()
    screenshot.save(img_byte_array, format='PNG')
    base64_image = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

    # Send screenshot to GPT-4 Vision model
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe what's happening in this screenshot."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        vision_response = response.choices[0].message.content
        log_trace(f"Saved screenshot: {filename}")
        log_trace(vision_response)
        print(f"Saved screenshot: {filename}")
        print(f"Vision model response: {vision_response}")
    except Exception as e:
        log_trace(f"Failed to send screenshot to vision model: {e}")
        print(f"Failed to send screenshot to vision model: {e}")

def log_trace(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TRACE_LOG_FILE, "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

def prompt_user():
    try:
        while True:
            user_input = input("Enter your question about the log (or 'exit' to quit, 'reset' to clear the log): ")
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'reset':
                with open(TRACE_LOG_FILE, "w") as log_file:
                    log_file.write("")
                print("Log has been cleared.")
            else:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an assistant. Provide an appropriate response based on the given log."},
                        {"role": "user", "content": f"The user asked: '{user_input}'. Based on the following log, provide an appropriate response:\n\n{open(TRACE_LOG_FILE, 'r').read()}"}
                    ]
                )
                print(response.choices[0].message.content)
    except KeyboardInterrupt:
        print("\nExiting gracefully...")

if __name__ == "__main__":
    print(f"Screen capture interval set to {CAPTURE_INTERVAL} seconds")
    
    # Start the capture screen function in a separate thread
    capture_thread = threading.Thread(target=lambda: [capture_screen() or time.sleep(CAPTURE_INTERVAL) for _ in iter(int, 1)])
    capture_thread.daemon = True
    capture_thread.start()

    try:
        # Run the user prompt in the main thread
        prompt_user()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    finally:
        print("Cleanup complete. Goodbye!")