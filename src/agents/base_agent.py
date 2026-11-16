"""
OmniSupport AI - Base Agent Class
==================================
Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import AGENT_CONFIG


@dataclass
class AgentResult:
    """
    Result from an agent's execution.

    Attributes:
        agent_name: Name of the agent
        success: Whether the agent completed successfully
        data: The agent's output data
        metadata: Additional information (timing, confidence, etc.)
        error: Error message if failed
    """
    agent_name: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self):
        """Add timestamp if not present."""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now().isoformat()


class BaseAgent(ABC):
    """
    Base class for all OmniSupport agents.

    Each agent is responsible for one specific task in the
    customer support pipeline.
    """

    def __init__(self, agent_type: str):
        """
        Initialize the agent.

        Args:
            agent_type: Agent type key from AGENT_CONFIG
        """
        self.agent_type = agent_type
        self.config = AGENT_CONFIG.get(agent_type, {})
        self.name = self.config.get("name", agent_type)
        self.description = self.config.get("description", "")
        self.icon = self.config.get("icon", "🤖")

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's task.

        Args:
            context: Input context containing:
                - complaint: User's complaint text
                - order_id: Order ID (if provided)
                - customer_id: Customer ID (if provided)
                - previous_results: Results from previous agents

        Returns:
            AgentResult with the agent's output
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """Get agent information."""
        return {
            "type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "icon": self.icon
        }

    def log(self, message: str, level: str = "INFO"):
        """
        Log a message with agent context.

        Args:
            message: The log message
            level: Log level (INFO, WARNING, ERROR)
        """
        print(f"[{self.icon} {self.name}] {level}: {message}")
