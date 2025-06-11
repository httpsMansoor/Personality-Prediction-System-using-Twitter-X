from requests_oauthlib import OAuth2Session
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, AUTHORIZATION_BASE_URL, TOKEN_URL, SCOPES

class TwitterService:
    def __init__(self, token=None):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_uri = REDIRECT_URI
        self.token = token
        self.oauth = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            scope=SCOPES,
            token=self.token
        )

    def get_authorization_url(self, code_challenge):
        """Get Twitter authorization URL."""
        return self.oauth.authorization_url(
            AUTHORIZATION_BASE_URL,
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )[0]

    def fetch_token(self, code_verifier, authorization_response):
        """Fetch OAuth token."""
        return self.oauth.fetch_token(
            TOKEN_URL,
            client_secret=self.client_secret,
            code_verifier=code_verifier,
            authorization_response=authorization_response
        )

    def get_user_by_username(self, username):
        """Get user data by username."""
        response = self.oauth.get(f"https://api.twitter.com/2/users/by/username/{username}")
        return response.json()

    def get_user_tweets(self, user_id):
        """Get user's recent tweets."""
        response = self.oauth.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=5&tweet.fields=text"
        )
        return response.json() 