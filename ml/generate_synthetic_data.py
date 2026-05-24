import csv
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "synthetic_lotto_history.csv"


def generate_one_draw(round_number):
    winning_numbers = sorted(random.sample(range(1, 46), 6))

    bonus_candidates = list(set(range(1, 46)) - set(winning_numbers))
    bonus_number = random.choice(bonus_candidates)

    return {
        "round": round_number,
        "n1": winning_numbers[0],
        "n2": winning_numbers[1],
        "n3": winning_numbers[2],
        "n4": winning_numbers[3],
        "n5": winning_numbers[4],
        "n6": winning_numbers[5],
        "bonus": bonus_number,
    }


def generate_history(total_rounds=1000, seed=42):
    random.seed(seed)

    rows = []

    for round_number in range(1, total_rounds + 1):
        row = generate_one_draw(round_number)
        rows.append(row)

    return rows


def save_history(rows):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = ["round", "n1", "n2", "n3", "n4", "n5", "n6", "bonus"]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = generate_history(total_rounds=1000, seed=42)
    save_history(rows)

    print(f"Synthetic lotto history saved to: {OUTPUT_PATH}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()