"""Convert resume to PDF."""
from fpdf import FPDF

def create_pdf():
    """Create PDF from text file."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Courier', size=12)
    
    with open('resume.txt') as f:
        text = f.read()
        
    pdf.multi_cell(0, 10, text)
    pdf.output('resume.pdf')

if __name__ == '__main__':
    create_pdf() 