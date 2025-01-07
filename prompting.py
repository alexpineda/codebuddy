from openai import OpenAI
import os
from utils import log_trace

class PromptHandler:
    def __init__(self, trace_log_file):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.trace_log_file = trace_log_file

    def process_screenshot(self, base64_image, filename, active_window_title):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "The following is a screenshot of a series of screenshots.\n" +
                        "The response will be added to an 'activity' log file, so only output relevant information.\n" +
                        "In the application that is purposed around this, the user may ask questions about their activity log in order to aid in their productivity and act as a short term memory."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe what's happening in this screenshot. The active window is: " + active_window_title
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
                max_tokens=500
            )
            
            vision_response = response.choices[0].message.content
            log_trace(f"Saved screenshot: {filename}", self.trace_log_file)
            log_trace(f"Active window: {active_window_title}", self.trace_log_file)
            log_trace(vision_response, self.trace_log_file)
            return True
        except Exception as e:
            log_trace(f"Failed to send screenshot to vision model: {e}", self.trace_log_file)
            print(f"Failed to send screenshot to vision model: {e}")
            return False

    def handle_user_inquiry(self, user_input):
        log_trace(f"USER INQUIRY: {user_input}", self.trace_log_file)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant. Provide an appropriate response based on the given users activity log. The log was generated by capturing screenshots of the users activity and using a vision model to write the log. The log may also contain previous responses from the user and the assistant."},
                {"role": "user", "content": f"The user asked: '{user_input}'. Based on the following log, provide an appropriate response:\n\n{open(self.trace_log_file, 'r').read()}"}
            ]
        )
        assistant_response = response.choices[0].message.content
        
        log_trace(f"ASSISTANT RESPONSE: {assistant_response}", self.trace_log_file)
        return assistant_response 