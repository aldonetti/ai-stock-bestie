"""Chart generation module using Plotly."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import constants


def create_price_chart(window_df: pd.DataFrame) -> go.Figure:
    """
    Create price chart with technical indicators.

    Args:
        window_df: DataFrame containing price data

    Returns:
        Plotly figure object
    """
    window_df = window_df.sort_index()

    if window_df.empty or len(window_df) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data to display chart",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    if not all(col in window_df.columns for col in required_cols):
        fig = go.Figure()
        fig.add_annotation(
            text="Missing required data columns",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("", ""),
        row_heights=[0.75, 0.25],
    )

    if len(window_df) > 0:
        valid_data = window_df.dropna(subset=["Open", "High", "Low", "Close"])
        if len(valid_data) > 0:
            fig.add_trace(
                go.Candlestick(
                    x=valid_data.index,
                    open=valid_data["Open"],
                    high=valid_data["High"],
                    low=valid_data["Low"],
                    close=valid_data["Close"],
                    name="Price",
                    showlegend=False,
                    increasing_line_color=constants.SUCCESS,
                    decreasing_line_color=constants.DANGER,
                    increasing_fillcolor=constants.SUCCESS,
                    decreasing_fillcolor=constants.DANGER,
                    line=dict(width=1),
                    whiskerwidth=0.6,
                    hovertemplate=(
                        "<b>Price Data</b><br>"
                        + "Open: $%{open:.2f}<br>"
                        + "High: $%{high:.2f}<br>"
                        + "Low: $%{low:.2f}<br>"
                        + "Close: $%{close:.2f}<br>"
                        + "Time: %{x|%H:%M:%S}<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor="rgba(255, 255, 255, 0.98)",
                        bordercolor=constants.BORDER,
                        font=dict(
                            size=12,
                            family="Inter, -apple-system, sans-serif",
                            color=constants.TEXT_PRIMARY,
                        ),
                    ),
                ),
                row=1,
                col=1,
            )

    if len(window_df) >= 5:
        ma = window_df["Close"].rolling(window=min(5, len(window_df))).mean().dropna()
        if len(ma) > 0:
            fig.add_trace(
                go.Scatter(
                    x=ma.index,
                    y=ma.values,
                    mode="lines",
                    name="5-min Moving Average",
                    line=dict(
                        color=constants.WARNING,
                        width=2,
                        dash="dot",
                        shape="spline",
                        smoothing=1.3,
                    ),
                    hovertemplate=(
                        "<b>Moving Average (5-min)</b><br>"
                        + "Value: $%{y:.2f}<br>"
                        + "Time: %{x|%H:%M:%S}<extra></extra>"
                    ),
                    connectgaps=False,
                    showlegend=True,
                    legendgroup="indicators",
                    fill=None,
                    hoverlabel=dict(
                        bgcolor="rgba(255, 255, 255, 0.98)",
                        bordercolor=constants.BORDER,
                        font=dict(
                            size=12,
                            family="Inter, -apple-system, sans-serif",
                            color=constants.TEXT_PRIMARY,
                        ),
                    ),
                ),
                row=1,
                col=1,
            )

    if len(window_df) >= 5:
        window_size = min(5, len(window_df))
        rolling_avg = window_df["Close"].rolling(window=window_size).mean()
        std = window_df["Close"].rolling(window=window_size).std()
        upper_band = rolling_avg + (2 * std)
        lower_band = rolling_avg - (2 * std)

        valid_mask = ~(upper_band.isna() | lower_band.isna())
        if valid_mask.sum() > 0:
            upper_band_clean = upper_band[valid_mask]
            lower_band_clean = lower_band[valid_mask]

        fig.add_trace(
            go.Scatter(
                x=upper_band_clean.index,
                y=upper_band_clean.values,
                mode="lines",
                name="Upper Band",
                line=dict(
                    color="rgba(74, 85, 104, 0.3)",
                    width=1,
                    dash="dash",
                    shape="spline",
                    smoothing=1.2,
                ),
                showlegend=True,
                legendgroup="bollinger",
                hovertemplate=(
                    "<b>Bollinger Upper Band</b><br>"
                    + "Resistance: $%{y:.2f}<br>"
                    + "Time: %{x|%H:%M:%S}<extra></extra>"
                ),
                connectgaps=False,
                hoverlabel=dict(
                    bgcolor="rgba(255, 255, 255, 0.98)",
                    bordercolor=constants.BORDER,
                    font=dict(
                        size=12,
                        family="Inter, -apple-system, sans-serif",
                        color=constants.TEXT_PRIMARY,
                    ),
                ),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=lower_band_clean.index,
                y=lower_band_clean.values,
                mode="lines",
                name="Lower Band",
                line=dict(
                    color="rgba(74, 85, 104, 0.3)",
                    width=1,
                    dash="dash",
                    shape="spline",
                    smoothing=1.2,
                ),
                showlegend=True,
                legendgroup="bollinger",
                hovertemplate=(
                    "<b>Bollinger Lower Band</b><br>"
                    + "Support: $%{y:.2f}<br>"
                    + "Time: %{x|%H:%M:%S}<extra></extra>"
                ),
                connectgaps=False,
                hoverlabel=dict(
                    bgcolor="rgba(255, 255, 255, 0.98)",
                    bordercolor=constants.BORDER,
                    font=dict(
                        size=12,
                        family="Inter, -apple-system, sans-serif",
                        color=constants.TEXT_PRIMARY,
                    ),
                ),
            ),
            row=1,
            col=1,
        )

    if len(window_df) > 0 and "Volume" in window_df.columns:
        volume_data = window_df["Volume"].dropna()
        if len(volume_data) > 0:
            colors = []
            close_prices_for_volume = window_df["Close"].dropna()
            for i in range(len(volume_data)):
                idx = volume_data.index[i]
                if idx in close_prices_for_volume.index:
                    price_idx = close_prices_for_volume.index.get_loc(idx)
                    if price_idx > 0:
                        prev_idx = close_prices_for_volume.index[price_idx - 1]
                        if (
                            close_prices_for_volume.loc[idx]
                            >= close_prices_for_volume.loc[prev_idx]
                        ):
                            colors.append(constants.SUCCESS_LIGHT)
                        else:
                            colors.append(constants.DANGER_LIGHT)
                    else:
                        colors.append(constants.SECONDARY_LIGHT)
                else:
                    colors.append(constants.SECONDARY_LIGHT)

            if len(colors) != len(volume_data):
                colors = [constants.SECONDARY_LIGHT] * len(volume_data)

        fig.add_trace(
            go.Bar(
                x=volume_data.index,
                y=volume_data.values,
                name="Volume",
                showlegend=False,
                marker_color=(
                    colors if len(colors) == len(volume_data) else constants.SECONDARY_LIGHT
                ),
                marker_line_color="rgba(0, 0, 0, 0)",
                marker_line_width=0,
                opacity=0.6,
                hovertemplate="<b>Trading Volume</b><br>"
                + "Volume: %{y:,.0f}<br>"
                + "Time: %{x|%H:%M:%S}<extra></extra>",
                hoverlabel=dict(
                    bgcolor="rgba(255, 255, 255, 0.98)",
                    bordercolor=constants.BORDER,
                    font=dict(
                        size=12,
                        family="Inter, -apple-system, sans-serif",
                        color=constants.TEXT_PRIMARY,
                    ),
                ),
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=650,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(
                size=10,
                color=constants.TEXT_SECONDARY,
                family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            ),
            bgcolor="rgba(0, 0, 0, 0)",
            bordercolor="rgba(0, 0, 0, 0)",
            borderwidth=0,
        ),
        margin=dict(l=85, r=55, t=30, b=90),
        hovermode="x unified",
        font=dict(
            family="'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            size=11,
            color=constants.TEXT_PRIMARY,
        ),
        plot_bgcolor=constants.SURFACE,
        paper_bgcolor=constants.BACKGROUND,
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.98)",
            bordercolor=constants.BORDER,
            font=dict(
                size=11,
                family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
                color=constants.TEXT_PRIMARY,
            ),
            align="left",
        ),
        dragmode="pan",
        xaxis_rangeslider_visible=False,
    )

    fig.update_xaxes(
        title_text="Time",
        row=2,
        col=1,
        showgrid=True,
        gridcolor=constants.BORDER_LIGHT,
        gridwidth=1,
        griddash="solid",
        showline=True,
        linecolor=constants.BORDER,
        linewidth=1,
        zeroline=False,
        title_font=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=13,
            color=constants.TEXT_PRIMARY,
            weight="bold",
        ),
        tickfont=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=11,
            color=constants.TEXT_SECONDARY,
        ),
        tickformat="%H:%M",
        tickangle=0,
        tickmode="linear",
        dtick=3600000,
    )

    fig.update_yaxes(
        title_text="Price ($)",
        row=1,
        col=1,
        showgrid=True,
        gridcolor=constants.BORDER_LIGHT,
        gridwidth=1,
        griddash="solid",
        showline=False,
        linecolor=constants.BORDER,
        linewidth=1,
        zeroline=True,
        zerolinecolor=constants.BORDER,
        zerolinewidth=1,
        title_font=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=13,
            color=constants.TEXT_PRIMARY,
            weight="bold",
        ),
        tickfont=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=11,
            color=constants.TEXT_SECONDARY,
        ),
        tickformat="$.2f",
        side="right",
        separatethousands=True,
    )

    fig.update_yaxes(
        title_text="Volume",
        row=2,
        col=1,
        showgrid=True,
        gridcolor=constants.BORDER_LIGHT,
        gridwidth=1,
        griddash="solid",
        showline=True,
        linecolor=constants.BORDER,
        linewidth=1,
        zeroline=False,
        title_font=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=13,
            color=constants.TEXT_PRIMARY,
            weight="bold",
        ),
        tickfont=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=11,
            color=constants.TEXT_SECONDARY,
        ),
        tickformat=",.0f",
        side="right",
        separatethousands=True,
    )

    fig.update_xaxes(
        row=1,
        col=1,
        showgrid=True,
        gridcolor=constants.BORDER_LIGHT,
        gridwidth=1,
        griddash="solid",
        showline=False,
        linecolor=constants.BORDER,
        linewidth=1,
        zeroline=False,
        showticklabels=False,
        tickfont=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=10,
            color=constants.TEXT_SECONDARY,
        ),
    )

    fig.update_annotations(
        font=dict(
            family="'Inter', 'SF Pro Display', -apple-system, sans-serif",
            size=13,
            color=constants.TEXT_PRIMARY,
            weight="bold",
        ),
    )

    return fig
