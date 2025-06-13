#!/usr/bin/env python3
"""
Job Analysis Script - Analyze job search results and applications
"""
import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

def load_data(jobs_dir: str, applications_dir: str) -> Tuple[List[Dict], List[Dict]]:
    """Load jobs and applications data from the most recent files."""
    jobs = []
    applications = []
    
    try:
        # Load jobs
        jobs_dir = Path(jobs_dir)
        if jobs_dir.exists():
            latest_jobs = sorted(jobs_dir.glob("jobs_*.json"))[-1]
            with open(latest_jobs, "r") as f:
                jobs = json.load(f)
            logger.info(f"Loaded {len(jobs)} jobs from {latest_jobs}")
            
        # Load applications
        applications_dir = Path(applications_dir)
        if applications_dir.exists():
            latest_applications = sorted(applications_dir.glob("applications_*.json"))[-1]
            with open(latest_applications, "r") as f:
                applications = json.load(f)
            logger.info(f"Loaded {len(applications)} applications from {latest_applications}")
            
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        
    return jobs, applications

def analyze_jobs(jobs: List[Dict]) -> Dict:
    """Analyze job data."""
    logger.info("\nStarting Job Analysis")
    logger.info("=" * 50)
    
    analysis = {
        "total_jobs": len(jobs),
        "jobs_by_platform": Counter(),
        "locations": Counter(),
        "remote_jobs": 0,
        "salary_stats": {
            "jobs_with_salary": 0,
            "min_salary": float("inf"),
            "max_salary": 0,
            "avg_salary": 0
        },
        "companies": Counter(),
        "requirements": Counter(),
        "core_tech_jobs": {
            "javascript": 0,
            "react": 0,
            "react_native": 0,
            "next": 0,
            "node": 0
        }
    }
    
    total_salary = 0
    
    logger.info(f"Processing {len(jobs)} jobs...")
    
    for job in jobs:
        # Count by platform
        analysis["jobs_by_platform"][job["platform"]] += 1
        
        # Count locations
        if job["location"]:
            analysis["locations"][job["location"]] += 1
            
        # Count remote jobs
        if job["remote"]:
            analysis["remote_jobs"] += 1
            
        # Analyze salary
        if job["salary_min"] and job["salary_max"]:
            analysis["salary_stats"]["jobs_with_salary"] += 1
            avg_salary = (job["salary_min"] + job["salary_max"]) / 2
            total_salary += avg_salary
            
            # Convert to monthly
            monthly_min = job["salary_min"] / 12
            monthly_max = job["salary_max"] / 12
            
            analysis["salary_stats"]["min_salary"] = min(
                analysis["salary_stats"]["min_salary"],
                monthly_min
            )
            analysis["salary_stats"]["max_salary"] = max(
                analysis["salary_stats"]["max_salary"],
                monthly_max
            )
            
        # Count companies
        if job["company"]:
            analysis["companies"][job["company"]] += 1
            
        # Count requirements
        for req in job["requirements"]:
            analysis["requirements"][req.lower()] += 1
            
        # Check for core technologies
        description = job["description"].lower()
        title = job["title"].lower()
        requirements = [req.lower() for req in job["requirements"]]
        
        if "javascript" in description or "javascript" in title or any("javascript" in req for req in requirements):
            analysis["core_tech_jobs"]["javascript"] += 1
        if "react" in description or "react" in title or any("react" in req for req in requirements):
            analysis["core_tech_jobs"]["react"] += 1
        if "react native" in description or "react native" in title or any("react native" in req for req in requirements):
            analysis["core_tech_jobs"]["react_native"] += 1
        if "next.js" in description or "next.js" in title or any("next.js" in req for req in requirements):
            analysis["core_tech_jobs"]["next"] += 1
        if "node" in description or "node.js" in title or any("node" in req for req in requirements):
            analysis["core_tech_jobs"]["node"] += 1
            
    # Calculate average salary
    if analysis["salary_stats"]["jobs_with_salary"] > 0:
        analysis["salary_stats"]["avg_salary"] = (
            total_salary / analysis["salary_stats"]["jobs_with_salary"]
        ) / 12  # Convert to monthly
        
    if analysis["salary_stats"]["min_salary"] == float("inf"):
        analysis["salary_stats"]["min_salary"] = 0
        
    # Log analysis results
    logger.info("\nAnalysis Results:")
    logger.info("-" * 50)
    logger.info(f"Total Jobs Found: {analysis['total_jobs']}")
    logger.info(f"Remote Jobs: {analysis['remote_jobs']} ({(analysis['remote_jobs']/analysis['total_jobs'])*100:.1f}%)")
    
    logger.info("\nJobs by Platform:")
    for platform, count in analysis["jobs_by_platform"].most_common():
        logger.info(f"  {platform}: {count} jobs")
    
    if analysis["salary_stats"]["jobs_with_salary"] > 0:
        logger.info("\nSalary Statistics (Monthly):")
        logger.info(f"  Jobs with Salary: {analysis['salary_stats']['jobs_with_salary']}")
        logger.info(f"  Minimum: ${analysis['salary_stats']['min_salary']:,.2f}")
        logger.info(f"  Average: ${analysis['salary_stats']['avg_salary']:,.2f}")
        logger.info(f"  Maximum: ${analysis['salary_stats']['max_salary']:,.2f}")
    
    logger.info("\nTop Companies:")
    for company, count in analysis["companies"].most_common(5):
        logger.info(f"  {company}: {count} jobs")
    
    logger.info("\nTop Requirements:")
    for req, count in analysis["requirements"].most_common(10):
        logger.info(f"  {req}: {count} jobs")
    
    logger.info("\nCore Technologies:")
    for tech, count in analysis["core_tech_jobs"].items():
        if count > 0:
            logger.info(f"  {tech}: {count} jobs ({(count/analysis['total_jobs'])*100:.1f}%)")
    
    return analysis

def analyze_applications(applications: List[Dict]) -> Dict:
    """Analyze application data."""
    logger.info("\nAnalyzing Applications")
    logger.info("=" * 50)
    
    analysis = {
        "total_applications": len(applications),
        "successful": 0,
        "failed": 0,
        "success_rate": 0,
        "methods": Counter(),
        "platforms": Counter(),
        "errors": Counter()
    }
    
    for app in applications:
        # Count success/failure
        if app.get("success", False):
            analysis["successful"] += 1
        else:
            analysis["failed"] += 1
            
        # Count methods
        analysis["methods"][app.get("method", "unknown")] += 1
        
        # Count platforms
        analysis["platforms"][app.get("platform", "unknown")] += 1
        
        # Count errors
        if error := app.get("error"):
            analysis["errors"][error] += 1
            
    if analysis["total_applications"] > 0:
        analysis["success_rate"] = (
            analysis["successful"] / analysis["total_applications"]
        ) * 100
        
    # Log application analysis
    logger.info(f"\nTotal Applications: {analysis['total_applications']}")
    logger.info(f"Successful: {analysis['successful']}")
    logger.info(f"Failed: {analysis['failed']}")
    logger.info(f"Success Rate: {analysis['success_rate']:.1f}%")
    
    logger.info("\nApplication Methods:")
    for method, count in analysis["methods"].most_common():
        logger.info(f"  {method}: {count}")
    
    logger.info("\nPlatforms:")
    for platform, count in analysis["platforms"].most_common():
        logger.info(f"  {platform}: {count}")
    
    if analysis["errors"]:
        logger.info("\nCommon Errors:")
        for error, count in analysis["errors"].most_common():
            logger.info(f"  {error}: {count}")
    
    return analysis

def generate_visualizations(jobs_analysis: Dict, output_dir: str):
    """Generate visualizations of the analysis."""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Jobs by Platform
        plt.figure(figsize=(10, 6))
        platforms = list(jobs_analysis["jobs_by_platform"].keys())
        counts = list(jobs_analysis["jobs_by_platform"].values())
        plt.bar(platforms, counts)
        plt.title("Jobs by Platform")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "jobs_by_platform.png")
        plt.close()
        
        # 2. Remote vs. Non-Remote
        plt.figure(figsize=(8, 8))
        remote = jobs_analysis["remote_jobs"]
        non_remote = jobs_analysis["total_jobs"] - remote
        plt.pie(
            [remote, non_remote],
            labels=["Remote", "Non-Remote"],
            autopct="%1.1f%%"
        )
        plt.title("Remote vs. Non-Remote Jobs")
        plt.tight_layout()
        plt.savefig(output_dir / "remote_jobs.png")
        plt.close()
        
        # 3. Salary Distribution
        if jobs_analysis["salary_stats"]["jobs_with_salary"] > 0:
            plt.figure(figsize=(10, 6))
            salary_data = [
                jobs_analysis["salary_stats"]["min_salary"],
                jobs_analysis["salary_stats"]["avg_salary"],
                jobs_analysis["salary_stats"]["max_salary"]
            ]
            plt.bar(
                ["Minimum", "Average", "Maximum"],
                salary_data,
                color=["red", "blue", "green"]
            )
            plt.title("Monthly Salary Distribution (USD)")
            plt.ylabel("USD")
            plt.tight_layout()
            plt.savefig(output_dir / "salary_distribution.png")
            plt.close()
            
        # 4. Core Technologies Distribution
        plt.figure(figsize=(10, 6))
        techs = list(jobs_analysis["core_tech_jobs"].keys())
        counts = list(jobs_analysis["core_tech_jobs"].values())
        plt.bar(techs, counts)
        plt.title("Jobs by Core Technology")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "core_technologies.png")
        plt.close()
        
        logger.info("Generated all visualizations")
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {str(e)}")

def save_report(jobs_analysis: Dict, applications_analysis: Dict, output_dir: str):
    """Save analysis report to file."""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"analysis_report_{timestamp}.txt"
        
        with open(report_file, "w") as f:
            f.write("Job Search and Application Analysis Report\n")
            f.write("========================================\n\n")
            
            # Job Statistics
            f.write("Job Statistics:\n")
            f.write(f"Total Jobs Found: {jobs_analysis['total_jobs']}\n\n")
            
            # Jobs by Platform
            f.write("Jobs by Platform:\n")
            for platform, count in jobs_analysis["jobs_by_platform"].items():
                f.write(f"- {platform}: {count}\n")
            f.write("\n")
            
            # Top 10 Locations
            f.write("Top 10 Locations:\n")
            for location, count in jobs_analysis["locations"].most_common(10):
                f.write(f"- {location}: {count}\n")
            f.write("\n")
            
            # Salary Statistics
            f.write("Salary Statistics:\n")
            f.write(f"Jobs with Salary Info: {jobs_analysis['salary_stats']['jobs_with_salary']}\n")
            f.write(f"Minimum: ${jobs_analysis['salary_stats']['min_salary']:.2f}/month\n")
            f.write(f"Maximum: ${jobs_analysis['salary_stats']['max_salary']:.2f}/month\n")
            f.write(f"Average: ${jobs_analysis['salary_stats']['avg_salary']:.2f}/month\n\n")
            
            # Core Technologies
            f.write("Core Technology Distribution:\n")
            for tech, count in jobs_analysis["core_tech_jobs"].items():
                f.write(f"- {tech.replace('_', ' ').title()}: {count} jobs\n")
            f.write("\n")
            
            # Remote Jobs
            f.write("Remote Work:\n")
            remote_percentage = (jobs_analysis["remote_jobs"] / jobs_analysis["total_jobs"]) * 100
            f.write(f"Remote Jobs: {jobs_analysis['remote_jobs']} ({remote_percentage:.1f}%)\n\n")
            
            # Application Statistics
            f.write("Application Statistics:\n")
            f.write(f"Total Applications: {applications_analysis['total_applications']}\n")
            f.write(f"Successful: {applications_analysis['successful']}\n")
            f.write(f"Failed: {applications_analysis['failed']}\n")
            f.write(f"Success Rate: {applications_analysis['success_rate']:.2f}%\n")
            
        logger.info(f"Saved analysis report to {report_file}")
        
    except Exception as e:
        logger.error(f"Error saving report: {str(e)}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze job search results")
    
    parser.add_argument(
        "--jobs-dir",
        help="Directory containing job search results",
        default="data/jobs"
    )
    
    parser.add_argument(
        "--applications-dir",
        help="Directory containing application results",
        default="data/applications"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for analysis results",
        default="reports"
    )
    
    parser.add_argument(
        "--visualizations-dir",
        help="Output directory for visualizations",
        default="reports/visualizations"
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        jobs, applications = load_data(args.jobs_dir, args.applications_dir)
        
        # Analyze data
        jobs_analysis = analyze_jobs(jobs)
        applications_analysis = analyze_applications(applications)
        
        # Generate visualizations
        generate_visualizations(jobs_analysis, args.visualizations_dir)
        
        # Save report
        save_report(jobs_analysis, applications_analysis, args.output_dir)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 