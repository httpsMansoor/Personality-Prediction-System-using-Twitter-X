import os
import logging
from flask import Flask, redirect, request, session, render_template, url_for, jsonify
from auth import generate_pkce_pair
from twitter import TwitterService
from prediction import (
    get_stored_prediction,
    save_prediction,
    predict_personality,
    get_prediction_stats
)
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

@app.route("/")
def index():
    """Homepage with a login link."""
    stats = get_prediction_stats()
    logged_in = "oauth_token" in session
    return render_template("index.html", stats=stats, logged_in=logged_in)

@app.route("/login")
def login():
    """Handles Twitter OAuth login."""
    if "oauth_token" in session:
        return redirect(url_for("index"))

    code_verifier, code_challenge = generate_pkce_pair()
    session["code_verifier"] = code_verifier

    twitter = TwitterService()
    auth_url = twitter.get_authorization_url(code_challenge)
    return redirect(auth_url)

@app.route("/callback")
def callback():
    """Handles OAuth callback."""
    if "code_verifier" not in session:
        return redirect(url_for("login"))

    twitter = TwitterService()
    try:
        token = twitter.fetch_token(
            session["code_verifier"],
            request.url
        )
        session["oauth_token"] = token
        return redirect(url_for("index"))
    except Exception as e:
        return f"Error during authentication: {str(e)}", 400

@app.route("/predict", methods=["GET", "POST"])
def predict_personality_route():
    """Fetches tweets and predicts MBTI personality."""
    if "oauth_token" not in session:
        return jsonify({"error": "Please log in first"}), 401

    if request.method == "GET":
        return redirect(url_for("index"))

    username = request.form.get("username", "").strip().lstrip('@')
    force_refresh = request.form.get("force_refresh", "false").lower() == "true"
    
    if not username:
        return jsonify({"error": "Please enter a Twitter username"}), 400

    # Check if we have a stored prediction and not forcing refresh
    if not force_refresh:
        stored_prediction = get_stored_prediction(username)
        if stored_prediction:
            return jsonify({
                "redirect_url": url_for("show_personality", 
                                      personality=stored_prediction['personality'],
                                      username=username,
                                      is_cached=True),
                "progress": 100,
                "status": "Using cached prediction",
                "step": 4
            })

    # If no stored prediction or force refresh, fetch and predict
    twitter = TwitterService(token=session["oauth_token"])
    
    try:
        # Get user ID from username
        user_data = twitter.get_user_by_username(username)

        if "data" not in user_data:
            return jsonify({"error": "Twitter user not found. Please check the username."}), 400

        user_id = user_data["data"]["id"]

        # Fetch recent tweets
        tweets = twitter.get_user_tweets(user_id)

        if not tweets.get("data"):
            return jsonify({"error": "No tweets found for this user. Please ensure the account has public tweets."}), 400

        # Predict MBTI personality
        tweet_texts = [tweet["text"] for tweet in tweets["data"]]
        predicted_personality = predict_personality(tweet_texts)

        # Save prediction to CSV
        save_prediction(username, predicted_personality, tweet_texts)

        return jsonify({
            "redirect_url": url_for("show_personality", 
                                  personality=predicted_personality,
                                  username=username,
                                  is_cached=False),
            "progress": 100,
            "status": "Analysis complete",
            "step": 4
        })

    except Exception as e:
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