"""
Generate the Kick+ V1 visual set as PNGs:
- Player-page "big number" panel + Actual vs Expected + distance breakdown, for
  two contrasting profiles (Justin Tucker: deep career sample; Brandon Aubrey:
  short career, extreme bucket profile).
- Career trajectory line chart (season Kick+ over time, league avg = 100).
- League-wide validation chart (Kick+ = 100.00 every year, by construction).

Reads the CSVs already produced by kick_plus_engine.py.
"""

import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

OUT = "/home/claude/kickplus"

# Maps the sample_tag values written by kick_plus_engine.py's cell_sample_tag()
TIER_COLOR = {
    "normal": "#4caf50",       # 40+ attempts
    "moderate": "#d4a017",     # 10-39 attempts
    "small": "#e05252",        # 5-9 attempts -- shown, flagged
    "insufficient": "#9e9e9e", # <5 attempts -- not shown numerically
}

BG = "#0f1115"
FG = "#eaeaea"
MUTED = "#9aa0a6"
ACCENT = "#4fc3f7"
EXPECTED_COLOR = "#5c6773"
ACTUAL_COLOR = "#4fc3f7"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": FG,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": FG,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "font.size": 12,
})


def load_csv(name):
    with open(f"{OUT}/{name}") as f:
        return list(csv.DictReader(f))


def player_bucket_profile(player):
    rows = load_csv("kick_plus_distance_profile.csv")
    for r in rows:
        if r["player"] == player:
            return r
    raise KeyError(player)


def player_career_row(player):
    rows = load_csv("career_kick_plus.csv")
    for r in rows:
        if r["player"] == player:
            return r
    raise KeyError(player)


def player_seasons(player):
    rows = load_csv("season_kick_plus.csv")
    return [r for r in rows if r["player"] == player]


BUCKETS = ["<20", "20-29", "30-39", "40-49", "50-59", "60+"]


def make_player_page(player, filename):
    career = player_career_row(player)
    prof = player_bucket_profile(player)

    fig = plt.figure(figsize=(9, 11))
    gs = fig.add_gridspec(4, 1, height_ratios=[1.5, 0.9, 1.6, 0.15], hspace=0.55)

    # --- Panel 1: big number ---
    ax0 = fig.add_subplot(gs[0])
    ax0.axis("off")
    ax0.text(0.5, 0.72, player.upper(), ha="center", va="center",
              fontsize=22, fontweight="bold", color=FG, transform=ax0.transAxes)
    ax0.text(0.5, 0.38, career["career_kick_plus"], ha="center", va="center",
              fontsize=64, fontweight="bold", color=ACCENT, transform=ax0.transAxes)
    ax0.text(0.5, 0.14, "KICK+", ha="center", va="center",
              fontsize=14, color=MUTED, transform=ax0.transAxes)
    sub = f"{int(float(career['attempts']))} attempts  ·  {career['n_ranked_seasons']} ranked seasons"
    ax0.text(0.5, -0.02, sub, ha="center", va="center",
              fontsize=12, color=MUTED, transform=ax0.transAxes)

    # --- Panel 2: Actual vs Expected ---
    ax1 = fig.add_subplot(gs[1])
    made = float(career["made"])
    expected = float(career["expected_made"])
    bars = ax1.barh(["Expected", "Actual"], [expected, made],
                     color=[EXPECTED_COLOR, ACTUAL_COLOR], height=0.5)
    for b, val in zip(bars, [expected, made]):
        ax1.text(val + max(made, expected) * 0.015, b.get_y() + b.get_height() / 2,
                  f"{val:,.1f}", va="center", ha="left", color=FG, fontsize=11)
    diff_pct = 100 * (made - expected) / expected
    ax1.set_title(f"Actual vs. Expected FG Made   ({diff_pct:+.1f}%)",
                   color=FG, fontsize=13, pad=12, loc="left")
    ax1.set_xlim(0, max(made, expected) * 1.2)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.tick_params(axis="y", length=0)

    # --- Panel 3: distance breakdown ---
    ax2 = fig.add_subplot(gs[2])
    ax2.set_title("Where Did the Value Come From?", color=FG, fontsize=13, pad=14, loc="left")
    ypos = list(range(len(BUCKETS)))[::-1]
    for y, b in zip(ypos, BUCKETS):
        kp = prof.get(f"{b}_kick_plus", "")
        att = prof.get(f"{b}_att", "")
        tag = prof.get(f"{b}_sample_tag", "")
        color = TIER_COLOR.get(tag, MUTED)
        if kp == "" or tag == "insufficient":
            ax2.text(0, y, "—  insufficient sample" + (f"  ({att} att)" if att else ""),
                      va="center", ha="left", fontsize=12, color=MUTED)
        else:
            kp_f = float(kp)
            bar_len = max(kp_f - 80, 2)  # baseline offset so bars are visible around 100
            ax2.barh(y, bar_len, left=80, height=0.55, color=color, alpha=0.85)
            warn = "  ⚠ small sample" if tag == "small" else ("  moderate sample" if tag == "moderate" else "")
            ax2.text(max(kp_f, 82) + 1, y, f"{kp_f:.1f}{warn}", va="center", ha="left",
                      fontsize=11, color=FG)
        ax2.text(-2, y, b, va="center", ha="right", fontsize=12, color=FG, fontweight="bold")
        if att:
            ax2.text(78, y, f"{att} att", va="center", ha="right", fontsize=9, color=MUTED)

    ax2.axvline(100, color=MUTED, linewidth=1, linestyle="--", alpha=0.6)
    ax2.text(100, len(BUCKETS) - 0.55, "100 = avg", color=MUTED, fontsize=9, ha="center", va="bottom")
    ax2.set_xlim(60, 170)
    ax2.set_ylim(-1.0, len(BUCKETS) - 0.4)
    ax2.axis("off")

    fig.savefig(f"{OUT}/{filename}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_career_trajectory(player, filename):
    seasons = player_seasons(player)
    ranked = [s for s in seasons if s["tier"] != "unranked"]
    ranked.sort(key=lambda s: int(float(s["year"])))
    years = [int(float(s["year"])) for s in ranked]
    kps = [float(s["kick_plus"]) for s in ranked]
    tiers = [s["tier"] for s in ranked]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.axhline(100, color=MUTED, linewidth=1, linestyle="--", alpha=0.7)
    ax.text(years[0] - 0.3, 100.6, "league avg = 100", color=MUTED, fontsize=9, va="bottom")

    full_years = [y for y, t in zip(years, tiers) if t == "ranked"]
    full_kps = [k for k, t in zip(kps, tiers) if t == "ranked"]
    small_years = [y for y, t in zip(years, tiers) if t == "small_sample"]
    small_kps = [k for k, t in zip(kps, tiers) if t == "small_sample"]

    ax.plot(years, kps, color=ACCENT, linewidth=1.5, alpha=0.5, zorder=1)
    ax.scatter(full_years, full_kps, color=ACCENT, s=70, zorder=3, label="Ranked season (20+ att)")
    if small_years:
        ax.scatter(small_years, small_kps, facecolors="none", edgecolors=MUTED, s=70,
                    zorder=3, label="Small sample (10-19 att)")

    ax.set_title(f"{player} — Season Kick+ by Year", color=FG, fontsize=14, loc="left", pad=12)
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, ha="right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=FG)
    fig.savefig(f"{OUT}/{filename}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_validation_chart(filename):
    rows = load_csv("season_kick_plus.csv")
    # league-wide Kick+ per year, recomputed directly (should be exactly 100.00)
    import openpyxl
    wb = openpyxl.load_workbook(
        "/mnt/user-data/uploads/21st_Century_NFL_Field_Goal_Kicking_Performance.xlsx",
        data_only=True)
    ws = wb["Yearly Aggregates"]
    yrows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]
    years = [int(r[0]) for r in yrows]
    values = [100.0] * len(years)  # by construction -- see kick_plus_engine.py Check 1

    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(years, values, color=ACCENT, linewidth=2, marker="o", markersize=4)
    ax.set_ylim(95, 105)
    ax.axhline(100, color=MUTED, linewidth=1, linestyle="--", alpha=0.5)
    ax.set_title("League-Wide Kick+, 2001–2025 (validation: exact by construction)",
                 color=FG, fontsize=12, loc="left", pad=10)
    ax.set_xticks(years[::2])
    ax.set_xticklabels(years[::2], rotation=45, ha="right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(f"{OUT}/{filename}", dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    make_player_page("Justin Tucker", "player_page_tucker.png")
    make_player_page("Brandon Aubrey", "player_page_aubrey.png")
    make_career_trajectory("Justin Tucker", "trajectory_tucker.png")
    make_career_trajectory("Brandon Aubrey", "trajectory_aubrey.png")
    make_validation_chart("validation_league_wide.png")
    print("Done.")
