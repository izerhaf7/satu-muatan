"""Modul domain MURNI (spec §5–§7, KEPUTUSAN.md K1/K6).

Aturan keras (CLAUDE.md #2):
- Tanpa import database, tanpa I/O, tanpa datetime.now().
- Semua koefisien bisnis masuk lewat parameter — tidak pernah hardcoded.

Fase 0 membekukan SIGNATURE saja. Implementasi = tugas agent `domain-engine`
(Fase 1), test-first, terhadap tabel angka terkoreksi di KEPUTUSAN.md K1.
"""
