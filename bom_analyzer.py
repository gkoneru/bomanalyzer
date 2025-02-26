import json
import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from openai import OpenAI

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

class BOMAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model: str = "o3-mini"):
        """
        Initialize the BOM Analyzer with OpenAI API key.
        
        Args:
            api_key: Your OpenAI API key
            model: OpenAI model to use (default: "o3-mini")
        """
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model
    
    def analyze_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze BOM order data for discrepancies using OpenAI's o3-mini model.
        """
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
            response = self.client.chat.completions.create(
                model=self.model,
                reasoning_effort="medium",
                messages=[
                    {"role": "system", "content": "You are a BOM validator assistant that identifies issues in order data."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and parse the JSON response
            result_text = response.choices[0].message.content
            return json.loads(result_text)
        
        except Exception as e:
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

def main():
    """
    Main function to run the BOM Analyzer.
    """
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OpenAI API key not found in environment variables.")
        print("Please set your API key using: export OPENAI_API_KEY='your-api-key'")
        api_key = input("Or enter your OpenAI API key now: ").strip()
        if not api_key:
            print("No API key provided. Exiting.")
            return
    
    # Initialize the analyzer
    analyzer = BOMAnalyzer(api_key)
    
    # Generate sample data
    print("Generating sample BOM order data with issues...")
    order_data = generate_sample_orders(include_issues=True)
    
    # Display the order data
    print("\n📋 Sample BOM Order Data:")
    print(json.dumps(order_data, indent=2))
    
    # Analyze the order
    print("\n🔍 Analyzing BOM order data...")
    analysis_results = analyzer.analyze_order(order_data)
    
    # Display the analysis report
    print("\n📊 Analysis Report:")
    report = analyzer.format_analysis_report(analysis_results)
    print(report)
    
    print("\n🔧 Full Analysis Details:")
    print(json.dumps(analysis_results, indent=2))

if __name__ == "__main__":
    main()
