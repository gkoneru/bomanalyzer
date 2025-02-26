import json
import os
import argparse
from typing import Dict, Any
from dotenv import load_dotenv
from bom_analyzer import BOMAnalyzer, generate_sample_orders

# Load environment variables from .env file
load_dotenv()

def save_results(analysis: Dict[str, Any], filename: str) -> None:
    """Save analysis results to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"Analysis results saved to {filename}")

def load_order(filename: str) -> Dict[str, Any]:
    """Load order data from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {filename}")
        return None

def main():
    parser = argparse.ArgumentParser(description='BOM Order Analyzer CLI')
    parser.add_argument('--input', '-i', help='Input JSON file containing order data')
    parser.add_argument('--output', '-o', help='Output file to save analysis results (JSON)')
    parser.add_argument('--csv', help='Save analysis to CSV report file')
    parser.add_argument('--sample', '-s', action='store_true', help='Generate and use sample data')
    parser.add_argument('--clean', '-c', action='store_true', help='Generate clean sample data without issues')
    parser.add_argument('--save-sample', help='Save generated sample to a file')
    parser.add_argument('--provider', choices=['openai', 'azure'], default='openai', help='API provider to use (openai or azure)')
    parser.add_argument('--model', default='o3-mini', help='Model to use (default: o3-mini)')
    parser.add_argument('--azure-endpoint', help='Azure OpenAI endpoint URL')
    parser.add_argument('--azure-deployment', help='Azure OpenAI deployment name')
    parser.add_argument('--azure-api-version', default='2024-02-01', help='Azure OpenAI API version')
    parser.add_argument('--reference-file', help='Path to reference data CSV file for item validation')
    parser.add_argument('--generate-reference', help='Generate sample reference data to specified file')
    parser.add_argument('--skip-local-validation', action='store_true', help='Skip local item validation (use only AI analysis)')
    
    args = parser.parse_args()
    
    # Check for API key based on provider
    if args.provider == 'azure':
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not api_key:
            print("⚠️ Azure OpenAI API key not found in environment variables.")
            print("Please set your API key using: export AZURE_OPENAI_API_KEY='your-api-key'")
            api_key = input("Or enter your Azure OpenAI API key now: ").strip()
            if not api_key:
                print("No API key provided. Exiting.")
                return
                
        # Check Azure-specific requirements
        if not args.azure_endpoint:
            if not os.environ.get("AZURE_OPENAI_ENDPOINT"):
                args.azure_endpoint = input("Enter your Azure OpenAI endpoint URL: ").strip()
                if not args.azure_endpoint:
                    print("Azure endpoint URL is required when using Azure provider. Exiting.")
                    return
            else:
                args.azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                
        if not args.azure_deployment:
            args.azure_deployment = input("Enter your Azure OpenAI deployment name: ").strip()
            if not args.azure_deployment:
                print("Azure deployment name is required when using Azure provider. Exiting.")
                return
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OpenAI API key not found in environment variables.")
            print("Please set your API key using: export OPENAI_API_KEY='your-api-key'")
            api_key = input("Or enter your OpenAI API key now: ").strip()
            if not api_key:
                print("No API key provided. Exiting.")
                return
    
    # Initialize the analyzer with appropriate provider and settings
    if args.provider == 'azure':
        analyzer = BOMAnalyzer(
            api_key=api_key,
            model=args.model,
            provider='azure',
            azure_endpoint=args.azure_endpoint,
            azure_deployment=args.azure_deployment,
            azure_api_version=args.azure_api_version,
            reference_file=args.reference_file
        )
    else:
        analyzer = BOMAnalyzer(
            api_key=api_key, 
            model=args.model,
            reference_file=args.reference_file
        )
    
    # Generate reference data if requested
    if args.generate_reference:
        analyzer.generate_reference_data(args.generate_reference)
        print(f"Generated reference data. You can now use --reference-file={args.generate_reference}")
        if not args.input and not args.sample and not args.clean:
            return
    
    # Determine the order data source
    order_data = None
    
    if args.input:
        print(f"Loading order data from {args.input}...")
        order_data = load_order(args.input)
        if not order_data:
            return
    elif args.sample or args.clean or not args.input:
        include_issues = not args.clean
        status = "clean" if args.clean else "problematic"
        print(f"Generating {status} sample BOM order data...")
        order_data = generate_sample_orders(include_issues=include_issues)
        
        if args.save_sample:
            with open(args.save_sample, 'w') as f:
                json.dump(order_data, f, indent=2)
            print(f"Sample data saved to {args.save_sample}")
    
    # Display the order data
    print("\n📋 BOM Order Data:")
    print(json.dumps(order_data, indent=2))
    
    # Analyze the order
    print("\n🔍 Analyzing BOM order data...")
    analysis_results = analyzer.analyze_order(
        order_data, 
        use_local_validation=not args.skip_local_validation
    )
    
    # Display the analysis report
    print("\n📊 Analysis Report:")
    report = analyzer.format_analysis_report(analysis_results)
    print(report)
    
    # Save results if requested
    if args.output:
        save_results(analysis_results, args.output)
    
    # Save to CSV if requested
    if args.csv:
        order_id = order_data.get("order_id", "unknown")
        analyzer.save_analysis_to_csv(order_id, analysis_results, args.csv)

if __name__ == "__main__":
    main()
