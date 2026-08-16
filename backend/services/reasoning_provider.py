from abc import ABC, abstractmethod




class ReasoningProviderError(Exception):
    """Base exception for clinical reasoning provider failures."""


class ReasoningUnavailableError(ReasoningProviderError):
    """Raised when the configured reasoning provider is unavailable."""


class ReasoningInvalidResponseError(ReasoningProviderError):
    """Raised when a provider returns an invalid reasoning response."""


class ReasoningProvider(ABC):

    @abstractmethod
    async def generate_reasoning(
        self,
        prompt: str,
    ) -> str:
        raise NotImplementedError
