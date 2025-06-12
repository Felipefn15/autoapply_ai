"""
Script to test the resume parser functionality.
"""
import json
from pathlib import Path
from app.main import AutoApplyAI

def print_parsed_resume(result):
    """Print parsed resume information in a formatted way."""
    print("\n=== Parsed Resume Information ===")
    print(f"Name: {result['full_name']}")
    print(f"Email: {result['email']}")
    print(f"Phone: {result['phone']}")
    print(f"Location: {result['location']}")
    
    if result['summary']:
        print("\nSummary:")
        print(result['summary'])
    
    if result['skills']:
        print("\nSkills:")
        # Group skills by category
        skill_categories = {
            'Languages': ['python', 'javascript', 'typescript', 'java', 'c#', 'ruby', 'php'],
            'Frontend': ['react', 'vue', 'angular', 'next.js', 'nuxt', 'html', 'css'],
            'Backend': ['node.js', 'django', 'flask', 'express', 'rails'],
            'Database': ['postgresql', 'mysql', 'mongodb', 'redis'],
            'Cloud/DevOps': ['aws', 'gcp', 'azure', 'docker', 'kubernetes'],
            'Other': []
        }
        
        categorized_skills = {cat: [] for cat in skill_categories}
        for skill in result['skills']:
            skill_lower = skill.lower()
            categorized = False
            for cat, patterns in skill_categories.items():
                if any(pattern in skill_lower for pattern in patterns):
                    categorized_skills[cat].append(skill)
                    categorized = True
                    break
            if not categorized:
                categorized_skills['Other'].append(skill)
        
        for category, skills in categorized_skills.items():
            if skills:
                print(f"\n{category}:")
                for skill in sorted(skills):
                    print(f"- {skill}")
    
    if result['experience']:
        print("\nExperience:")
        for exp in result['experience']:
            print(f"\n{exp['position']} at {exp['company']}")
            if exp['location']:
                print(f"Location: {exp['location']}")
            if exp['start_date'] or exp['end_date']:
                date_range = f"{exp['start_date'] or 'Unknown'} - {exp['end_date'] or 'Unknown'}"
                if exp['duration']:
                    date_range += f" ({exp['duration']})"
                print(f"Period: {date_range}")
            print("Description:")
            print(exp['description'])
            if exp['skills']:
                print("Skills used:")
                for skill in exp['skills']:
                    print(f"- {skill}")
    
    if result['education']:
        print("\nEducation:")
        for edu in result['education']:
            print(f"\n{edu['degree']}")
            if edu['field']:
                print(f"Field: {edu['field']}")
            print(f"Institution: {edu['institution']}")
            if edu['start_date'] or edu['end_date']:
                print(f"Period: {edu['start_date'] or 'Unknown'} - {edu['end_date'] or 'Unknown'}")
            if edu['details']:
                print("Details:")
                print(edu['details'])
    
    if result['languages']:
        print("\nLanguages:")
        for lang in result['languages']:
            print(f"- {lang}")
    
    if result['certifications']:
        print("\nCertifications:")
        for cert in result['certifications']:
            print(f"- {cert}")
    
    print(f"\nOriginal Format: {result['original_format']}")

def main():
    """Main function to test resume parser."""
    app = AutoApplyAI()
    
    # Process all resumes
    processed_resumes = app.process_resumes()
    
    if not processed_resumes:
        print("\nNo resumes were processed successfully.")
        return
    
    # Print parsed information for each resume
    for resume_data in processed_resumes:
        print_parsed_resume(resume_data)
        
        # Check if parsed data was saved
        output_file = app.output_dir / f"{Path(resume_data['original_format']).stem}_parsed.json"
        if output_file.exists():
            print(f"\nParsed data saved to: {output_file}")
            
            # Verify saved data
            with output_file.open('r', encoding='utf-8') as f:
                saved_data = json.load(f)
                if saved_data == resume_data:
                    print("✓ Saved data matches parsed data")
                else:
                    print("⚠ Warning: Saved data differs from parsed data")

if __name__ == "__main__":
    main() 