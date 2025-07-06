import copy
import json
from typing import Any


def maybe_load_json(data):
    """Attempt to load a JSON string, return the original data if it fails."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return data


def apply_diff(
    data: dict[str, Any],
    diff: dict[str, Any],
    do_delete: bool = True,
    clone: bool = True,
):
    """Apply a doover compatible diff to a JSON / dict object.

    Returns a new object with the diff applied.

    To modify the object in-place, pass `clone=False`.
    """
    if clone:
        data = copy.deepcopy(data)

    if not isinstance(diff, dict) or not isinstance(data, dict):
        # if data is not a dict, we can't apply the diff
        # so we just return the diff
        return diff

    for k, v in diff.items():
        if isinstance(v, dict):
            # print(f"applying: ({type(k)}) {k} -> ({type(v)}) {v} (data: ({type(data)}) {data})")
            data[k] = apply_diff(data.get(k, {}), v, do_delete=do_delete, clone=False)
        elif v is None:
            # del data[k]
            if do_delete:
                # if do_delete is True, remove the key from the dict
                data.pop(k, None)
            else:
                # if do_delete is False, set the key to None
                data[k] = None
        else:
            data[k] = v
    return data


def generate_diff(old, new):
    """Generate a doover compatible diff between two JSON / dict objects.

    A diff will contain all keys that are different between the two objects.

    Any keys that are in the old object but not in the new object will be set to None.
    """
    if not isinstance(new, dict) or not isinstance(old, dict):
        return new

    diff = {}
    for k, v in new.items():
        if isinstance(v, dict):
            d = generate_diff(old.get(k, {}), v)
            if d:
                diff[k] = generate_diff(old.get(k, {}), v)
        elif k not in old or old[k] != v:
            diff[k] = v
    for k in old.keys() - new.keys():
        diff[k] = None
    return diff
