from abc import ABC, abstractmethod
import docx

class BaseParser(ABC):
    """
    Abstract base class for all SOP parsers. 
    This guarantees that any future parser will have a parse() method.
    """
    @abstractmethod
    def parse(self, file_path: str) -> list[str]:
        pass

class DocxSOPParser(BaseParser):
    def parse(self, file_path: str) -> list[str]:
        try:
            doc = docx.Document(file_path)
        except docx.opc.exceptions.PackageNotFoundError:
            raise ValueError(f"The file {file_path} is not a valid .docx document or does not exist.")
        except Exception as e:
            raise ValueError(f"Failed to read the .docx file: {e}")

        extracted_steps = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                extracted_steps.append(text)
                
        return extracted_steps