import os
import time
from flask import Flask, request, jsonify
from google import genai
from google.genai import errors

app = Flask(__name__)

# List of active models to try sequentially
CANDIDATE_MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

def query_gemini_sre_analysis(log_content: str) -> str:
    """Helper function to execute Gemini API queries with resilient fallbacks."""
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client()
    prompt = f"""
    Act as a senior DevOps/SRE engineer. Analyze the following log/code snippet.
    
    Provide your response in this exact format:
    1. Error Identified:
    2. Possible Root Cause:
    3. Recommended Troubleshooting Steps (numbered list):

    <logs>
    {log_content}
    </logs>
    """

    for model_name in CANDIDATE_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except errors.APIError as e:
            error_str = str(e)
            # Catch transient 503 capacity issues AND 404 endpoint deprecations
            if any(code in error_str for code in ["503", "UNAVAILABLE", "404", "NOT_FOUND"]):
                print(f"Model '{model_name}' failed with: {error_str}. Falling back to next model...")
                time.sleep(1)
                continue
            else:
                # Re-raise unhandled exceptions (e.g. invalid API keys or auth failures)
                raise e

    raise RuntimeError("All configured Gemini API model endpoints failed or are overloaded.")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return jsonify({
        "status": "healthy",
        "service": "devops-gemini-analyzer"
    }), 200


@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    """POST endpoint receiving JSON payloads."""
    data = request.get_json()

    if not data or 'content' not in data:
        return jsonify({
            "error": "Bad Request",
            "message": "Missing 'content' key in JSON request body."
        }), 400

    content = data['content']
    if not str(content).strip():
        return jsonify({
            "error": "Bad Request",
            "message": "'content' field cannot be empty."
        }), 400

    try:
        analysis_result = query_gemini_sre_analysis(content)
        return jsonify({
            "status": "success",
            "analysis": analysis_result
        }), 200
    except ValueError as ve:
        return jsonify({"error": "Configuration Error", "message": str(ve)}), 500
    except Exception as e:
        return jsonify({"error": "Processing Error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)