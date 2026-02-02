"""
Core Interfaces Module

Abstract base classes defining contracts for all services.
Architect/Mason define interfaces here for consistent patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IdeaSource(ABC):
    """Interface for idea generation sources."""
    
    @abstractmethod
    def generate(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate an idea from this source.
        
        Args:
            context: Optional context for idea generation
            
        Returns:
            Dictionary containing idea details (title, description, etc.)
        """
        pass


class RepositoryCreator(ABC):
    """Interface for repository creation services."""
    
    @abstractmethod
    def create(self, name: str, description: str, **options) -> str:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            **options: Additional options (private, template, etc.)
            
        Returns:
            URL of the created repository
        """
        pass


class SessionManager(ABC):
    """Interface for managing agent sessions."""
    
    @abstractmethod
    def create_session(self, repo_url: str, prompt: str) -> str:
        """
        Create a new agent session.
        
        Args:
            repo_url: URL of the repository to work on
            prompt: Initial prompt for the session
            
        Returns:
            Session ID
        """
        pass
    
    @abstractmethod
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current status of a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary containing session status details
        """
        pass


class ContentExtractor(ABC):
    """Interface for extracting content from various sources."""
    
    @abstractmethod
    def extract(self, source: str) -> str:
        """
        Extract content from a source.
        
        Args:
            source: URL or path to extract from
            
        Returns:
            Extracted text content
        """
        pass


# Type aliases for common return types
IdeaDict = Dict[str, Any]
SessionStatus = Dict[str, Any]
