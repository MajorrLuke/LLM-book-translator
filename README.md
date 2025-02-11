# PDF Translator

A Python-based tool that translates PDF documents while preserving images and formatting using Claude AI. This tool maintains the original layout, handles multiple PDF files in batch processing, and supports various image formats.

## Features

- Translates PDF documents to any target language
- Preserves original images and their positioning
- Maintains document formatting and layout
- Supports multiple image formats (RGB, CMYK, JPEG, JPEG2000)
- Handles batch processing of multiple PDF files
- Automatic text wrapping and page formatting
- Conservative margin handling for better readability

## Prerequisites

- Python 3.7 or higher
- Anthropic API key

## Installation

1. Clone the repository:

bash
git clone https://github.com/yourusername/pdf-translator.git
cd pdf-translator

2. Install required dependencies:

bash
pip install -r requirements.txt

3. Create a `.env` file in the root directory and add your Anthropic API key:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

## Project Structure

```
pdf-translator/
├── books/              # Input directory for PDF files
├── translated_pdfs/    # Output directory for translated files
├── .env               # Environment variables
├── .gitignore        # Git ignore file
├── requirements.txt   # Python dependencies
└── run.py            # Main script
```

## Usage

1. Place your PDF files in the `books` directory
2. Run the script:
```bash
python run.py
```
3. When prompted, enter your desired target language (e.g., Spanish, French, German)
4. The script will process each PDF file and save the translated versions in the `translated_pdfs` directory

## Technical Details

- Uses Claude 3 Haiku for high-quality translations
- Implements proper image scaling and positioning
- Handles various PDF image encodings (FlateDecode, DCTDecode, JPXDecode)
- Custom paragraph styling for optimal readability
- Error handling for both translation and PDF processing
- Maintains aspect ratios of embedded images

## Error Handling

The script includes comprehensive error handling for:
- PDF reading/writing operations
- Image extraction and processing
- Translation service communication
- File system operations

## Limitations

- Maximum token limit of 4096 for translations
- Requires proper PDF formatting in source files
- Image quality depends on original PDF


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Anthropic's Claude AI for translation capabilities
- PyPDF2 for PDF processing
- ReportLab for PDF generation
- Pillow for image processing
