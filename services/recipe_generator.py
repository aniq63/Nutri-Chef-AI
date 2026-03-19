import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from warnings import filterwarnings
filterwarnings("ignore")

class NutriChefAI:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        try:
            self.system_prompt = """YOUR FULL PROMPT HERE"""

            self.prompt = PromptTemplate(
                template=self.system_prompt,
                input_variables=["ingredients", "cuisine"]
            )

            self.llm = ChatGroq(model_name=model_name)
            self.chain = self.prompt | self.llm

        except Exception as e:
            raise RuntimeError(f"Initialization failed: {str(e)}")

    def _generate(self, ingredients, cuisine):
        return self.chain.invoke({
            "ingredients": ingredients,
            "cuisine": cuisine
        })

    def _parse(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                return json.loads(text[start:end])
            except Exception:
                raise ValueError("Invalid JSON response")

    def run(self, ingredients, cuisine):
        try:
            response = self._generate(ingredients, cuisine)

            if not hasattr(response, "content"):
                raise ValueError("Invalid LLM response")

            parsed = self._parse(response.content)

            return {
                "success": True,
                "data": parsed,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }

    # Final method for formatted JSON output (optional)
    def run_json(self, ingredients, cuisine):
        result = self.run(ingredients, cuisine)
        return json.dumps(result, indent=2)