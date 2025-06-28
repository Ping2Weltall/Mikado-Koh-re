# 🧠 MK-Watch – Mikado-Kohärenz-Wächter

**MK-Watch** ist ein Analyse-Tool zur strukturellen Konsistenz von Theorie-Threads, Markdown-Dokumenten und Forschungsnotizen. Es erkennt fehlende Definitionsblöcke, sprunghafte Referenzketten und schlägt Diagrammstrukturen zur Stabilisierung vor.  
Entwickelt als Teil des [AbyssChronoChain](https://github.com/dein-benutzername/AbyssChronoChain)-Projekts.

---

## 🔍 Was macht MK-Watch?

MK-Watch analysiert Textdokumente (z. B. `.md`, `.txt`, `.ipynb`) und prüft:

- Ob alle **Schlüsselelemente** einer Theorie vorhanden sind (Definitionen, Parameter, Ableitungen, Schlussfolgerungen)
- Ob **Begriffe korrekt eingeführt** wurden, bevor sie verwendet werden
- Ob die **Referenzkette** logisch und chronologisch konsistent ist
- Ob zyklische oder sprunghafte Verweise auf frühere Abschnitte auftreten
- Optional: Visualisierung als **Diagrammstruktur** (z. B. mit Mermaid)

---

## ⚙️ Installation

```bash
git clone https://github.com/dein-benutzername/mk-watch.git
cd mk-watch
pip install -r requirements.txt
