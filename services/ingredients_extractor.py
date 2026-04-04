import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from utils.logger import logging

# Load environment variables from .env file
load_dotenv()

class FoodAnalyzer:
    """
    Handles image segmentation and ingredient extraction via LogMeal API.
    Designed for integration with FastAPI and production workflows.
    """

    def __init__(self):
        # Fetching from .env; using None as default to handle missing keys gracefully
        self.api_token = os.getenv("INGREDIENTS_RECOGINATION_TOKEN")
        self.base_url = os.getenv("LOGMEAL_BASE_URL", "https://api.logmeal.com/v2")
        self.endpoint = f"{self.base_url}/image/segmentation/complete"
        
        if not self.api_token:
            logging.critical("API_USER_TOKEN not found in environment variables!")
            raise ValueError("Missing API Token. Please check your .env file.")
        
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        logging.info("FoodAnalyzer initialized with environment credentials.")

    def get_ingredients(self, image_content: bytes, confidence_threshold: float = 0.30) -> List[str]:
        """
        Processes image bytes (ideal for FastAPI UploadFile) and extracts ingredients.
        """
        try:
            logging.info("Dispatching request to LogMeal API.")
            
            # Using 'image_content' as bytes makes it easier to handle 
            # FastAPI's UploadFile.file.read() later.
            files = {"image": ("image.jpg", image_content, "image/jpeg")}
            response = requests.post(
                self.endpoint, 
                headers=self.headers, 
                files=files, 
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_response(data, confidence_threshold)

        except requests.exceptions.Timeout:
            logging.error("API request timed out.")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error: {http_err} | Response: {response.text}")
        except Exception as e:
            logging.critical(f"Unexpected error in FoodAnalyzer: {e}")
        
        return []

    def _parse_response(self, data: Dict[str, Any], threshold: float) -> List[str]:
        """Parses JSON response and filters by confidence threshold."""
        ingredients = []
        results = data.get('segmentation_results', [])

        for item in results:
            recs = item.get('recognition_results') or []
            if not recs: continue

            top = recs[0]
            name, prob = top.get('name'), top.get('prob', 0)

            if name and prob >= threshold:
                ingredients.append(name)

        unique_ingredients = list(set(ingredients))
        logging.info(f"Successfully extracted {len(unique_ingredients)} unique ingredients.")
        return unique_ingredients