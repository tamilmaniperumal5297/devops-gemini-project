import os
import time
from google import genai
from google.genai import errors

# Sample log output representing a backend database resolution failure
SAMPLE_LOG = """
2026-09-25 14:10:02,112 [ERROR] django.request: Internal Server Error: /api/v1/checkout
Traceback (most recent call last):
  File "site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "apps/orders/views.py", line 42, in checkout
    db_conn = psycopg2.connect(host="postgres-db.internal", port=5432, timeout=5)
psycopg2.OperationalError: could not translate host name "postgres-db.internal" to address: Name or service not known
"""

def analyze_logs(log_data: str):
    """Sends log data to Gemini with automatic model fallback for 503 errors."""

    # 1. Verify API Key exists in environment
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("Error: GEMINI_API_KEY environment variable is not set.")

    # 2. Instantiate the GenAI Client
    client = genai.Client()

    # 3. Construct a structured engineering prompt
    prompt = f"""
    Act as a senior DevOps/SRE engineer. Analyze the following application log.
    
    Provide your response in this format:
    1. Error Identified:
    2. Possible Root Cause:
    3. Recommended Troubleshooting Steps (numbered list):

    <logs>
    {log_data}
    </logs>
    """

    # List of candidate models to try sequentially if high demand (503) occurs
    candidate_models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
    
    response = None
    
    print("Sending log data to Gemini for analysis...\n")

    for model_name in candidate_models:
        try:
            print(f"Attempting API request using model: '{model_name}'...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            # If request succeeds, exit loop
            print(f"Successfully generated response using '{model_name}'!\n")
            break
        except errors.APIError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"Warning: Model '{model_name}' returned 503 (High Demand). Trying fallback model...")
                time.sleep(1) # Brief pause before fallback attempt
                continue
            else:
                # Re-raise non-503 errors (e.g., Auth, Invalid Key)
                raise e

    if not response:
        print("Error: All model endpoints are currently overloaded. Please retry in 1 minute.")
        return

    # 4. Output the structured analysis
    print("=== SRE Incident Analysis ===")
    print(response.text)
    print("=============================")

if __name__ == "__main__":
    analyze_logs(SAMPLE_LOG)