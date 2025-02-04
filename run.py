import PyPDF2
from anthropic import Anthropic
import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image
import io
from reportlab.lib import utils
from reportlab.platypus import Image as RLImage
from dotenv import load_dotenv
from time import sleep
from tqdm import tqdm

def create_pdf_page(text, pagesize=letter):
    """Create a PDF page with properly wrapped text."""
    packet = BytesIO()
    doc = SimpleDocTemplate(
        packet,
        pagesize=pagesize,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    # Create custom style for translated text
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Convert text to paragraphs
    story = []
    paragraphs = text.split('\n\n')  # Split by double newline for paragraphs
    for para in paragraphs:
        if para.strip():
            p = Paragraph(para.replace('\n', '<br/>'), custom_style)
            story.append(p)
            story.append(Spacer(1, 12))
    
    # Build the PDF
    doc.build(story)
    packet.seek(0)
    return PdfReader(packet)

def extract_images(page):
    """Extract images from a PDF page."""
    images = []
    if '/Resources' in page and '/XObject' in page['/Resources']:
        xObject = page['/Resources']['/XObject'].get_object()
        for obj in xObject:
            if xObject[obj]['/Subtype'] == '/Image':
                images.append(xObject[obj])
    return images

def read_pdf_with_images(pdf_path):
    """Read content and images from a PDF file."""
    text_by_page = []
    images_by_page = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text_by_page.append(page.extract_text())
                images_by_page.append(extract_images(page))
        return text_by_page, images_by_page, pdf_reader
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None, None, None

def extract_and_save_image(image_object):
    """Extract image data and convert to PIL Image."""
    try:
        if '/ColorSpace' in image_object:
            if image_object['/ColorSpace'] == '/DeviceRGB':
                mode = "RGB"
            elif image_object['/ColorSpace'] == '/DeviceCMYK':
                mode = "CMYK"
            else:
                mode = "RGB"
        else:
            mode = "RGB"
        
        if '/Filter' in image_object:
            image_data = image_object.get_data()
            if image_object['/Filter'] == '/FlateDecode':
                size = (image_object['/Width'], image_object['/Height'])
                img = Image.frombytes(mode, size, image_data)
                return img
            elif image_object['/Filter'] == '/DCTDecode':
                img = Image.open(io.BytesIO(image_data))
                return img
            elif image_object['/Filter'] == '/JPXDecode':
                img = Image.open(io.BytesIO(image_data))
                return img
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def create_pdf_page_with_images(text, images, pagesize=letter):
    """Create a PDF page with properly wrapped text and images."""
    packet = BytesIO()
    
    # Calculate available space with more conservative margins
    available_width = pagesize[0] - 2.5*inch  # Increased margin
    available_height = pagesize[1] - 3*inch   # Increased margin
    
    doc = SimpleDocTemplate(
        packet,
        pagesize=pagesize,
        leftMargin=1.25*inch,  # Increased margin
        rightMargin=1.25*inch, # Increased margin
        topMargin=1.25*inch,   # Increased margin
        bottomMargin=1.75*inch # Increased margin for footer space
    )
    
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceBefore=6,
        spaceAfter=6
    )
    
    story = []
    
    # Add images with proper scaling
    for img_obj in images:
        pil_img = extract_and_save_image(img_obj)
        if pil_img:
            # Save image to temporary buffer
            img_buffer = BytesIO()
            pil_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Get image dimensions
            img_width = pil_img.width
            img_height = pil_img.height
            aspect = img_height / float(img_width)
            
            # Scale image to fit within available space
            # Limit maximum dimensions to 80% of available space
            max_width = min(available_width * 0.8, img_width)
            max_height = min(available_height * 0.4, img_height)  # Use only 40% of height
            
            # Calculate new dimensions maintaining aspect ratio
            if img_width > max_width:
                new_width = max_width
                new_height = new_width * aspect
            else:
                new_width = img_width
                new_height = img_height
            
            # If height is still too large, scale down based on height
            if new_height > max_height:
                new_height = max_height
                new_width = new_height / aspect
            
            # Create ReportLab image with scaled dimensions
            img = RLImage(img_buffer, width=new_width, height=new_height)
            story.append(img)
            story.append(Spacer(1, 12))
    
    # Add text paragraphs
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        if para.strip():
            p = Paragraph(para.replace('\n', '<br/>'), custom_style)
            story.append(p)
            story.append(Spacer(1, 12))
    
    try:
        doc.build(story)
        packet.seek(0)
        return PdfReader(packet)
    except Exception as e:
        print(f"Error building PDF: {e}")
        # Fallback to text-only version if image processing fails
        return create_pdf_page(text, pagesize)

def translate_text(client, text, target_language="English"):
    """Translate text using Claude."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                temperature=0,
                system="You are a professional translator. Translate the given text accurately while maintaining its meaning and style.",
                messages=[{
                    "role": "user",
                    "content": f"Please translate the following text to {target_language}:\n\n{text}"
                }]
            )
            return message.content[0].text if isinstance(message.content, list) else message.content
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Translation attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {retry_delay} seconds...")
                sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Error during translation after {max_retries} attempts: {e}")
                return None

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in .env file")
        return
        
    client = Anthropic(api_key=api_key)

    # Define books directory
    books_dir = Path("books")
    if not books_dir.exists():
        print("Creating 'books' directory...")
        books_dir.mkdir(exist_ok=True)
        print("Please place your PDF files in the 'books' directory and run the script again.")
        return

    # Get target language
    while True:
        target_language = input("Enter target language (e.g., Spanish, French, etc.): ").strip()
        if target_language and target_language.isalpha():
            break
        print("Please enter a valid language name using alphabetic characters.")

    # Create output directory if it doesn't exist
    output_dir = Path("translated_pdfs")
    output_dir.mkdir(exist_ok=True)

    # Get all PDF files from the books directory
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the 'books' directory.")
        return

    print(f"Found {len(pdf_files)} PDF files to translate.")

    # Process each PDF file
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        
        # Read PDF
        print("Reading PDF...")
        text_by_page, images_by_page, original_pdf = read_pdf_with_images(pdf_file)
        
        if text_by_page and original_pdf:
            # Create a PDF writer for the output
            pdf_writer = PdfWriter()
            
            # Process each page
            for i, (page_text, page_images) in enumerate(tqdm(list(zip(text_by_page, images_by_page)), 
                desc="Translating pages", unit="page")):
                print(f"Translating page {i+1} of {len(text_by_page)}...")
                translated_text = translate_text(client, page_text, target_language)
                
                if translated_text:
                    # Create new page with translated text and images
                    new_page_pdf = create_pdf_page_with_images(translated_text, page_images)
                    translated_page = new_page_pdf.pages[0]
                    pdf_writer.add_page(translated_page)
                else:
                    print(f"Translation failed for page {i+1}")

            # Save the translated PDF
            output_file = output_dir / f"translated_{pdf_file.stem}.pdf"
            try:
                with open(output_file, "wb") as output_pdf:
                    pdf_writer.write(output_pdf)
                print(f"Translation completed! Saved to: {output_file}")
            except IOError as e:
                print(f"Error saving translated PDF: {e}")
        else:
            print(f"Failed to read PDF file: {pdf_file.name}")

    print("\nAll translations completed!")

if __name__ == "__main__":
    main()
