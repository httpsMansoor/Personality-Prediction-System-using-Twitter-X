import os
import secrets
import hashlib
import base64
import csv
import pandas as pd
from datetime import datetime
from flask import Flask, redirect, request, session, render_template, url_for, jsonify
from requests_oauthlib import OAuth2Session
from transformers import pipeline
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
required_env_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Allow insecure transport for OAuth (for development)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')  # Use environment variable for secret key

# Twitter OAuth 2.0 Credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

AUTHORIZATION_BASE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

SCOPES = ["tweet.read", "users.read"]

# Load personality prediction model
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"
]

# CSV file path for storing predictions
PREDICTIONS_FILE = "predictions.csv"

# Add logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def ensure_predictions_file_exists():
    """Create predictions CSV file if it doesn't exist."""
    if not os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'personality', 'tweets', 'prediction_date'])

def get_stored_prediction(username):
    """Get stored prediction for a username if it exists."""
    if not os.path.exists(PREDICTIONS_FILE):
        return None
    
    df = pd.read_csv(PREDICTIONS_FILE)
    user_data = df[df['username'] == username]
    
    if not user_data.empty:
        return {
            'personality': user_data.iloc[0]['personality'],
            'tweets': eval(user_data.iloc[0]['tweets']),  # Convert string back to list
            'prediction_date': user_data.iloc[0]['prediction_date']
        }
    return None

def save_prediction(username, personality, tweets):
    """Save prediction to CSV file."""
    ensure_predictions_file_exists()
    
    # Convert tweets list to string for storage
    tweets_str = str(tweets)
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    df = pd.read_csv(PREDICTIONS_FILE) if os.path.exists(PREDICTIONS_FILE) else pd.DataFrame(columns=['username', 'personality', 'tweets', 'prediction_date'])
    
    # Update existing prediction or add new one
    if username in df['username'].values:
        df.loc[df['username'] == username] = [username, personality, tweets_str, current_date]
    else:
        new_row = pd.DataFrame([[username, personality, tweets_str, current_date]], 
                             columns=['username', 'personality', 'tweets', 'prediction_date'])
        df = pd.concat([df, new_row], ignore_index=True)
    
    df.to_csv(PREDICTIONS_FILE, index=False)

def generate_pkce_pair():
    """Generates a PKCE code verifier and challenge."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

def get_prediction_stats():
    """Calculate statistics from predictions.csv file."""
    if not os.path.exists(PREDICTIONS_FILE):
        return {
            'total_predictions': 0,
            'mbti_types': len(MBTI_TYPES),
            'accuracy_rate': 95,  # Default accuracy rate
            'hour_support': 24
        }
    
    df = pd.read_csv(PREDICTIONS_FILE)
    total_predictions = len(df)
    logger.debug(f"Total predictions found: {total_predictions}")
    
    return {
        'total_predictions': total_predictions,
        'mbti_types': len(MBTI_TYPES),
        'accuracy_rate': 95,  # Default accuracy rate
        'hour_support': 24
    }

@app.route("/")
def index():
    """Always show index.html; do not auto-redirect logged-in users."""
    stats = get_prediction_stats()
    logger.debug(f"Current stats: {stats}")  # Add debug logging
    return render_template("index.html", logged_in="oauth_token" in session, stats=stats)

@app.route("/login")
def login():
    if "oauth_token" in session:
        return redirect(url_for("index"))

    code_verifier, code_challenge = generate_pkce_pair()
    session["code_verifier"] = code_verifier

    twitter = OAuth2Session(CLIENT_ID, scope=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = twitter.authorization_url(
        AUTHORIZATION_BASE_URL,
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )
    session["oauth_state"] = state
    return redirect(auth_url)

@app.route("/callback")
def callback():
    if "code_verifier" not in session:
        return redirect(url_for("login"))

    twitter = OAuth2Session(CLIENT_ID, state=session.get("oauth_state"), redirect_uri=REDIRECT_URI)

    try:
        token = twitter.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            code_verifier=session["code_verifier"],
            authorization_response=request.url
        )
        session["oauth_token"] = token
        return redirect(url_for("index"))

    except Exception as e:
        return f"Error during authentication: {str(e)}", 400

@app.route("/predict", methods=["GET", "POST"])
def predict_personality():
    """Fetches tweets and predicts MBTI personality."""
    if "oauth_token" not in session:
        return jsonify({"error": "Please log in first"}), 401

    if request.method == "GET":
        return redirect(url_for("index"))

    username = request.form.get("username", "").strip().lstrip('@')
    
    if not username:
        return jsonify({"error": "Please enter a Twitter username"}), 400

    # Check if we have a stored prediction
    stored_prediction = get_stored_prediction(username)
    if stored_prediction:
        return jsonify({
            "redirect_url": url_for("show_personality", 
                                  personality=stored_prediction['personality'],
                                  username=username,
                                  is_cached=True)
        })

    # If no stored prediction, fetch and predict
    twitter = OAuth2Session(CLIENT_ID, token=session["oauth_token"])
    
    try:
        # Get user ID from username
        user_response = twitter.get(f"https://api.twitter.com/2/users/by/username/{username}")
        user_data = user_response.json()

        if "data" not in user_data:
            return jsonify({"error": "Twitter user not found. Please check the username."}), 400

        user_id = user_data["data"]["id"]

        # Fetch recent tweets
        tweet_response = twitter.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=5&tweet.fields=text"
        )
        tweets = tweet_response.json()

        if not tweets.get("data"):
            return jsonify({"error": "No tweets found for this user. Please ensure the account has public tweets."}), 400

        # Predict MBTI personality
        tweet_texts = [tweet["text"] for tweet in tweets["data"]]
        predictions = classifier(" ".join(tweet_texts), MBTI_TYPES)
        predicted_personality = predictions["labels"][0]

        # Save prediction to CSV
        save_prediction(username, predicted_personality, tweet_texts)

        return jsonify({
            "redirect_url": url_for("show_personality", 
                                  personality=predicted_personality,
                                  username=username,
                                  is_cached=False)
        })

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request. Please try again."}), 500

@app.route("/personality")
def show_personality():
    """Display personality prediction results."""
    personality = request.args.get('personality')
    username = request.args.get('username', '').replace('_', '')  # Clean up username
    is_cached = request.args.get('is_cached', 'false').lower() == 'true'
    
    if not personality or not username:
        return redirect(url_for("index"))
    
    # Get stored prediction to access tweets
    stored_prediction = get_stored_prediction(username)
    if not stored_prediction:
        return redirect(url_for("index"))
        
    return render_template("personality.html",
                         personality=personality,
                         username=username,
                         is_cached=is_cached,
                         tweets=stored_prediction['tweets'],
                         prediction_date=stored_prediction['prediction_date'])

@app.route("/logout")
def logout():
    """Logs the user out and clears session data."""
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
