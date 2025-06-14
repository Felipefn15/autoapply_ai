"""Script to search for job posts in LinkedIn feed."""
import argparse
import asyncio
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from loguru import logger

from app.job_search.linkedin_scraper import LinkedInScraper
from app.utils.text_extractor import extract_emails_from_text

async def search_linkedin_feed(config: Dict, keywords: List[str], output_dir: str) -> None:
    """Search LinkedIn feed for job posts."""
    # Initialize scraper
    scraper = LinkedInScraper(config)
    await scraper.setup()
    
    try:
        logger.info("\nSearching LinkedIn feed for job posts")
        logger.info("=" * 50)
        logger.info(f"Keywords: {', '.join(keywords)}")
        
        # Search for posts
        posts = await scraper.search_feed_posts(keywords)
        
        logger.info(f"\nFound {len(posts)} potential job posts")
        
        # Process posts
        jobs = []
        for post in posts:
            # Extract emails from post text
            emails = extract_emails_from_text(post['text'])
            
            # Create job entry
            job = {
                'title': f"LinkedIn Post by {post['author']}",
                'company': post['author'],
                'location': 'Remote',  # Default to remote, we can try to extract location later
                'description': post['text'],
                'url': post['url'],
                'author_profile': post['author_profile'],
                'platform': 'linkedin_feed',
                'application_method': 'email' if emails else 'linkedin',
                'emails': emails,
                'posted_at': post['posted_at'],
                'keywords_matched': [k for k in keywords if k.lower() in post['text'].lower()],
                'is_feed_post': True
            }
            
            jobs.append(job)
            
        if jobs:
            # Create output directory
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save jobs
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f'linkedin_feed_jobs_{timestamp}.json'
            
            with open(output_file, 'w') as f:
                json.dump(jobs, f, indent=2)
                
            logger.info(f"\nSaved {len(jobs)} jobs to {output_file}")
            
            # Print summary
            logger.info("\nJob Post Summary:")
            logger.info("-" * 50)
            for job in jobs:
                logger.info(f"Author: {job['company']}")
                logger.info(f"Keywords: {', '.join(job['keywords_matched'])}")
                logger.info(f"Emails found: {', '.join(job['emails']) if job['emails'] else 'None'}")
                logger.info(f"URL: {job['url']}")
                logger.info("-" * 50)
        else:
            logger.warning("No relevant job posts found")
            
    finally:
        await scraper.cleanup()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/config.yaml',
                      help='Path to config file')
    parser.add_argument('--keywords', required=True, nargs='+',
                      help='Keywords to search for')
    parser.add_argument('--output-dir', default='data/jobs',
                      help='Directory to save job posts')
    args = parser.parse_args()
    
    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)
        
    # Search LinkedIn feed
    await search_linkedin_feed(config, args.keywords, args.output_dir)

if __name__ == '__main__':
    asyncio.run(main()) 