import os
import torch
from bs4 import BeautifulSoup
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

class SignalClassifier:
    def __init__(self):
        print("🧠 Loading AI Model onto GPU (This takes a moment on first run)...")
        # Check if CUDA (your Nvidia GPU) is actually available
        self.device = 0 if torch.cuda.is_available() else -1
        
        if self.device == 0:
            print("🟢 SUCCESS: Nvidia GPU Detected. Using CUDA.")
        else:
            print("🟡 WARNING: GPU not detected. Falling back to CPU.")

        # We use a fast, highly accurate model for categorization
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=self.device
        )
        
        # The categories we want the AI to look for in the startup blogs
        self.target_categories = [
            "Engineering Infrastructure Scaling",
            "Artificial Intelligence and Machine Learning",
            "Hiring and Team Expansion",
            "General Company News"
        ]

    def clean_html(self, raw_html: str) -> str:
        """Strips HTML tags to save AI tokens."""
        soup = BeautifulSoup(raw_html, "lxml")
        
        for element in soup(["script", "style", "nav", "footer"]):
            element.extract()
            
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]

    def analyze_signal(self, raw_html: str) -> dict:
        """Cleans the text and asks the AI to classify it."""
        clean_text = self.clean_html(raw_html)
        
        if len(clean_text) < 100:
            return {"category": "Too Short / Error", "confidence": 0.0}

        result = self.classifier(
            clean_text,
            self.target_categories,
            multi_label=False
        )
        
        return {
            "category": result["labels"][0],
            "confidence": result["scores"][0]
        }
