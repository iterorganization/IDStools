# Fix NumPy 2 compatibility for deprecated `np.NaN` usage

## Summary

This PR fixes NumPy 2 compatibility issues caused by deprecated `np.NaN` usage in `IDStools`.

NumPy 2 removed the `np.NaN` alias. In the current codebase, this causes runtime failures in fallback paths that
construct missing-data arrays, most visibly in `plotkineticprofiles` when toroidal velocity data is absent.

## Root Cause

`IDStools` still used `np.NaN` in a few computation and helper paths:

- `idstools/domain/kineticprofiles.py`
- `idstools/utils/idshelper.py`

When these branches execute under NumPy 2, Python raises:

```text
AttributeError: `np.NaN` was removed in the NumPy 2.0 release. Use `np.nan` instead.
```

## Changes

- Replaced all runtime `np.NaN` usages with `np.nan`
- Updated stale comments in `idstools/domain/ecstray.py` for consistency
- Added a focused regression test to prevent reintroducing `np.NaN` in package sources

## Verification

### Automated

```bash
conda run -n imas pytest tests/test_numpy_compatibility.py -q
```

Result:

```text
1 passed in 0.01s
```

### Reproduction Check

Verified that the local source tree is used:

```bash
conda run -n imas env PYTHONPATH=/Users/yun/git/IDStools python -c 'import idstools; print(idstools.__file__)'
```

Verified that the previous NumPy 2 failure path no longer crashes:

```bash
conda run -n imas env -u DISPLAY PYTHONPATH=/Users/yun/git/IDStools \
  python /Users/yun/git/IDStools/scripts/plotkineticprofiles \
  --uri "imas:hdf5?path=/Users/yun/git/Yun_ITER_Machine_Mapping_Workshop/data/TCV/TCV interpolated" \
  --save --directory /tmp/idstools_numpy2_fix_test
```

Result:

- command exits successfully
- figure is saved under `/tmp/idstools_numpy2_fix_test`
- the previous `np.NaN` `AttributeError` is no longer reproduced

## Scope / Non-Goals

- This PR only addresses NumPy 2 compatibility for deprecated `np.NaN`
- This PR does not change plotting backend behavior on macOS
- This PR does not modify data access or machine-specific plotting logic

## Risk

Low.

This is a narrow alias replacement from `np.NaN` to `np.nan`, which is the supported NumPy spelling and preserves
the intended missing-data semantics.
