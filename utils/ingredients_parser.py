import re

class IngredientParser:
    """
    Parses raw ingredient strings into structured dicts with grams.
    Example input: "200g broccoli, cut into florets"
    Output: {"name": "broccoli", "grams": 200}
    """

    # rough conversion constants (prototype, can refine later)
    UNIT_TO_GRAMS = {
        # mass
        "g": 1,
        "gram": 1,
        "grams": 1,
        "kg": 1000,
        "kilogram": 1000,
        "mg": 0.001,
        "oz": 28.35,
        "ounce": 28.35,
        "ounces": 28.35,

        # volume approximations
        "tbsp": 13.5,
        "tablespoon": 13.5,
        "tablespoons": 13.5,
        "tsp": 4.5,
        "teaspoon": 4.5,
        "teaspoons": 4.5,
        "cup": 240,
        "cups": 240
    }

    # fallback weights for 1 unit items (rough estimate)
    DEFAULT_WEIGHTS = {
        "lemon": 100,
        "apple": 180,
        "banana": 120,
        "egg": 50
    }

    def parse(self, ingredients: list):
        structured = []

        for item in ingredients:
            item_lower = item.lower()

            # extract quantity (number)
            qty_match = re.search(r"(\d+(\.\d+)?)", item_lower)
            qty = float(qty_match.group(1)) if qty_match else 1

            # detect unit (pick first matching)
            unit = None
            for u in self.UNIT_TO_GRAMS:
                if re.search(rf"\b{u}\b", item_lower):
                    unit = u
                    break

            # clean name: remove number, unit, extra text after comma
            name = re.sub(r"(\d+(\.\d+)?)", "", item_lower)
            if unit:
                name = re.sub(rf"\b{unit}\b", "", name)
            name = name.split(",")[0].strip()

            # convert to grams
            if unit:
                grams = qty * self.UNIT_TO_GRAMS[unit]
            else:
                # fallback for 1-item counts
                grams = qty * self.DEFAULT_WEIGHTS.get(name, 100)

            structured.append({
                "name": name,
                "grams": round(grams, 2)
            })

        return structured