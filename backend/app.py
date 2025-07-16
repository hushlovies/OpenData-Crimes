from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/greet", methods=["GET"])
def greet():
    name = "Alice"
    message = f"Bonjour, {name} !"
    return jsonify({"message": message})

if __name__ == "__main__":
    app.run(port=5000)
