# components/charts.py
import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


def line_chart(df, x, y, title=""):
    fig = px.line(df, x=x, y=y, title=title)
    st.plotly_chart(fig, width="stretch")


def bar_chart(df, x, y, title=""):
    fig = px.bar(df, x=x, y=y, title=title)
    st.plotly_chart(fig, width="stretch")


def pie_chart(df, names, values, title=""):
    fig = px.pie(df, names=names, values=values, title=title)
    st.plotly_chart(fig, width="stretch")


def scatter_chart(df, x, y, color=None, size=None, title=""):
    fig = px.scatter(df, x=x, y=y, color=color, size=size, title=title)
    st.plotly_chart(fig, width="stretch")


def histogram(df, x, title=""):
    fig = px.histogram(df, x=x, title=title)
    st.plotly_chart(fig, width="stretch")


def build_interest_chart(df_top: pd.DataFrame) -> go.Figure:
    """
    관심도 Top N 모델 차트 (Bar + 보조 라벨)
    df_top: model_id, brand_name, model_name_kr, naver_search_index, google_trend_index, interest_score ...
    """
    chart_df = df_top.copy()
    chart_df["label"] = chart_df["brand_name"] + " " + chart_df["model_name_kr"]

    # 관심도 점수 0~100 스케일
    chart_df["interest_score"] = (
        pd.to_numeric(chart_df["interest_score"], errors="coerce").fillna(0.0) * 100.0
    )

    fig = go.Figure()

    fig.add_bar(
        x=chart_df["label"],
        y=chart_df["interest_score"],
        name="관심도 점수(0~100)",
        text=chart_df["interest_score"].round(1),
        textposition="outside",
    )

    fig.update_layout(
        xaxis=dict(title="모델"),
        yaxis=dict(
            title="관심도 점수(0~100)",
            range=[0, max(100, chart_df["interest_score"].max() * 1.2)],
        ),
        margin=dict(l=40, r=40, t=10, b=80),
    )

    return fig
