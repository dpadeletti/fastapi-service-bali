import os
import json
import requests
import boto3


class AIService:
    def __init__(self):
        self.env = os.getenv("ENVIRONMENT", "development")
        self.model_bedrock = "amazon.nova-lite-v1:0"

        if self.env == "prod":
            self.bedrock = boto3.client("bedrock-runtime", region_name="eu-north-1")

    def generate_chat_response(self, prompt: str) -> str:
        if self.env == "prod":
            body = json.dumps({
                "inferenceConfig": {"max_new_tokens": 512, "temperature": 0.7},
                "messages": [{"role": "user", "content": [{"text": prompt}]}]
            })
            response = self.bedrock.invoke_model(
                modelId=self.model_bedrock,
                body=body
            )
            response_body = json.loads(response.get("body").read())
            return response_body["output"]["message"]["content"][0]["text"]
        else:
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3", "prompt": prompt, "stream": False}
                )
                return response.json().get("response", "")
            except Exception as e:
                return f"Errore locale: Assicurati che Ollama sia attivo! ({e})"


ai_service = AIService()