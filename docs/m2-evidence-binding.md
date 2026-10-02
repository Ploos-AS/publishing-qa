# M2.5 — Evidence binding

Evidence is only useful when it is relevant to the finding it is meant to verify.

## Bindings

Projects declare which evidence producers may be used for which findings. Bindings may match:

- finding ID
- stable claim/check ID
- finding category
- file glob

A binding then names one or more configured evidence producers.

## Example

```yaml
evidence:
  producers:
    - id: edu65xx-sim
      type: simulator
      command: ./tools/run-examples
  bindings:
    - match:
        category: code
        file: "docs/65xx/**/*.md"
      producers: [edu65xx-sim]
```

A PDF build producer bound to category `build` therefore cannot verify a factual CPU finding.

## Stable checks

For mature courses, stable `claim_id` / check IDs are preferred over broad category bindings. This allows a specific claim such as an instruction timing table or worked example to be tied to a dedicated test.

## Validation

Bindings referencing unknown producers are configuration errors. Empty catch-all bindings are rejected.

The binding layer selects candidate evidence producers; the verification layer still decides what the resulting evidence is strong enough to establish.
