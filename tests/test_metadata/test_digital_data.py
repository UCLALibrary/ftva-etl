from unittest import TestCase
from src.ftva_etl.metadata.digital_data import get_dcp_info, get_dpx_info


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
