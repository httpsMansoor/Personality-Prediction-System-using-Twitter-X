Twitter Personality Analyzer

A Flask-based web application that analyzes Twitter users' personalities using their tweets and predicts their MBTI personality type.

Features:
- Twitter OAuth 2.0 authentication
- Fetches recent tweets from any public Twitter profile
- Uses BART-large-MNLI model for personality prediction
- Caches predictions for faster repeated analysis
- Beautiful and responsive UI
- Real-time personality analysis
- Displays analyzed tweets and prediction confidence

Setup Instructions:
1. Clone the repository
2. Create a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install dependencies:
   pip install -r requirements.txt
4. Create a .env file with the following variables:
   CLIENT_ID=your_twitter_client_id
   CLIENT_SECRET=your_twitter_client_secret
   REDIRECT_URI=your_redirect_uri
   SECRET_KEY=your_flask_secret_key
5. Run the application:
   python app.py

Environment Variables:
- CLIENT_ID: Twitter API Client ID
- CLIENT_SECRET: Twitter API Client Secret
- REDIRECT_URI: OAuth callback URL
- SECRET_KEY: Flask application secret key

Project Structure:
- app.py: Main Flask application
- templates/: HTML templates
  - index.html: Home page with login and analysis form
  - personality.html: Results page showing personality prediction
- static/: Static assets (CSS, JS, images)
- predictions.csv: Cached predictions database

Dependencies:
- Flask: Web framework
- requests_oauthlib: OAuth 2.0 client
- transformers: NLP model for personality prediction
- python-dotenv: Environment variable management
- pandas: Data handling for predictions storage
- torch: Required for transformers

Security Notes:
- Never commit your .env file
- Keep your API credentials secure
- Use HTTPS in production
- Implement rate limiting for API calls

License:
MIT License

Author:
[Mansoor Akhtr]

Version:
1.0.0 
