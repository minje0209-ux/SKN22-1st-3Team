# src/dashboard/components/images.py
import pathlib
import streamlit as st

# 현재 파일: .../src/dashboard/components/images.py
# 프로젝트 루트: .../SKN22-1st-3Team
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _resolve_image_path(path_str: str) -> pathlib.Path:
    """
    DB에 저장된 image_path가 상대 경로일 때
    Streamlit이 읽을 수 있는 절대경로로 변환.
    """
    p = pathlib.Path(path_str)

    # 이미 절대경로면 그대로
    if p.is_absolute():
        return p

    # dashboard 기준 상대경로 시도
    from_dashboard = pathlib.Path(__file__).resolve().parents[1] / p
    if from_dashboard.is_file():
        return from_dashboard

    # 프로젝트 루트 기준
    from_root = PROJECT_ROOT / p
    if from_root.is_file():
        return from_root

    # 다 실패하면 원본 경로 그대로 반환
    return p


def image_card(title: str, image_url: str, caption: str | None = None):
    st.markdown(f"**{title}**")

    img_path = _resolve_image_path(image_url)

    if not img_path.is_file():
        st.warning(f"이미지 파일을 찾을 수 없습니다.\n\n`{image_url}`")
        if caption:
            st.caption(caption)
        return

    st.image(str(img_path), width="stretch")

    if caption:
        st.caption(caption)
