# Changelog

## 0.7.0 - 2026-08-06
### Changed
- Refactored legacy `mams_metadata.py` to mirror NDM `mams_metadata_ndm.py` module
- Updated logic to align with current specs

## 0.6.3 - 2026-07-31
### Changed
- Updated `get_media_type()` logic to return lowercased values for media type, as MAMS expects

## 0.6.2 - 2026-07-30
### Changed
- Updated field names to align with what MAMS expects:
  - `inventory_ids` -> `inventory_id`
  - `source_ids` -> `source_identifier`
  - NOTE: The MAMS expects the keys `inventory_id` and `source_identifier` (singular) for these data fields, even though the values are lists of strings. The keys are not pluralized, but the values are still lists. We are accepting this inconsistency to avoid costly changes in the MAMS.

## 0.6.1 - 2026-07-24
### Changed
- Updated `get_media_type()` logic to classify DPX as "Video" rather than "Image", as MAMS expects

## 0.6.0 - 2026-07-14

### Added
- Added `mams_metadata_ndm.py` module for formatting NDM metadata
- Implemented new logic per NDM specs

## 0.5.1 - 2026-06-30

### Changed
- Fixed bug related to parsing of dates from MARC records with only year and month

## 0.5.0 - 2026-06-24

### Changed
- Refactored `mams_metadata.py` for clarity and to integrate metadata-formatting logic previously handled in external script.

## 0.4.0 - 2026-06-16

### Added
- New `DigitalDataClient.get_records()` method for paginated retrieval of FTVA Digital Data records, with optional query and field filtering.

## 0.3.4 - 2026-06-10

### Changed
- Updated key from `copyright_release_date` to `copyright_date` for date output in `marc.py` module.

## 0.3.3 - 2026-06-04

### Fixed
- Added `click` as an explicit dependency due to a [bug](https://github.com/explosion/spaCy/issues/13971) with `spacy`

## 0.3.2 - 2026-05-20

### Added
- New `FilemakerClient.find_all_records()` method for paginated retrieval of all records matching a query, supporting exact matches, ranges, and excluded values.

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
