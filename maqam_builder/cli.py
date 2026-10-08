"""Command-line interface: ``python -m maqam_builder --help``."""

from __future__ import annotations

import argparse
import sys
import textwrap

from . import builder
from .data import DROMOI, MAKAMS

LEGEND = ("Koma accidentals: ♭¹ = one koma (≈23¢) flat, ♯⁴ = four komas sharp, "
          "etc. 1 koma = 1/53 octave.")


def _print_makam(scale: builder.Scale, makam) -> None:
    print(f"\n{scale.title} — tonic {scale.tonic}, {scale.direction}ending")
    print(f"{'Deg':>3}  {'Note':<6} {'Greek':<7} {'Perde':<12} {'Step':<20}"
          f"{'Komas':>5} {'Cents':>7} {'Hz':>8}")
    for n in scale.notes:
        print(f"{n.degree:>3}  {n.name:<6} {n.greek:<7} {n.perde:<12} {n.step:<20}"
              f"{n.komas:>5} {n.cents:>7.1f} {n.frequency:>8.2f}")


def _print_dromos(scale: builder.Scale) -> None:
    print(f"\n{scale.title} — tonic {scale.tonic}, {scale.direction}ending")
    print(f"{'Deg':>3}  {'Note':<6} {'Greek':<7} {'Cents':>6} {'Hz':>8}")
    for n in scale.notes:
        print(f"{n.degree:>3}  {n.name:<6} {n.greek:<7} {n.cents:>6.0f} {n.frequency:>8.2f}")


def _wrap(text: str, indent: str = "    ") -> str:
    return textwrap.fill(text, width=88, initial_indent=indent,
                         subsequent_indent=indent + "  ")


def cmd_list(_args) -> None:
    print("Greek dromoi (12-TET):")
    for key, d in DROMOI.items():
        parent = MAKAMS[d.makam].name if d.makam else "— (Greek-born)"
        print(f"  {key:<12} {d.name} / {d.greek:<14} on {d.tonic:<3} ← makam {parent}")
    print("\nTurkish makams (53-koma):")
    for key, m in MAKAMS.items():
        print(f"  {key:<12} {m.name:<10} on {m.tonic:<4} steps {'-'.join(map(str, m.steps))}")


def cmd_makam(args) -> None:
    _, makam = builder.find_makam(args.name)
    print(f"Makam {makam.name}: {makam.description}")
    print(f"Seyir: {makam.seyir}; güçlü (dominant): degree {makam.guclu + 1}")
    directions = ["asc", "desc"] if makam.descending or args.both else ["asc"]
    for direction in directions:
        _print_makam(builder.build_makam(args.name, args.tonic, direction, args.a4), makam)
    print("\n" + LEGEND)


def cmd_dromos(args) -> None:
    _, dromos = builder.find_dromos(args.name)
    print(f"Dromos {dromos.name} ({dromos.greek}): {dromos.description}")
    directions = ["asc", "desc"] if dromos.descending else ["asc"]
    for direction in directions:
        _print_dromos(builder.build_dromos(args.name, args.tonic, direction, args.a4))

    if dromos.makam:
        makam = MAKAMS[dromos.makam]
        tonic = args.tonic or dromos.tonic
        print(f"\nOriginal makam {makam.name} transposed to {tonic}, for comparison:")
        mk = sorted(builder.build_makam(dromos.makam, tonic).notes, key=lambda n: n.degree)
        dr = sorted(builder.build_dromos(args.name, args.tonic).notes, key=lambda n: n.degree)
        print(f"{'Deg':>3}  {'Fret':<6} {'Makam':<6} {'Δ cents':>8}")
        for d, m in zip(dr, mk):
            print(f"{d.degree:>3}  {d.name:<6} {m.name:<6} {m.cents - d.cents:>+8.0f}")

    print("\nTips — playing the dromos so it moves like the makam:")
    for direction in directions:
        tips = builder.dromos_tips(args.name, args.tonic, direction)
        if tips:
            print(f"  {direction}ending:")
        for tip in tips:
            makam_note = f", makam {tip.makam_note}" if tip.makam_note else ""
            print(_wrap(f"{tip.dromos_note} (degree {tip.degree}{makam_note}): {tip.text}"))
    for tip in dromos.tips:
        print(_wrap("• " + tip, "  "))
    if dromos.makam:
        print()
        for line in builder.TECHNIQUE.values():
            print(_wrap(line, ""))
        print(LEGEND)


def cmd_identify(args) -> None:
    result = builder.identify(args.notes)
    print("Dromoi:", ", ".join(result["dromoi"]) or "none")
    print("Makams:", ", ".join(result["makams"]) or "none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="maqam_builder",
        description="Notes of Turkish makams (53-koma) and Greek dromoi "
                    "(12-TET), with tips for bending the dromos toward the makam.")
    parser.add_argument("--a4", type=float, default=440.0, help="reference pitch (Hz)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list all dromoi and makams").set_defaults(func=cmd_list)

    p = sub.add_parser("makam", help="show a Turkish makam")
    p.add_argument("name")
    p.add_argument("--tonic", help="transpose, e.g. D, Eb, B-1 (koma offset)")
    p.add_argument("--both", action="store_true", help="also show descending form")
    p.set_defaults(func=cmd_makam)

    p = sub.add_parser("dromos", help="show a Greek dromos with microtonal tips")
    p.add_argument("name")
    p.add_argument("--tonic", help="transpose, e.g. E, A, F#")
    p.set_defaults(func=cmd_dromos)

    p = sub.add_parser("identify", help="name the dromos/makam from its first notes")
    p.add_argument("notes", nargs="+", help="tonic first, e.g. D Eb F#")
    p.set_defaults(func=cmd_identify)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (KeyError, ValueError) as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 1
    return 0
