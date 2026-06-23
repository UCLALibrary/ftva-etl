from unittest import TestCase
from src.ftva_etl.metadata.digital_data import (
    get_dcp_info,
    get_dpx_info,
    get_record_type_and_match_asset,
)


class TestDigitalData(TestCase):
    def test_dcp_info(self):
        # Very simple Digital Data record for DCP.
        dcp_record = {
            "file_type": "DCP",
            "file_name": "not relevant",
            "file_folder_name": "folder name",
            "sub_folder_name": "sub folder name",
        }

        dcp_info = get_dcp_info(dcp_record)
        # File name must be empty.
        self.assertEqual(dcp_info["file_name"], "")
        # Other values should match.
        # Note that these methods may rename some field names, which is intentional.
        self.assertEqual(dcp_info["folder_name"], "folder name")
        self.assertEqual(dcp_info["sub_folder_name"], "sub folder name")
        # `file_type` should be "DCP"
        self.assertEqual(dcp_info["file_type"], "DCP")

    def test_dpx_info(self):
        # Very simple Digital Data record for DPX.
        dpx_record = {
            "file_type": "DPX",
            "file_name": "not relevant",
            "file_folder_name": "folder name",
            "sub_folder_name": "sub folder name",
        }

        dpx_info = get_dpx_info(dpx_record)
        # File name must be empty.
        self.assertEqual(dpx_info["file_name"], "")
        # Other values should match.
        # Note that these methods may rename some field names, which is intentional.
        self.assertEqual(dpx_info["folder_name"], "folder name")
        # For DPX, do not include subfolders.
        self.assertNotIn("sub_folder_name", dpx_info)
        # `file_type` should be "DPX"
        self.assertEqual(dpx_info["file_type"], "DPX")

    def test_get_record_type_and_match_asset(self):
        """Test the get_record_type_and_match_asset function."""
        test_digital_data_records = [
            {
                "uuid": "12345",
                "inventory_numbers": ["INV001"],
            },  # Record 1: no track relationship indicated in DD record
            {
                "uuid": "67890",
                "inventory_numbers": ["INV002"],
                "incoming_relationships": [
                    {
                        "relationship_type": "isTrackOf",
                        "source_uuid": "12345",
                    }
                ],
            },  # Record 2: track relationship indicated in DD record targeting asset 12345
            {
                "uuid": "78901",
                "inventory_numbers": ["INV003"],
                "incoming_relationships": [
                    {
                        "relationship_type": "isPartOf",
                        "source_uuid": "12345",
                    }
                ],
            },  # Record 3: wrong relationship type indicated in DD record targeting asset 12345
            {
                "uuid": "12345",
                "inventory_numbers": ["INV004"],
                "incoming_relationships": [
                    {
                        "relationship_type": "isTrackOf",
                        "source_uuid": "78901",
                    },
                    {
                        "relationship_type": "isTrackOf",
                        "source_uuid": "67890",
                    },
                ],
            },  # Record 4: multiple track relationships indicated in DD record
        ]
        expected_results = [
            {
                "record_type": "asset",
            },  # Record 1 should be an asset
            {
                "record_type": "track",
                "match_asset": "12345",
            },  # Record 2 should be a track, with match_asset set to UUID of the asset
            {
                "record_type": "asset",
            },  # Record 3 should be an asset
            {
                "record_type": "track",
                "match_asset": "78901",
            },  # Record 4 should be a track, with match_asset set from the first relationship
        ]

        # Zip together the two lists to get tuples of (dd_record, expected_result)
        for dd_record, expected_result in zip(
            test_digital_data_records, expected_results
        ):
            with self.subTest(dd_record=dd_record, expected_result=expected_result):
                result = get_record_type_and_match_asset(dd_record)
                self.assertEqual(result, expected_result)
