import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API = "http://127.0.0.1:8000"

STRATEGY_LABELS = {
    "static": "Статическая цена",
    "epsilon_greedy": "Epsilon-Greedy",
    "ucb": "UCB",
    "stackelberg": "Стэкельберг: лучший ответ",
}

st.set_page_config(
    page_title="Адаптивное ценообразование",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Платформа адаптивного ценообразования")
st.caption("Моделирование стратегий ценообразования на основе теории игр и данных маркетплейса")

def get(path):
    try:
        return requests.get(f"{API}{path}").json()
    except Exception:
        st.error("Backend не запущен. Сначала запустите FastAPI на порту 8000.")
        st.stop()

def post(path, payload=None):
    try:
        return requests.post(f"{API}{path}", json=payload or {}).json()
    except Exception:
        st.error("Backend не запущен. Сначала запустите FastAPI на порту 8000.")
        st.stop()

tab1, tab2, tab3 = st.tabs([
    "1. Создание эксперимента",
    "2. Запуск",
    "3. Аналитика и выбор лучшей стратегии",
])

with tab1:
    st.header("Создание эксперимента")

    st.info(
        "Можно использовать параметры, рассчитанные по датасету Kaggle. "
        "Для этого CSV-файл должен лежать в папке data/."
    )

    if st.button("Калибровать параметры по датасету"):
        calibration = get("/api/experiments/calibrate")
        st.session_state["calibration"] = calibration
        st.success("Параметры рассчитаны по датасету.")
        st.json(calibration)

    calibration = st.session_state.get("calibration", {})

    with st.form("experiment_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input("Название эксперимента", "Российский маркетплейс: сравнение стратегий")
            market_size = st.number_input(
                "Размер рынка",
                100,
                100000,
                int(calibration.get("market_size", 1000)),
                step=100,
            )
            time_horizon = st.number_input("Количество раундов", 10, 5000, 300, step=10)

        with col2:
            beta = st.number_input(
                "Чувствительность к цене beta",
                0.001,
                1.0,
                float(calibration.get("beta", 0.05)),
                step=0.005,
                format="%.4f",
            )
            v_mean = st.number_input(
                "Средняя оценка товара покупателем",
                1.0,
                100000.0,
                float(calibration.get("v_mean", 50.0)),
                step=1.0,
            )

        with col3:
            price_min = st.number_input(
                "Минимальная цена",
                1.0,
                100000.0,
                float(calibration.get("price_min", 20.0)),
                step=1.0,
            )
            price_max = st.number_input(
                "Максимальная цена",
                1.0,
                100000.0,
                float(calibration.get("price_max", 80.0)),
                step=1.0,
            )
            price_step = st.number_input("Шаг цены", 1.0, 10000.0, 5.0, step=1.0)

        selected_labels = st.multiselect(
            "Выберите стратегии для сравнения",
            options=list(STRATEGY_LABELS.keys()),
            default=["static", "epsilon_greedy", "ucb", "stackelberg"],
            format_func=lambda x: STRATEGY_LABELS[x],
        )

        submit = st.form_submit_button("Создать эксперимент")

    if submit:
        result = post("/api/experiments", {
            "name": name,
            "market_size": int(market_size),
            "time_horizon": int(time_horizon),
            "beta": float(beta),
            "v_mean": float(v_mean),
            "price_min": float(price_min),
            "price_max": float(price_max),
            "price_step": float(price_step),
            "strategies": selected_labels,
        })

        st.success(f"Создан эксперимент ID: {result['experiment_id']}")

    st.subheader("Список экспериментов")
    experiments = get("/api/experiments")
    st.dataframe(pd.DataFrame(experiments), use_container_width=True)

with tab2:
    st.header("Запуск эксперимента")

    experiment_id = st.number_input("ID эксперимента", 1, 1000000, 1, step=1)

    if st.button("Запустить моделирование"):
        result = post(f"/api/experiments/{int(experiment_id)}/run")
        st.success(f"Эксперимент завершён. Лучшая стратегия: {STRATEGY_LABELS.get(result['best_strategy'], result['best_strategy'])}")

with tab3:
    st.header("Аналитика результатов")

    result_experiment_id = st.number_input("Загрузить эксперимент ID", 1, 1000000, 1, step=1)

    if st.button("Показать результаты"):
        results = get(f"/api/experiments/{int(result_experiment_id)}/results")
        metrics = get(f"/api/experiments/{int(result_experiment_id)}/metrics")

        if not results:
            st.warning("Результаты не найдены. Сначала запустите эксперимент.")
            st.stop()

        df = pd.DataFrame(results)
        metrics_df = pd.DataFrame(metrics)

        df["strategy_label"] = df["strategy_name"].map(STRATEGY_LABELS)

        pivot = metrics_df.pivot(
            index="strategy_name",
            columns="metric_name",
            values="metric_value"
        ).reset_index()

        pivot["strategy_label"] = pivot["strategy_name"].map(STRATEGY_LABELS)

        best_row = pivot.sort_values("cumulative_revenue", ascending=False).iloc[0]
        best_strategy = best_row["strategy_label"]

        st.success(f"Лучшая стратегия: {best_strategy}")

        st.markdown(
            f"""
            **Почему эта стратегия лучше:**  
            стратегия **{best_strategy}** получила наибольшую суммарную выручку.
            Сравнение проводится по метрикам:
            - суммарная выручка;
            - средняя выручка за раунд;
            - средний спрос;
            - волатильность цены;
            - итоговая цена.
            """
        )

        st.subheader("Сводная таблица метрик")
        st.dataframe(pivot, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                df,
                x="round",
                y="price",
                color="strategy_label",
                title="Динамика цен по стратегиям",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                df,
                x="round",
                y="revenue",
                color="strategy_label",
                title="Выручка за каждый раунд",
            )
            st.plotly_chart(fig, use_container_width=True)

        df["cumulative_revenue"] = df.groupby("strategy_label")["revenue"].cumsum()

        col3, col4 = st.columns(2)

        with col3:
            fig = px.line(
                df,
                x="round",
                y="cumulative_revenue",
                color="strategy_label",
                title="Накопленная выручка",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col4:
            fig = px.scatter(
                df,
                x="price",
                y="demand",
                color="strategy_label",
                title="Зависимость спроса от цены",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Исходные результаты")
        st.dataframe(df, use_container_width=True)