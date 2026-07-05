from PyPDF2 import PdfReader
import io

def extract_text_from_pdf(file_input) -> str:
    """
    Extract text from a PDF. 
    Can handle a file path (string) or a file-like object (stream) from a web upload.
    """
    extracted_text = []

    try:
        # If it's bytes, wrap it in a BytesIO stream
        if isinstance(file_input, bytes):
            file_input = io.BytesIO(file_input)
        
        # PdfReader can take a file path or a stream
        reader = PdfReader(file_input)

        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)

        return "\n".join(extracted_text)

    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""

# The __main__ block is now kept only for quick standalone testing if needed,
# but the core logic is fully compatible with web uploads.
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "rb") as f:
            print(extract_text_from_pdf(f))
    else:
        print("Usage: python pdf_reader.py <path_to_pdf>")
