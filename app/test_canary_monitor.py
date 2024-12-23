
import unittest
from unittest.mock import patch
import logging
from canary_monitor import check_cpu_usage, check_memory_usage, check_disk_usage

class TestCanaryMonitor(unittest.TestCase):

    @patch('canary_monitor.psutil.cpu_percent', return_value=75)
    def test_check_cpu_usage(self, mock_cpu_percent):
        with self.assertLogs('canary_monitor', level='INFO') as log:
            usage = check_cpu_usage()
            self.assertIn('CPU usage is normal', log.output[0])
            self.assertEqual(usage, 75)

    @patch('canary_monitor.psutil.virtual_memory')
    def test_check_memory_usage(self, mock_virtual_memory):
        mock_virtual_memory.return_value.percent = 60
        with self.assertLogs('canary_monitor', level='INFO') as log:
            usage = check_memory_usage()
            self.assertIn('Memory usage is normal', log.output[0])
            self.assertEqual(usage, 60)

    @patch('canary_monitor.psutil.disk_usage')
    def test_check_disk_usage(self, mock_disk_usage):
        mock_disk_usage.return_value.percent = 85
        with self.assertLogs('canary_monitor', level='WARNING') as log:
            usage = check_disk_usage()
            self.assertIn('High disk usage detected', log.output[0])
            self.assertEqual(usage, 85)

if __name__ == '__main__':
    unittest.main()
