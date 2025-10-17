# Changelog

## 0.1.1 - 2025-10-17

### Fixed

- 4-character years with hyphens as placeholders, like `[198-]` and `[19--]`, are preserved as-is.
- SRU call number search results can be refined by limiting to FTVA holdings, and better matching against FTVA inventory number suffixes.

## 0.1.0 - 2025-10-08

### Added

- `audio_class` is included in JSON.
- Several date field variants can populated from MARC bib 264 fields, when present.

### Changed

- Title logic takes the Filemaker PD `production_type` field into account.
