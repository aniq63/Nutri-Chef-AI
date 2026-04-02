import os
from typing import Optional
from dotenv import load_dotenv
from serpapi import GoogleSearch
from utils.logger import logging

class ImageSearchService:
    """
    Service class to handle image fetching via SerpAPI.
    Designed to be instantiated once and used across FastAPI routes.
    """

    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("SERPAPI_KEY")
        
        # Validation for the API Key during initialization
        if not self.api_key:
            logging.error("ImageSearchService: SERPAPI_KEY is missing in the .env file.")
        else:
            logging.info("ImageSearchService initialized successfully.")

    def get_first_image_url(self, query: str) -> Optional[str]:
        """
        Queries Google Images and returns the 'original' URL of the first result.
        
        Args:
            query (str): The search term (e.g., 'Spaghetti Carbonara').
            
        Returns:
            Optional[str]: The image URL if found, None otherwise.
        """
        if not self.api_key:
            logging.error("Search attempted without a valid API Key.")
            return None

        params = {
            "engine": "google_images",
            "q": query,
            "api_key": self.api_key
        }

        try:
            logging.info(f"Searching for image: '{query}'")
            search = GoogleSearch(params)
            results = search.get_dict()

            # Check for API-level errors in the response
            if "error" in results:
                logging.error(f"SerpAPI Error: {results['error']}")
                return None

            # Extract the first image
            images = results.get("images_results", [])
            if images:
                image_url = images[0].get("original")
                logging.info(f"Image found for '{query}': {image_url}")
                return image_url

            logging.warning(f"No image results found for: '{query}'")
            return None

        except Exception as e:
            # Captures connection issues or unexpected API changes
            logging.exception(f"Unexpected exception during SerpAPI call: {e}")
            return None