import unittest
from unittest.mock import patch, ANY
import sys
from pathlib import Path
import tempfile
import shutil

# Add the project root to the Python path, so we can import the `markdrop` module
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdrop.main import main

class TestMarkdropCLI(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test output
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    @patch('sys.argv')
    @patch('markdrop.main.markdrop')
    def test_convert_command(self, mock_markdrop, mock_argv):
        """Test that the 'convert' command calls the markdrop function with the correct arguments."""
        # Set the command-line arguments for this test
        sys.argv = ['markdrop', 'convert', 'dummy.pdf', '--output_dir', self.test_dir]
        main()
        mock_markdrop.assert_called_once_with('dummy.pdf', self.test_dir, ANY)

    @patch('sys.argv')
    @patch('markdrop.main.process_markdown')
    def test_describe_command(self, mock_process_markdown, mock_argv):
        """Test that the 'describe' command calls the process_markdown function."""
        sys.argv = ['markdrop', 'describe', 'dummy.md', '--output_dir', self.test_dir]
        main()
        mock_process_markdown.assert_called_once()

    @patch('sys.argv')
    @patch('markdrop.main.analyze_pdf_images')
    def test_analyze_command(self, mock_analyze_pdf_images, mock_argv):
        """Test that the 'analyze' command calls the analyze_pdf_images function."""
        sys.argv = ['markdrop', 'analyze', 'dummy.pdf', '--output_dir', self.test_dir]
        main()
        mock_analyze_pdf_images.assert_called_once_with('dummy.pdf', self.test_dir, verbose=True, save_images=False)

    @patch('sys.argv')
    @patch('markdrop.main.setup_keys')
    def test_setup_command(self, mock_setup_keys, mock_argv):
        """Test that the 'setup' command calls the setup_keys function."""
        sys.argv = ['markdrop', 'setup', 'gemini']
        main()
        mock_setup_keys.assert_called_once_with('gemini')

    @patch('sys.argv')
    @patch('markdrop.main.generate_descriptions')
    def test_generate_command(self, mock_generate_descriptions, mock_argv):
        """Test that the 'generate' command calls the generate_descriptions function."""
        sys.argv = ['markdrop', 'generate', 'dummy_images', '--output_dir', self.test_dir]
        main()
        mock_generate_descriptions.assert_called_once_with(
            input_path='dummy_images',
            output_dir=self.test_dir,
            prompt='Describe the image in detail.',
            llm_client=['gemini']
        )

if __name__ == '__main__':
    unittest.main()