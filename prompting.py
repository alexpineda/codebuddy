import datetime
from openai import OpenAI
import os
from utils import append_log
from tools.suggested_context_finder import SuggestedContextFinder

built_in_models = [
    {
        "key_name": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1/",
    },
    {
        "key_name": "OPENAI_API_KEY",
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1/",
    },
    {
        "key_name": "ANTHROPIC_API_KEY",
        "model": "claude-3-5-sonnet-20241022",
        "base_url": "https://api.anthropic.com/v1/",
    },
]


class Client:
    def __init__(self, model_config):
        api_key = model_config.get("key_name") and os.getenv(model_config["key_name"])
        base_url = model_config.get("base_url")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_config["model"]


class AppPrompts:
    def __init__(self, config):
        custom_models = config["custom_models"] or []
        self.models = built_in_models + custom_models
        client_config = next(m for m in self.models if m["model"] == config["qa_model"])
        self.client = Client(client_config)

    def prompt(self, prompt_text):
        print("DEBUG:")
        print(f"Model: {self.client.model}")
        print(f"API Key (first 8 chars): {self.client.client.api_key[:8]}...")
        print(f"Base URL: {self.client.client.base_url}")
        response = self.client.client.chat.completions.create(
            model=self.client.model, messages=[{"role": "user", "content": prompt_text}]
        )
        return response.choices[0].message.content


class SessionPrompts:
    def __init__(self, session):
        self.session = session
        config = session.config
        custom_models = config["custom_models"] or []
        self.models = built_in_models + custom_models

        self.vision = Client(
            next(m for m in self.models if m["model"] == config["screen_vision_model"])
        )
        self.qa = Client(
            next(m for m in self.models if m["model"] == config["qa_model"])
        )
        self.privacy_vision = Client(
            next(m for m in self.models if m["model"] == config["privacy_vision_model"])
        )

        self.context_finder = SuggestedContextFinder()
        self.interval = config["capture_interval"]

    @property
    def session_log_filepath(self):
        return self.session.current_session["session_log_filepath"]

    def prompt(self, prompt_text):
        response = self.qa.client.chat.completions.create(
            model=self.qa.model, messages=[{"role": "user", "content": prompt_text}]
        )
        return response.choices[0].message.content

    def process_screenshot(self, base64_image, filename, active_window_title):
        try:
            response = self.vision.client.chat.completions.create(
                model=self.vision.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are a screenshot analysis assistant.
                        You are part of an application that is purposed around aiding the user in their productivity and act as a short term memory.
                        The following is a screenshot of a series of screenshots of the user's screen taken in {self.interval} second intervals.
                        A screenshot will not be taken if the user is on the same screen they started this application on (command line console).
                        The response will be added cumulatively to an 'activity' log file where another assistant will read the log and respond to the user about their activity.
                        Feel free to use the context of the previous screenshots to help you describe the current screenshot.
                        Use any special encoding or formatting to aid in the process of describing the screenshot, including compression of repetitive text or repeating screenshots.
                        """,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Screenshot of the user's screen taken at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. The active window is: {active_window_title}",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=2000,
            )

            vision_response = response.choices[0].message.content
            append_log(f"Active window: {active_window_title}", self.session_log_filepath)
            append_log(vision_response, self.session_log_filepath)
            return True
        except Exception as e:
            print(f"Failed to send screenshot to vision model: {e}")
            return False

    def handle_user_inquiry(self, user_input: str) -> str:
        try:
            # Get suggested context before forming the prompt
            # context = self.context_finder.get_suggested_context(self.session_log_filepath)

            # # Add context to the prompt if confidence is high enough
            # context_prompt = ""
            # if context["confidence"] > 0.4:
            #     context_prompt = "\nRecent context:"
            #     if context["file_path"]:
            #         context_prompt += f"\nFile: {context['file_path']}"

            # print(f"Context: {context_prompt}")

            # Combine with existing prompt logic
            with open(self.session_log_filepath, "r") as f:
                log_content = f.read()

            response = self.qa.client.chat.completions.create(
                model=self.qa.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                     You are an assistant that is purposed around aiding the user in their productivity and act as a short term memory.
                     Provide an appropriate response based on the given users activity log.
                     The activity log is generated by capturing screenshots of the users activity and using a vision model to write the log. 
                     The log may also contain previous responses from the user and you, assistant.
                     Screenshots are taken in {self.interval} second intervals, unless the user is on the same screen they started this application on (command line console).
                     Be positive. The user is working on something important. The user is trying to get things done and needs help.
                     Talk like a really smart engineer, quirky, super sharp, no bullshit, full of insights, helpful, to the point. We are pumped to be working togethor, can get annoyed with each other sometimes, and want to be efficient and make great products.
                     """,
                    },
                    {
                        "role": "assistant",
                        "content": f"Latest activity log: {log_content}. How can I help you?",
                    },
                    {"role": "user", "content": user_input},
                ],
            )
            assistant_response = response.choices[0].message.content

            append_log(f"USER INQUIRY: {user_input}", self.session_log_filepath)
            append_log(
                f"ASSISTANT RESPONSE: {assistant_response}", self.session_log_filepath
            )

            return assistant_response
        except Exception as e:
            print(f"Failed to handle user inquiry: {e}")
            return "Sorry, I couldn't process your request."
