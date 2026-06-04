class PipelineError(RuntimeError):
    """Base pipeline error."""


class DiscoveryError(PipelineError):
    """Raised when provider endpoints are unavailable."""


class NormalizeError(PipelineError):
    """Raised when payload structure is invalid."""
