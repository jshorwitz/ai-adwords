"""Agent orchestration system for cross-channel ads platform."""

try:
    from .multi_platform_agents import register_multi_platform_agents
    from .runner import agent_registry
    
    # Register multi-platform agents if available
    register_multi_platform_agents(agent_registry)
    
except ImportError:
    # Multi-platform agents not available
    pass

__all__ = ["agent_registry"]
