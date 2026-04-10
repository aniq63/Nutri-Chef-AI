import json
import os
import traceback
from typing import Dict, Any
from warnings import filterwarnings

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Your custom logging import
from utils.logger import logging
from config.constants import SYSTEM_PROMPT

filterwarnings("ignore")

class NutriChefAI:
    def __init__(self, model_name: str = None):
        """
        Initializes the AI Chef with API keys, logging, and LangChain orchestration.
        """
        try:
            # 1. Load .env and verify GROQ_API_KEY
            load_dotenv()
            self.api_key = os.getenv("GROQ_API_KEY")
            
            if not self.api_key:
                logging.error("NutriChefAI: GROQ_API_KEY not found in environment.")
                raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

            # 2. Determine Model Name (Constructor Argument > Env Var > Default)
            env_model = os.getenv("GROQ_MODEL_NAME")
            self.model_name = model_name or env_model or "llama-3.3-70b-versatile"
            
            logging.info(f"Initializing NutriChefAI with model: {self.model_name}")

            # 3. Setup Prompt and LLM
            self.system_prompt = SYSTEM_PROMPT
            self.prompt = PromptTemplate(
                template=self.system_prompt,
                input_variables=["ingredients", "cuisine"]
            )

            # Passing the API key explicitly for clarity.
            # Adding timeout and max_retries for robust cloud connectivity (Railway).
            self.llm = ChatGroq(
                model_name=self.model_name,
                groq_api_key=self.api_key,
                request_timeout=60.0,
                max_retries=3
            )
            
            # Using LangChain Expression Language (LCEL)
            self.chain = self.prompt | self.llm
            
            logging.info(f"NutriChefAI: Components initialized successfully for model {self.model_name}.")

        except Exception as e:
            logging.error(f"NutriChefAI Initialization failed: {str(e)}")
            logging.error(traceback.format_exc())
            raise RuntimeError(f"Initialization failed: {str(e)}")

    def _generate(self, ingredients: str, cuisine: str):
        """Internal method to invoke the LLM chain."""
        logging.info(f"Generating recipe for Cuisine: {cuisine} with Ingredients: {ingredients[:50]}...")
        return self.chain.invoke({
            "ingredients": ingredients,
            "cuisine": cuisine
        })

    def _parse(self, text: str) -> Dict[str, Any]:
        """Handles JSON parsing with fallback logic for markdown blocks."""
        try:
            logging.info("Attempting to parse LLM response to JSON.")
            return json.loads(text)
        except json.JSONDecodeError:
            logging.warning("Standard JSON parsing failed. Attempting regex/substring extraction.")
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start == -1 or end == 0:
                    raise ValueError("No JSON braces found in response.")
                
                parsed_data = json.loads(text[start:end])
                logging.info("JSON extracted successfully via substring.")
                return parsed_data
            except Exception as e:
                logging.error(f"JSON Parsing Error: {str(e)} | Raw Content: {text[:100]}...")
                raise ValueError("The AI response could not be parsed into a valid JSON format.")

    def run(self, ingredients: str, cuisine: str) -> Dict[str, Any]:
        """Main execution logic for the FastAPI route."""
        try:
            # Step 1: Generate
            response = self._generate(ingredients, cuisine)

            if not hasattr(response, "content") or not response.content:
                logging.error("LLM returned an empty or invalid response object.")
                raise ValueError("Invalid LLM response received.")

            # Step 2: Parse
            parsed = self._parse(response.content)

            logging.info("Recipe generation and parsing completed successfully.")
            return {
                "success": True,
                "data": parsed,
                "error": None
            }

        except Exception as e:
            err_msg = str(e)
            # Surface specific Groq decommissioning error if present
            if "decommissioned" in err_msg.lower():
                logging.critical(f"MODEL DECOMMISSIONED ERROR: {err_msg}")
            
            logging.error(f"NutriChefAI.run Error: {err_msg}")
            logging.error(traceback.format_exc())
            
            return {
                "success": False,
                "data": None,
                "error": err_msg
            }

    def run_json(self, ingredients: str, cuisine: str) -> str:
        """Returns the result as a formatted JSON string."""
        result = self.run(ingredients, cuisine)
        return json.dumps(result, indent=2)