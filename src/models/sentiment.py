# src/models/sentiment.py
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, Any
from loguru import logger
from ..config import settings

class SentimentModel:
    """Wrapper class for sentiment analysis model"""
    
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.device_name = "GPU" if self.device == 0 else "CPU"
        
        logger.info(f"Loading model on {self.device_name}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                settings.MODEL_NAME
            )
            
            if self.device == 0:
                self.model = self.model.to('cuda')
            
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
                batch_size=settings.MAX_BATCH_SIZE,
                truncation=True,
                max_length=512
            )
            
            logger.info(f"✅ Model loaded successfully on {self.device_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def predict(self, text: str) -> Dict[str, Any]:
        """Predict sentiment for single text"""
        result = self.pipeline(text)[0]
        return {
            "label": result["label"].upper(),
            "score": float(result["score"])
        }
    
    def predict_batch(self, texts: list) -> list:
        """Predict sentiment for batch of texts"""
        results = self.pipeline(texts)
        return [{
            "label": r["label"].upper(),
            "score": float(r["score"])
        } for r in results]
    
    def get_info(self) -> Dict:
        """Get model information"""
        return {
            "model_name": settings.MODEL_NAME,
            "device": self.device_name,
            "max_batch_size": settings.MAX_BATCH_SIZE,
            "parameters": sum(p.numel() for p in self.model.parameters())
        }