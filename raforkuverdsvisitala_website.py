import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches
import io
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Raforkuverðsvísitala", layout="wide")

# --- HIDE NUMBER SPINNERS (CSS) ---
st.markdown("""
    <style>
    input[type="number"]::-webkit-outer-spin-button,
    input[type="number"]::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    input[type="number"] {
        -moz-appearance: textfield;
    }
    </style>
""", unsafe_allow_html=True)

# --- COLORS (Preserved from your original) ---
BLUE_DARK = "#003366"
BLUE_LIGHT = "#6699CC"
GREEN = "#3b8132"
RED = "#c30010"
BG_LIGHT = "#f8f9fa"
BORDER_GRAY = "#dee2e6"

# --- DATA LOADING ---
@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE = os.path.join(BASE_DIR, "gjaldskrar.xlsx")
    
    verd_tett = pd.read_excel(FILE, sheet_name="VA210")
    verd_dreif = pd.read_excel(FILE, sheet_name="VA230")
    vnv = pd.read_excel(FILE, sheet_name="VNV")
    sala = pd.read_excel(FILE, sheet_name="Sala")

    verd_tett.columns = ["Ár", "Fastagjald", "Aflgjald", "Orkugjald"]
    verd_dreif.columns = ["Ár", "Fastagjald", "Aflgjald", "Orkugjald"]
    vnv.columns = ["Ár", "VNV", "Hækkun"]
    sala.columns = ["Ár", "HV", "LV", "Mean"]

    df_tett = verd_tett.merge(vnv, on="Ár")
    df_dreif = verd_dreif.merge(vnv, on="Ár")
    
    return df_tett, df_dreif, sala, BASE_DIR

df_tett, df_dreif, sala, BASE_DIR = load_data()

# --- SIDEBAR: INPUTS ---
FILE_LOGO = os.path.join(BASE_DIR, "lota_logo.png")
if os.path.exists(FILE_LOGO):
    st.sidebar.image(FILE_LOGO, width=120)

st.sidebar.title("Forsendur")

entry_ref = st.sidebar.number_input("Viðmiðunarár", min_value=2011, max_value=2025, value=2016, format="%d")
entry_klst = st.sidebar.number_input("Nýtingartími (klst)", value=4150, format="%d")
entry_afl = st.sidebar.number_input("Afl (kW)", value=3200, format="%d")
area_var = st.sidebar.selectbox("Svæði", ["Þéttbýli", "Dreifbýli"])

# --- CALCULATIONS ---
df = df_tett.copy() if area_var == "Þéttbýli" else df_dreif.copy()
df = df.merge(sala, on="Ár")

ORKA = entry_afl * entry_klst

# Unadjusted
df["FD"] = df["Fastagjald"] + df["Aflgjald"] * entry_afl + df["Orkugjald"] * ORKA
df["Sala"] = df["Mean"] * ORKA
df["Total"] = df["FD"] + df["Sala"]
df["Sala_HV"] = df["HV"] * ORKA
df["Sala_LV"] = df["LV"] * ORKA

# Discounted
try:
    cpi_ref = df.loc[df["Ár"] == entry_ref, "VNV"].values[0]
except IndexError:
    cpi_ref = df["VNV"].iloc[-1]

df["FD_n"] = df["FD"] * (cpi_ref / df["VNV"])
df["Sala_n"] = df["Sala"] * (cpi_ref / df["VNV"])
df["Total_n"] = df["Total"] * (cpi_ref / df["VNV"])

# Index
try:
    ref_total = df.loc[df["Ár"] == entry_ref, "Total"].values[0]
except IndexError:
    ref_total = df["Total"].iloc[0]

df["Index"] = (df["Total"] / ref_total) * 100
df["Index_n"] = (df["Total_n"] / ref_total) * 100

latest_year = int(df["Ár"].iloc[-1])
fd_val = df["FD"].iloc[-1]
sala_val = df["Sala"].iloc[-1]
total_val = df["Total"].iloc[-1]
latest_idx = df["Index"].iloc[-1]
latest_idx_n = df["Index_n"].iloc[-1]

# --- MAIN DASHBOARD ---
st.title("Raforkuverðsvísitala")

col1, col2, col3 = st.columns([1.3, 1, 1])

with col1:
    st.markdown(f"""
    <div style="background-color: #e6f2ff; padding: 20px; border-radius: 8px; border: 1px solid #cce0ff; height: 240px; display: flex; flex-direction: column; justify-content: center;">
        <div style="font-weight: bold; font-size: 1.15em; color: #333333; margin-bottom: 15px;">Sundurliðun kostnaðar ({latest_year})</div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 1.1em; color: #333333;">
            <span>Flutningur + dreifing:</span><span>{fd_val:,.0f} kr.</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 1.1em; color: #333333;">
            <span>Sala:</span><span>{sala_val:,.0f} kr.</span>
        </div>
        <hr style="border-top: 2px solid {BLUE_DARK}; margin: 12px 0;">
        <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.3em; color: {BLUE_DARK};">
            <span>Heildarkostnaður:</span><span>{total_val:,.0f} kr.</span>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; border-radius: 8px; border: 2px solid #f0f2f6; 
                background-color: #ffffff; height: 240px; display: flex; flex-direction: column; 
                justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <p style="margin: 0; font-size: 1.2em; font-weight: bold; color: {BLUE_DARK};">Raforkuverðsvísitala</p>
        <p style="margin: 0; font-size: 3.5em; font-weight: bold; color: {BLUE_LIGHT};">{latest_idx:.1f}</p>
        <p style="margin: 0; font-size: 1em; font-style: italic; color: #666666;">(m.v. árið {entry_ref})</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; border-radius: 8px; border: 2px solid #f0f2f6; 
                background-color: #ffffff; height: 240px; display: flex; flex-direction: column; 
                justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <p style="margin: 0; font-size: 1.2em; font-weight: bold; color: {BLUE_DARK};">Raforkuverðsvísitala núvirt</p>
        <p style="margin: 0; font-size: 3.5em; font-weight: bold; color: {BLUE_LIGHT};">{latest_idx_n:.1f}</p>
        <p style="margin: 0; font-size: 0.9em; font-style: italic; color: #666666;">Hækkun umfram verðlag m.v. VNV (m.v. árið {entry_ref})</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- WEB PLOTTING ---
def format_mkr(x, pos):
    return f"{x/1_000_000:,.1f}"
formatter = FuncFormatter(format_mkr)
FLAT_SIZE = (6, 3.2) 

fig1, ax1 = plt.subplots(figsize=FLAT_SIZE, dpi=100)
ax1.plot(df["Ár"], df["FD"], color=BLUE_DARK, lw=2.5, label="Ónúvirt")
ax1.plot(df["Ár"], df["FD_n"], color=BLUE_DARK, linestyle=":", lw=2, label="Núvirt")
ax1.set_title("Flutningur + dreifing", weight='bold')
ax1.yaxis.set_major_formatter(formatter)
ax1.set_ylabel("m.kr.")
ax1.legend(frameon=False)
ax1.grid(True, axis='y', linestyle="--", alpha=0.4)

fig2, ax2 = plt.subplots(figsize=FLAT_SIZE, dpi=100)
ax2.fill_between(df["Ár"], df["Sala_LV"], df["Sala_HV"], color=GREEN, alpha=0.1)
ax2.plot(df["Ár"], df["Sala"], color=GREEN, lw=2.5, label="Ónúvirt")
ax2.plot(df["Ár"], df["Sala_n"], color=GREEN, linestyle=":", lw=2, label="Núvirt")
ax2.set_title("Sala", weight='bold')
ax2.yaxis.set_major_formatter(formatter)
ax2.set_ylabel("m.kr.")
ax2.legend(frameon=False)
ax2.grid(True, axis='y', linestyle="--", alpha=0.4)

# Stacked Area Chart for Total
fig3, ax3 = plt.subplots(figsize=FLAT_SIZE, dpi=100)
ax3.stackplot(df["Ár"], df["FD"], df["Sala"], labels=["Flutningur + dreifing", "Sala"], colors=[BLUE_DARK, GREEN], alpha=0.5)
ax3.set_title("Heildar raforkukostnaður", weight='bold')
ax3.yaxis.set_major_formatter(formatter)
ax3.set_ylabel("m.kr.")
ax3.legend(frameon=False, loc='upper left')
ax3.grid(True, axis='y', linestyle="--", alpha=0.4)

fig4, ax4 = plt.subplots(figsize=FLAT_SIZE, dpi=100)
ax4.axhline(100, color='grey', linestyle='--', linewidth=1, alpha=0.7)
ax4.plot(df["Ár"], df["Index"], color=RED, lw=2.5, label="Vísitala")
ax4.plot(df["Ár"], df["Index_n"], color=RED, linestyle=":", lw=2, label="Núvirt")
ax4.set_title("Raforkuverðsvísitala", weight='bold')
ax4.set_ylabel("Vísitala")
ax4.legend(frameon=False)
ax4.grid(True, axis='y', linestyle="--", alpha=0.4)

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.pyplot(fig1)
    st.pyplot(fig3) 
with chart_col2:
    st.pyplot(fig2)
    st.pyplot(fig4)

# --- PDF GENERATION ---
def create_pdf():
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        
        def add_header(fig, title_text):
            rect = patches.Rectangle((0, 0.94), 1, 0.06, transform=fig.transFigure, facecolor=BLUE_DARK, zorder=0)
            fig.patches.append(rect)
            fig.text(0.05, 0.96, title_text, color='white', fontsize=16, weight='bold', va='center')
            fig.text(0.95, 0.96, "LOTA ehf.", color='white', fontsize=10, ha='right', va='center', alpha=0.8)

        # PAGE 1: EXECUTIVE SUMMARY
        fig_p1 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax_p1 = fig_p1.add_subplot(111)
        ax_p1.axis('off')
        add_header(fig_p1, "")

        ax_p1.text(0.05, 0.90, "RAFORKUVERÐSVÍSITALA", fontsize=24, weight='bold', color=BLUE_DARK)
        ax_p1.text(0.05, 0.87, f"Niðurstöður og samantekt fyrir árið {latest_year}", fontsize=12, color='#666666')

        # Assumptions Table
        ax_p1.text(0.08, 0.80, "Valdar forsendur", fontsize=13, weight='bold', color=BLUE_DARK)
        table_data_left = [["Viðmiðunarár", str(entry_ref)], ["Nýtingartími", f"{entry_klst} klst"], ["Afl", f"{entry_afl} kW"], ["Svæði", area_var]]
        table_left = ax_p1.table(cellText=table_data_left, loc='center', bbox=[0.08, 0.67, 0.84, 0.12], edges='horizontal')
        
        # Financials Table
        ax_p1.text(0.08, 0.58, f"Sundurliðun kostnaðar ({latest_year})", fontsize=13, weight='bold', color=BLUE_DARK)
        str_fd = f"{fd_val:,.0f} kr.".replace(",", ".")
        str_sala = f"{sala_val:,.0f} kr.".replace(",", ".")
        str_tot = f"{total_val:,.0f} kr.".replace(",", ".")
        table_data_right = [["Flutningur + dreifing", str_fd], ["Sala", str_sala], ["Heildarkostnaður", str_tot]]
        table_right = ax_p1.table(cellText=table_data_right, loc='center', bbox=[0.08, 0.43, 0.84, 0.12], edges='horizontal')

        for table in [table_left, table_right]:
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            for (row, col), cell in table.get_celld().items():
                cell.set_height(0.2)
                if col == 1: cell.set_text_props(ha='right')
                if table == table_right and row == 2:
                    cell.set_text_props(weight='bold', color=BLUE_DARK)
                    cell.set_facecolor('#eef6ff')

        # KPI Cards
        card1 = patches.FancyBboxPatch((0.05, 0.12), 0.43, 0.22, boxstyle="round,pad=0.02", facecolor=BG_LIGHT, edgecolor=BORDER_GRAY, transform=ax_p1.transAxes)
        ax_p1.add_patch(card1)
        ax_p1.text(0.265, 0.30, "Raforkuverðsvísitala", fontsize=12, weight='bold', ha='center', color=BLUE_DARK)
        ax_p1.text(0.265, 0.19, f"{latest_idx:.1f}", fontsize=42, weight='bold', ha='center', color=BLUE_LIGHT)
        ax_p1.text(0.265, 0.15, f"(m.v. árið {entry_ref})", fontsize=9, ha='center', color='#888888')

        card2 = patches.FancyBboxPatch((0.52, 0.12), 0.43, 0.22, boxstyle="round,pad=0.02", facecolor=BG_LIGHT, edgecolor=BORDER_GRAY, transform=ax_p1.transAxes)
        ax_p1.add_patch(card2)
        ax_p1.text(0.735, 0.30, "Raforkuverðs. núvirt", fontsize=12, weight='bold', ha='center', color=BLUE_DARK)
        ax_p1.text(0.735, 0.19, f"{latest_idx_n:.1f}", fontsize=42, weight='bold', ha='center', color=BLUE_LIGHT)
        ax_p1.text(0.735, 0.14, "Hækkun umfram verðlag m.v. VNV", fontsize=8, ha='center', color='#888888')

        pdf.savefig(fig_p1)
        plt.close(fig_p1)

        # Charts Helper for PDF
        def clean_ax(ax, title):
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.yaxis.set_major_formatter(formatter)
            ax.set_title(title, loc='left', fontsize=12, weight='bold', pad=15)
            ax.grid(True, axis='y', linestyle='-', color='#eeeeee')

        # PAGE 2: BREAKDOWN
        fig_p2 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        add_header(fig_p2, "")
        gs2 = fig_p2.add_gridspec(2, 1, hspace=0.4, top=0.85, bottom=0.1, left=0.15, right=0.85)
        
        ax_pdf1 = fig_p2.add_subplot(gs2[0, 0])
        ax_pdf1.plot(df["Ár"], df["FD"], color=BLUE_DARK, lw=2, label="Ónúvirt")
        ax_pdf1.plot(df["Ár"], df["FD_n"], color=BLUE_DARK, ls=":", lw=2, label="Núvirt")
        clean_ax(ax_pdf1, "Flutningur + dreifing")
        ax_pdf1.legend(frameon=False)

        ax_pdf2 = fig_p2.add_subplot(gs2[1, 0])
        ax_pdf2.fill_between(df["Ár"], df["Sala_LV"], df["Sala_HV"], color=GREEN, alpha=0.1)
        ax_pdf2.plot(df["Ár"], df["Sala"], color=GREEN, lw=2, label="Ónúvirt")
        ax_pdf2.plot(df["Ár"], df["Sala_n"], color=GREEN, ls=":", lw=2, label="Núvirt")
        clean_ax(ax_pdf2, "Sala")
        ax_pdf2.legend(frameon=False)

        pdf.savefig(fig_p2)
        plt.close(fig_p2)

        # PAGE 3: TOTALS
        fig_p3 = plt.figure(figsize=(8.27, 11.69), dpi=150)
        add_header(fig_p3, "")
        gs3 = fig_p3.add_gridspec(2, 1, hspace=0.4, top=0.85, bottom=0.1, left=0.15, right=0.85)

        ax_pdf3 = fig_p3.add_subplot(gs3[0, 0])
        ax_pdf3.stackplot(df["Ár"], df["FD"], df["Sala"], labels=["Flutningur + dreifing", "Sala"], colors=[BLUE_LIGHT, GREEN], alpha=0.5)
        clean_ax(ax_pdf3, "Heildar raforkukostnaður")
        ax_pdf3.legend(frameon=False, loc='upper left')

        ax_pdf4 = fig_p3.add_subplot(gs3[1, 0])
        ax_pdf4.axhline(100, color='grey', ls='--', lw=1, alpha=0.5)
        ax_pdf4.plot(df["Ár"], df["Index"], color=RED, lw=2, label="Vísitala")
        ax_pdf4.plot(df["Ár"], df["Index_n"], color=RED, ls=":", lw=2, label="Núvirt")
        clean_ax(ax_pdf4, "Raforkuverðsvísitala")
        ax_pdf4.set_ylabel("Vísitala")
        ax_pdf4.legend(frameon=False)

        pdf.savefig(fig_p3)
        plt.close(fig_p3)
    
    return buffer.getvalue()

st.sidebar.divider()
pdf_data = create_pdf()
st.sidebar.download_button(
    label="📄 Sækja niðurstöður (PDF)",
    data=pdf_data,
    file_name=f"Raforkuverdsvisitala_{latest_year}.pdf",
    mime="application/pdf"
)
