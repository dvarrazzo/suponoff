import unittest
from . import testutils
import supcast.config
import supcast.supcredis

class TestState(unittest.TestCase):
    sup = None

    @classmethod
    def setUpClass(cls):
        cls.sup = testutils.run_supervisor(
            config='config1.ini')
        supcast.set_redis_url('redis://localhost:6379')

    @classmethod
    def tearDownClass(cls):
        testutils.stop_supervisor(cls.sup)

    def test_state(self):
        state = supcast.get_all_state()
        print(state)
