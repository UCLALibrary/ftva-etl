# Changelog
## 0.3.1 - 2026-04-08

### Changed
- Updated the default Filemaker layout used by the Filemaker client.

## 0.3.0 - 2026-03-23

### Changed
- Merged changes from `legacy_fm_changes` branch, which includes functionality for obtaining metadata from legacy records matching only Filemaker data.

## 0.2.0 - 2026-03-17

### Fixed

- Fixed logic for obtaining episode title metadata from Filemaker records.
 
### Added

- Convenience wrappers around `fmrest.Server.get_records()` and `fmrest.Server.edit_record()` are added on the Filemaker client.

## 0.1.5 - 2026-03-03

### Changed

- `file_type` included in output for DPX records

## 0.1.4 - 2026-01-27

### Added

- Logging enabled, with configuration options exposed by `ftva_etl.metadata.utils.configure_logging()`.

### Changed

- Logs are generated when `creators` cannot be recognized unambiguously from MARC 245 $c.

### Fixed

- Parsing of `creators` from MARC 245 $c is improved by allowing more flexible attribution phrases.

## 0.1.3 - 2025-11-13

### Changes

- Handling of `title` and `date` fields from MARC records is updated.
- `inventory_number` field is pluralized to `inventory_numbers`

## 0.1.2 - 2025-10-20

### Fixed

- MARC 245 $c parsing for directors is improved by splitting on semicolons.

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
