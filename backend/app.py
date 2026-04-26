'''import os
import logging
import mysql.connector
import razorpay
from flask import Flask, request, jsonify, g, current_app
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers.schedules import ExponentialDecay
from werkzeug.utils import secure_filename
import jwt
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from werkzeug.security import generate_password_hash, check_password_hash

# Import the preprocess function from our model code
from analyze_image import analyze_file,analyze_video,analyze_document

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Basic Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
class Config:
    """Central configuration class for the Flask app."""
    SECRET_KEY = os.getenv('SECRET_KEY', '26ea88a85eaabdf1b8d04523452ef842f6f702c87c6a1633')
    # App settings
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv', 'pdf', 'docx', 'txt'}
    MODEL_FILENAME = 'model1_18epochs_valacc0.9252.hdf5'

    # Database settings - Use environment variables in production!
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
    DB_NAME = os.getenv('DB_NAME', 'myapp')

    # Razorpay settings - Use environment variables in production!
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_lENL2EMmm4YrZs')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'PKNn2lW0AjUSrBLTCRZh8ARM')

    # Google OAuth settings
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '813989156011-6aht2rsbeqq09qvqeushsv3rnpbr8bv2.apps.googleusercontent.com')

# --- Application Factory ---
def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # CORS Configuration: Allows requests from http://localhost:5173 with credentials
    CORS(app, supports_credentials=True, origins="http://localhost:5173")

    # --- Load Keras Model ---
    try:
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['MODEL_FILENAME'])
        custom_objects = {'ExponentialDecay': ExponentialDecay}
        app.model = load_model(model_path, custom_objects=custom_objects)
        logging.info("✅ Keras model loaded successfully.")
    except Exception as e:
        logging.critical(f"❌ FATAL: Could not load Keras model: {e}")
        app.model = None

    # --- Initialize Razorpay Client ---
    app.razorpay_client = razorpay.Client(
        auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET'])
    )

    return app

app = create_app()

# --- Database Connection Handling ---
def get_db():
    """Opens a new database connection if one is not already open for the current request."""
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            database=app.config['DB_NAME']
        )
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Helper Functions ---
def allowed_file(filename: str) -> bool:
    """Checks if a file's extension is in the allowed set."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def _is_subscribed(user_row):
    """Check if the user's subscription is currently active."""
    expires = user_row.get("subscription_expires")
    if not expires:
        return False
    return expires > datetime.datetime.utcnow()
def get_user_from_token():
    """Extracts user data from JWT token in Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user
    except:
        return None

# --- API Routes ---

@app.route("/predict", methods=["POST"])
def predict_route():
    """Handles file uploads for AI analysis with auth and credits check."""
    if not analyze_file:
        return jsonify({"error": "AI analyzer module is not available. Check server logs."}), 503

    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required. Please login again."}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    mimetype = file.mimetype
    # Simple cost logic: videos cost more (you can expand for other types)
    cost = 5 if "video" in mimetype else 1

    # Subscription & Credits logic
    if user['is_subscribed']:
        logging.info(f"Subscribed user {user['id']} analyzing. No credit cost.")
    elif user['credits'] >= cost:
        logging.info(f"User  {user['id']} analyzing. Cost: {cost}. Credits left: {user['credits'] - cost}")
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET credits = credits - %s WHERE id = %s", (cost, user['id']))
        db.commit()
        cursor.close()
    else:
        logging.warning(f"User  {user['id']} has insufficient credits.")
        return jsonify({"error": "Insufficient credits. Please subscribe for unlimited analysis."}), 402

    try:
        file_bytes = file.read()
        filename = file.filename.lower()
        
        # Route to specific analyzers based on extension (expand as needed)
        if filename.endswith((".jpg", ".jpeg", ".png")):
            result = analyze_file(file_bytes, mimetype)  # Your image analyzer
            result["type"] = "image"
        elif filename.endswith((".mp4", ".avi", ".mov", ".mkv")):
           result = analyze_video(file_bytes)  # ✅ Video analyzer
           result["type"] = "video"
        elif filename.endswith((".pdf", ".docx", ".txt")):
            result = analyze_document(file_bytes)  # ✅ Document analyzer
            result["type"] = "document"
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        return jsonify(result)
    except Exception as e:
        logging.error(f"❌ An error occurred during prediction: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route("/create-order", methods=["POST"])
def create_order_route():
    """Creates a payment order using Razorpay."""
    data = request.get_json()
    if not data or "amount" not in data:
        return jsonify({"error": "Amount is required"}), 400

    amount = int(data["amount"]) * 100  # Amount in paise
    try:
        order = app.razorpay_client.order.create({
            "amount": amount, "currency": "INR", "payment_capture": 1
        })
        return jsonify(order)
    except Exception as e:
        logging.error(f"❌ Razorpay order creation failed: {e}")
        return jsonify({"error": "Could not create payment order"}), 500
@app.route("/payment-success", methods=["POST"])
def payment_success_route():
    auth_user = get_user_from_token()
    if not auth_user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    order_id, payment_id, signature = data.get("razorpay_order_id"), data.get("razorpay_payment_id"), data.get("razorpay_signature")
    if not all([order_id, payment_id, signature]):
        return jsonify({"error": "Payment details are required"}), 400

    try:
        app.razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })

        new_expiry = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        expiry_str = new_expiry.strftime("%Y-%m-%d %H:%M:%S")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET subscription_expires = %s WHERE id = %s",
                       (expiry_str, auth_user['id']))
        db.commit()
        cursor.close()
        return jsonify({"message": f"Subscription activated until {expiry_str}"})

    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Payment signature verification failed"}), 400
    except Exception as e:
        return jsonify({"error": "An internal error occurred"}), 500
@app.route("/signup", methods=["POST"])
def signup_route():
    """Handles user signup with default credits."""
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"error": "Username, email, and password are required"}), 400

    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already registered"}), 409

        hashed_password = generate_password_hash(password)
        
        cursor.execute(
            "INSERT INTO users (username, email, password, credits, is_subscribed) VALUES (%s, %s, %s, %s, %s)",
            (username, email, hashed_password, 20, False)
        )
        user_id = cursor.lastrowid
        db_conn.commit()

        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        user_data = {
            'id': user_id, 'username': username, 'email': email,
            'credits': 20, 'is_subscribed': False
        }

        return jsonify({"message": "Signup successful", "token": token, "user": user_data}), 201
    except Exception as e:
        db_conn.rollback()
        logging.error(f"Signup Error: {e}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()

@app.route("/login", methods=["POST"])
def login_route():
    """Handles user login and returns JWT token."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "Email and password are required"}), 400

    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid email or password"}), 401

        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        user_data = {
            'id': user['id'], 'username': user['username'], 'email': user['email'],
            'credits': user['credits'], 'is_subscribed': user['is_subscribed']
        }

        return jsonify({"message": "Login successful", "token": token, "user": user_data}), 200
    except Exception as e:
        logging.error(f"Login Error: {e}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()

@app.route("/profile", methods=["GET"])
def profile_route():
    """Returns user profile data from JWT token."""
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Token is invalid or user not found"}), 401
    
    # Remove password from response
    user.pop('password', None)
    return jsonify({"user": user}), 200

@app.route("/google-login", methods=["POST"])
def google_login_route():
    """Handles Google OAuth login/signup."""
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Google token is missing"}), 400

    try:
        # Verify token with Google
        id_info = id_token.verify_oauth2_token(token, requests.Request(), app.config['GOOGLE_CLIENT_ID'])

        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")

        db_conn = get_db()
        cursor = db_conn.cursor(dictionary=True)

        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            logging.info(f"New user from Google: {email}. Creating account.")
            hashed_password = generate_password_hash(os.urandom(16).hex())
            cursor.execute(
                "INSERT INTO users (username, email, password, credits, is_subscribed) VALUES (%s, %s, %s, %s, %s)",
                (name or email.split('@')[0], email, hashed_password, 20, False)
            )
            user_id = cursor.lastrowid
            db_conn.commit()
            # Fetch the new user
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

        # Create JWT token for your app
        app_token = jwt.encode(
            {
                "user_id": user["id"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

        # Return user info without password
        user_data = {
            "id": user["id"], "username": user["username"], "email": user["email"],
            "credits": user["credits"], "is_subscribed": user["is_subscribed"],
            "picture": picture,
        }

        return jsonify({"message": "Google login successful", "token": app_token, "user": user_data}), 200

    except ValueError as e:
        logging.error(f"Google Token Verification Error: {e}")
        return jsonify({"error": "Invalid Google token"}), 401
    except Exception as e:
        logging.error(f"Error during Google login: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()

# --- Main Execution ---
if __name__ == "__main__":
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)'''


'''from dotenv import load_dotenv
load_dotenv()
import os
import logging
import uuid
import mysql.connector
import razorpay
from flask import Flask, request, jsonify, g, current_app
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from analyze_image import analyze_file, analyze_video, analyze_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "avi", "mov", "mkv", "pdf", "docx", "txt"}

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
    DB_NAME = os.getenv("DB_NAME", "myapp")

    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    CORS(app, supports_credentials=True, origins="*")

    app.razorpay_client = razorpay.Client(
        auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"])
    )
    return app


app = create_app()


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=app.config["DB_HOST"],
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
            database=app.config["DB_NAME"],
        )
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def _is_subscribed(user_row) -> bool:
    expires_str = user_row.get("subscription_expires")
    if not expires_str:
        return False
    try:
        expires = datetime.datetime.strptime(str(expires_str), "%Y-%m-%d %H:%M:%S")
        return expires > datetime.datetime.utcnow()
    except Exception:
        return False


def get_user_from_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = data["user_id"]
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            return None
        user["is_subscribed"] = _is_subscribed(user)
        user.pop("password", None)
        return user
    except Exception:
        return None


def get_file_cost(filename: str) -> int:
    ext = filename.rsplit(".", 1)[1].lower()
    if ext in {"mp4", "avi", "mov", "mkv"}:
        return 5
    return 1


def save_temp_file(file) -> str:
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(temp_path)
    return temp_path


def read_temp_file_bytes(temp_path: str) -> bytes:
    with open(temp_path, "rb") as f:
        return f.read()


@app.route("/predict", methods=["POST"])
def predict_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify({"error": "Unsupported file type"}), 400

    cost = get_file_cost(filename)
    if not user["is_subscribed"] and user.get("credits", 0) < cost:
        return jsonify({"error": "Insufficient credits"}), 402

    if not user["is_subscribed"]:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET credits = credits - %s WHERE id = %s", (cost, user["id"]))
        db.commit()
        cursor.close()

    temp_path = save_temp_file(file)
    try:
        file_bytes = read_temp_file_bytes(temp_path)
        ext = filename.rsplit(".", 1)[1].lower()

        if ext in {"jpg", "jpeg", "png"}:
            result = analyze_file(file_bytes, file.mimetype)
            result["type"] = "image"
        elif ext in {"mp4", "avi", "mov", "mkv"}:
            result = analyze_video(file_bytes)
            result["type"] = "video"
        elif ext in {"pdf", "docx", "txt"}:
            result = analyze_document(file_bytes)
            result["type"] = "document"
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        return jsonify(result)
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({"error": "Internal analysis error"}), 500
    finally:
        os.remove(temp_path)


@app.route("/create-order", methods=["POST"])
def create_order_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    amount = int(data.get("amount", 0))
    if amount < 100:
        return jsonify({"error": "Minimum amount is 100 INR"}), 400

    try:
        order = app.razorpay_client.order.create({
            "amount": amount * 100,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {"user_id": user["id"]}
        })
        return jsonify(order), 201
    except Exception as e:
        logging.error(f"Order creation failed: {e}")
        return jsonify({"error": "Order creation failed"}), 500


@app.route("/payment-success", methods=["POST"])
def payment_success_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")

    if not all([order_id, payment_id, signature]):
        return jsonify({"error": "Payment details required"}), 400

    try:
        app.razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT subscription_expires FROM users WHERE id=%s", (user["id"],))
        row = cursor.fetchone()
        now = datetime.datetime.utcnow()

        if row and row[0]:
            current_expiry = datetime.datetime.strptime(str(row[0]), "%Y-%m-%d %H:%M:%S")
            new_expiry = current_expiry + datetime.timedelta(days=30) if current_expiry > now else now + datetime.timedelta(days=30)
        else:
            new_expiry = now + datetime.timedelta(days=30)

        cursor.execute("UPDATE users SET subscription_expires=%s WHERE id=%s",
                       (new_expiry.strftime("%Y-%m-%d %H:%M:%S"), user["id"]))
        db.commit()
        cursor.close()
        return jsonify({"message": f"Subscription activated until {new_expiry}"}), 200

    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Signature verification failed"}), 400
    except Exception as e:
        logging.error(f"Payment error: {e}")
        return jsonify({"error": "Payment verification error"}), 500


@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    webhook_secret = app.config["RAZORPAY_WEBHOOK_SECRET"]
    body = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    try:
        app.razorpay_client.utility.verify_webhook_signature(body, signature, webhook_secret)
        payload = request.get_json()
        if payload.get("event") == "payment.captured":
            user_id = payload["payload"]["payment"]["entity"]["notes"].get("user_id")
            if user_id:
                db = get_db()
                cursor = db.cursor()
                cursor.execute("UPDATE users SET subscription_expires = DATE_ADD(NOW(), INTERVAL 1 MONTH) WHERE id=%s", (user_id,))
                db.commit()
                cursor.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"error": "Webhook signature failed"}), 400


@app.route("/signup", methods=["POST"])
def signup_route():
    data = request.get_json()
    username, email, password = data.get("username"), data.get("email"), data.get("password")

    if not all([username, email, password]) or len(password) < 6:
        return jsonify({"error": "Username, email, and password (min 6 chars) required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, email, password, credits, subscription_expires) VALUES (%s, %s, %s, %s, %s)",
        (username, email, hashed_password, 20, None)
    )
    db.commit()

    user_id = cursor.lastrowid
    token = jwt.encode({"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                       app.config["SECRET_KEY"], algorithm="HS256")
    cursor.execute("SELECT id, username, email, credits, subscription_expires FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    user["is_subscribed"] = _is_subscribed(user)
    cursor.close()

    return jsonify({"message": "Signup successful", "token": token, "user": user}), 201


@app.route("/login", methods=["POST"])
def login_route():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    if not all([email, password]):
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    user["is_subscribed"] = _is_subscribed(user)
    user.pop("password", None)
    token = jwt.encode({"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                       app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"message": "Login successful", "token": token, "user": user}), 200


@app.route("/profile", methods=["GET"])
def profile_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Invalid token or user not found"}), 401
    return jsonify({"user": user}), 200


@app.route("/google-login", methods=["POST"])
def google_login_route():
    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"error": "Google token missing"}), 400

    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), app.config["GOOGLE_CLIENT_ID"])
        email, name, picture = id_info.get("email"), id_info.get("name"), id_info.get("picture")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            hashed_password = generate_password_hash(secrets.token_hex(16))
            username = name or email.split("@")[0]
            cursor.execute(
                "INSERT INTO users (username, email, password, credits, subscription_expires) VALUES (%s, %s, %s, %s, %s)",
                (username, email, hashed_password, 20, None)
            )
            db.commit()
            user_id = cursor.lastrowid
            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cursor.fetchone()

        user["is_subscribed"] = _is_subscribed(user)
        user["picture"] = picture
        user.pop("password", None)

        app_token = jwt.encode({"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                               app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"message": "Google login successful", "token": app_token, "user": user}), 200

    except Exception as e:
        logging.error(f"Google login error: {e}")
        return jsonify({"error": "Google login failed"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)'''


# backend/app.py

'''from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env

import os
import logging
import uuid
import mysql.connector
import razorpay
from flask import Flask, request, jsonify, g, current_app
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Assuming your analysis functions are in this file
from analyze_image import analyze_file, analyze_video, analyze_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Configuration ---
class Config:
    # It's critical to use environment variables for secrets
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    UPLOAD_FOLDER = "uploads"
    #MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "avi", "mov", "mkv", "pdf", "docx", "txt"}

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD") # Rely on .env, no default
    DB_NAME = os.getenv("DB_NAME", "myapp")

    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# --- Application Factory ---
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Restrict origins in production for security
    CORS(app, supports_credentials=True, origins=os.getenv("FRONTEND_URL", "http://localhost:5173"))

    app.razorpay_client = razorpay.Client(
        auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"])
    )
    return app

app = create_app()

# --- Database Connection ---
def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=app.config["DB_HOST"],
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
            database=app.config["DB_NAME"],
        )
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# --- Helper Functions ---
def _is_subscribed(user_row):
    """Helper to check if a user's subscription is active."""
    expires_str = user_row.get("subscription_expires")
    if not expires_str:
        return False
    try:
        # Assuming expires_str is a datetime object from the DB
        return expires_str > datetime.datetime.utcnow()
    except TypeError: # Fallback if it's a string
        try:
            expires = datetime.datetime.strptime(str(expires_str), "%Y-%m-%d %H:%M:%S")
            return expires > datetime.datetime.utcnow()
        except:
            return False

def _get_user_and_check_subscription(user_id):
    """✅ RELIABLE HELPER: Fetches a user and calculates their subscription status."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        user["is_subscribed"] = _is_subscribed(user)
        user.pop("password", None)
    return user

def get_user_from_token():
    """Extracts user from token and uses the reliable helper."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return _get_user_and_check_subscription(data["user_id"])
    except Exception:
        return None'
def get_user_from_token():
    auth_header = request.headers.get('Authorization')
    logging.info(f"Authorization header: {auth_header}")

    if not auth_header or not auth_header.startswith("Bearer "):
        logging.warning("Authorization header missing or malformed")
        return None

    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data.get('user_id')
        if not user_id:
            logging.warning("Token missing user_id")
            return None

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            logging.warning(f"User not found: {user_id}")
            return None

        user['is_subscribed'] = _is_subscribed(user)
        user.pop('password', None)
        return user

    except jwt.ExpiredSignatureError:
        logging.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logging.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logging.error(f"Error decoding JWT: {e}")
        return None


# --- API Routes ---
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


''def _is_subscribed(user_row) -> bool:
    expires_str = user_row.get("subscription_expires")
    if not expires_str:
        return False
    try:
        expires = datetime.datetime.strptime(str(expires_str), "%Y-%m-%d %H:%M:%S")
        return expires > datetime.datetime.utcnow()
    except Exception:
        return False''


def get_user_from_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = data["user_id"]
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            return None
        user["is_subscribed"] = _is_subscribed(user)
        user.pop("password", None)
        return user
    except Exception:
        return None


def get_file_cost(filename: str) -> int:
    ext = filename.rsplit(".", 1)[1].lower()
    if ext in {"mp4", "avi", "mov", "mkv"}:
        return 5
    return 1


def save_temp_file(file) -> str:
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(temp_path)
    return temp_path


def read_temp_file_bytes(temp_path: str) -> bytes:
    with open(temp_path, "rb") as f:
        return f.read()
@app.route("/predict", methods=["POST"])
def predict_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if not file or file.filename.strip() == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify({"error": "Unsupported file type"}), 400

    cost = get_file_cost(filename)

    # Check subscription / credits
    if not user.get("is_subscribed", False):
        if user.get("credits", 0) < cost:
            return jsonify({"error": "Insufficient credits"}), 402
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE users SET credits = credits - %s WHERE id = %s", (cost, user["id"]))
            db.commit()
            cursor.close()
            logging.info(f"Deducted {cost} credits from user {user['id']}")
        except Exception as e:
            logging.error(f"Credit deduction failed for user {user['id']}: {e}")
            return jsonify({"error": "Failed to deduct credits"}), 500

    temp_path = save_temp_file(file)
    try:
        file_bytes = read_temp_file_bytes(temp_path)
        ext = filename.rsplit(".", 1)[1].lower()

        logging.info(f"User {user['id']} is analyzing a {ext} file.")

        if ext in {"jpg", "jpeg", "png"}:
            result = analyze_file(file_bytes, file.mimetype)
            result["type"] = "image"
        elif ext in {"mp4", "avi", "mov", "mkv"}:
            result = analyze_video(file_bytes)
            result["type"] = "video"
        elif ext in {"pdf", "docx", "txt"}:
            result = analyze_document(file_bytes)
            result["type"] = "document"
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Prediction error for user {user['id']}: {e}", exc_info=True)
        return jsonify({"error": "Internal analysis error"}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            logging.info(f"Temporary file {temp_path} deleted")


@app.route("/create-order", methods=["POST"])
def create_order_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401
    # ... (rest of the function is fine)
    data = request.get_json(); amount = int(data.get("amount", 0))
    if amount <= 0: return jsonify({"error": "Invalid amount"}), 400
    try:
        order = app.razorpay_client.order.create({ "amount": amount * 100, "currency": "INR", "payment_capture": 1 })
        return jsonify(order), 201
    except Exception as e:
        logging.error(f"Order creation failed: {e}")
        return jsonify({"error": "Order creation failed"}), 500

@app.route("/payment-success", methods=["POST"])
def payment_success_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401
    # ... (verification logic is fine)
    data = request.get_json();
    # ...
    try:
        app.razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": data.get("razorpay_order_id"),
            "razorpay_payment_id": data.get("razorpay_payment_id"),
            "razorpay_signature": data.get("razorpay_signature")
        })

        # Logic to extend subscription is good
        now = datetime.datetime.utcnow()
        current_expiry = user.get("subscription_expires")
        new_expiry = current_expiry + datetime.timedelta(days=30) if current_expiry and current_expiry > now else now + datetime.timedelta(days=30)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET subscription_expires=%s WHERE id=%s", (new_expiry, user["id"]))
        db.commit()
        cursor.close()

        # ✅ IMPROVED: Return the full, updated user object
        updated_user = _get_user_and_check_subscription(user["id"])
        return jsonify({"message": "Subscription activated!", "user": updated_user}), 200
    except Exception as e:
        logging.error(f"Payment error: {e}")
        return jsonify({"error": "Payment verification error"}), 500

@app.route("/signup", methods=["POST"])
def signup_route():
    data = request.get_json()
    username, email, password = data.get("username"), data.get("email"), data.get("password")
    if not all([username, email, password]) or len(password) < 6:
        return jsonify({"error": "All fields and a password of at least 6 characters are required"}), 400
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, email, password, credits) VALUES (%s, %s, %s, %s)",
        (username, email, hashed_password, 20)
    )
    db.commit()
    user_id = cursor.lastrowid
    
    token = jwt.encode({"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
    
    # ✅ FIXED: Use the reliable helper to get the new user data
    new_user = _get_user_and_check_subscription(user_id)
    cursor.close()

    return jsonify({"message": "Signup successful", "token": token, "user": new_user}), 201

@app.route("/login", methods=["POST"])
def login_route():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    if not all([email, password]):
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
    
    # ✅ Use the reliable helper to get complete user data
    logged_in_user = _get_user_and_check_subscription(user["id"])

    return jsonify({"message": "Login successful", "token": token, "user": logged_in_user}), 200

@app.route("/profile", methods=["GET"])
def profile_route():
    # ✅ This route is now much simpler and more reliable
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Invalid token or user not found"}), 401
    return jsonify({"user": user}), 200

@app.route("/google-login", methods=["POST"])
def google_login_route():
    data = request.get_json()
    token = data.get("token")
    if not token: return jsonify({"error": "Google token missing"}), 400
    
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), app.config["GOOGLE_CLIENT_ID"])
        email, name, picture = id_info.get("email"), id_info.get("name"), id_info.get("picture")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user_row = cursor.fetchone()

        if user_row:
            user_id = user_row["id"]
        else:
            hashed_password = generate_password_hash(secrets.token_hex(16))
            username = name or email.split("@")[0]
            cursor.execute("INSERT INTO users (username, email, password, credits) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, 20))
            db.commit()
            user_id = cursor.lastrowid
        
        user = _get_user_and_check_subscription(user_id)
        user["picture"] = picture # Add picture from Google

        app_token = jwt.encode({"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
        return jsonify({"message": "Google login successful", "token": app_token, "user": user}), 200
    except Exception as e:
        logging.error(f"Google login error: {e}")
        return jsonify({"error": "Google login failed"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)'''


from dotenv import load_dotenv
load_dotenv()

import os
import logging
import uuid
import mysql.connector
import razorpay
from flask import Flask, request, jsonify, g, current_app
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from analyze_image import analyze_file, analyze_video, analyze_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# --- Configuration ---
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "avi", "mov", "mkv", "pdf", "docx", "txt"}
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "myapp")
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


# --- Application Factory ---
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    CORS(app, supports_credentials=True, origins=os.getenv("FRONTEND_URL", "http://localhost:5173"))
    app.razorpay_client = razorpay.Client(
        auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"])
    )
    return app


app = create_app()


# --- Database Connection ---
def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=app.config["DB_HOST"],
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
            database=app.config["DB_NAME"],
        )
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# --- Helper Functions ---
def _is_subscribed(user_row):
    expires_str = user_row.get("subscription_expires")
    if not expires_str:
        return False
    try:
        return expires_str > datetime.datetime.utcnow()
    except TypeError:
        try:
            expires = datetime.datetime.strptime(str(expires_str), "%Y-%m-%d %H:%M:%S")
            return expires > datetime.datetime.utcnow()
        except:
            return False


def _get_user_and_check_subscription(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        user["is_subscribed"] = _is_subscribed(user)
        user.pop("password", None)
    return user


def get_user_from_token():
    auth_header = request.headers.get("Authorization")
    logging.info(f"Authorization header: {auth_header}")
    if not auth_header or not auth_header.startswith("Bearer "):
        logging.warning("Authorization header missing or malformed")
        return None
    token = auth_header.split(" ")[1]
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return _get_user_and_check_subscription(data.get("user_id"))
    except Exception as e:
        logging.error(f"Error decoding JWT: {e}")
        return None


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def get_file_cost(filename: str) -> int:
    ext = filename.rsplit(".", 1)[1].lower()
    return 5 if ext in {"mp4", "avi", "mov", "mkv"} else 1


def save_temp_file(file) -> str:
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(temp_path)
    return temp_path


def read_temp_file_bytes(temp_path: str) -> bytes:
    with open(temp_path, "rb") as f:
        return f.read()


# --- Routes ---
@app.route("/predict", methods=["POST"])
def predict_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    file = request.files["file"]
    if not file or file.filename.strip() == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify({"error": "Unsupported file type"}), 400

    cost = get_file_cost(filename)
    if not user.get("is_subscribed", False) and user.get("credits", 0) < cost:
        return jsonify({"error": "Insufficient credits"}), 402

    if not user.get("is_subscribed", False):
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE users SET credits = credits - %s WHERE id = %s", (cost, user["id"]))
            db.commit()
            cursor.close()
            logging.info(f"Deducted {cost} credits from user {user['id']}")
        except Exception as e:
            logging.error(f"Credit deduction failed for user {user['id']}: {e}")
            return jsonify({"error": "Failed to deduct credits"}), 500

    temp_path = save_temp_file(file)
    try:
        file_bytes = read_temp_file_bytes(temp_path)
        ext = filename.rsplit(".", 1)[1].lower()

        logging.info(f"User {user['id']} is analyzing a {ext} file.")
        if ext in {"jpg", "jpeg", "png"}:
            result = analyze_file(file_bytes, file.mimetype)
            result["type"] = "image"
        elif ext in {"mp4", "avi", "mov", "mkv"}:
            result = analyze_video(file_bytes)
            result["type"] = "video"
        elif ext in {"pdf", "docx", "txt"}:
            result = analyze_document(file_bytes)
            result["type"] = "document"
        else:
            return jsonify({"error": "Unsupported file type"}), 400
        return jsonify(result)
    except Exception as e:
        logging.error(f"Prediction error for user {user['id']}: {e}", exc_info=True)
        return jsonify({"error": "Internal analysis error"}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            logging.info(f"Temporary file {temp_path} deleted")


@app.route("/create-order", methods=["POST"])
def create_order_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    amount = int(data.get("amount", 799))
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        order = app.razorpay_client.order.create({
            "amount": amount * 100,
            "currency": "INR",
            "payment_capture": 1
        })
        return jsonify(order), 201
    except Exception as e:
        logging.error(f"Order creation failed: {e}")
        return jsonify({"error": "Order creation failed"}), 500


@app.route("/payment-success", methods=["POST"])
def payment_success_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    try:
        app.razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": data.get("razorpay_order_id"),
            "razorpay_payment_id": data.get("razorpay_payment_id"),
            "razorpay_signature": data.get("razorpay_signature")
        })

        now = datetime.datetime.utcnow()
        current_expiry = user.get("subscription_expires")
        new_expiry = current_expiry + datetime.timedelta(days=30) if current_expiry and current_expiry > now else now + datetime.timedelta(days=30)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET subscription_expires=%s WHERE id=%s", (new_expiry, user["id"]))
        db.commit()
        cursor.close()

        updated_user = _get_user_and_check_subscription(user["id"])
        return jsonify({"message": "Subscription activated!", "user": updated_user}), 200
    except Exception as e:
        logging.error(f"Payment error: {e}")
        return jsonify({"error": "Payment verification error"}), 500


@app.route("/signup", methods=["POST"])
def signup_route():
    data = request.get_json()
    username, email, password = data.get("username"), data.get("email"), data.get("password")
    if not all([username, email, password]) or len(password) < 6:
        return jsonify({"error": "All fields and password min length 6 required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, email, password, credits) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, 20))
    db.commit()
    user_id = cursor.lastrowid
    token = jwt.encode({"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
    new_user = _get_user_and_check_subscription(user_id)
    cursor.close()
    return jsonify({"message": "Signup successful", "token": token, "user": new_user}), 201


@app.route("/login", methods=["POST"])
def login_route():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    if not all([email, password]):
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
    logged_in_user = _get_user_and_check_subscription(user["id"])
    return jsonify({"message": "Login successful", "token": token, "user": logged_in_user}), 200


@app.route("/profile", methods=["GET"])
def profile_route():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Invalid token or user not found"}), 401
    return jsonify({"user": user}), 200


@app.route("/google-login", methods=["POST"])
def google_login_route():
    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"error": "Google token missing"}), 400
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), app.config["GOOGLE_CLIENT_ID"])
        email, name, picture = id_info.get("email"), id_info.get("name"), id_info.get("picture")
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user_row = cursor.fetchone()

        if user_row:
            user_id = user_row["id"]
        else:
            hashed_password = generate_password_hash(secrets.token_hex(16))
            username = name or email.split("@")[0]
            cursor.execute("INSERT INTO users (username, email, password, credits) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, 20))
            db.commit()
            user_id = cursor.lastrowid

        user = _get_user_and_check_subscription(user_id)
        user["picture"] = picture
        app_token = jwt.encode({"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
        return jsonify({"message": "Google login successful", "token": app_token, "user": user}), 200
    except Exception as e:
        logging.error(f"Google login error: {e}")
        return jsonify({"error": "Google login failed"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
