from fastapi import status


class AuthException(Exception):
    """Base class of all JWT Exceptions"""

    pass


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
