"""Line and pie charts for financial calculators."""
import matplotlib.pyplot as plt


def _style_axes(ax, title):
    fig = ax.figure
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")
    ax.set_title(title, color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#555")


def line_chart(labels, series_dict, title="Growth over time", xlabel="Period"):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    styles = {
        "Compound": {"color": "#2ecc71", "linestyle": "-"},
        "Simple interest": {"color": "#f39c12", "linestyle": "-"},
        "No interest": {"color": "#95a5a6", "linestyle": "--"},
        "Compound interest": {"color": "#2ecc71", "linestyle": "-"},
    }
    default_colors = ["#2ecc71", "#f39c12", "#95a5a6"]
    plotted = 0
    for i, (name, values) in enumerate(series_dict.items()):
        if values is None or len(values) == 0:
            continue
        style = styles.get(name, {"color": default_colors[i % 3], "linestyle": "-"})
        xs = range(len(values))
        ax.plot(
            xs,
            values,
            label=name,
            color=style["color"],
            linestyle=style["linestyle"],
            linewidth=2.0,
        )
        plotted += 1
    if plotted == 0:
        ax.text(0.5, 0.5, "No chart data", ha="center", va="center", color="#888", transform=ax.transAxes)
    _style_axes(ax, title)
    ax.set_xlabel(xlabel, color="white", fontsize=8)
    if plotted:
        ax.legend(facecolor="#2b2b2b", labelcolor="white", fontsize=8, loc="upper left")
    step = max(1, len(labels) // 8) if labels else 1
    if labels:
        ax.set_xticks(range(0, len(labels), step))
        ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)], rotation=0)
    plt.tight_layout()
    return fig


def pie_chart(slices, title="Breakdown"):
    labels, values = zip(*[(k, v) for k, v in slices.items() if v > 0])
    if not values:
        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_facecolor("#2b2b2b")
        ax.text(0.5, 0.5, "No data", ha="center", va="center", color="#888")
        ax.axis("off")
        return fig
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_facecolor("#2b2b2b")
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6", "#f39c12"]
    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors[: len(values)],
        textprops={"color": "white", "fontsize": 8},
    )
    ax.set_title(title, color="white", fontsize=10)
    plt.tight_layout()
    return fig


def comparison_pie(amount_a, amount_b, label_a, label_b, title="Comparison"):
    return pie_chart({label_a: amount_a, label_b: amount_b}, title=title)


def bar_chart(labels, values, title="Breakdown", xlabel="Period", color="#3b8ed0"):
    fig, ax = plt.subplots(figsize=(5, 3))
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")
    xs = range(len(values))
    ax.bar(xs, values, color=color, width=0.7)
    ax.set_title(title, color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=7)
    step = max(1, len(labels) // 8)
    ax.set_xticks(range(0, len(labels), step))
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)], rotation=0)
    ax.set_xlabel(xlabel, color="white", fontsize=8)
    for spine in ax.spines.values():
        spine.set_color("#555")
    plt.tight_layout()
    return fig
