import requests
from typing import List, Dict
from dotenv import load_dotenv
import os
from utils.logger import logging

class NutritionService:
    def __init__(self, base_url: str = "https://api.nal.usda.gov/fdc/v1"):
        load_dotenv()
        api_key_env = os.getenv('USDA_API_KEY')
        self.api_key = api_key_env.strip() if api_key_env else None
        self.base_url = base_url
        
        if not self.api_key:
            logging.error("NutritionService: USDA_API_KEY is missing!")
        else:
            logging.info("NutritionService initialized successfully.")

    def _fetch_per_100g(self, ingredient: str) -> Dict[str, float]:
        """Fetch nutrition per 100g from USDA."""
        logging.info(f"Fetching nutrition data for: {ingredient}")
        try:
            response = requests.get(
                f"{self.base_url}/foods/search",
                params={
                    "query": ingredient,
                    "pageSize": 1,
                    "api_key": self.api_key
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()
            foods = data.get("foods", [])

            if not foods:
                logging.warning(f"No USDA data found for '{ingredient}'")
                raise ValueError(f"No data found for '{ingredient}'")

            nutrients_raw = foods[0].get("foodNutrients", [])
            nutrients = {
                n.get("nutrientName"): n.get("value", 0)
                for n in nutrients_raw
            }

            logging.info(f"Successfully fetched nutrition for {ingredient}")
            return {
                "calories": nutrients.get("Energy", 0),
                "protein": nutrients.get("Protein", 0),
                "carbs": nutrients.get("Carbohydrate, by difference", 0),
                "fat": nutrients.get("Total lipid (fat)", 0),
                "fiber": nutrients.get("Fiber, total dietary", 0),
            }
        except requests.exceptions.Timeout:
            logging.error(f"Timeout while fetching nutrition for {ingredient}")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error for {ingredient}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error fetching nutrition for {ingredient}: {str(e)}")
            raise

    def get_total_nutrition(self, ingredients: List[Dict]) -> Dict:
        """
        Calculate total nutrition for a list of ingredients.
        """
        if not ingredients:
            logging.warning("get_total_nutrition called with empty ingredient list")
            raise ValueError("Ingredient list cannot be empty")

        logging.info(f"Calculating total nutrition for {len(ingredients)} ingredients")
        totals = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0,
            "fiber": 0.0
        }

        details = []
        errors = []

        for item in ingredients[:8]:
            name = item.get("name")
            grams = item.get("grams")

            if not name or grams is None:
                logging.error(f"Invalid ingredient format: {item}")
                errors.append({"item": item, "error": "Invalid format"})
                continue

            try:
                per100 = self._fetch_per_100g(name)
                scale = grams / 100.0
                scaled = {
                    k: round(v * scale, 2)
                    for k, v in per100.items()
                }

                for key in totals:
                    totals[key] += scaled[key]

                details.append({
                    "name": name,
                    "grams": grams,
                    "nutrition": scaled
                })

            except Exception as e:
                logging.error(f"Failed to process {name}: {str(e)}")
                errors.append({
                    "name": name,
                    "error": str(e)
                })

        logging.info("Total nutrition calculation completed")

        return {
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "details": details,
            "errors": errors
        }