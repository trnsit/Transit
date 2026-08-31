import urllib.parse
from datetime import datetime, timedelta, timezone
import httpx
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.modules.accounts.models import User, UserOAuthToken
from app.security.jwt import create_access_token, decode_access_token
from app.security.password import hash_password

router = APIRouter(prefix='/auth/google', tags=['google-oauth'])

@router.get('/login')
async def get_google_login_url():
    """ Generate the Google authorization URL.
    We sign a state token to protect against CSRF. """

    state_token = create_access_token(
        data={'purpose': 'google_state'}, 
        expires_delta=timedelta(minutes=10)
    )

    params = {
        'client_id': settings.google_client_id,
        'redirect_uri': settings.google_redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state_token,
        'access_type': 'offline', # Request refresh token
        'prompt': 'select_account'
    }

    authorization_url = f'https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}'
    return {'url': authorization_url}

@router.get('/callback')
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_session)
):
    # Handle the redirect callback from Google.

    # 1. Verify the state parameter to prevent CSRF
    payload = decode_access_token(state)
    if not payload or payload.get('purpose') != 'google_state':
        raise HTTPException(status_code=400, detail='Invalid or expired state parameter.')

    # 2. Exchange the Authorization Code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': settings.google_client_id,
                'client_secret': settings.google_client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.google_redirect_uri,
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to retrieve token from Google.')

        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        
        if not access_token:
            raise HTTPException(status_code=400, detail='No access token received from Google.')

        # 3. Retrieve User Profile from Google userinfo API
        userinfo_response = await client.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to fetch user info from Google.')

        userinfo = userinfo_response.json()
        email = userinfo.get('email')

        if not email:
            raise HTTPException(status_code=400, detail='Google account has no email address.')

    # 4. Check if user already exists in local database
    user_query = await db.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()

    if not user:
        # Create a new user since they are signing up via Google

        # Generate a secure random password as they authenticate via SSO
        random_password = secrets.token_urlsafe(32)
        password_hash = hash_password(random_password)

        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True
        )
        db.add(user)
        await db.flush() # Populates user.id without committing

    # 5. Store or update the Google OAuth credentials
    token_query = await db.execute(
        select(UserOAuthToken).where(
            UserOAuthToken.user_id == user.id,
            UserOAuthToken.provider == 'google'
        )
    )
    oauth_token = token_query.scalar_one_or_none()

    expires_at = None
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    if oauth_token:
        oauth_token.access_token = access_token
        if refresh_token:
            oauth_token.refresh_token = refresh_token
        oauth_token.expires_at = expires_at

    else:
        oauth_token = UserOAuthToken(
            user_id=user.id,
            provider='google',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(oauth_token)

    await db.commit()

    # 6. Generate our own local JWT access token for this user
    local_access_token = create_access_token(data={'sub': user.email})

    # Redirect back to the frontend login-success handler page
    return RedirectResponse(
        url=f'http://localhost:3000/login-success?token={local_access_token}'
    )
