from setuptools import setup, find_packages

setup(
    name="markdrop",
    
    version="0.3.2.0",

    packages=find_packages(),
    install_requires=[
        "beautifulsoup4",
        "docling",
        "docling_core==2.16.0",
        "openai",
        "openpyxl",
        "pandas",
        "Pillow",
        "protobuf",
        "python-dotenv",
        "pymupdf",
        "torch",
        "tqdm",
        "transformers",
        "timm",
        "requests",
        "qwen_vl_utils",
        "google-generativeai",
        "vllm"
    ],
    author="Shorya Sethia",
    author_email="shoryasethia4may@gmail.com",
    description="A comprehensive PDF processing toolkit that converts PDFs to markdown with advanced AI-powered features for image and table analysis. Supports local files and URLs, preserves document structure, extracts high-quality images, detects tables using advanced ML models, and generates detailed content descriptions using multiple LLM providers including OpenAI and Google's Gemini.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/shoryasethia/markdrop",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup :: Markdown",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    python_requires=">=3.10",
    keywords="pdf markdown converter ai llm table-extraction image-analysis document-processing gemini openai",
)
