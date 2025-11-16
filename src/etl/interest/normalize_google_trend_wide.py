# src/etl/interest/normalize_google_trend_wide.py

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple, List, Any

from sqlalchemy import text

from src.db.connection import get_engine


BASE_DIR = Path(__file__).resolve().parents[3]
GOOGLE_DIR = BASE_DIR / "data" / "raw" / "google"


def load_model_map() -> Dict[Tuple[str, str], int]:
    """
    car_model에서 (brand_name, model_name_kr) -> model_id 매핑을 만든다.
    """
    engine = get_engine(echo=False)
    sql = text(
        """
        SELECT model_id, brand_name, model_name_kr
        FROM car_model
        """
    )

    mapping: Dict[Tuple[str, str], int] = {}
    with engine.connect() as conn:
        for row in conn.execute(sql).mappings():
            key = (row["brand_name"], row["model_name_kr"])
            mapping[key] = row["model_id"]

    return mapping


def guess_brand_from_filename(path: Path) -> str | None:
    """
    파일명으로부터 브랜드를 추정한다.
    - 파일명에 HYUNDAI 포함 → '현대'
    - 파일명에 KIA 포함 → '기아'
    """
    name_upper = path.name.upper()
    if "HYUNDAI" in name_upper:
        return "현대"
    if "KIA" in name_upper:
        return "기아"
    return None


def open_skip_category_line(path: Path):
    """
    첫 줄이 '카테고리:' 로 시작하면 그 줄은 건너뛰고
    나머지로 csv.DictReader 를 만들 수 있도록 파일 객체를 리턴.
    """
    f = path.open("r", encoding="utf-8-sig")
    # 첫 줄 미리 읽어보고 '카테고리:' 면 버리고, 아니면 다시 사용
    first = f.readline()
    if first.strip().startswith("카테고리:"):
        # 그대로 두고 다음 줄부터 DictReader가 읽게 함
        pass
    else:
        # 카테고리 라인이 아니면, 파일 포인터를 처음으로 돌려서 전체 사용
        f.seek(0)
    return f


def normalize_google_trend_wide(run_id: str) -> Path:
    """
    data/raw/google/<run_id> 안의
      *hyundai*all.csv
      *kia*all.csv
    파일들을 wide CSV 로 보고,
    (model_id, month) 단위의 월별 구글 트렌드 지수로 정규화한다.

    출력:
      data/raw/google/<run_id>/google_trend_<run_id>_normalized.csv

    스키마:
      model_id, month, google_trend_index
    """
    folder = GOOGLE_DIR / run_id
    if not folder.exists():
        raise FileNotFoundError(f"폴더가 없습니다: {folder}")

    # 대소문자 상관 없이 hyundai/kia + all 이 들어간 파일 찾기
    existing_files: List[Path] = []
    for p in folder.iterdir():
        if not p.is_file():
            continue
        name_lower = p.name.lower()
        if "all" in name_lower and ("hyundai" in name_lower or "kia" in name_lower):
            existing_files.append(p)

    if not existing_files:
        raise FileNotFoundError(
            f"{folder} 에서 *hyundai*all.csv / *kia*all.csv 패턴의 파일을 찾을 수 없습니다."
        )

    model_map = load_model_map()
    print(f"[INFO] car_model 매핑 로드 완료: {len(model_map)} 개")

    # (model_id, month) -> indices
    bucket: Dict[Tuple[int, str], List[int]] = defaultdict(list)

    used_columns: Dict[str, int] = {}
    skipped_columns: List[str] = []

    for path in existing_files:
        brand_name = guess_brand_from_filename(path)
        if not brand_name:
            print(f"[WARN] 브랜드 추정 실패, 스킵: {path}")
            continue

        print(f"[INFO] 구글 트렌드 wide CSV 로딩: {path} (brand={brand_name})")

        with open_skip_category_line(path) as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"[WARN] 헤더 없음, 스킵: {path}")
                continue

            fieldnames = reader.fieldnames
            # 첫 번째 컬럼 (예: '주') 를 날짜 컬럼으로 사용
            date_col = fieldnames[0]

            # 헤더 분석: 어떤 컬럼을 model_id로 사용할지 결정
            col_to_model_id: Dict[str, int] = {}
            for col in fieldnames[1:]:
                raw_name = col.strip()
                # "캐스퍼: (대한민국)" → "캐스퍼"
                if ":" in raw_name:
                    trend_name = raw_name.split(":", 1)[0].strip()
                else:
                    trend_name = raw_name

                key = (brand_name, trend_name)
                model_id = model_map.get(key)
                if model_id is not None:
                    col_to_model_id[col] = model_id
                    used_columns[f"{brand_name}:{trend_name}"] = model_id
                else:
                    skipped_columns.append(f"{brand_name}:{trend_name}")

            print(
                f"[INFO] 매핑된 컬럼 수: {len(col_to_model_id)} "
                f"(전체 {len(fieldnames) - 1} 중)"
            )

            # 실제 데이터 행 처리
            for row in reader:
                date_str = (row.get(date_col) or "").strip()
                if not date_str:
                    continue
                # YYYY-MM-01 로 월 키 통일 (주간 데이터 기준)
                if len(date_str) < 7:
                    print(f"[WARN] 예기치 않은 날짜 형식 스킱: {date_str}")
                    continue
                month = date_str[:7] + "-01"

                for col, model_id in col_to_model_id.items():
                    val_str = (row.get(col) or "").strip()
                    if not val_str:
                        continue
                    try:
                        idx = int(float(val_str))
                    except ValueError:
                        print(
                            f"[WARN] index 파싱 실패 스킵: "
                            f"date={date_str}, col={col}, value={val_str}"
                        )
                        continue

                    bucket[(model_id, month)].append(idx)

    # 평균값 계산
    rows: List[Dict[str, Any]] = []
    for (model_id, month), indices in bucket.items():
        if not indices:
            continue
        avg_idx = sum(indices) / len(indices)
        google_trend_index = round(avg_idx)
        rows.append(
            {
                "model_id": model_id,
                "month": month,
                "google_trend_index": google_trend_index,
            }
        )

    print(f"[INFO] 정규화된 (model_id, month) 개수: {len(rows)}")

    out_path = folder / f"google_trend_{run_id}_normalized.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["model_id", "month", "google_trend_index"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] 정규화 CSV 저장 완료: {out_path}")

    # 디버깅용 요약
    print("---------- 매핑 요약 ----------")
    print(f"사용된 컬럼 수: {len(used_columns)}")
    print(f"스킵된 컬럼 수: {len(skipped_columns)}")
    print("--------------------------------")

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="구글 트렌드 wide CSV → 월별 지수 정규화"
    )
    parser.add_argument("--run-id", required=True, help="실행 ID (예: 25_11_16)")

    args = parser.parse_args()
    normalize_google_trend_wide(run_id=args.run_id)


if __name__ == "__main__":
    main()
