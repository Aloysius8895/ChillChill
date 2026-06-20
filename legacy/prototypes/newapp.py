from flask import Flask, jsonify, send_from_directory
import os

# Initialize the Flask app
app = Flask(__name__, static_folder='frontend')

# --- MOCK LOGIC: Replace/Import your actual AI functions here ---
def analyze():
    return {"status": "data_processed"}

def call_claude(data):
    return {"security": 100, "efficiency": 76, "sustainability": 59}

def local_fallback(data):
    return {"message": "Using fallback data"}
# ----------------------------------------------------------------

# --- ROUTES ---

@app.route("/")
def home():
    """Serves the main landing page."""
    return send_from_directory('frontend', 'index.html')

@app.route("/<path:filename>")
def serve_feature(filename):
    """Serves individual feature pages from the frontend/features folder."""
    return send_from_directory('frontend/features', filename)

@app.route("/api/analyze")
def get_analysis():
    """API endpoint for the AI Recommendation Engine."""
    data = analyze()
    ai_recs = call_claude(data)
    if ai_recs:
        return jsonify(ai_recs)
    return jsonify({"message": "API is working!"})

if __name__ == '__main__':
    # Running on port 8000 as per your previous setup
    app.run(port=8000, debug=True)