import unittest
from app.services.processor import process_data

class TestProcessor(unittest.TestCase):
    def test_empty_input(self):
        self.assertTrue(process_data([]).empty)

    def test_valid_input(self):
        sample = [{
            "name": "Test",
            "location": {"city": "X", "country": "Y", "latitude": 1, "longitude": 2},
            "extra": {"slots": 10}
        }]
        df = process_data(sample)
        self.assertEqual(df.iloc[0]['station_count'], 10)

if __name__ == '__main__':
    unittest.main()
