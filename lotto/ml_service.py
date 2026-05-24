import random
from pathlib import Path

from .models import Ticket
from .services import generate_random_numbers


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml" / "model" / "best_lotto_model.joblib"
HISTORY_PATH = BASE_DIR / "ml" / "data" / "synthetic_lotto_history.csv"


def load_model_bundle():
    import joblib

    if not MODEL_PATH.exists():
        raise FileNotFoundError("ML 모델 파일이 없습니다. 먼저 ml 컨테이너에서 학습을 실행해주세요.")

    return joblib.load(MODEL_PATH)


def load_history():
    import pandas as pd

    if not HISTORY_PATH.exists():
        raise FileNotFoundError("ML 학습용 이력 데이터가 없습니다.")

    df = pd.read_csv(HISTORY_PATH)

    rows = []

    for _, row in df.iterrows():
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


def build_prediction_features(rows, feature_columns):
    import pandas as pd

    """
    최신 이력 기준으로 1~45번 각각의 feature row를 만든다.
    """
    history = rows

    feature_rows = []

    for target_number in range(1, 46):
        recent_5 = history[-5:]
        recent_10 = history[-10:]
        recent_20 = history[-20:]

        feature_rows.append({
            "target_number": target_number,
            "recent_5_count": count_appearances(recent_5, target_number),
            "recent_10_count": count_appearances(recent_10, target_number),
            "recent_20_count": count_appearances(recent_20, target_number),
            "total_count": count_appearances(history, target_number),
            "rounds_since_last_seen": rounds_since_last_seen(history, target_number),
            "is_odd": 1 if target_number % 2 == 1 else 0,
            "number_group": get_number_group(target_number),
        })

    return pd.DataFrame(feature_rows)[feature_columns]


def normalize_probabilities(scores, temperature=1.5):
    """
    모델 점수를 weighted sampling에 사용할 확률로 변환한다.
    temperature가 높을수록 추천이 더 다양해진다.
    """
    adjusted_scores = [max(score, 0.000001) ** (1 / temperature) for score in scores]
    total = sum(adjusted_scores)

    return [score / total for score in adjusted_scores]


def weighted_sample_numbers(probabilities):
    numbers = list(range(1, 46))

    selected_numbers = random.choices(
        population=numbers,
        weights=probabilities,
        k=12,
    )

    unique_numbers = []

    for number in selected_numbers:
        if number not in unique_numbers:
            unique_numbers.append(number)

        if len(unique_numbers) == 6:
            break

    while len(unique_numbers) < 6:
        candidate = random.randint(1, 45)

        if candidate not in unique_numbers:
            unique_numbers.append(candidate)

    return sorted(unique_numbers)


def user_already_has_same_numbers(user, draw, numbers):
    normalized_numbers = sorted(numbers)

    return Ticket.objects.filter(
        user=user,
        draw=draw,
        numbers=normalized_numbers,
    ).exists()


def recommend_lotto_numbers(user, draw):
    """
    ML 모델을 사용해 추천 번호를 생성한다.
    모델/데이터 로드 실패 시 일반 랜덤 번호로 fallback한다.
    """
    try:
        model_bundle = load_model_bundle()
        model = model_bundle["model"]
        feature_columns = model_bundle["feature_columns"]

        rows = load_history()
        X_pred = build_prediction_features(rows, feature_columns)

        probabilities_for_positive = model.predict_proba(X_pred)[:, 1]
        sampling_probabilities = normalize_probabilities(probabilities_for_positive)

        for _ in range(20):
            numbers = weighted_sample_numbers(sampling_probabilities)

            if not user_already_has_same_numbers(user, draw, numbers):
                return numbers

        return generate_random_numbers()

    except Exception:
        return generate_random_numbers()
