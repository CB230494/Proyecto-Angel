# =========================
# 📊 Diagrama MPGP – Exportador (matplotlib, rama "Sí" ajustable)
# =========================
# - Controles para: inicio de rama Sí, espaciado y modo compacto
# - Flecha de retroalimentación curva (evita cruces)
# - Exporta PNG, PDF y PPTX
# =========================

import io, textwrap
from dataclasses import dataclass
from typing import Tuple, List

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import patches
from pptx import Presentation
from pptx.util import Inches
from PIL import Image

# -------- Estilos --------
BLUE = "#1F4E79"; BORDER = "#9BBBD9"; LIGHTBLUE = "#DCEBF7"
LIGHTYELLOW = "#FFF8E1"; BLACK = "#000000"; BG = "#F7FAFF"

# -------- Config --------
st.set_page_config(page_title="Diagrama MPGP – Exportador", layout="wide")
st.title("Diagrama de Flujo – Modelo Preventivo de Gestión Policial (layout limpio)")
st.caption("Rama **Sí** ajustable (inicio + espaciado). Exporta PNG, PDF y PPTX.")

# -------- Entradas --------
colA, colB = st.columns(2)
with colA:
    t_inicio = st.text_input("INICIO", "Planificación preventiva anual")
    b1 = st.text_area("Bloque 1", "Definición y calendarización de Delegaciones\n(Procedimiento 1.1 MPGP)", height=72)
    b2 = st.text_area("Bloque 2", "Apreciación situacional del territorio\n(Procedimiento 1.2)", height=72)
    b3 = st.text_area("Bloque 3", "Identificación de factores de riesgo y delitos\n(DATAPOL, estadísticas, patrullaje)", height=72)
    q_dec = st.text_input("Decisión", "¿Se identifican riesgos prioritarios?")
with colB:
    s1 = st.text_area("SÍ 1", "Priorización de riesgos y delitos\n(Pareto, MIC-MAC, Triángulo de violencias)", height=72)
    s2 = st.text_area("SÍ 2", "Construcción de líneas de acción preventivas\n(Procedimiento 2.3)", height=72)
    s3 = st.text_area("SÍ 3", "Planificación de programas policiales preventivos\n(Procedimiento 2.4)", height=72)
    s4 = st.text_area("SÍ 4", "Elaboración de órdenes de servicio para operativos", height=72)
    s5 = st.text_area("SÍ 5", "Implementación en terreno\n• Patrullajes preventivos\n• Respuesta inmediata\n• Supervisión\n• Coordinación local", height=96)
    s6 = st.text_area("SÍ 6", "Reporte de operativos (RAP, DATAPOL, informes)", height=72)
    s7 = st.text_area("SÍ 7", "Evaluación de cumplimiento (Trazabilidad 3.1 y 3.2)", height=72)
    s8 = st.text_area("SÍ 8", "Retroalimentación a la planificación preventiva", height=72)

colC, colD = st.columns(2)
with colC:
    n1 = st.text_area("NO 1", "Patrullaje rutinario y vigilancia continua", height=72)
    n2 = st.text_area("NO 2", "Registro de factores menores en RAP", height=72)
    n3 = st.text_area("NO 3", "Integración al análisis situacional", height=72)
with colD:
    t_fin = st.text_area("FIN", "Evaluación global de resultados\n(Indicadores, metas, impacto – 3.3)", height=72)

st.markdown("### ⚙️ Ajustes de layout (rama **Sí**)")
colS1, colS2, colS3 = st.columns(3)
with colS1:
    # Valor alto = más arriba (y en esta figura el eje Y crece hacia arriba)
    start_si = st.slider("Inicio rama SÍ (más arriba ⇡)", min_value=80, max_value=140, value=100, step=2)
with colS2:
    espaciado_deseado = st.slider("Espaciado vertical deseado", min_value=6, max_value=16, value=10, step=1)
with colS3:
    compacto = st.toggle("Modo compacto (alturas reducidas)", value=True)

# -------- Utilidades de dibujo --------
@dataclass
class Node:
    x: float; y: float; w: float; h: float; text: str; shape: str; fc: str; ec: str = BLUE

def wrap(txt: str, max_chars: int) -> str:
    parts = []
    for block in txt.split("\n"):
        parts.append(textwrap.fill(block, width=max_chars))
    return "\n".join(parts)

def draw_node(ax, n: Node, fontsize=9):
    if n.shape == "rect":
        ax.add_patch(patches.FancyBboxPatch(
            (n.x - n.w/2, n.y - n.h/2), n.w, n.h,
            boxstyle="round,pad=0.02,rounding_size=6",
            linewidth=1.8, edgecolor=n.ec, facecolor=n.fc
        ))
    elif n.shape == "oval":
        ax.add_patch(patches.Ellipse((n.x, n.y), n.w, n.h, linewidth=1.8, edgecolor=n.ec, facecolor=n.fc))
    elif n.shape == "diamond":
        vx = [(n.x, n.y + n.h/2), (n.x + n.w/2, n.y), (n.x, n.y - n.h/2), (n.x - n.w/2, n.y)]
        ax.add_patch(patches.Polygon(vx, closed=True, linewidth=1.8, edgecolor=n.ec, facecolor=n.fc))
    ax.text(n.x, n.y, wrap(n.text, max_chars=int(n.w/6.5)), ha="center", va="center", fontsize=9, color=BLACK)

def arrow(ax, p1: Tuple[float,float], p2: Tuple[float,float], label: str = "", curve: float = 0.0, color: str = BLUE):
    style = f"arc3,rad={curve}" if curve != 0 else "arc3"
    ax.add_patch(patches.FancyArrowPatch(p1, p2, connectionstyle=style,
                                         arrowstyle="-|>", mutation_scale=12,
                                         linewidth=1.6, color=color))
    if label:
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        ax.text(mx, my + 2, label, color=color, fontsize=9, ha="center")

# -------- Dibujo principal --------
def draw_diagram() -> bytes:
    # Lienzo “lógico”: ancho=200, alto=170
    W, H = 200, 170
    fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

    # Columnas (x): izquierda / centro / derecha
    X_L, X_C, X_R = 50, 100, 150

    # Columna central (y)
    Yc = {"inicio":150, "b1":132, "b2":114, "b3":96, "dec":78, "fin":22}

    # Nodos centrales
    nodes = [
        Node(X_C, Yc["inicio"], 60, 16, f"INICIO\n{t_inicio}", "oval", LIGHTBLUE),
        Node(X_C, Yc["b1"], 64, 14, b1, "rect", "#FFFFFF"),
        Node(X_C, Yc["b2"], 64, 14, b2, "rect", "#FFFFFF"),
        Node(X_C, Yc["b3"], 64, 14, b3, "rect", "#FFFFFF"),
        Node(X_C, Yc["dec"], 44, 16, q_dec, "diamond", LIGHTYELLOW),
        Node(X_C, Yc["fin"], 66, 16, f"FIN\n{t_fin}", "oval", LIGHTBLUE),
    ]
    n_inicio, n_b1, n_b2, n_b3, n_dec, n_fin = nodes

    # ------ Rama SÍ (ajustable) ------
    n_items = 8
    bottom_safe = 34   # no bajar de acá para no chocar con FIN
    # Calcula espaciado efectivo para que todo quepa desde start_si hasta bottom_safe
    espaciado_maximo = max(6.0, (start_si - bottom_safe) / (n_items - 1))
    step = min(espaciado_deseado, espaciado_maximo)

    # Altura de cajas (más baja en compacto)
    h_si = 12 if compacto else 14
    h_si5 = h_si + 2

    Ys = [start_si - i*step for i in range(n_items)]
    Stexts = [s1, s2, s3, s4, s5, s6, s7, s8]
    Snodes = []
    for i, y in enumerate(Ys):
        h = h_si5 if i == 4 else h_si
        Snodes.append(Node(X_R, y, 74, h, Stexts[i], "rect", "#FFFFFF"))
    nodes += Snodes

    # ------ Rama NO (alineada con los 3 primeros SÍ) ------
    Ntexts = [n1, n2, n3]
    Nnodes = [Node(X_L, Ys[i], 74, h_si, Ntexts[i], "rect", "#FFFFFF") for i in range(3)]
    nodes += Nnodes

    # Dibuja nodos
    for nd in nodes:
        draw_node(ax, nd)

    # Helpers
    def top(n: Node): return (n.x, n.y + n.h/2)
    def bottom(n: Node): return (n.x, n.y - n.h/2)
    def left(n: Node): return (n.x - n.w/2, n.y)
    def right(n: Node): return (n.x + n.w/2, n.y)

    # Flechas columna central
    arrow(ax, bottom(n_inicio), top(n_b1))
    arrow(ax, bottom(n_b1), top(n_b2))
    arrow(ax, bottom(n_b2), top(n_b3))
    arrow(ax, bottom(n_b3), top(n_dec))

    # Decisión → ramas
    arrow(ax, right(n_dec), left(Snodes[0]), label="Sí")
    arrow(ax, left(n_dec), right(Nnodes[0]), label="No")

    # Cadenas
    for a, b in zip(Snodes[:-1], Snodes[1:]): arrow(ax, bottom(a), top(b))
    for a, b in zip(Nnodes[:-1], Nnodes[1:]): arrow(ax, bottom(a), top(b))

    # Retroalimentación (curva, último SÍ → Bloque 2)
    arrow(ax, left(Snodes[-1]), right(n_b2), label="Retroalimentación", curve=0.25)

    # Cierre hacia FIN (Bloque 2 → FIN)
    arrow(ax, bottom(n_b2), top(n_fin))

    # Título y marco
    ax.text(100, 164, "Modelo Preventivo de Gestión Policial – Función de Operacionales",
            ha="center", va="center", fontsize=12, color=BLUE, weight="bold")
    ax.add_patch(patches.Rectangle((3, 3), 200-6, 170-8, fill=False, linewidth=1.5, edgecolor=BORDER))

    # Export PNG bytes
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", dpi=220)
    plt.close(fig)
    return buf.getvalue()

# -------- Exportadores --------
def make_pdf(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO(); img.save(out, format="PDF"); return out.getvalue()

def make_pptx(png_bytes: bytes) -> bytes:
    prs = Presentation(); slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(0.2), Inches(0.2), width=Inches(9.6))
    out = io.BytesIO(); prs.save(out); return out.getvalue()

# -------- Render & Descargas --------
png_bytes = draw_diagram()
pdf_bytes = make_pdf(png_bytes)
pptx_bytes = make_pptx(png_bytes)

st.subheader("Vista previa")
st.image(png_bytes, use_column_width=True)

c1, c2, c3 = st.columns(3)
with c1: st.download_button("⬇️ PNG", png_bytes, "diagrama_modelo_preventivo.png", "image/png")
with c2: st.download_button("⬇️ PDF", pdf_bytes, "diagrama_modelo_preventivo.pdf", "application/pdf")
with c3: st.download_button("⬇️ PPTX", pptx_bytes, "diagrama_modelo_preventivo.pptx",
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation")

st.info("Si aún no cabe: subí el **Inicio rama SÍ** y/o activa **Modo compacto**.")

