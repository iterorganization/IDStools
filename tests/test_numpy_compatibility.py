from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_numpy_nan_alias_not_used_in_package_sources():
    package_files = list((ROOT / "idstools").rglob("*.py"))
    assert package_files, "No Python source files found under idstools/"

    offenders = []
    for path in package_files:
        text = path.read_text(encoding="utf-8")
        if "np.NaN" in text:
            offenders.append(path.relative_to(ROOT))

    assert not offenders, f"Deprecated NumPy alias np.NaN found in: {', '.join(map(str, offenders))}"
