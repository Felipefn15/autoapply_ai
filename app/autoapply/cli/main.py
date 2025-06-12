"""
Main CLI Module - Entry point for AutoApply.AI
"""
import sys
import argparse
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from ..core.resume import ResumeManager
from ..core.jobs import JobManager
from ..core.matching import JobMatcher
from ..core.automation import JobApplicator
from ..config.settings import Config, config
from ..utils.logging import setup_logger

# Setup logger
logger = setup_logger("cli")

# Setup rich console
console = Console()

# Create typer app
app = typer.Typer(
    name="autoapply",
    help="AutoApply.AI - Automated job search and application tool",
    add_completion=False
)

def version_callback(value: bool):
    """Print version information."""
    if value:
        console.print("AutoApply.AI v0.1.0")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version information.",
        callback=version_callback,
        is_eager=True,
    )
):
    """AutoApply.AI - Automated job search and application tool."""
    pass

@app.command()
def configure(
    config_file: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
        exists=False
    )
):
    """Configure AutoApply.AI settings."""
    try:
        # Load existing config if available
        config = Config.load(config_file)
        
        # Save configuration
        config.save(config_file)
        console.print("[green]Configuration saved successfully![/green]")
        
    except Exception as e:
        logger.error(f"Error configuring application: {str(e)}")
        console.print(f"[red]Error configuring application: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def search(
    resume_file: Path = typer.Argument(
        ...,
        help="Path to resume file.",
        exists=True
    ),
    platform: str = typer.Option(
        None,
        "--platform",
        "-p",
        help="Job platform to search (remotive, weworkremotely)."
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of jobs to process."
    )
):
    """Search for matching jobs."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Parse resume
            task = progress.add_task("Parsing resume...", total=None)
            resume_manager = ResumeManager()
            resume_data = resume_manager.parse(str(resume_file))
            progress.update(task, completed=True)
            
            # Search for jobs
            task = progress.add_task("Searching for jobs...", total=None)
            job_manager = JobManager()
            jobs = job_manager.search(platform)
            progress.update(task, completed=True)
            
            # Match jobs
            task = progress.add_task(f"Matching {len(jobs)} jobs...", total=len(jobs))
            matcher = JobMatcher(config.api.groq_api_key)
            matches = matcher.match(resume_data, jobs[:limit])
            progress.update(task, completed=True)
            
            # Display results
            console.print("\n[bold]Top Matches:[/bold]\n")
            for job, match_result in matches:
                console.print(f"[bold blue]{job.title}[/bold blue] at [bold]{job.company}[/bold]")
                console.print(f"Match Score: [green]{match_result.match_score:.2f}[/green]")
                console.print("Reasons:")
                for reason in match_result.match_reasons:
                    console.print(f"  ✓ {reason}")
                console.print("Potential Concerns:")
                for concern in match_result.mismatch_reasons:
                    console.print(f"  ⚠ {concern}")
                console.print(f"URL: [link]{job.url}[/link]\n")
            
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        console.print(f"[red]Error searching jobs: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def apply(
    resume_file: Path = typer.Argument(
        ...,
        help="Path to resume file.",
        exists=True
    ),
    platform: str = typer.Option(
        None,
        "--platform",
        "-p",
        help="Job platform to search (remotive, weworkremotely)."
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        "-l",
        help="Maximum number of jobs to apply to."
    ),
    min_score: float = typer.Option(
        0.8,
        "--min-score",
        "-s",
        help="Minimum match score to apply (0-1)."
    )
):
    """Search for matching jobs and apply automatically."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Parse resume
            task = progress.add_task("Parsing resume...", total=None)
            resume_manager = ResumeManager()
            resume_data = resume_manager.parse(str(resume_file))
            progress.update(task, completed=True)
            
            # Search for jobs
            task = progress.add_task("Searching for jobs...", total=None)
            job_manager = JobManager()
            jobs = job_manager.search(platform)
            progress.update(task, completed=True)
            
            # Match jobs
            task = progress.add_task(f"Matching {len(jobs)} jobs...", total=len(jobs))
            matcher = JobMatcher(config.api.groq_api_key)
            matches = matcher.match(resume_data, jobs)
            progress.update(task, completed=True)
            
            # Filter matches by score
            qualified_matches = [(job, match) for job, match in matches 
                               if match.match_score >= min_score][:limit]
            
            if not qualified_matches:
                console.print("[yellow]No jobs found matching minimum score criteria.[/yellow]")
                raise typer.Exit(0)
            
            # Apply to jobs
            task = progress.add_task(f"Applying to {len(qualified_matches)} jobs...", total=len(qualified_matches))
            applicator = JobApplicator()
            applicator.apply_batch(resume_data, [job for job, _ in qualified_matches])
            progress.update(task, completed=True)
            
            # Display results
            console.print("\n[bold]Application Results:[/bold]\n")
            for job, match_result in qualified_matches:
                console.print(f"[bold blue]{job.title}[/bold blue] at [bold]{job.company}[/bold]")
                console.print(f"Match Score: [green]{match_result.match_score:.2f}[/green]")
                console.print(f"URL: [link]{job.url}[/link]\n")
            
    except Exception as e:
        logger.error(f"Error applying to jobs: {str(e)}")
        console.print(f"[red]Error applying to jobs: {str(e)}[/red]")
        raise typer.Exit(1)

def run():
    """Run the CLI application."""
    try:
        app()
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        console.print(f"[red]An unexpected error occurred: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    run() 