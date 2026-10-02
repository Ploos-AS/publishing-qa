# Publication QA

Publishing QA is opt-in per repository and is configured in `publishing-qa.yml`.

## Metadata

A repository may require a YAML metadata file and named fields such as:

- title
- subtitle
- author
- publisher
- copyright
- license
- language
- ISBNs per edition/format

ISBN checks in M1.2 are structural: length and accidental reuse are checked. Assignment ownership and registration are outside deterministic QA.

## Artifacts

Repositories can declare release artifacts that must exist after build hooks run, for example HTML, EPUB and PDF outputs.

## Chapter manifest

A `chapters.yml` manifest can define canonical reading order. M1.2 detects missing chapter files and duplicate manifest entries.

## Design rule

The central engine does not assume a Ploos repository layout. Each publication declares its source paths, language directories, metadata file, chapter manifest and required outputs.
