from setuptools import setup, find_packages

setup(
    name="markdrop",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "pymupdf",
        "docling",
        "transformers",
        "torch",
        "Pillow",
        "tqdm"
    ],
    author="Shorya Sethia",
    author_email="shoryasethia4may@gmail.com",
    description="A tool to convert PDFs to markdown with image and table extraction",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/shoryasethia/markdrop",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)