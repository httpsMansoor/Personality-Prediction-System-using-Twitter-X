import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
required_env_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Allow insecure transport for OAuth (for development)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Twitter OAuth 2.0 Credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

# OAuth URLs
AUTHORIZATION_BASE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# OAuth Scopes
SCOPES = ["tweet.read", "users.read"]

# MBTI Types
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"
]

# File paths
PREDICTIONS_FILE = "predictions.csv" 