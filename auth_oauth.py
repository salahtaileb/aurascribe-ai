from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError
import os

# Skeleton OIDC config — remplacer par IdP prod (Keycloak / Azure AD / Auth0)
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "https://example-issuer/")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "aura-client")
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{OIDC_ISSUER}/authorize",
    tokenUrl=f"{OIDC_ISSUER}/token",
    scopes={"emr.write": "Ecrire dans l'EMR", "scribe.read": "Lire sorties scribe"}
)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # En prod : récupérer JWKS et valider signature RS256
        pub = os.getenv("OIDC_PUBLIC_KEY") or os.getenv("OIDC_CLIENT_SECRET")
        payload = jwt.decode(token, pub, algorithms=["RS256"], audience=OIDC_CLIENT_ID, issuer=OIDC_ISSUER)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Jeton invalide") from e

def require_scope(required_scope: str):
    async def dep(token_payload: dict = Depends(verify_token)):
        scopes = token_payload.get("scope", "")
        if isinstance(scopes, str):
            scopes = scopes.split()
        if required_scope not in scopes:
            raise HTTPException(status_code=403, detail="Accès refusé: scope manquant")
        return token_payload
    return dep