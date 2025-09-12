"""Agent-focused CLI interface for agent orchestration and management."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .agents.runner import agent_registry, AgentRunner

app = typer.Typer(help="AI AdWords Agent Management CLI")
console = Console()
logger = logging.getLogger(__name__)


@app.command("list")
def list_agents():
    """List all available agents."""
    try:
        agents = agent_registry.list_agents()
        
        if not agents:
            console.print("No agents registered", style="yellow")
            return
        
        table = Table(title="Available Agents")
        table.add_column("Agent Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Description", style="white")
        
        # Categorize agents by type with descriptions
        agent_info = {
            "ingestor-google": ("Ingestor", "Pull Google Ads metrics via GAQL"),
            "ingestor-reddit": ("Ingestor", "Pull Reddit Ads metrics (mockable)"),  
            "ingestor-x": ("Ingestor", "Pull X/Twitter Ads metrics (mockable)"),
            "touchpoint-extractor": ("Transform", "Extract touchpoints from events"),
            "conversion-uploader": ("Activation", "Upload conversions to platforms"),
            "budget-optimizer": ("Decision", "Optimize campaign budgets based on CAC/ROAS"),
            "keywords-hydrator": ("Decision", "Enrich keywords from external APIs"),
        }
        
        for agent_name in sorted(agents):
            agent_type, description = agent_info.get(agent_name, ("Unknown", "No description"))
            table.add_row(agent_name, agent_type, description)
        
        console.print(table)
        console.print(f"\n📊 Total agents: {len(agents)}")
        
    except Exception as e:
        console.print(f"❌ Failed to list agents: {e}", style="red")
        raise typer.Exit(1)


@app.command("run")
def run_agent(
    agent_name: str = typer.Argument(help="Name of the agent to run"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run in dry-run mode"),
    start_date: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"), 
    params: Optional[str] = typer.Option(None, "--params", help="JSON parameters"),
):
    """Run a specific agent job."""
    try:
        # Validate agent exists
        if agent_name not in agent_registry.list_agents():
            console.print(f"❌ Agent '{agent_name}' not found", style="red")
            available = ", ".join(agent_registry.list_agents())
            console.print(f"Available agents: {available}")
            raise typer.Exit(1)
        
        # Parse parameters
        parsed_params = None
        if params:
            try:
                parsed_params = json.loads(params)
            except json.JSONDecodeError as e:
                console.print(f"❌ Invalid JSON parameters: {e}", style="red")
                raise typer.Exit(1)
        
        # Parse date window
        window = None
        if start_date or end_date:
            window = {}
            if start_date:
                window["start"] = start_date
            if end_date:
                window["end"] = end_date
        
        console.print(f"🚀 Running agent: {agent_name}", style="yellow")
        if dry_run:
            console.print("🔍 DRY RUN MODE", style="yellow")
        if window:
            console.print(f"📅 Date range: {window.get('start', 'N/A')} to {window.get('end', 'N/A')}")
        
        # Run agent
        runner = AgentRunner(agent_registry)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {agent_name}...", total=None)
            
            result = asyncio.run(runner.run_agent(
                agent_name=agent_name,
                params=parsed_params,
                window=window,
                dry_run=dry_run,
            ))
        
        # Display results
        if result.ok:
            console.print("✅ Agent completed successfully!", style="green")
            
            # Show metrics
            if result.metrics:
                table = Table(title="Agent Metrics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", justify="right", style="yellow")
                
                for key, value in result.metrics.items():
                    table.add_row(key, str(value))
                
                console.print(table)
            
            # Show notes
            if result.notes:
                console.print("\n📝 Notes:")
                for note in result.notes:
                    console.print(f"  • {note}")
            
            if result.records_written:
                console.print(f"\n📊 Records written: {result.records_written}")
        
        else:
            console.print("❌ Agent failed!", style="red")
            if result.error:
                console.print(f"Error: {result.error}", style="red")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"❌ Failed to run agent: {e}", style="red")
        raise typer.Exit(1)


@app.command("status")
def agent_status():
    """Show agent run status and history."""
    try:
        console.print("📊 Agent Status Dashboard", style="yellow")
        
        # TODO: Implement actual database query for agent_runs table
        # This would show recent agent runs with status, duration, etc.
        
        # Mock status data
        recent_runs = [
            {
                "agent": "ingestor-google",
                "run_id": "abc123",
                "started_at": "2025-01-10T10:00:00Z",
                "finished_at": "2025-01-10T10:05:00Z",
                "ok": True,
                "records_written": 156,
            },
            {
                "agent": "touchpoint-extractor", 
                "run_id": "def456",
                "started_at": "2025-01-10T10:15:00Z",
                "finished_at": "2025-01-10T10:16:00Z",
                "ok": True,
                "records_written": 23,
            },
            {
                "agent": "budget-optimizer",
                "run_id": "ghi789",
                "started_at": "2025-01-10T11:00:00Z",
                "finished_at": None,
                "ok": None,
                "records_written": None,
            },
        ]
        
        table = Table(title="Recent Agent Runs")
        table.add_column("Agent", style="cyan")
        table.add_column("Run ID", style="dim")
        table.add_column("Started", style="yellow")
        table.add_column("Duration", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Records", justify="right")
        
        for run in recent_runs:
            started = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
            
            if run["finished_at"]:
                finished = datetime.fromisoformat(run["finished_at"].replace("Z", "+00:00"))
                duration = str(finished - started).split(".")[0]  # Remove microseconds
                status = "✅ OK" if run["ok"] else "❌ FAIL"
                records = str(run["records_written"]) if run["records_written"] else "-"
            else:
                duration = "Running..."
                status = "🔄 RUNNING"
                records = "-"
            
            table.add_row(
                run["agent"],
                run["run_id"][:8],
                started.strftime("%H:%M:%S"),
                duration,
                status,
                records,
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Failed to get agent status: {e}", style="red")
        raise typer.Exit(1)


@app.command("test")
def test_agent(
    agent_name: str = typer.Argument(help="Name of the agent to test"),
):
    """Quick test run of an agent in dry-run mode."""
    console.print(f"🧪 Testing agent: {agent_name}", style="yellow")
    
    # Run with yesterday's data in dry-run mode
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    return asyncio.run(
        run_agent_async(
            agent_name=agent_name,
            dry_run=True,
            start_date=yesterday,
            end_date=yesterday,
        )
    )


async def run_agent_async(
    agent_name: str,
    dry_run: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    params: Optional[dict] = None,
):
    """Async helper for running agents."""
    
    window = None
    if start_date or end_date:
        window = {}
        if start_date:
            window["start"] = start_date
        if end_date:
            window["end"] = end_date
    
    runner = AgentRunner(agent_registry)
    result = await runner.run_agent(
        agent_name=agent_name,
        params=params,
        window=window,
        dry_run=dry_run,
    )
    
    return result


@app.command("demo")
def demo_workflow():
    """Run a demo workflow showing agent orchestration."""
    try:
        console.print("🎬 Running Agent Demo Workflow", style="bold yellow")
        console.print("This demonstrates the agent orchestration system\n")
        
        # Demo workflow: ingest → transform → optimize
        demo_agents = [
            ("ingestor-google", "Ingest Google Ads data"),
            ("ingestor-reddit", "Ingest Reddit Ads data (mock)"),
            ("touchpoint-extractor", "Extract touchpoints from events"),
            ("budget-optimizer", "Analyze and optimize budgets"),
        ]
        
        from datetime import date, timedelta
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        all_results = []
        
        for agent_name, description in demo_agents:
            console.print(f"\n🔄 {description}...", style="cyan")
            
            runner = AgentRunner(agent_registry)
            result = asyncio.run(runner.run_agent(
                agent_name=agent_name,
                window={"start": yesterday, "end": yesterday},
                dry_run=True,  # Always dry run for demo
            ))
            
            if result.ok:
                console.print(f"✅ {agent_name} completed", style="green")
                if result.records_written:
                    console.print(f"   📊 Would process {result.records_written} records")
                if result.notes:
                    for note in result.notes[:2]:  # Show first 2 notes
                        console.print(f"   • {note}", style="dim")
            else:
                console.print(f"❌ {agent_name} failed: {result.error}", style="red")
            
            all_results.append(result)
        
        # Summary
        console.print(f"\n🎯 Demo Workflow Complete", style="bold green")
        successful = sum(1 for r in all_results if r.ok)
        console.print(f"✅ {successful}/{len(demo_agents)} agents completed successfully")
        
        if successful == len(demo_agents):
            console.print("🎉 All agents would work together to process ads data!", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    # Import agents to register them
    from .agents import ingestors, transforms, activations, decisions
    
    app()
