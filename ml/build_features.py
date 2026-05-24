import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_PATH = DATA_DIR / "synthetic_lotto_history.csv"
OUTPUT_PATH = DATA_DIR / "ml_lotto_dataset.csv"


def load_history():
    rows = []

    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            numbers = [
                int(row["n1"]),
                int(row["n2"]),
                int(row["n3"]),
                int(row["n4"]),
                int(row["n5"]),
                int(row["n6"]),
            ]

            rows.append({
                "round": int(row["round"]),
                "numbers": numbers,
                "bonus": int(row["bonus"]),
            })

    return rows


def count_appearances(history_slice, target_number):
    count = 0

    for row in history_slice:
        if target_number in row["numbers"]:
            count += 1

    return count


def rounds_since_last_seen(history_slice, target_number):
    for distance, row in enumerate(reversed(history_slice), start=1):
        if target_number in row["numbers"]:
            return distance

    return len(history_slice) + 1


def get_number_group(number):
    if 1 <= number <= 10:
        return 1
    if 11 <= number <= 20:
        return 2
    if 21 <= number <= 30:
        return 3
    if 31 <= number <= 40:
        return 4
    return 5


def build_dataset(rows, min_history_rounds=20):
    dataset = []

    for current_index in range(min_history_rounds, len(rows) - 1):
        history = rows[:current_index + 1]
        next_draw_numbers = set(rows[current_index + 1]["numbers"])
        current_round = rows[current_index]["round"]

        for target_number in range(1, 46):
            recent_5 = history[-5:]
            recent_10 = history[-10:]
            recent_20 = history[-20:]

            row = {
                "current_round": current_round,
                "target_number": target_number,

                "recent_5_count": count_appearances(recent_5, target_number),
                "recent_10_count": count_appearances(recent_10, target_number),
                "recent_20_count": count_appearances(recent_20, target_number),
                "total_count": count_appearances(history, target_number),
                "rounds_since_last_seen": rounds_since_last_seen(history, target_number),

                "is_odd": 1 if target_number % 2 == 1 else 0,
                "number_group": get_number_group(target_number),

                "label": 1 if target_number in next_draw_numbers else 0,
            }

            dataset.append(row)

    return dataset


def save_dataset(dataset):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "current_round",
        "target_number",
        "recent_5_count",
        "recent_10_count",
        "recent_20_count",
        "total_count",
        "rounds_since_last_seen",
        "is_odd",
        "number_group",
        "label",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dataset)


def main():
    rows = load_history()
    dataset = build_dataset(rows)
    save_dataset(dataset)

    positive_count = sum(row["label"] for row in dataset)
    negative_count = len(dataset) - positive_count

    print(f"ML dataset saved to: {OUTPUT_PATH}")
    print(f"Total rows: {len(dataset)}")
    print(f"Positive labels: {positive_count}")
    print(f"Negative labels: {negative_count}")
    print(f"Positive ratio: {positive_count / len(dataset):.4f}")


if __name__ == "__main__":
    main()