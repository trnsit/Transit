import urllib.parse

import httpx

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.modules.accounts.dependencies import get_current_user
from app.modules.accounts.models import User, UserOAuthToken
from app.security.jwt import create_access_token, decode_access_token

router = APIRouter(prefix='/auth/github', tags=['github-oauth'])

@router.get('/login')
async def get_github_login_url(current_user: User = Depends(get_current_user)):
    """ Generate the GitHub authorization URL. We securely embed the logged-in
    user's email in the 'state' parameter to identify them on the callback. """

    # Create a short-lived token to use as the state parameter
    state_token = create_access_token(data={'sub': current_user.email})
    
    params = {
        'client_id': settings.github_client_id,
        'redirect_uri': settings.github_redirect_uri,
        'scope': 'repo read:user', # 'repo' scope is needed to scan private repos
        'state': state_token
    }
    
    authorization_url = f'https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}'
    return {'url': authorization_url}

@router.get('/callback')
async def github_callback(code: str, state: str, db: AsyncSession = Depends(get_session)):
    # Handle the redirect callback from GitHub.

    # 1. Decode and verify the state parameter to find the local user
    payload = decode_access_token(state)
    if not payload or not payload.get('sub'):
        raise HTTPException(status_code=400, detail='Invalid state parameter.')
    
    email = payload['sub']
    
    # Retrieve user from database
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='User not found.')
        
    # 2. Exchange the Authorization Code for an Access Token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': settings.github_client_id,
                'client_secret': settings.github_client_secret,
                'code': code,
                'redirect_uri': settings.github_redirect_uri,
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail='Failed to retrieve token from GitHub.')
            
                # Exchange response parsing
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail=f"GitHub authorization failed: {token_data.get('error_description', 'No access token received')}"
            )
            
    # Determine expiration datetime
    expires_at = None
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    # 3. Store or update the token in the database
    token_query = await db.execute(
        select(UserOAuthToken).where(
            UserOAuthToken.user_id == user.id,
            UserOAuthToken.provider == 'github'
        )
    )
    oauth_token = token_query.scalar_one_or_none()
    
    if oauth_token:
        oauth_token.access_token = access_token
        if refresh_token:
            oauth_token.refresh_token = refresh_token
        oauth_token.expires_at = expires_at
    else:
        oauth_token = UserOAuthToken(
            user_id=user.id,
            provider='github',
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(oauth_token)
        
    await db.commit()
    
    # 4. Redirect the user back to the frontend dashboard (adjust URL if needed)
    return RedirectResponse(url='http://localhost:3000/dashboard')
