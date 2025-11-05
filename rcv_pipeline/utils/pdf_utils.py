"""
Simple PDF text extraction utilities.
"""
import os
from pathlib import Path
import PyPDF2
import pdfplumber

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using multiple methods.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string, or None if extraction failed
    """
    try:
        # Try pdfplumber first (usually better)
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text.strip():
                return text
        
        # Fallback to PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text if text.strip() else None
            
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def clean_text(text):
    """
    Clean extracted text by removing excessive whitespace.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def process_pdf_directory(input_dir, output_dir):
    """
    Process all PDF files in a directory and convert to text.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory to save text files
        
    Returns:
        Dictionary with processing statistics
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files (search recursively to support sample data in subdirectories)
    pdf_files = list(input_path.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir} (searched recursively)")
        return {"processed": 0, "successful": 0, "failed": 0}
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    stats = {"processed": 0, "successful": 0, "failed": 0}
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        
        # Extract text
        text = extract_text_from_pdf(pdf_file)
        
        if text:
            # Clean text
            cleaned_text = clean_text(text)
            
            # Save to text file
            output_file = output_path / f"{pdf_file.stem}.txt"
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
                
                print(f"  ✓ Saved: {output_file.name}")
                stats["successful"] += 1
                
            except Exception as e:
                print(f"  ✗ Error saving {output_file.name}: {e}")
                stats["failed"] += 1
        else:
            print(f"  ✗ Failed to extract text from {pdf_file.name}")
            stats["failed"] += 1
        
        stats["processed"] += 1
    
    print(f"\nProcessing complete: {stats['successful']} successful, {stats['failed']} failed")
    return stats
