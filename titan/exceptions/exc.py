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


class PasswordTooSmall(Exception):
    pass


class Oauth2AuthError(AuthException):
    pass


class OAuth2EmailPrivdedError(AuthException):
    pass


class DatabaseUserFetchError(AuthException):
    pass
