# filepath: website/app.py
from flask import Flask, render_template, jsonify
import redis
import json
import os

app = Flask(__name__)

# Configure Redis connection using environment variables or defaults
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "redis"))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,  # Decode responses to strings
    )
    redis_client.ping()  # Check connection
    print("Successfully connected to Redis")
except redis.exceptions.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
    redis_client = None  # Set client to None if connection fails


@app.route("/")
def index():
    redis_data = {}
    error_message = None
    if redis_client:
        try:
            keys = redis_client.keys("*")
            for key in keys:
                try:
                    # Attempt to get value based on type
                    key_type = redis_client.type(key)
                    if key_type == "string":
                        value = redis_client.get(key)
                        # Try decoding JSON if it looks like it
                        if value and value.startswith(("[", "{")):
                            try:
                                value = json.dumps(json.loads(value), indent=2)
                            except json.JSONDecodeError:
                                pass  # Keep original string if not valid JSON
                    elif key_type == "list":
                        value = redis_client.lrange(key, 0, -1)  # Get all items
                        # Try decoding JSON items
                        value = [
                            (
                                json.dumps(json.loads(item), indent=2)
                                if isinstance(item, str) and item.startswith(("[", "{"))
                                else item
                            )
                            for item in value
                        ]
                    elif key_type == "hash":
                        value = redis_client.hgetall(key)
                    elif key_type == "set":
                        value = list(redis_client.smembers(key))
                    elif key_type == "zset":
                        value = redis_client.zrange(key, 0, -1, withscores=True)
                    else:
                        value = f"Unsupported type: {key_type}"
                    redis_data[key] = value
                except Exception as e:
                    redis_data[key] = f"Error reading key '{key}': {e}"
        except redis.exceptions.ConnectionError as e:
            error_message = f"Could not connect to Redis: {e}"
            redis_data = {}  # Clear data if connection lost
        except Exception as e:
            error_message = f"An error occurred fetching data from Redis: {e}"
    else:
        error_message = "Redis client is not connected."

    return render_template(
        "index.html", redis_data=redis_data, error_message=error_message
    )


@app.route("/api/redis")
def api_redis():
    redis_data = {}
    error_message = None
    if redis_client:
        try:
            keys = redis_client.keys("*")
            for key in keys:
                try:
                    # Attempt to get value based on type
                    key_type = redis_client.type(key)
                    if key_type == "string":
                        value = redis_client.get(key)
                        if value and value.startswith(("[", "{")):
                            try:
                                value = json.loads(value)
                            except json.JSONDecodeError:
                                pass
                    elif key_type == "list":
                        value = redis_client.lrange(key, 0, -1)
                        value = [
                            (
                                json.loads(item)
                                if isinstance(item, str) and item.startswith(("[", "{"))
                                else item
                            )
                            for item in value
                        ]
                    elif key_type == "hash":
                        value = redis_client.hgetall(key)
                    elif key_type == "set":
                        value = list(redis_client.smembers(key))
                    elif key_type == "zset":
                        value = redis_client.zrange(key, 0, -1, withscores=True)
                    else:
                        value = f"Unsupported type: {key_type}"
                    redis_data[key] = value
                except Exception as e:
                    redis_data[key] = f"Error reading key '{key}': {e}"
        except redis.exceptions.ConnectionError as e:
            return jsonify({"error": f"Could not connect to Redis: {e}"}), 500
        except Exception as e:
            return (
                jsonify({"error": f"An error occurred fetching data from Redis: {e}"}),
                500,
            )
    else:
        return jsonify({"error": "Redis client is not connected."}), 500

    return jsonify(redis_data)


if __name__ == "__main__":
    app.run(
        debug=True, host="0.0.0.0", port=5001
    )  # Run on a different port than default 5000
