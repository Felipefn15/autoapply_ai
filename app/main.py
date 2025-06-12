#!/usr/bin/env python3
"""
AutoApply.AI - Main Application
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

from dotenv import load_dotenv
from loguru import logger

from app.resume.parser import ResumeParser
from app.job_search.searcher import JobSearcher, JobPosting
from app.matching.matcher import JobMatcher, MatchResult
from app.automation.applicator import JobApplicator

# Load environment variables
load_dotenv()

# Verify required environment variables
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY environment variable is required. Please set it in your .env file.")

# Configure logging
logger.add(
    "logs/autoapply_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

class AutoApplyAI:
    """Main application class for AutoApply.AI"""
    
    def __init__(self):
        """Initialize AutoApply.AI components."""
        # Load configuration
        from app.autoapply.config.settings import Config
        self.config = Config()
        
        self.resume_parser = ResumeParser()
        self.job_searcher = JobSearcher()
        self.job_matcher = JobMatcher(api_key=os.getenv('GROQ_API_KEY'))
        self.job_applicator = JobApplicator()
        
        # Ensure required directories exist
        self.data_dir = Path("data")
        self.resumes_dir = self.data_dir / "resumes"
        self.cache_dir = self.data_dir / "cache"
        self.output_dir = self.data_dir / "output"
        self.logs_dir = Path("logs")
        
        for directory in [self.data_dir, self.resumes_dir, self.cache_dir, self.output_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.min_match_score = 0.5
        self.max_jobs_per_source = 50
        self.batch_size = 5
    
    def get_available_resumes(self) -> List[Path]:
        """
        Get list of available resume files in the resumes directory.
        
        Returns:
            List of Path objects for each resume file
        """
        # Get all PDF and TXT files in the resumes directory
        resume_files = []
        for ext in ['.pdf', '.txt']:
            resume_files.extend(self.resumes_dir.glob(f'*{ext}'))
        
        if not resume_files:
            logger.warning("No resume files found in %s", self.resumes_dir)
            logger.info("Please add PDF or TXT resume files to the resumes directory")
        
        return resume_files
    
    def process_resumes(self) -> List[Dict]:
        """
        Process all available resume files.
        
        Returns:
            List of parsed resume data dictionaries
        """
        processed_resumes = []
        resume_files = self.get_available_resumes()
        
        for resume_file in resume_files:
            try:
                logger.info("Processing resume: %s", resume_file.name)
                resume_data = self.resume_parser.parse(resume_file)
                processed_resumes.append(resume_data)
                
                # Save parsed data to output directory
                output_file = self.output_dir / f"{resume_file.stem}_parsed.json"
                self._save_resume_data(resume_data, output_file)
                
            except Exception as e:
                logger.error("Error processing resume %s: %s", resume_file.name, str(e))
        
        return processed_resumes
    
    def _save_resume_data(self, resume_data: Dict, output_file: Path) -> None:
        """
        Save parsed resume data to JSON file.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            output_file: Path where to save the JSON file
        """
        import json
        
        try:
            with output_file.open('w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2, ensure_ascii=False)
            logger.info("Saved parsed resume data to %s", output_file)
        except Exception as e:
            logger.error("Error saving resume data to %s: %s", output_file, str(e))
    
    def search_jobs(self) -> List[JobPosting]:
        """Search for matching jobs across all sources."""
        all_jobs = []
        
        try:
            # Search each source
            for source in ['linkedin', 'indeed', 'remotive', 'weworkremotely', 'stackoverflow']:
                try:
                    jobs = self.job_searcher.search(source)
                    logger.info(f"Found {len(jobs)} matching jobs on {source}")
                    all_jobs.extend(jobs[:self.max_jobs_per_source])
                except Exception as e:
                    logger.error(f"Error searching {source}: {str(e)}")
                    continue
            
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            raise
    
    def match_jobs(self, resume_data: Dict, jobs: List[JobPosting]) -> List[Tuple[JobPosting, MatchResult]]:
        """Match resume with job postings in batches."""
        results = []
        total_jobs = len(jobs)
        batch_size = 3  # Reduced batch size for better rate limiting
        num_batches = (total_jobs + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_jobs)
            batch_jobs = jobs[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{num_batches} ({start_idx + 1}-{end_idx} of {total_jobs} jobs)")
            
            try:
                batch_results = self.job_matcher.match(resume_data, batch_jobs)
                results.extend(batch_results)
                
                # Add a small delay between batches to help with rate limiting
                if batch_num < num_batches - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch_num + 1}: {str(e)}")
                # Continue with next batch instead of failing completely
                continue
        
        return results
    
    def apply_to_jobs(self, resume_data: Dict, matched_jobs: List[JobPosting]) -> None:
        """
        Apply to matched jobs automatically.
        
        Args:
            resume_data: Dictionary containing parsed resume information
            matched_jobs: List of matched jobs to apply to
        """
        try:
            self.job_applicator.apply_batch(resume_data, matched_jobs)
        except Exception as e:
            logger.error("Error applying to jobs: %s", str(e))
    
    def run(self, resume_path: Optional[str] = None):
        """Run the AutoApply.AI workflow."""
        try:
            logger.info("Starting AutoApply.AI workflow")
            
            # Get resume path
            if not resume_path:
                resume_files = list(self.resumes_dir.glob("*.pdf")) + list(self.resumes_dir.glob("*.txt"))
                if not resume_files:
                    raise ValueError("No resume files found in data/resumes")
                resume_path = str(resume_files[0])
            
            # Process resume
            logger.info(f"Processing resume: {Path(resume_path).name}")
            resume_data = self.process_resume(resume_path)
            
            # Search for jobs
            logger.info("Searching for jobs across all platforms...")
            jobs = self.job_searcher.search()  # Search all platforms
            logger.info(f"Found {len(jobs)} total jobs")
            
            if not jobs:
                logger.warning("No jobs found. Please check your search criteria and try again.")
                return
            
            # Match jobs with resume
            logger.info("Matching jobs with resume...")
            matched_jobs = self.match_jobs(resume_data, jobs)
            logger.info(f"Found {len(matched_jobs)} matching jobs")
            
            if not matched_jobs:
                logger.warning("No matching jobs found. Please check your matching criteria and try again.")
                return
            
            # Save results
            self.save_results(resume_path, matched_jobs)
            
            # Apply to jobs if auto-apply is enabled
            if self.config.application.auto_apply:
                logger.info("Auto-applying to matched jobs...")
                self.apply_to_jobs(resume_data, [job for job, _ in matched_jobs])
            else:
                logger.info("Auto-apply is disabled. Review the matches and enable auto-apply in config.py to apply automatically.")
            
            logger.info("AutoApply.AI workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Error in AutoApply.AI workflow: {str(e)}")
            raise
    
    def process_resume(self, resume_path: str) -> Dict:
        """
        Process a single resume file.
        
        Args:
            resume_path: Path to the resume file
            
        Returns:
            Dictionary containing parsed resume information
        """
        try:
            resume_data = self.resume_parser.parse(Path(resume_path))
            
            # Save parsed data
            output_path = self.output_dir / f"{Path(resume_path).stem}_parsed.json"
            self._save_resume_data(resume_data, output_path)
            
            return resume_data
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            raise
    
    def save_results(self, resume_path: str, matched_jobs: List[Tuple[JobPosting, MatchResult]]) -> None:
        """Save matching results to a file."""
        try:
            # Create results directory if it doesn't exist
            results_dir = Path("data/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resume_name = Path(resume_path).stem
            output_file = results_dir / f"matches_{resume_name}_{timestamp}.txt"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"AutoApply.AI - Job Matching Results\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Resume: {resume_path}\n")
                f.write(f"Total Jobs Matched: {len(matched_jobs)}\n\n")
                
                for job, match in matched_jobs:
                    f.write(f"Job Title: {job.title}\n")
                    f.write(f"Company: {job.company}\n")
                    f.write(f"Location: {job.location}\n")
                    f.write(f"URL: {job.url}\n")
                    f.write(f"Platform: {job.platform}\n")
                    f.write(f"Posted: {job.posted_date}\n")
                    f.write(f"Match Score: {match.score:.2f}\n")
                    
                    if match.match_reasons:
                        f.write("\nMatch Reasons:\n")
                        for reason in match.match_reasons:
                            f.write(f"✓ {reason}\n")
                    
                    if match.mismatch_reasons:
                        f.write("\nMismatch Reasons:\n")
                        for reason in match.mismatch_reasons:
                            f.write(f"✗ {reason}\n")
                    
                    f.write("\n" + "="*80 + "\n\n")
            
            logger.info(f"Saved matching results to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise

def main():
    """Main entry point."""
    try:
        # Check for required environment variables
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            logger.error("GROQ_API_KEY environment variable is not set")
            raise ValueError("GROQ_API_KEY environment variable is required")

        app = AutoApplyAI()
        app.run()
    except Exception as e:
        logger.error("Application error: {}", str(e))
        raise

if __name__ == "__main__":
    main() 