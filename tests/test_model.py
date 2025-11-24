import unittest
from datetime import datetime
from model import Event, Issue, State

class TestModel(unittest.TestCase):

    def test_enum_values(self):
        # Just making sure the enum returns the right strings
        self.assertEqual(State.open, 'open')
        self.assertEqual(State.closed, 'closed')

    def test_create_event(self):
        # Happy path for creating an event
        payload = {
            'event_type': 'labeled',
            'author': 'dev_user',
            'event_date': '2025-01-01T12:00:00',
            'label': 'bug',
            'comment': 'needs fix'
        }
        e = Event(payload)
        
        self.assertEqual(e.event_type, 'labeled')
        self.assertEqual(e.author, 'dev_user')
        # Check that date parsing worked
        self.assertTrue(isinstance(e.event_date, datetime))
        self.assertEqual(e.label, 'bug')

    def test_event_broken_date(self):
        # This checks if the try/except block handles bad dates
        bad_data = {
            'event_type': 'labeled',
            'event_date': 'garbage-date-string' 
        }
        e = Event(bad_data)
        self.assertIsNone(e.event_date)

    def test_event_empty(self):
        # Check what happens if we pass None
        e = Event(None)
        self.assertIsNone(e.event_type)

    def test_create_full_issue(self):
        # Create an event to put inside the issue
        event_info = {
            'event_type': 'commented', 
            'event_date': '2025-01-01T12:00:00'
        }
        
        issue_data = {
            'url': 'http://test.com',
            'creator': 'admin',
            'labels': ['bug'],
            'state': 'open',
            'assignees': ['me'],
            'title': 'Broken login',
            'text': 'Fix it',
            'number': '42',
            'created_date': '2025-01-01T10:00:00',
            'updated_date': '2025-01-02T10:00:00',
            'timeline_url': 'http://test.com/timeline',
            'events': [event_info] 
        }
        
        i = Issue(issue_data)

        self.assertEqual(i.number, 42)
        self.assertEqual(i.state, State.open)
        self.assertIsNotNone(i.created_date)
        
        # Verify the event list parsed correctly
        self.assertEqual(len(i.events), 1)
        self.assertEqual(i.events[0].event_type, 'commented')

    def test_issue_exceptions(self):
        # Sending bad data to trigger all the exception handlers in Issue
        broken_payload = {
            'state': 'closed',
            'number': 'not-a-number', # Should default to -1
            'created_date': 'bad-date',
            'updated_date': 'bad-date',
            'events': []
        }
        i = Issue(broken_payload)

        self.assertEqual(i.number, -1)
        self.assertIsNone(i.created_date)
        self.assertIsNone(i.updated_date)

    def test_issue_none(self):
        # Initialize with nothing
        i = Issue(None)
        self.assertIsNone(i.url)

if __name__ == '__main__':
    unittest.main()