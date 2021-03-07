from typing import Optional


class AuthException(Exception):
    def __init__(self, message: str = "AuthException happened"):
        super().__init__(message)


class JWTDecodeError(AuthException):
    pass


class JWTInvalidToken(AuthException):
    pass


class AccessTokenRequired(AuthException):
    pass


class RefreshTokenRequired(AuthException):
    pass


class FreshTokenRequired(AuthException):
    pass


class RevokedAccessToken(AuthException):
    pass


class RevokedRefreshToken(AuthException):
    pass


class RevokedFreshToken(AuthException):
    pass


class PasswordTooSmall(Exception):
    pass


class JSONEncodeError(AuthException):
    pass


class JSONDecodeError(AuthException):
    pass


class Oauth2AuthorizationError(AuthException):
    pass


class OAuth2MissingScope(AuthException):
    pass


class OAuth2EmailPrivdedError(AuthException):
    pass


class OAuth2MissingInfo(AuthException):
    pass
