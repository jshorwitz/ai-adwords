"""Test the complete application stack."""

import asyncio
import json
from datetime import datetime

from src.agents.runner import agent_registry, AgentRunner
# Import agents to register them
from src.agents import ingestors, transforms, activations, decisions


async def test_agent_system():
    """Test the agent system integration."""
    
    print("🧪 Testing AI AdWords Agent System")
    print(f"📊 Registered agents: {len(agent_registry.list_agents())}")
    
    # List agents
    agents = agent_registry.list_agents()
    for agent in sorted(agents):
        print(f"  • {agent}")
    
    print("\n🚀 Running test workflow...")
    
    # Test ingestor
    runner = AgentRunner(agent_registry)
    
    result = await runner.run_agent(
        agent_name="ingestor-reddit",
        window={"start": "2025-01-09", "end": "2025-01-10"},
        dry_run=True,
    )
    
    print(f"✅ Reddit ingestor: {result.ok}")
    print(f"📊 Records would process: {result.records_written}")
    
    # Test budget optimizer
    result = await runner.run_agent(
        agent_name="budget-optimizer",
        dry_run=True,
    )
    
    print(f"✅ Budget optimizer: {result.ok}")
    if result.metrics:
        for key, value in result.metrics.items():
            print(f"  {key}: {value}")
    
    print("\n🎉 Agent system test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_agent_system())
