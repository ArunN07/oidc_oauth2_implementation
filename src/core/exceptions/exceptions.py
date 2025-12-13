
class BaseAppException(Exception):
    """
    Base exception for application errors.

    All custom exceptions inherit from this class to provide
    a consistent interface.

    Attributes
    ----------
    message : str
        Human-readable error message.
    detail : str, optional
        Additional error details.
    """

    def __init__(self, message: str, detail: str | None = None):
        """
        Initialize the exception.

        Parameters
        ----------
        message : str
            Human-readable error message.
        detail : str, optional
            Additional error details.
        """
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class AuthError(BaseAppException):
    """
    Exception for authentication errors.

    Raised when authentication fails due to invalid credentials,
    expired tokens, or authorization failures.
    """

    def __init__(self, message: str = "Authentication failed", detail: str | None = None):
        """
        Initialize authentication error.

        Parameters
        ----------
        message : str, optional
            Error message (default: "Authentication failed").
        detail : str, optional
            Additional error details.
        """
        super().__init__(message=message, detail=detail)


class ConfigError(BaseAppException):
    """
    Exception for configuration errors.

    Raised when required configuration is missing or invalid.
    """

    def __init__(self, message: str = "Configuration error", detail: str | None = None):
        """
        Initialize configuration error.

        Parameters
        ----------
        message : str, optional
            Error message (default: "Configuration error").
        detail : str, optional
            Additional error details.
        """
        super().__init__(message=message, detail=detail)


class ProviderNotSupportedError(BaseAppException):
    """
    Exception when an unsupported provider is requested.

    Raised when the user requests an authentication provider
    that is not implemented or configured.

    Attributes
    ----------
    provider : str
        The requested provider name.
    supported_providers : list[str]
        List of supported provider names.
    """

    def __init__(self, provider: str, supported_providers: list[str] | None = None):
        """
        Initialize provider not supported error.

        Parameters
        ----------
        provider : str
            The requested unsupported provider.
        supported_providers : list[str], optional
            List of supported providers.
        """
        supported = supported_providers or ["github", "azure", "google"]
        message = f"Provider '{provider}' is not supported. Supported: {', '.join(supported)}"
        super().__init__(message=message, detail=f"Unsupported provider: {provider}")
        self.provider = provider
        self.supported_providers = supported


class TokenValidationError(AuthError):
    """Exception for token validation failures."""

    def __init__(self, message: str = "Token validation failed", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class TokenExpiredError(AuthError):
    """Exception when token has expired."""

    def __init__(self, message: str = "Token has expired", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class InvalidCredentialsError(AuthError):
    """Exception for invalid credentials."""

    def __init__(self, message: str = "Invalid credentials", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class OAuth2CallbackError(AuthError):
    """Exception for OAuth2 callback errors."""

    def __init__(self, message: str = "OAuth2 callback failed", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class UserNotFoundError(AuthError):
    """Exception when user information cannot be retrieved."""

    def __init__(self, message: str = "User not found", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class MissingConfigurationError(ConfigError):
    """Exception when required configuration is missing."""

    def __init__(self, config_key: str):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message=message, detail=config_key)
        self.config_key = config_key


class DatabaseException(BaseAppException):
    """Base exception for database errors."""

    def __init__(self, message: str = "Database error", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class DatabaseConnectionError(DatabaseException):
    """Exception for database connection failures."""

    def __init__(self, message: str = "Failed to connect to database", detail: str | None = None):
        super().__init__(message=message, detail=detail)
