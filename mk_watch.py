# mk_watch.py

import re
import argparse
import yaml
from pathlib import Path

def load_config(path="terms.yml"):
    """Lädt kritische Begriffe und Theorieblöcke aus YAML-Datei."""
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return cfg["required_blocks"], cfg["critical_terms"]

def parse_sections(text):
    """Zerlegt das Dokument in Abschnitte anhand von Markdown-Überschriften."""
    sections = re.split(r'\n#+\s+', text)
    return [s.strip() for s in sections if s.strip()]

def find_missing_blocks(sections, required_blocks):
    """Prüft, ob alle erwarteten Theorieblöcke vorhanden sind."""
    found = [block for block in required_blocks if any(block.lower() in s.lower() for s in sections)]
    missing = [block for block in required_blocks if block not in found]
    return missing

def find_critical_terms(sections, critical_terms):
    """Sucht nach kritischen Begriffen ohne vorherige Einführung."""
    introduced = set()
    missing_refs = []

    for i, section in enumerate(sections):
        for term in critical_terms:
            if term in section:
                if term not in introduced:
                    missing_refs.append((term, i + 1))
                introduced.add(term)
    return missing_refs

def analyze_reference_chain(sections):
    """Analysiert die Reihenfolge von Referenzen (z. B. Abschnitt 1 → 5 → 2)."""
    pattern = re.compile(r'Abschnitt\s+(\d+)')
    chain = []

    for section in sections:
        refs = pattern.findall(section)
        chain.extend(int(r) for r in refs)

    return chain

def main(filepath, cfg_path):
    text = Path(filepath).read_text(encoding='utf-8')
    sections = parse_sections(text)
    required_blocks, critical_terms = load_config(cfg_path)

    print(f"\n🔍 Analysiere Datei: {filepath}\n")

    # 1. Fehlende Theorieblöcke
    missing = find_missing_blocks(sections, required_blocks)
    if missing:
        print("❗ Fehlende Theorieblöcke:")
        for block in missing:
            print(f"   – {block}")
    else:
        print("✅ Alle Theorieblöcke vorhanden.")

    # 2. Kritische Begriffe ohne Einleitung
    missing_refs = find_critical_terms(sections, critical_terms)
    if missing_refs:
        print("\n⚠️ Kritische Begriffe ohne Einleitung:")
        for term, sec in missing_refs:
            print(f"   – {term} erstmals in Abschnitt {sec}")
    else:
        print("\n✅ Alle kritischen Begriffe wurden eingeführt.")

    # 3. Referenzkette analysieren
    chain = analyze_reference_chain(sections)
    if chain:
        print("\n🔗 Referenzkette erkannt:")
        print("   Abschnittsfolge:", " → ".join(map(str, chain)))
        if chain != sorted(chain):
            print("   ⚠ Chronologie durchbrochen – evtl. Neuordnung nötig")
    else:
        print("\nℹ️ Keine expliziten Abschnittsverweise gefunden.")

    print("\n🧠 MK-Watch abgeschlossen.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MK-Watch – Mikado-Kohärenz-Wächter")
    parser.add_argument("filepath", help="Pfad zur Markdown-Datei")
    parser.add_argument("--config", "-c", default="terms.yml", help="Pfad zur YAML-Konfigurationsdatei")
    args = parser.parse_args()
    main(args.filepath, args.config)