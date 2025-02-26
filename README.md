# BOM Order Analyzer

A Python application that analyzes Bill of Materials (BOM) order data for missing entries or discrepancies using OpenAI's o3-mini model.

## Features

- Validates BOM item data for completeness and correctness
- Identifies missing required fields
- Validates item number formats against expected patterns
- Detects duplicate line IDs
- Provides detailed analysis reports with severity ratings
- Suggests corrections for problematic entries
- Command-line interface for batch processing

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/bom-order-analyzer.git
   cd bom-order-analyzer
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY='your-api-key'
   ```

## Usage

### Generate and Analyze Sample Data

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
- `bom_cli.py` - Command-line interface
- `item_validator.py` - Item number validation utilities
- `requirements.txt` - Python dependencies

## OpenAI Model Options

This application uses OpenAI's o3-mini model by default, but you can configure it to use other models:

| Model | Description | Use Case |
|-------|-------------|----------|
| o3-mini | Light and fast model with reasoning capabilities | Quick validation of BOM data |

To change the model, modify the `model` parameter in the `analyze_order` method in `bom_analyzer.py`.

## License

MIT
