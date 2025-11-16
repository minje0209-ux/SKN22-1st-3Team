-- =====================================================
--  init_schema.sql
--  국내 자동차 시장 트렌드 분석 프로젝트 - DB 스키마
-- =====================================================
SET
    NAMES utf8mb4;

SET
    FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. car_model
-- =====================================================
CREATE TABLE IF NOT EXISTS car_model (
    model_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '내부 모델 ID',
    danawa_model_id INT UNSIGNED NOT NULL COMMENT '다나와 모델 식별자',
    brand_name VARCHAR(50) NOT NULL COMMENT '브랜드명 (현대/기아)',
    model_name_kr VARCHAR(200) NOT NULL COMMENT '모델명 (예: 쏘나타 디 엣지)',
    danawa_model_url VARCHAR(500) NOT NULL COMMENT '다나와 모델 상세 URL',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시각',
    UNIQUE KEY uk_car_model_danawa (danawa_model_id),
    KEY idx_car_model_brand (brand_name, model_name_kr)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '현대/기아 차량 모델 마스터';

-- =====================================================
-- 2. car_model_image
-- =====================================================
CREATE TABLE IF NOT EXISTS car_model_image (
    image_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '이미지 ID',
    model_id INT UNSIGNED NOT NULL COMMENT 'FK → car_model.model_id',
    image_url VARCHAR(500) NOT NULL COMMENT '원본 이미지 URL',
    local_path VARCHAR(500) NULL COMMENT '다운로드 이미지 경로',
    content_type VARCHAR(100) NULL COMMENT 'MIME 타입',
    image_binary LONGBLOB NULL COMMENT '썸네일 이미지 바이너리 (선택)',
    is_primary TINYINT(1) NOT NULL DEFAULT 1 COMMENT '대표 이미지 여부',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    KEY idx_image_model (model_id),
    KEY idx_image_primary (model_id, is_primary),
    CONSTRAINT fk_image_model FOREIGN KEY (model_id) REFERENCES car_model(model_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '모델 썸네일/이미지 정보';

-- =====================================================
-- 3. model_monthly_interest
-- =====================================================
CREATE TABLE IF NOT EXISTS model_monthly_interest (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_id INT UNSIGNED NOT NULL COMMENT 'FK → car_model.model_id',
    month DATE NOT NULL COMMENT '기준 월 (YYYY-MM-01)',
    naver_search_index INT NULL COMMENT '네이버 검색 지수',
    google_trend_index INT NULL COMMENT '구글 트렌드 지수 (0~100)',
    danawa_pop_rank INT NULL COMMENT '다나와 인기순 랭킹',
    danawa_pop_rank_size INT NULL COMMENT '랭킹 산출 대상 개수',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    UNIQUE KEY uk_interest_model_month (model_id, month),
    KEY idx_interest_month (month),
    CONSTRAINT fk_interest_model FOREIGN KEY (model_id) REFERENCES car_model(model_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '월간 관심도 (네이버/구글/다나와)';

-- =====================================================
-- 4. model_monthly_sales
-- =====================================================
CREATE TABLE IF NOT EXISTS model_monthly_sales (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_id INT UNSIGNED NOT NULL COMMENT 'FK → car_model.model_id',
    month DATE NOT NULL COMMENT '기준 월',
    sales_units INT NOT NULL COMMENT '해당 월 판매량(대)',
    market_total_units INT NULL COMMENT '전체 시장 판매량(선택)',
    adoption_rate DECIMAL(7, 4) NULL COMMENT '점유율 (판매량/전체)',
    source VARCHAR(50) NOT NULL DEFAULT 'DANAWA' COMMENT '데이터 출처',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    UNIQUE KEY uk_sales_model_month (model_id, month),
    KEY idx_sales_month (month),
    CONSTRAINT fk_sales_model FOREIGN KEY (model_id) REFERENCES car_model(model_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '월간 판매실적/보급률';

-- =====================================================
-- 5. market_monthly_summary
-- =====================================================
CREATE TABLE IF NOT EXISTS market_monthly_summary (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    month DATE NOT NULL COMMENT '기준 월',
    region_code VARCHAR(20) NOT NULL COMMENT '지역 코드',
    vehicle_type VARCHAR(50) NULL COMMENT '차종',
    segment VARCHAR(50) NULL COMMENT '세그먼트',
    fuel_type VARCHAR(50) NULL COMMENT '연료 타입',
    registration_count INT NOT NULL COMMENT '등록 대수',
    source VARCHAR(100) NOT NULL COMMENT '출처',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    KEY idx_market_month (month),
    KEY idx_market_filters (vehicle_type, fuel_type, segment)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '공공데이터 월간 등록현황';

-- =====================================================
-- 6. blog_article
-- =====================================================
CREATE TABLE IF NOT EXISTS blog_article (
    article_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '블로그 글 ID',
    model_id INT UNSIGNED NOT NULL COMMENT 'FK → car_model.model_id',
    month DATE NOT NULL COMMENT '분석 기준 월',
    search_keyword VARCHAR(200) NOT NULL COMMENT '검색 키워드',
    search_rank INT NOT NULL COMMENT '검색 순위 (1~3)',
    title VARCHAR(300) NOT NULL COMMENT '블로그 글 제목',
    url VARCHAR(500) NOT NULL COMMENT '블로그 링크',
    summary TEXT NULL COMMENT '요약',
    content_plain MEDIUMTEXT NOT NULL COMMENT '정제된 본문 텍스트',
    posted_at DATETIME NULL COMMENT '블로그 등록일',
    collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '수집 시각',
    UNIQUE KEY uk_blog_url (url),
    KEY idx_blog_model_month (model_id, month),
    KEY idx_blog_model_rank (model_id, search_rank),
    CONSTRAINT fk_blog_model FOREIGN KEY (model_id) REFERENCES car_model(model_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '블로그 상위 3개 글';

-- =====================================================
-- 7. blog_token_monthly
-- =====================================================
CREATE TABLE IF NOT EXISTS blog_token_monthly (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_id INT UNSIGNED NOT NULL COMMENT 'FK → car_model.model_id',
    month DATE NOT NULL COMMENT '기준 월',
    token VARCHAR(100) NOT NULL COMMENT '단어(명사)',
    total_count INT NOT NULL COMMENT '등장 횟수',
    token_rank INT NOT NULL COMMENT '순위 (1 = 최다)',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    UNIQUE KEY uk_token_model_month (model_id, month, token),
    KEY idx_token_rank (model_id, month, token_rank),
    KEY idx_model_month (model_id, month),
    CONSTRAINT fk_token_model FOREIGN KEY (model_id) REFERENCES car_model(model_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '월간 블로그 키워드 빈도';

-- =====================================================
-- 8. blog_wordcloud
-- =====================================================
CREATE TABLE IF NOT EXISTS blog_wordcloud (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_id INT UNSIGNED NOT NULL COMMENT 'FK → car_model.model_id',
    month DATE NOT NULL COMMENT '기준 월',
    image_path VARCHAR(500) NOT NULL COMMENT '워드클라우드 이미지 경로',
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    UNIQUE KEY uk_wc_model_month (model_id, month),
    CONSTRAINT fk_wc_model FOREIGN KEY (model_id) REFERENCES car_model(model_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '월간 워드클라우드 이미지';

-- =====================================================
-- 1. car_model 수정: 메타데이터 일부 추가
-- =====================================================
ALTER TABLE
    car_model
MODIFY
    danawa_model_id INT UNSIGNED NULL COMMENT '다나와 모델 식별자',
MODIFY
    danawa_model_url VARCHAR(500) NULL COMMENT '다나와 모델 상세 URL';

-- =====================================================
-- 9. model_monthly_interest_detail: 네이버 데이터랩 디테일 테이블 추가
-- =====================================================
CREATE TABLE model_monthly_interest_detail (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'PK',
    model_id INT UNSIGNED NOT NULL COMMENT 'car_model.model_id FK',
    month DATE NOT NULL COMMENT '월 단위(YYYY-MM-01)',
    device VARCHAR(10) NULL COMMENT 'pc 또는 mobile',
    gender VARCHAR(10) NULL COMMENT 'male 또는 female',
    age_group VARCHAR(10) NULL COMMENT '연령대 필터 예: 10,20,30… 필요 시 확장',
    ratio FLOAT NOT NULL COMMENT '네이버 검색 지수 (해당 모델 기간 내 최고값=100 기반 비율)',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '레코드 생성 시각',
    UNIQUE KEY uk_model_month_filter (model_id, month, device, gender, age_group),
    KEY idx_model_month (model_id, month),
    CONSTRAINT fk_interest_detail_model FOREIGN KEY (model_id) REFERENCES car_model(model_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '네이버 검색량 상세 지표 (디바이스/성별/연령대 단위 RAW)';

SET
    FOREIGN_KEY_CHECKS = 1;