import json
import os
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Tuple
import pandas as pd
from openai import OpenAI, AzureOpenAI


# Sample data generation
def generate_sample_orders(include_issues: bool = True) -> Dict[str, Any]:
    """
    Generate sample BOM order data with deliberate issues if specified.
    """
    base_order = {
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
            {
                "line_id": "L002",
                "item_number": "CAP-3300-10V",
                "description": "10V Capacitor",
                "quantity": 50,
                "unit_price": 0.75,
                "category": "Components"
            },
            {
                "line_id": "L003",
                "item_number": "RES-2K-0.25W",
                "description": "2K Ohm Resistor",
                "quantity": 100,
                "unit_price": 0.25,
                "category": "Components"
            }
        ]
    }
    
    if not include_issues:
        return base_order
    
    # Create a version with issues
    problematic_order = base_order.copy()
    problematic_items = base_order["items"].copy()
    
    # Issue 1: Missing entry (missing unit_price)
    problematic_items.append({
        "line_id": "L004",
        "item_number": "IC-8085",
        "description": "Microprocessor",
        "quantity": 2,
        # unit_price is missing
        "category": "Electronics"
    })
    
    # Issue 2: Wrong item number format
    problematic_items.append({
        "line_id": "L005",
        "item_number": "CONN-7777",  # Should be CONN-DB9-F
        "description": "DB9 Female Connector",
        "quantity": 10,
        "unit_price": 1.20,
        "category": "Connectors"
    })
    
    # Issue 3: Duplicate line_id
    problematic_items.append({
        "line_id": "L003",  # Duplicate line_id
        "item_number": "DIODE-1N4001",
        "description": "1A Diode",
        "quantity": 25,
        "unit_price": 0.15,
        "category": "Components"
    })
    
    problematic_order["items"] = problematic_items
    return problematic_order


class ItemValidator:
    """
    Validates BOM item numbers against reference data and pattern rules.
    """
    def __init__(self, reference_file: Optional[str] = None):
        """
        Initialize the validator with optional reference data.
        
        Args:
            reference_file: Path to CSV file with reference data
        """
        self.reference_items = {}
        self.item_patterns = {
            "PCB": r"^PCB-[A-Z]\d{4}$",            # PCB-X7700
            "CAP": r"^CAP-\d{4}-\d{1,3}V$",        # CAP-3300-10V
            "RES": r"^RES-\d+[KM]?-\d+\.\d+W$",    # RES-2K-0.25W
            "IC": r"^IC-\d{4}[A-Z]?$",             # IC-8085
            "CONN": r"^CONN-[A-Z0-9]+-[MF]$",      # CONN-DB9-F
            "DIODE": r"^DIODE-\d{1}N\d{4}$",       # DIODE-1N4001
        }
        
        if reference_file and os.path.exists(reference_file):
            self.load_reference_data(reference_file)
    
    def load_reference_data(self, filename: str) -> None:
        """
        Load reference data from a CSV file.
        
        Expected CSV format:
        item_number,description,category
        """
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.reference_items[row['item_number']] = {
                        'description': row['description'],
                        'category': row['category']
                    }
            print(f"Loaded {len(self.reference_items)} reference items")
        except Exception as e:
            print(f"Error loading reference data: {str(e)}")
    
    def validate_item_number(self, item_number: str) -> Tuple[bool, str]:
        """
        Validate an item number against patterns and reference data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if it exists in reference data
        if item_number in self.reference_items:
            return True, ""
        
        # Check if it matches any pattern
        prefix = item_number.split('-')[0] if '-' in item_number else ""
        
        if prefix in self.item_patterns:
            pattern = self.item_patterns[prefix]
            if re.match(pattern, item_number):
                return True, ""
            else:
                return False, f"Item number {item_number} does not match expected pattern {pattern}"
        
        return False, f"Unknown item number prefix: {prefix}"
    
    def suggest_correction(self, item_number: str) -> Optional[str]:
        """
        Suggest a correction for an invalid item number.
        
        Returns:
            Suggested correct item number or None
        """
        prefix = item_number.split('-')[0] if '-' in item_number else ""
        
        # Simple correction for common prefixes
        if prefix == "CONN" and not item_number.endswith("-M") and not item_number.endswith("-F"):
            # Missing gender indicator
            return f"{item_number}-F"
        
        # Check reference data for similar items
        similar_items = []
        for ref_item in self.reference_items:
            if prefix in ref_item:
                similar_items.append(ref_item)
        
        if similar_items:
            return similar_items[0]  # Return first similar item
        
        return None
    
    def generate_reference_data(self, output_file: str) -> None:
        """
        Generate sample reference data file.
        """
        reference_data = [
            ["item_number", "description", "category"],
            ["PCB-X7700", "Main Circuit Board", "Electronics"],
            ["CAP-3300-10V", "10V Capacitor", "Components"],
            ["RES-2K-0.25W", "2K Ohm Resistor", "Components"],
            ["IC-8085", "Microprocessor", "Electronics"],
            ["CONN-DB9-F", "DB9 Female Connector", "Connectors"],
            ["CONN-DB9-M", "DB9 Male Connector", "Connectors"],
            ["DIODE-1N4001", "1A Diode", "Components"],
            ["PCB-A1234", "Power Supply Board", "Electronics"],
            ["CAP-2200-25V", "25V Capacitor", "Components"],
            ["RES-10K-0.50W", "10K Ohm Resistor", "Components"]
        ]
        
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(reference_data)
            print(f"Generated reference data saved to {output_file}")
        except Exception as e:
            print(f"Error generating reference data: {str(e)}")


class BOMAnalyzer:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "o3-mini",
        provider: Literal["openai", "azure"] = "openai",
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        azure_api_version: str = "2024-02-01",
        reference_file: Optional[str] = None
    ):
        """
        Initialize the BOM Analyzer with API configuration.
        
        Args:
            api_key: Your API key (OpenAI or Azure OpenAI)
            model: Model to use (default: "o3-mini")
            provider: API provider to use ("openai" or "azure")
            azure_endpoint: Azure OpenAI endpoint URL (required if provider is "azure")
            azure_deployment: Azure OpenAI deployment name (required if provider is "azure")
            azure_api_version: Azure OpenAI API version
            reference_file: Path to CSV file with reference data for item validation
        """
        self.model = model
        self.provider = provider
        
        if provider == "azure":
            if not azure_endpoint or not azure_deployment:
                raise ValueError("Azure endpoint and deployment name are required when using Azure OpenAI")
                
            self.client = AzureOpenAI(
                api_key=api_key or os.environ.get("AZURE_OPENAI_API_KEY"),
                api_version=azure_api_version,
                azure_endpoint=azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
            )
            self.azure_deployment = azure_deployment
        else:
            self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
            self.azure_deployment = None
            
        # Initialize item validator
        self.item_validator = ItemValidator(reference_file)
    
    def validate_item_numbers(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate all item numbers in an order against reference data and patterns.
        
        Args:
            order_data: BOM order data dictionary
            
        Returns:
            List of validation issues found
        """
        validation_issues = []
        
        for item in order_data.get("items", []):
            item_number = item.get("item_number")
            if not item_number:
                continue
                
            valid, error_message = self.item_validator.validate_item_number(item_number)
            
            if not valid:
                line_id = item.get("line_id", "unknown")
                suggestion = self.item_validator.suggest_correction(item_number)
                
                issue = {
                    "issue_type": "Invalid Item Number",
                    "location": f"Line ID {line_id}",
                    "description": error_message,
                    "severity": "medium",
                    "recommendation": "Check and correct item number format" + 
                                     (f" (suggested: {suggestion})" if suggestion else "")
                }
                validation_issues.append(issue)
        
        return validation_issues
    
    def analyze_order(self, order_data: Dict[str, Any], use_local_validation: bool = True) -> Dict[str, Any]:
        """
        Analyze BOM order data for discrepancies using OpenAI's o3-mini model.
        
        Args:
            order_data: BOM order data dictionary
            use_local_validation: Whether to use local item number validation
            
        Returns:
            Analysis results dictionary
        """
        # First perform local validation if enabled
        validation_issues = []
        if use_local_validation:
            validation_issues = self.validate_item_numbers(order_data)
        
        # Prepare the prompt for the model
        order_json = json.dumps(order_data, indent=2)
        
        prompt = f"""
        You are a BOM (Bill of Materials) order validator.
        
        Please analyze the following order data for issues such as:
        1. Missing required fields (all items should have line_id, item_number, description, quantity, unit_price, category)
        2. Incorrect item number formats
        3. Duplicate line IDs
        4. Any other anomalies or inconsistencies
        
        Order data:
        {order_json}
        
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "issues_found": true/false,
            "total_issues": <number of issues>,
            "analysis": [
                {{
                    "issue_type": "<type of issue>",
                    "location": "<where in the order>",
                    "description": "<detailed description>",
                    "severity": "high/medium/low",
                    "recommendation": "<suggested fix>"
                }},
                ...
            ]
        }}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            # Handle different API providers
            if self.provider == "azure":
                response = self.client.chat.completions.create(
                    model=self.azure_deployment,  # For Azure, use deployment name instead of model
                    messages=[
                        # {"role": "system", "content": "You are a BOM validator assistant that identifies issues in order data."},
                        {"role": "user", "content": prompt}
                    ]
                    # temperature=0.1  # Low temperature for more deterministic output
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    reasoning_effort="medium",
                    messages=[
                        # {"role": "system", "content": "You are a BOM validator assistant that identifies issues in order data."},
                        {"role": "user", "content": prompt}
                    ]
                    # temperature=0.1  # Low temperature for more deterministic output
                )
            
            # Extract and parse the JSON response
            result_text = response.choices[0].message.content
            ai_analysis = json.loads(result_text)
            
            # Combine AI analysis with local validation results
            if validation_issues and ai_analysis.get("issues_found", False):
                ai_analysis["analysis"].extend(validation_issues)
                ai_analysis["total_issues"] = len(ai_analysis["analysis"])
            elif validation_issues:
                ai_analysis = {
                    "issues_found": True,
                    "total_issues": len(validation_issues),
                    "analysis": validation_issues
                }
                
            return ai_analysis
        
        except Exception as e:
            # If there's an error with the API but we have validation results, return those
            if validation_issues:
                return {
                    "issues_found": True,
                    "total_issues": len(validation_issues),
                    "analysis": validation_issues
                }
            
            # Otherwise return an error
            return {
                "issues_found": True,
                "total_issues": 1,
                "analysis": [
                    {
                        "issue_type": "API Error",
                        "location": "System",
                        "description": f"Error calling OpenAI API: {str(e)}",
                        "severity": "high",
                        "recommendation": "Check API key and connectivity"
                    }
                ]
            }
    
    def format_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """
        Format the analysis results into a readable report.
        """
        if not analysis.get("issues_found", False):
            return "✅ No issues found in the BOM order data."
        
        report = f"🚨 Found {analysis.get('total_issues', 0)} issues in the BOM order:\n\n"
        
        for i, issue in enumerate(analysis.get("analysis", []), 1):
            severity_icon = "🔴" if issue.get("severity") == "high" else "🟠" if issue.get("severity") == "medium" else "🟡"
            
            report += f"{severity_icon} Issue #{i}: {issue.get('issue_type')}\n"
            report += f"   Location: {issue.get('location')}\n"
            report += f"   Description: {issue.get('description')}\n"
            report += f"   Recommendation: {issue.get('recommendation')}\n\n"
        
        return report
        
    def save_analysis_to_csv(self, order_id: str, analysis: Dict[str, Any], filename: str) -> None:
        """
        Save analysis results to a CSV file for reporting and tracking.
        
        Args:
            order_id: The ID of the analyzed order
            analysis: The analysis results dictionary
            filename: Path to save the CSV file
        """
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'order_id', 'issue_id', 'issue_type', 
                         'location', 'severity', 'description', 'recommendation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if not analysis.get("issues_found", False):
                # Write a single row for no issues
                writer.writerow({
                    'timestamp': timestamp,
                    'order_id': order_id,
                    'issue_id': 'N/A',
                    'issue_type': 'None',
                    'location': 'N/A',
                    'severity': 'N/A',
                    'description': 'No issues found',
                    'recommendation': 'N/A'
                })
            else:
                # Write each issue as a separate row
                for i, issue in enumerate(analysis.get("analysis", []), 1):
                    writer.writerow({
                        'timestamp': timestamp,
                        'order_id': order_id,
                        'issue_id': f"{order_id}-{i}",
                        'issue_type': issue.get('issue_type', 'Unknown'),
                        'location': issue.get('location', 'Unknown'),
                        'severity': issue.get('severity', 'Unknown'),
                        'description': issue.get('description', ''),
                        'recommendation': issue.get('recommendation', '')
                    })
        
        print(f"Analysis saved to CSV: {filename}")
    
    def generate_reference_data(self, output_file: str) -> None:
        """
        Generate sample reference data file.
        
        Args:
            output_file: Path to save the generated reference data
        """
        self.item_validator.generate_reference_data(output_file)
