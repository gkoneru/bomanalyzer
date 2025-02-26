### Using Azure OpenAI


# Single order analysis with Azure OpenAI
python bom_cli.py --sample --provider azure --azure-endpoint "https://your-resource.openai.azure.com" --azure-deployment "your-deployment-name"

# Batch processing with Azure OpenAI
python batch_processor.py --input-dir ./sample_orders --provider azure --azure-deployment "your-deployment-name"

# BOM Order Analyzer

A Python application that analyzes Bill of Materials (BOM) order data for missing entries or discrepancies using OpenAI's o3-mini model or Azure OpenAI Service.

## Features

- Validates BOM item data for completeness and correctness
- Identifies missing required fields
- Validates item number formats against expected patterns
- Detects duplicate line IDs
- Provides detailed analysis reports with severity ratings
- Suggests corrections for problematic entries
- Command-line interface for batch processing
- Supports both OpenAI and Azure OpenAI services

## Setup

1. Clone this repository:
   
   git clone https://github.com/yourusername/bom-order-analyzer.git
   cd bom-order-analyzer
   

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set your API key:

   For OpenAI:
   ```
   export OPENAI_API_KEY='your-api-key'
   ```

   For Azure OpenAI:
   ```
   export AZURE_OPENAI_API_KEY='your-azure-api-key'
   export AZURE_OPENAI_ENDPOINT='https://your-resource-name.openai.azure.com'
   ```

## Usage

### Single Order Processing

#### Generate and Analyze Sample Data

```bash
python bom_cli.py --sample
```

### Generate Clean Sample Data (No Issues)

```bash
python bom_cli.py --clean
```

### Save Sample Data to a File

```bash
python bom_cli.py --sample --save-sample sample_order.json
```

### Analyze an Existing Order File

```bash
python bom_cli.py --input your_order_file.json
```

### Save Analysis Results

```bash
# Save as JSON
python bom_cli.py --input your_order_file.json --output analysis_results.json

# Save as CSV report
python bom_cli.py --input your_order_file.json --csv analysis_report.csv

# Save as both JSON and CSV
python bom_cli.py --input your_order_file.json --output analysis_results.json --csv analysis_report.csv
```

### Generate Reference Data for Item Validation

```bash
python item_validator.py
```

### Batch Processing

Process multiple BOM order files at once:

```bash
# Generate 5 sample orders for testing
python batch_processor.py --generate-samples 5

# Process all orders in a directory
python batch_processor.py --input-dir ./sample_orders --output-dir ./analysis_results

# Create consolidated CSV report
python batch_processor.py --input-dir ./sample_orders --csv consolidated_report.csv

# Generate samples and process them in one command
python batch_processor.py --generate-samples 10 --csv consolidated_report.csv
```

## Sample Order Data Structure

```json
{
  "order_id": "ORD-2025-7834",
  "customer": "Acme Electronics",
  "date": "2025-02-26",
  "priority": "High",
  "items": [
    {
      "line_id": "L001",
      "item_number": "PCB-X7700",
      "description": "Main Circuit Board",
      "quantity": 5,
      "unit_price": 120.50,
      "category": "Electronics"
    },
    ...
  ]
}
```

## Analysis Output Structure

```json
{
  "issues_found": true,
  "total_issues": 3,
  "analysis": [
    {
      "issue_type": "Missing Field",
      "location": "Line ID L004",
      "description": "Missing required field 'unit_price'",
      "severity": "high",
      "recommendation": "Add unit_price field to complete the entry"
    },
    ...
  ]
}
```

## Project Structure

- `bom_analyzer.py` - Core BOM analysis functionality
- `bom_cli.py` - Command-line interface for single orders
- `batch_processor.py` - Process multiple BOM orders in batch
- `item_validator.py` - Item number validation utilities
- `requirements.txt` - Python dependencies

## OpenAI Model Options

This application supports multiple model options:

| Model | Provider | Description | Use Case |
|-------|----------|-------------|----------|
| o3-mini | OpenAI | Light and fast model with reasoning capabilities | Quick validation of BOM data |
| o1-mini | OpenAI | Basic analytical model | Simple validation tasks |
| GPT-4o | Azure OpenAI | Full featured model available on Azure | Enterprise-grade validation with Azure security compliance |

To specify the model and provider:
```bash
# For OpenAI
python bom_cli.py --sample --provider openai --model o3-mini

# For Azure OpenAI
python bom_cli.py --sample --provider azure --model your-model --azure-endpoint "https://your-resource.openai.azure.com" --azure-deployment "your-deployment-name"
```

## License

MIT
