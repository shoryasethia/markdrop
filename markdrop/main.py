import argparse
from pathlib import Path
from .process import markdrop, add_downloadable_tables, MarkDropConfig
from .parse import process_markdown, ProcessorConfig, AIProvider
from .helper import analyze_pdf_images
from .setup_keys import setup_keys
from .models.img_descriptions import generate_descriptions

def main():
    

    parser = argparse.ArgumentParser(
        description="MarkDrop: A comprehensive PDF processing toolkit.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 'convert' command
    convert_parser = subparsers.add_parser('convert', help='Convert PDF to markdown and HTML. Deprecates make_markdown, extract_images, and extract_tables_from_pdf functions.')
    convert_parser.add_argument('input_path', type=str, help='Path or URL to the input PDF file')
    convert_parser.add_argument('--output_dir', type=str, default='output', help='Directory to save output files')
    convert_parser.add_argument('--add_tables', action='store_true', help='Add downloadable tables to the HTML output')

    # 'describe' command
    describe_parser = subparsers.add_parser('describe', help='Generate descriptions for images and tables in a markdown file')
    describe_parser.add_argument('input_path', type=str, help='Path to the markdown file')
    describe_parser.add_argument('--output_dir', type=str, default='output', help='Directory to save the processed file')
    describe_parser.add_argument('--ai_provider', type=str, choices=['gemini', 'openai'], default='gemini', help='AI provider to use')
    describe_parser.add_argument('--remove_images', action='store_true', help='Remove images from the markdown file')
    describe_parser.add_argument('--remove_tables', action='store_true', help='Remove tables from the markdown file')

    # 'analyze' command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze images in a PDF file')
    analyze_parser.add_argument('input_path', type=str, help='Path or URL to the PDF file')
    analyze_parser.add_argument('--output_dir', type=str, default='output/analysis', help='Directory to save analysis results')
    analyze_parser.add_argument('--save_images', action='store_true', help='Save extracted images')

    # 'setup' command
    setup_parser = subparsers.add_parser('setup', help='Set up API keys for AI providers')
    setup_parser.add_argument('provider', type=str, choices=['gemini', 'openai'], help='The AI provider to set up (gemini or openai)')

    # 'generate' command for image descriptions
    generate_parser = subparsers.add_parser('generate', help='Generate descriptions for images')
    generate_parser.add_argument('input_path', type=str, help='Path to an image file or a directory of images')
    generate_parser.add_argument('--output_dir', type=str, default='output/descriptions', help='Directory to save the descriptions CSV')
    generate_parser.add_argument('--prompt', type=str, default='Describe the image in detail.', help='Prompt for the AI model')
    generate_parser.add_argument('--llm_client', nargs='+', default=['gemini'], help='List of LLM clients to use')

    args = parser.parse_args()

    if args.command == 'convert':
        config = MarkDropConfig()
        output_dir = Path(args.output_dir)
        html_path = markdrop(args.input_path, str(output_dir), config)
        if args.add_tables:
            add_downloadable_tables(html_path, config)
        print(f"Conversion complete. Output saved in {output_dir}")

    elif args.command == 'describe':
        config = ProcessorConfig(
            input_path=str(Path(args.input_path)),
            output_dir=str(Path(args.output_dir)),
            ai_provider=AIProvider(args.ai_provider),
            remove_images=args.remove_images,
            remove_tables=args.remove_tables
        )
        process_markdown(config)
        print(f"Description generation complete. Output saved in {args.output_dir}")

    elif args.command == 'analyze':
        analyze_pdf_images(args.input_path, args.output_dir, verbose=True, save_images=args.save_images)
        print(f"Analysis complete. Results saved in {args.output_dir}")

    elif args.command == 'setup':
        setup_keys(args.provider)

    elif args.command == 'generate':
        generate_descriptions(
            input_path=args.input_path,
            output_dir=args.output_dir,
            prompt=args.prompt,
            llm_client=args.llm_client
        )
        print(f"Image description generation complete. Output saved in {args.output_dir}")

if __name__ == "__main__":
    main()