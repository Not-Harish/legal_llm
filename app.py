# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from agent_runner import run_agent_for_input

app = Flask(__name__)
CORS(app)

@app.route("/api/send-message", methods=["POST"])
def send_message():
    data = request.json
    user_input = data.get("message", "")
    responses = run_agent_for_input(user_input)

    print("📤 Returning:", responses)

    return jsonify([
        { "message": str(msg), "timestamp": "" } for msg in responses
    ])



@app.route("/api/generate-document", methods=["POST"])
def generate_document():
    data = request.json
    instruction = data.get("instruction", "")
    content = data.get("content", "")

    # Simulate document generation with instruction
    response = f"{content}\n\n✍️ AI-generated note: {instruction}"
    return jsonify({
        "content": response
    })

if __name__ == "__main__":
    app.run(debug=True)
