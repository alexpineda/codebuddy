import datetime
import os
import requests
from utils import append_log
from tools.suggested_context_finder import SuggestedContextFinder

built_in_providers = [
    {
        "provider": "openai",
        "api_key_name": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/",
        "chat_completions_url": "v1/chat/completions",
        "auth_header_name": "Authorization",
        "max_output_tokens": 16_384,
        "system": "message_role",
        "models": ["gpt-4o-mini", "gpt-4o"],
        "response_mapping": {
            "content": "choices.0.message.content",
            "model": "model",
            "usage": "usage"
        }
    },
    {
        "provider": "anthropic",
        "api_key_name": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/",
        "chat_completions_url": "v1/messages",
        "extra_headers": {
            "anthropic-version": "2023-06-01"
        },
        "auth_header_name": "x-api-key",
        "max_output_tokens": 8192,
        "models": ["claude-3-5-sonnet-20241022"],
        "system": "top_level_field",
        "response_mapping": {
            "content": "content.0.text",
            "model": "model",
            "usage": "usage"
        }
    }
]


class Client:
    def __init__(self, model_config, providers=built_in_providers):
        self.provider = next(p for p in providers if model_config["model"] in p["models"])
        self.api_key = self.provider.get("api_key_name") and os.getenv(self.provider["api_key_name"])
        self.base_url = self.provider.get("base_url", "http://localhost:8000/")
        self.model = model_config["model"]
        self.chat_completions_url = self.provider.get("chat_completions_url", "chat/completions")
        self.extra_headers = self.provider.get("extra_headers", {})

    def _get_nested_value(self, obj, path):
        """Get a value from a nested dictionary using a dot-separated path"""
        for key in path.split('.'):
            try:
                if key.isdigit():
                    obj = obj[int(key)]
                else:
                    obj = obj[key]
            except (KeyError, IndexError, TypeError):
                return None
        return obj

    def create_chat_completion(self, messages, system_message=None, max_tokens=None):
        headers = {
            "Content-Type": "application/json",
            **self.extra_headers  # Merge provider-specific extra headers
        }
        if self.api_key:
            auth_value = f"Bearer {self.api_key}" if self.provider.get("auth_header_name") == "Authorization" else self.api_key
            headers[self.provider.get("auth_header_name", "Authorization")] = auth_value
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens if max_tokens else self.provider.get("max_output_tokens", 8192)
        }

        if system_message:
            if self.provider.get("system") == "message_role":
                payload["messages"] = [{"role": "system", "content": system_message}] + payload["messages"]
            elif self.provider.get("system") == "top_level_field":
                payload["system"] = system_message

        response = requests.post(
            f"{self.base_url}{self.chat_completions_url}",
            headers=headers,
            json=payload,
            timeout=60  # Add timeout to handle slow local models
        )
        response.raise_for_status()
        raw_response = response.json()
        
        # Map the response according to provider's response mapping
        mapping = self.provider.get("response_mapping", {})
        mapped_response = {
            key: self._get_nested_value(raw_response, path)
            for key, path in mapping.items()
        }
        return mapped_response


class AppPrompts:
    def __init__(self, config):
        custom_providers = config.get("custom_providers", [])
        self.providers = built_in_providers + custom_providers
        
        # Flatten models for backward compatibility
        self.models = []
        for provider in self.providers:
            for model in provider["models"]:
                self.models.append({"model": model})
        
        client_config = next(m for m in self.models if m["model"] == config["qa_model"])
        self.client = Client(client_config, providers=self.providers)

    def prompt(self, prompt_text):
        response = self.client.create_chat_completion(
            messages=[{"role": "user", "content": prompt_text}]
        )
        return response["content"]

class CustomInstructions:
    def __init__(self, config):
        self.vision = self.load_instructions("instructions_vision.txt")
        self.qa = self.load_instructions("instructions_qa.txt")
        self.privacy = self.load_instructions("instructions_privacy.txt")
    
    def load_instructions(self, filepath):
        with open(filepath, 'r') as file:
            return file.read()

class SessionPrompts:
    def __init__(self, session):
        self.session = session
        config = session.config

        self.providers = built_in_providers + config.get("custom_providers", [])
        self.custom_instructions = CustomInstructions(config)

        # Flatten models for backward compatibility
        self.models = []
        for provider in self.providers:
            for model in provider["models"]:
                self.models.append({"model": model})

        self.vision = Client(
            next(m for m in self.models if m["model"] == config["screen_vision_model"]),
            providers=self.providers
        )
        self.qa = Client(
            next(m for m in self.models if m["model"] == config["qa_model"]),
            providers=self.providers
        )
        self.privacy_vision = Client(
            next(m for m in self.models if m["model"] == config["privacy_vision_model"]),
            providers=self.providers
        )

        self.context_finder = SuggestedContextFinder()
        self.interval = config["capture_interval"]

    @property
    def session_log_filepath(self):
        return self.session.current_session["session_log_filepath"]

    def prompt(self, prompt_text):
        response = self.qa.create_chat_completion(
            messages=[{"role": "user", "content": prompt_text}]
        )
        return response["content"]

    def process_screenshot(self, base64_image, filename, active_window_title):
        try:
            system_message = self.custom_instructions.vision.replace("{capture_interval}", str(self.interval))
            response = self.vision.create_chat_completion(
                system_message=system_message,
                messages=[
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

            vision_response = response["content"]
            self.session.write_to_log(f"Active window: {active_window_title}")
            self.session.write_to_log(vision_response)
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

            system_message = self.custom_instructions.qa.replace("{capture_interval}", str(self.interval))
            response = self.qa.create_chat_completion(
                system_message=system_message,
                messages=[
                    {
                        "role": "assistant",
                        "content": f"Latest activity log: {log_content}. How can I help you?",
                    },
                    {"role": "user", "content": user_input},
                ],
            )
            assistant_response = response["content"]

            self.session.write_to_log(f"USER INQUIRY: {user_input}")
            self.session.write_to_log(f"ASSISTANT RESPONSE: {assistant_response}")

            return assistant_response
        except Exception as e:
            print(f"Failed to handle user inquiry: {e}")
            return "Sorry, I couldn't process your request."
