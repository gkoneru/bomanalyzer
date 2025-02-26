import os
import json
import argparse
import glob
from typing import List, Dict, Any
from dotenv import load_dotenv
from bom_analyzer import BOMAnalyzer, generate_sample_orders

# Load environment variables from .env file
load_dotenv()

def process_batch(
    input_dir: str, 
    output_dir: str, 
    csv_report: str = None,
    provider: str = 'openai',
    model: str = 'o3-mini',
    azure_endpoint: str = None,
    azure_deployment: str = None,
    azure_api_version: str = '2024-02-01',
    reference_file: str = None,
    skip_local_validation: bool = False
) -> None:
    """
    Process all JSON files in the input directory and save analysis results to the output directory.
    
    Args:
        input_dir: Directory containing BOM order JSON files
        output_dir: Directory to save analysis results
        csv_report: Optional CSV file to save consolidated report
        provider: API provider to use ('openai' or 'azure')
        model: Model to use (default: 'o3-mini')
        azure_endpoint: Azure OpenAI endpoint URL
        azure_deployment: Azure OpenAI deployment name
        azure_api_version: Azure OpenAI API version
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check for API key based on provider
    if provider == 'azure':
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not api_key:
            print("⚠️ Azure OpenAI API key not found in environment variables.")
            print("Please set your API key using: export AZURE_OPENAI_API_KEY='your-api-key'")
            api_key = input("Or enter your Azure OpenAI API key now: ").strip()
            if not api_key:
                print("No API key provided. Exiting.")
                return
                
        # Check Azure-specific requirements
        if not azure_endpoint:
            azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            if not azure_endpoint:
                azure_endpoint = input("Enter your Azure OpenAI endpoint URL: ").strip()
                if not azure_endpoint:
                    print("Azure endpoint URL is required when using Azure provider. Exiting.")
                    return
                
        if not azure_deployment:
            azure_deployment = input("Enter your Azure OpenAI deployment name: ").strip()
            if not azure_deployment:
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
    if provider == 'azure':
        analyzer = BOMAnalyzer(
            api_key=api_key,
            model=model,
            provider='azure',
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            azure_api_version=azure_api_version,
            reference_file=reference_file
        )
    else:
        analyzer = BOMAnalyzer(
            api_key=api_key, 
            model=model,
            reference_file=reference_file
        )
    
    # Find all JSON files in the input directory
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Process each file
    for i, json_file in enumerate(json_files, 1):
        file_name = os.path.basename(json_file)
        print(f"\n[{i}/{len(json_files)}] Processing {file_name}...")
        
        try:
            # Load order data
            with open(json_file, 'r') as f:
                order_data = json.load(f)
            
            # Analyze the order
            analysis_results = analyzer.analyze_order(
                order_data, 
                use_local_validation=not skip_local_validation
            )
            
            # Save analysis results to output directory
            output_file = os.path.join(output_dir, f"analysis_{file_name}")
            with open(output_file, 'w') as f:
                json.dump(analysis_results, f, indent=2)
            
            # Add to CSV report if requested
            if csv_report:
                order_id = order_data.get("order_id", os.path.splitext(file_name)[0])
                analyzer.save_analysis_to_csv(order_id, analysis_results, csv_report)
            
            # Display summary
            issues_found = analysis_results.get("issues_found", False)
            total_issues = analysis_results.get("total_issues", 0)
            status = f"🚨 {total_issues} issues found" if issues_found else "✅ No issues"
            print(f"Completed: {status}")
            
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
    
    print(f"\nBatch processing complete. Results saved to {output_dir}")
    if csv_report:
        print(f"Consolidated report saved to {csv_report}")

def generate_sample_batch(output_dir: str, num_samples: int = 5) -> None:
    """
    Generate sample BOM orders for testing batch processing.
    
    Args:
        output_dir: Directory to save sample files
        num_samples: Number of sample files to generate
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(1, num_samples + 1):
        # Alternate between clean and problematic samples
        include_issues = (i % 2 == 0)
        
        # Generate sample data
        sample_data = generate_sample_orders(include_issues=include_issues)
        
        # Modify order ID to make each sample unique
        sample_data["order_id"] = f"ORD-2025-{7800 + i}"
        
        # Add random variations to make samples more diverse
        if i % 3 == 0:
            sample_data["priority"] = "Medium"
        elif i % 3 == 1:
            sample_data["priority"] = "Low"
        
        # Save sample to file
        status = "problematic" if include_issues else "clean"
        filename = os.path.join(output_dir, f"sample_order_{i}_{status}.json")
        
        with open(filename, 'w') as f:
            json.dump(sample_data, f, indent=2)
    
    print(f"Generated {num_samples} sample files in {output_dir}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='BOM Order Batch Processor')
    parser.add_argument('--input-dir', '-i', help='Directory containing BOM order JSON files')
    parser.add_argument('--output-dir', '-o', default='./analysis_results', help='Directory to save analysis results')
    parser.add_argument('--csv', help='Save consolidated analysis to CSV report file')
    parser.add_argument('--generate-samples', '-g', type=int, help='Generate sample files (specify number)')
    parser.add_argument('--samples-dir', default='./sample_orders', help='Directory to save generated samples')
    parser.add_argument('--provider', choices=['openai', 'azure'], default='openai', help='API provider to use (openai or azure)')
    parser.add_argument('--model', default='o3-mini', help='Model to use (default: o3-mini)')
    parser.add_argument('--azure-endpoint', help='Azure OpenAI endpoint URL')
    parser.add_argument('--azure-deployment', help='Azure OpenAI deployment name')
    parser.add_argument('--azure-api-version', default='2024-02-01', help='Azure OpenAI API version')
    parser.add_argument('--reference-file', help='Path to reference data CSV file for item validation')
    parser.add_argument('--generate-reference', help='Generate sample reference data to specified file')
    parser.add_argument('--skip-local-validation', action='store_true', help='Skip local item validation (use only AI analysis)')
    
    args = parser.parse_args()
    
    # Generate samples if requested
    if args.generate_samples:
        generate_sample_batch(args.samples_dir, args.generate_samples)
        if not args.input_dir:
            # If input directory wasn't specified, use the samples directory
            args.input_dir = args.samples_dir
    
    # Process batch if input directory is specified
    if args.input_dir:
        process_batch(
            args.input_dir, 
            args.output_dir, 
            args.csv,
            provider=args.provider,
            model=args.model,
            azure_endpoint=args.azure_endpoint,
            azure_deployment=args.azure_deployment,
            azure_api_version=args.azure_api_version,
            reference_file=args.reference_file,
            skip_local_validation=args.skip_local_validation
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
