from . import CrabDBTestCase

class JobIdentifyTestCase(CrabDBTestCase):
    def test_identify(self):
        """Test that _check_job correctly identifies jobs."""

        id_ = self.store._check_job('host1', 'user1', None, 'command1')
        self.assertEqual(id_, 1, 'First job should have ID 1')

        id_ = self.store._check_job('host2', 'user1', None, 'command1')
        self.assertEqual(id_, 2, 'Job on new host should have new ID')

        id_ = self.store._check_job('host1', 'user2', None, 'command1')
        self.assertEqual(id_, 3, 'Job for new user should have new ID')

        id_ = self.store._check_job('host1', 'user1', None, 'command2')
        self.assertEqual(id_, 4, 'Job for new command should have new ID')

        id_ = self.store._check_job('host1', 'user1', None, 'command1')
        self.assertEqual(id_, 1, 'Original job should have ID 1')

        id_ = self.store._check_job('host1', 'user1', 'crabid1', 'command1')
        self.assertEqual(id_, 1, 'Original job should have ID 1 with crabid')

        id_ = self.store._check_job('host1', 'user1', 'crabid1', 'command3')
        self.assertEqual(id_, 1, 'Original job should have ID 1 by crabid')

        id_ = self.store._check_job('host1', 'user1', None, 'command3')
        self.assertEqual(id_, 1, 'Original job should have ID 1 by new command')

        id_ = self.store._check_job('host1', 'user1', None, 'command1')
        self.assertEqual(id_, 5, 'Original command should now be a new job')

        id_ = self.store._check_job('host1', 'user1', 'crabid2', 'command4')
        self.assertEqual(id_, 6, 'Additional new command creates new job')

        id_ = self.store._check_job('host1', 'user1', 'crabid3', 'command4')
        self.assertEqual(id_, 7, 'New ID should create  another new job')
