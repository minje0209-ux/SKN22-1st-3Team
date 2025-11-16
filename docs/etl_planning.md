# ETL Planning – 국내 자동차 시장 트렌드 분석 프로젝트

본 문서는 본 프로젝트에서 사용되는 전체 ETL(Extract–Transform–Load) 흐름을
**한눈에 파악**하고,  
**추후 admin 페이지 자동화/스케줄링/유지보수에 바로 활용**할 수 있도록 정리한 설계 문서입니다.

---

# 1. ETL 전체 순서 요약 (Top-level Summary)

본 프로젝트의 데이터 수집·정제·적재 흐름은 **4개의 메인 ETL 라인**으로 구성된다.

## Sequence Overview

1. **다나와 → 모델 메타 + 월간 판매량**

   - Selenium 크롤링
   - CSV 정규화(normalization)
   - car_model / car_model_image / model_monthly_sales 적재

2. **네이버 데이터랩 → 월간 관심도**

   - Naver DataLab API 호출
   - device/gender 단위 RAW 적재 (detail)
   - 월간 관심도 지표 집계 (model_monthly_interest)

3. **구글 트렌드 → 월간 관심도 보조 지표**

   - 구글 트렌드 wide-format CSV 수작업 수집
   - 모델명 매핑 + 정규화
   - monthly_interest의 google_trend_index 업데이트

4. **네이버 블로그 + 워드클라우드 → 텍스트 분석**
   - 네이버 검색 API로 상위 3개 블로그 글 검색
   - 본문 크롤링 → 정제
   - 형태소 분석 (Kiwi) → 명사 추출 → 빈도 계산
   - 워드클라우드 이미지 생성
   - blog_article / blog_token_monthly / blog_wordcloud 적재

→ **대시보드 4개 페이지(Overview/관심도/보급률/상세분석)가 전부 이 데이터에 기반한다.**

---

# 2. ETL 세부 내용 (Detailed Workflow)

아래는 실제 구현한 코드 흐름 기준으로 완성된 ETL 단계별 상세 설명이다.  
Admin 페이지 버튼화/자동화의 근간이 될 문서이다.

---

# 2.1 다나와 데이터 (판매량 / 모델 메타)

## 2.1.1 월별 판매/메타 크롤링 (Selenium)

### 입력

- 다나와 "신차 판매실적" 웹페이지

### 출력

- {brand}\_model_sales_YYYY_MM_00.csv
- {brand}\_model_meta_YYYY_MM_00.csv

### 요약

- 현대/기아 brand filter 적용
- 월 단위로 테이블 parse
- 총 2종 CSV 저장: 판매량 / 메타 정보(URL, 이미지 등 일부)

---

## 2.1.2 정규화(normalize)

### 주요 처리

- 숫자 파싱
- 전월대비 / 전년대비 문자열에서 숫자 분리
- market_total_units 계산
- adoption_rate = sales_units / market_total_units

---

## 2.1.3 car_model 후보 추출 → 적재

### 입력

- 모든 normalized sales CSV

### 처리

- (brand, model_name_kr) 기준 aggregation
  - first_month
  - last_month
  - months_count
  - total_sales

### 출력

- car_model_candidates.csv

### DB 적재

- car_model insert
- 초기에는 danawa_model_id, danawa_model_url은 NULL

---

## 2.1.4 모델 메타 → car_model & car_model_image 갱신

### 입력

- normalized meta CSV

### 처리

- 모델명 매칭 (brand + model_name_kr)
- car_model 업데이트:
  - danawa_model_id
  - danawa_model_url
- car_model_image insert:
  - image_url
  - is_primary = 1
  - 중복 URL은 스킵

---

## 2.1.5 월 판매량 적재 (model_monthly_sales)

### 입력

- normalized sales CSV

### 처리

- model_id 매칭
- model_monthly_sales upsert:
  - sales_units
  - market_total_units
  - adoption_rate
  - source="DANAWA"

---

# 2.2 네이버 데이터랩 (Monthly Interest)

## 2.2.1 API 호출 → RAW 크롤링

### 입력

- car_model 테이블의 모델명들
- start-date, end-date

### 처리

- Naver DataLab API 반복 호출
- device(pc/mo), gender(m/f) 조합 지원
- age-group은 현재 제외 (확장 가능)

### 출력

- naver*trend_raw*\*.csv
  - model_id
  - date (YYYY-MM-01)
  - device
  - gender
  - ratio (0~100 normalized)

---

## 2.2.2 detail 테이블 적재

테이블: model_monthly_interest_detail

필드  
model_id, month, device, gender, age_group, ratio

upsert 기준  
(model_id, month, device, gender, age_group)

---

## 2.2.3 월간 통합 지표 요약 (model_monthly_interest)

집계 방식

- 동일 월, 동일 모델에 대해 ratio를 합산 또는 평균 → naver_search_index

업데이트

- model_monthly_interest.naver_search_index 갱신
- google_trend_index는 다음 단계에서 추가됨

---

# 2.3 구글 트렌드

## 2.3.1 wide-format CSV → 정규화

입력 파일

- HYUNDAIall.csv
- KIAall.csv

문제

- 모델명이 제각각
- week 데이터를 month 데이터로 변환 필요

처리

- header 파싱 → car_model과 매칭
- 날짜별 지수를 월 단위로 통일

출력

- google*trend*{run_id}\_normalized.csv

---

## 2.3.2 DB 적재

작업

- model_monthly_interest.google_trend_index upsert

결과

- NAVER + GOOGLE 기반 관심도 점수 계산 가능

---

# 2.4 네이버 블로그 + 워드클라우드

## 2.4.1 블로그 상위 3개 검색 → 본문 크롤링

입력

- 모델명
- 검색 키워드: 모델명 후기

방법

1. 네이버 검색 API로 URL 3개 획득
2. 각 URL 본문 requests/Selenium 크롤링
3. HTML 제거
4. Kiwi 형태소 분석 → 명사 count 생성

---

## 2.4.2 저장 테이블

1. blog_article
2. blog_token_monthly
3. blog_wordcloud

---

# 3. Admin Page 구성 제안

1. 다나와 최신 데이터 수집
2. CSV → DB 반영
3. 네이버 API 호출
4. detail → interest 집계
5. 구글 트렌드 반영
6. 블로그/워드클라우드 실행
7. 전체 지표 재집계
8. 로그 조회

---

# 4. 결론

본 문서는 ETL 전체 흐름을 정리한 문서이며,  
추후 개선·자동화·스케줄링의 기반 자료로 사용한다.
