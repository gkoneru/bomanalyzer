import re
import csv
import os
from typing import Dict, List, Optional, Tuple

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

if __name__ == "__main__":
    # Example usage
    validator = ItemValidator()
    
    # Generate sample reference data
    validator.generate_reference_data("reference_items.csv")
    
    # Load the generated data
    validator.load_reference_data("reference_items.csv")
    
    # Test some validations
    test_items = [
        "PCB-X7700",       # Valid
        "CAP-3300-10V",    # Valid
        "RES-2K-0.25W",    # Valid
        "CONN-7777",       # Invalid (missing gender)
        "IC-8085X",        # Valid
        "DIODE-2N4001"     # Invalid (should be 1N)
    ]
    
    for item in test_items:
        valid, error = validator.validate_item_number(item)
        status = "✅ Valid" if valid else f"❌ Invalid: {error}"
        
        if not valid:
            suggestion = validator.suggest_correction(item)
            if suggestion:
                status += f"\n  Suggestion: {suggestion}"
        
        print(f"Item {item}: {status}")
