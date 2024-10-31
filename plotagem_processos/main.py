import time
import psutil
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Monitor do Sistema",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS Personalizado
st.markdown(
    """
    <style>
        .metric-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 14px;
            color: #586069;
        }
        .stPlotlyChart {
            background-color: white;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Constantes
CHART_HEIGHT = 300


def get_process_count():
    return len(psutil.pids())


def get_cpu_usage():
    return psutil.cpu_percent(interval=1)


def get_memory_usage():
    return psutil.virtual_memory().used // 1000000


def format_bytes(bytes):
    """Converte bytes para formato legível"""
    for unit in ["MB", "GB", "TB"]:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def create_plot(df, title, y_label, color):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[df.columns[0]],
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}",
        )
    )

    y_min = df[df.columns[0]].min()
    y_max = df[df.columns[0]].max()
    y_range = y_max - y_min
    padding = y_range * 0.1 if y_range > 0 else 1

    fig.update_layout(
        title=None,
        xaxis_title="Tempo",
        yaxis_title=y_label,
        yaxis=dict(range=[max(0, y_min - padding), y_max + padding]),
        height=CHART_HEIGHT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.1)",
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.1)",
        zeroline=False,
    )

    return fig


def display_metric_card(placeholder, title, value, unit):
    placeholder.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value} {unit}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def main():
    # Configuração da barra lateral
    st.sidebar.title("⚙️ Configurações")
    update_interval = st.sidebar.slider(
        "Intervalo de Atualização (segundos)", 1, 30, 10
    )
    chart_history = st.sidebar.slider("Pontos no Histórico", 10, 100, 30)

    # Conteúdo principal
    st.title("📊 Painel de Monitoramento do Sistema")
    st.markdown("Monitoramento em tempo real dos recursos do sistema")

    # Inicializar DataFrames
    if "process_data" not in st.session_state:
        st.session_state.process_data = pd.DataFrame(columns=["Processos"])
        st.session_state.cpu_data = pd.DataFrame(columns=["Uso de CPU"])
        st.session_state.ram_data = pd.DataFrame(columns=["Uso de RAM"])

    # Criar placeholders para métricas
    metric_cols = st.columns(3)
    process_metric = metric_cols[0].empty()
    cpu_metric = metric_cols[1].empty()
    ram_metric = metric_cols[2].empty()

    # Adicionar espaçamento
    st.markdown("---")

    # Criar duas colunas para gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💻 Utilização da CPU")
        cpu_chart = st.empty()

        st.subheader("🔢 Contagem de Processos")
        process_chart = st.empty()

    with col2:
        st.subheader("🎯 Uso de Memória RAM")
        ram_chart = st.empty()

        # Informações do sistema (estático)
        st.subheader("📱 Informações do Sistema")
        system_info = {
            "Sistema Operacional": f"{psutil.os.name}",
            "Núcleos de CPU": psutil.cpu_count(),
            "RAM Total": format_bytes(psutil.virtual_memory().total // 1000000),
            "Tempo de Inicialização": datetime.fromtimestamp(
                psutil.boot_time()
            ).strftime("%d/%m/%Y %H:%M:%S"),
        }

        for key, value in system_info.items():
            st.metric(key, value)

    # Loop principal de atualização
    while True:
        current_time = pd.Timestamp.now()

        # Obter valores atuais
        process_count = get_process_count()
        cpu_usage = get_cpu_usage()
        ram_usage = get_memory_usage()

        # Atualizar DataFrames
        st.session_state.process_data.loc[current_time] = process_count
        st.session_state.cpu_data.loc[current_time] = cpu_usage
        st.session_state.ram_data.loc[current_time] = ram_usage

        # Manter apenas o número especificado de pontos no histórico
        st.session_state.process_data = st.session_state.process_data.tail(
            chart_history
        )
        st.session_state.cpu_data = st.session_state.cpu_data.tail(chart_history)
        st.session_state.ram_data = st.session_state.ram_data.tail(chart_history)

        # Atualizar cartões de métricas
        display_metric_card(process_metric, "Processos", process_count, "ativos")
        display_metric_card(cpu_metric, "Uso da CPU", f"{cpu_usage:.1f}", "%")
        display_metric_card(ram_metric, "Uso da RAM", format_bytes(ram_usage), "")

        # Atualizar gráficos
        cpu_chart.plotly_chart(
            create_plot(st.session_state.cpu_data, "Uso da CPU", "Uso (%)", "#FF6B6B"),
            use_container_width=True,
        )

        process_chart.plotly_chart(
            create_plot(
                st.session_state.process_data,
                "Processos Ativos",
                "Quantidade",
                "#4ECDC4",
            ),
            use_container_width=True,
        )

        ram_chart.plotly_chart(
            create_plot(
                st.session_state.ram_data, "Uso de Memória", "Uso (MB)", "#45B7D1"
            ),
            use_container_width=True,
        )

        # Aguardar próxima atualização
        time.sleep(update_interval)


if __name__ == "__main__":
    main()
