# Calorie Tracker

A Python script that tracks your daily food intake using a local LLM (Qwen3) to calculate nutritional information.

## Features

- 🍽️ Interactive food entry (type and amount)
- 🤖 Uses local Qwen3 LLM for nutritional analysis
- 💾 Saves daily data to JSON files (`tracker/YY-MM-DD.json`)
- 📊 Calculates remaining calories from 3000 daily limit
- 🔄 Automatic Git commit and push

## Requirements

- Python 3.7+
- Local Qwen3 LLM running on `http://localhost:11434`
- Git repository initialized

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install requests
   ```

## Usage

Run the calorie tracker:

```bash
python calorie_tracker.py
```

The script will:
1. Ask for the food you ate
2. Ask for the amount
3. Query the local LLM for nutritional info
4. Save the data to a daily JSON file
5. Show your daily calorie summary
6. Commit and push the changes to Git

## Example

```
🍽️  Calorie Tracker
========================================
What food did you eat? (e.g., 'ramen noodles'): pizza
How much did you eat? (e.g., '200g', '1 cup'): 2 slices

🤖 Querying LLM for nutritional info...
📊 LLM Response: 25 45 18 420
💾 Saved to tracker/25-10-13.json

========================================
📈 Daily Calorie Summary
========================================
🎯 Daily Limit: 3000 calories
🔥 Consumed: 420.0 calories
💚 Remaining: 2580.0 calories
✅ You're doing great! Keep it up!

🔄 Committing to Git...
✅ Successfully committed and pushed to GitHub!
```

## File Structure

```
tracker/
├── 25-10-13.json    # Daily tracking files (YY-MM-DD format)
├── 25-10-14.json
└── ...
```

Each daily file contains:
```json
{
  "entries": [
    {
      "timestamp": "2025-10-13T15:30:00.123456",
      "food": "pizza",
      "amount": "2 slices",
      "nutrition": {
        "proteins": 25.0,
        "carbs": 45.0,
        "fat": 18.0,
        "calories": 420.0
      }
    }
  ],
  "total_calories": 420.0
}
```

## Configuration

You can modify the daily calorie limit by editing the `CalorieTracker` initialization in `calorie_tracker.py`:

```python
tracker = CalorieTracker(daily_limit=2500)  # Change from default 3000
```
