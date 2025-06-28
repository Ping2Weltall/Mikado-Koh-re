#!/usr/bin/env python3
# mk_watch.py
# 🧠 MK-Watch – Mikado-Kohärenz-Wächter
# Vollständiges, Copy&Paste-fähiges Skript mit Grafik- & Simulation-Checks

import re
import argparse
import yaml
from pathlib import Path

# +++ 1) Konfigurations­loader +++
def load_config(path: str = "terms.yml"):
    """Lädt required_blocks und critical_terms aus einer YAML-Datei."""
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    required = cfg.get("required_blocks", [])
    critical = cfg.get("critical_terms", [])
    return required, critical

# +++ 2) Text in Abschnitte zerlegen +++
def parse_sections(text: str):
    """Zerlegt das Dokument in Abschnitte anhand von Markdown-Überschriften."""
    parts = re.split(r'\n#+\s+', text)
    return [sec.strip() for sec in parts if sec.strip()]

# +++ 3) Theorie­blöcke prüfen +++
def find_missing_blocks(sections, required_blocks):
    """Prüft, ob alle erwarteten Theorieblöcke vorhanden sind."""
    found = [b for b in required_blocks if any(b.lower() in s.lower() for s in sections)]
    missing = [b for b in required_blocks if b not in found]
    return missing

# +++ 4) Kritische Begriffe prüfen +++
def find_critical_terms(sections, critical_terms):
    """
    Sucht nach kritischen Begriffen ohne vorherige Einführung.
    Gibt Liste von (Begriff, Abschnittsnummer) zurück.
    """
    introduced = set()
    missing_refs = []
    for idx, sec in enumerate(sections, start=1):
        for term in critical_terms:
            if term in sec and term not in introduced:
                missing_refs.append((term, idx))
            if term in sec:
                introduced.add(term)
    return missing_refs

# +++ 5) Referenzkette analysieren +++
def analyze_reference_chain(sections):
    """
    Analysiert alle „Abschnitt X“-Referenzen in der Reihenfolge ihres Auftretens.
    Liefert Liste von Abschnittsnummern.
    """
    pattern = re.compile(r'Abschnitt\s+(\d+)')
    chain = []
    for sec in sections:
        refs = pattern.findall(sec)
        chain.extend(int(n) for n in refs)
    return chain

# +++ 6) Bilddateien prüfen +++
def find_image_references(text: str):
    """
    Findet alle Markdown-Image-Tags ![alt](path) 
    und prüft, ob die Datei existiert.
    """
    pattern = re.compile(r'!\[.*?\]\(([^)]+)\)')
    missing = []
    for path in pattern.findall(text):
        if not Path(path).exists():
            missing.append(path)
    return missing

# +++ 7) Abbildungs­zitate erfassen +++
def find_figure_citations(sections):
    """
    Sucht nach „Abbildung X“ in Abschnitten.
    Gibt Liste von (Nummer, Abschnittsnummer) zurück.
    """
    figs = []
    for idx, sec in enumerate(sections, start=1):
        for m in re.finditer(r'Abbildung\s+(\d+)', sec):
            figs.append((int(m.group(1)), idx))
    return figs

# +++ 8) Simulations­blöcke zählen +++
def find_simulation_blocks(text: str):
    """
    Sucht nach ```simulation\n...``` Codeblöcken.
    Gibt (Anzahl, Liste der Blockinhalte) zurück.
    """
    blocks = re.findall(r'```(?:python\s+)?simulation\n(.*?)```', text, flags=re.S)
    return len(blocks), blocks

# +++ 9) Haupt­funktion +++
def main(filepath: str, cfg_path: str):
    # Datei einlesen
    p = Path(filepath)
    if not p.exists():
        print(f"❌ Datei nicht gefunden: {filepath}")
        return
    text = p.read_text(encoding="utf-8")
    sections = parse_sections(text)

    # Config laden
    required_blocks, critical_terms = load_config(cfg_path)

    print(f"\n🔍 Analysiere: {filepath}\n")

    # 1. Theorieblöcke
    missing = find_missing_blocks(sections, required_blocks)
    if missing:
        print("❗ Fehlende Theorieblöcke:")
        for b in missing:
            print(f"   – {b}")
    else:
        print("✅ Alle Theorieblöcke vorhanden.")

    # 2. Kritische Begriffe
    miss_terms = find_critical_terms(sections, critical_terms)
    if miss_terms:
        print("\n⚠ Kritische Begriffe ohne Einleitung:")
        for term, sec in miss_terms:
            print(f"   – {term} erstmals in Abschnitt {sec}")
    else:
        print("\n✅ Alle kritischen Begriffe eingeführt.")

    # 3. Referenzkette
    chain = analyze_reference_chain(sections)
    if chain:
        print("\n🔗 Referenzkette:")
        print("   Abschnittsfolge:", " → ".join(map(str, chain)))
        if chain != sorted(chain):
            print("   ⚠ Chronologie durchbrochen – Neuordnung nötig")
    else:
        print("\nℹ Keine Abschnittsverweise gefunden.")

    # 4. Bilder prüfen
    missing_imgs = find_image_references(text)
    if missing_imgs:
        print("\n🖼 Fehlende Bilddateien:")
        for img in missing_imgs:
            print(f"   – {img}")
    else:
        print("\n✅ Alle referenzierten Bilder vorhanden.")

    # 5. Abbildungen
    figs = find_figure_citations(sections)
    if figs:
        print("\n🔎 Abbildungs-Verweise:")
        for num, sec in figs:
            print(f"   – Abbildung {num} in Abschnitt {sec}")
    else:
        print("\nℹ Keine Abbildungs-Verweise gefunden.")

    # 6. Simulationen
    sim_count, sim_blocks = find_simulation_blocks(text)
    if sim_count:
        print(f"\n⚙️ {sim_count} Simulation-Codeblock(s) erkannt.")
    else:
        print("\nℹ Keine Simulation-Codeblöcke gefunden.")

    print("\n🧠 MK-Watch abgeschlossen.\n")

# +++ 10) CLI-Argumente +++
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MK-Watch – Mikado-Kohärenz-Wächter für Markdown-Theorie-Threads"
    )
    parser.add_argument("filepath", help="Pfad zur Markdown-Datei (.md, .txt, .ipynb)")
    parser.add_argument(
        "--config", "-c",
        default="terms.yml",
        help="Pfad zur YAML-Konfigurationsdatei (terms.yml)"
    )
    args = parser.parse_args()
    main(args.filepath, args.config)