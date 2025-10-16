#!/usr/bin/env python3
"""
Calorie Tracker - A Python script that tracks food intake using a local LLM.

This script:
1. Takes user input for food type and amount
2. Sends data to a local Qwen3 LLM to get nutritional information
3. Saves the data to a daily JSON file
4. Calculates and displays remaining calories for the day
5. Commits and pushes the data to git
"""

import argparse
import json
import os
import re
import requests
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class CalorieTracker:
    """Main calorie tracker class."""
    
    def __init__(self, daily_limit: int = 3000, llm_url: str = "http://localhost:11434/api/generate"):
        """Initialize the calorie tracker.
        
        Args:
            daily_limit: Daily calorie limit (default: 3000)
            llm_url: URL for the local LLM API
        """
        self.daily_limit = daily_limit
        self.llm_url = llm_url
        self.tracker_dir = Path("tracker")
        self.tracker_dir.mkdir(exist_ok=True)
        
        # Pull latest changes from git at startup
        self.pull_from_git()
    
    def pull_from_git(self) -> None:
        """Pull latest changes from git repository to sync daily tracker files."""
        try:
            print("📥 Pulling latest data from GitHub...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print("✅ Successfully pulled latest data from GitHub")
            else:
                print(f"⚠️  Git pull completed with warnings: {result.stderr.strip()}")
        except Exception as e:
            print(f"⚠️  Warning: Could not pull from git: {e}")
            print("📝 Continuing with local data...")
    
    def load_daily_data(self, date_str: str) -> List[Dict]:
        """Load existing daily data from JSON file.
        
        Args:
            date_str: Date string in YY-MM-DD format
            
        Returns:
            List of existing food entries for the day
        """
        file_path = self.tracker_dir / f"{date_str}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data.get('entries', [])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Warning: Could not read existing data from {file_path}: {e}")
                return []
        return []
    
    def get_user_input(self, food_descriptions: List[str] = None) -> List[str]:
        """Get food descriptions with amounts from arguments or user input.
        
        Args:
            food_descriptions: List of food descriptions with amounts from command line args
        
        Returns:
            List of food descriptions including amounts
        """
        print("🍽️  Calorie Tracker")
        print("=" * 40)
        
        # Get food descriptions with amounts (from args or prompt)
        if food_descriptions:
            print(f"Processing {len(food_descriptions)} food items:")
            for i, food in enumerate(food_descriptions, 1):
                print(f"  {i}. {food}")
            return food_descriptions
        else:
            food_description = input("What did you eat? (include amount, e.g., '200g ramen noodles', '2 slices pizza'): ").strip()
            if not food_description:
                raise ValueError("Food description cannot be empty")
            return [food_description]
    
    def query_llm(self, food_description: str) -> Dict[str, float]:
        """Query the local LLM for nutritional information.
        
        Args:
            food_description: Description of the food with amount included
            
        Returns:
            Dictionary with nutritional information
        """
        prompt = f"You are a calorie tracking application. Your user ate {food_description}, how many proteins, carbs, fat and total number of calories did it have? Provide only 4 numbers, cut the rest"
        
        payload = {
            "model": "qwen3:8b",
            "prompt": prompt,
            "stream": False
        }
        
        try:
            print(f"🤖 Querying LLM for nutritional info...")
            response = requests.post(self.llm_url, json=payload)
            response.raise_for_status()
            
            llm_response = response.json().get("response", "")
            print(f"📊 LLM Response: {llm_response}")
            
            return self.parse_nutritional_data(llm_response)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query LLM: {e}")
    
    def parse_nutritional_data(self, llm_response: str) -> Dict[str, float]:
        """Parse nutritional data from LLM response.
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            Dictionary with parsed nutritional data
        """
        # Extract numbers from the response
        numbers = re.findall(r'\d+\.?\d*', llm_response)
        
        if len(numbers) < 4:
            raise ValueError(f"Expected 4 numbers from LLM, got {len(numbers)}: {numbers}")
        
        try:
            return {
                "proteins": float(numbers[0]),
                "carbs": float(numbers[1]),
                "fat": float(numbers[2]),
                "calories": float(numbers[3])
            }
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse nutritional data: {e}")
    
    def save_to_file(self, food_description: str, nutrition: Dict[str, float]) -> str:
        """Save food entry to daily JSON file.
        
        Args:
            food_description: Description of the food with amount included
            nutrition: Nutritional information
            
        Returns:
            Path to the saved file
        """
        today = datetime.now()
        date_str = today.strftime('%y-%m-%d')
        filename = f"{date_str}.json"
        filepath = self.tracker_dir / filename
        
        # Load existing data for the day
        existing_entries = self.load_daily_data(date_str)
        
        # Create new entry
        entry = {
            "timestamp": today.isoformat(),
            "food": food_description,
            "nutrition": nutrition
        }
        
        # Add new entry to existing entries
        existing_entries.append(entry)
        
        # Calculate total calories
        total_calories = sum(e["nutrition"]["calories"] for e in existing_entries)
        
        # Create complete data structure
        data = {
            "entries": existing_entries,
            "total_calories": total_calories,
            "date": date_str
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved to {filepath}")
        print(f"📊 Total entries today: {len(existing_entries)}")
        return str(filepath)
    
    def calculate_remaining_calories(self) -> Tuple[float, float]:
        """Calculate remaining calories for today.
        
        Returns:
            Tuple of (consumed_calories, remaining_calories)
        """
        today = datetime.now()
        date_str = today.strftime('%y-%m-%d')
        
        # Load existing entries for today
        existing_entries = self.load_daily_data(date_str)
        
        # Calculate total consumed calories
        consumed = sum(entry["nutrition"]["calories"] for entry in existing_entries)
        remaining = self.daily_limit - consumed
        
        return consumed, remaining
    
    def display_existing_entries(self) -> None:
        """Display existing food entries for today."""
        today = datetime.now()
        date_str = today.strftime('%y-%m-%d')
        existing_entries = self.load_daily_data(date_str)
        
        if existing_entries:
            print(f"\n📋 Existing entries for today ({date_str}):")
            print("-" * 40)
            for i, entry in enumerate(existing_entries, 1):
                timestamp = entry["timestamp"].split("T")[1][:5]  # Show only time
                nutrition = entry["nutrition"]
                print(f"{i}. [{timestamp}] {entry['food']}")
                print(f"   🥩 {nutrition['proteins']:.1f}g protein, 🍞 {nutrition['carbs']:.1f}g carbs, "
                      f"🥑 {nutrition['fat']:.1f}g fat, 🔥 {nutrition['calories']:.1f} cal")
            print("-" * 40)
        else:
            print(f"\n📋 No entries found for today ({date_str})")
            print("-" * 40)
    
    def display_daily_summary(self, consumed: float, remaining: float):
        """Display daily calorie summary.
        
        Args:
            consumed: Calories consumed today
            remaining: Calories remaining for today
        """
        print("\n" + "=" * 40)
        print("📈 Daily Calorie Summary")
        print("=" * 40)
        print(f"🎯 Daily Limit: {self.daily_limit} calories")
        print(f"🔥 Consumed: {consumed:.1f} calories")
        print(f"💚 Remaining: {remaining:.1f} calories")
        
        if remaining < 0:
            print(f"⚠️  You've exceeded your daily limit by {abs(remaining):.1f} calories!")
        elif remaining < 200:
            print("⚡ You're almost at your daily limit!")
        else:
            print("✅ You're doing great! Keep it up!")
    
    def git_commit_and_push(self, filepath: str):
        """Commit and push the tracker file to git.
        
        Args:
            filepath: Path to the file to commit
        """
        try:
            print("\n🔄 Committing to Git...")
            
            # Add the file
            subprocess.run(['git', 'add', filepath], check=True, cwd='.')
            
            # Create commit message
            today = datetime.now().strftime('%Y-%m-%d')
            commit_msg = f"Update calorie tracker for {today}"
            
            # Commit
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True, cwd='.')
            
            # Push
            subprocess.run(['git', 'push'], check=True, cwd='.')
            
            print("✅ Successfully committed and pushed to GitHub!")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git operation failed: {e}")
            print("You may need to manually commit and push the changes.")
    
    def run(self, food_descriptions: List[str] = None):
        """Main execution method.
        
        Args:
            food_descriptions: List of food descriptions with amounts from command line args
        """
        try:
            # Display existing entries and current status
            self.display_existing_entries()
            consumed, remaining = self.calculate_remaining_calories()
            
            if consumed > 0:
                print(f"🔥 Current status: {consumed:.1f}/{self.daily_limit} calories consumed")
                print(f"💚 Remaining: {remaining:.1f} calories")
                print()
            
            # Get user input (from args or interactive)
            food_descriptions = self.get_user_input(food_descriptions)
            
            # Process each food item sequentially
            filepaths = []
            for i, food_description in enumerate(food_descriptions, 1):
                print(f"\n🔄 Processing item {i}/{len(food_descriptions)}: {food_description}")
                
                # Query LLM for nutritional data
                nutrition = self.query_llm(food_description)
                
                # Save to file
                filepath = self.save_to_file(food_description, nutrition)
                filepaths.append(filepath)
                
                # Show calories for this item
                print(f"✅ Added: {nutrition['calories']:.1f} calories")
            
            # Calculate and display final daily summary
            consumed, remaining = self.calculate_remaining_calories()
            self.display_daily_summary(consumed, remaining)
            
            # Git commit and push only after all items are processed
            if filepaths:
                print(f"\n🔄 Committing all {len(food_descriptions)} food entries to Git...")
                self.git_commit_and_push(filepaths[0])  # All entries go to the same daily file
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Entry point for the calorie tracker."""
    parser = argparse.ArgumentParser(
        description="Calorie Tracker - Track your food intake using a local LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                              # Interactive mode - prompts for input
  %(prog)s "2 slices pizza"                             # Single food entry
  %(prog)s "150g chicken breast" "1 cup rice"           # Multiple food entries
  %(prog)s "300ml milk" "1 apple" "50g nuts"            # Batch processing multiple items
  %(prog)s "1 cup rice with vegetables"                 # Complex food description
        """
    )
    
    parser.add_argument(
        "foods", 
        nargs="*", 
        help="Description(s) of the food eaten including amounts (e.g., '2 slices pizza', '150g chicken breast')"
    )
    
    args = parser.parse_args()
    
    # Convert empty list to None for interactive mode
    food_descriptions = args.foods if args.foods else None
    
    tracker = CalorieTracker()
    tracker.run(food_descriptions)


if __name__ == "__main__":
    main()