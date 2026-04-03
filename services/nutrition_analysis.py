import requests
from typing import List, Dict
from dotenv import load_dotenv
import os

class NutritionService:
    def __init__(self,base_url: str = "https://api.nal.usda.gov/fdc/v1"):
        load_dotenv()
        self.api_key = os.getenv('USDA_API_KEY')
        self.base_url = base_url

    def _fetch_per_100g(self, ingredient: str) -> Dict[str, float]:
        """Fetch nutrition per 100g from USDA."""
        response = requests.get(
            f"{self.base_url}/foods/search",
            params={
                "query": ingredient,
                "pageSize": 1,
                "api_key": self.api_key
            },
            timeout=5
        )

        response.raise_for_status()
        foods = response.json().get("foods", [])
        if not foods:
            raise ValueError(f"No data found for '{ingredient}'")

        nutrients_raw = foods[0].get("foodNutrients", [])

        nutrients = {
            n.get("nutrientName"): n.get("value", 0)
            for n in nutrients_raw
        }

        return {
            "calories": nutrients.get("Energy", 0),
            "protein": nutrients.get("Protein", 0),
            "carbs": nutrients.get("Carbohydrate, by difference", 0),
            "fat": nutrients.get("Total lipid (fat)", 0),
            "fiber": nutrients.get("Fiber, total dietary", 0),
        }

    def get_total_nutrition(self, ingredients: List[Dict]) -> Dict:
        """
        ingredients = [
            {"name": "apple", "grams": 150},
            {"name": "rice", "grams": 200}
        ]
        """
        if not ingredients:
            raise ValueError("Ingredient list cannot be empty")

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
                errors.append({
                    "name": name,
                    "error": str(e)
                })

        return {
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "details": details,
            "errors": errors
        }