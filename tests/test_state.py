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
        sup = state['supervisors']['localhost-19001']
        self.assertEqual(sup['url'], 'http://localhost:19001')
        self.assertEqual(sorted(sup['tags']), ['foo', 'tag1:a'])

        g1 = sup['groups']['p1']
        self.assertEqual(g1['tags'], ['tag2:b'])
        p1 = g1['processes']['p1']
        self.assertEqual(p1['statename'], 'RUNNING')
        self.assert_(isinstance(p1['pid'], int))

        g2 = sup['groups']['p2']
        self.assertEqual(sorted(g2['tags']), ['bar', 'tag2:b'])
        self.assertEqual(len(g2['processes']), 3)
        p2 = g2['processes']['p2_0']
        self.assertEqual(p2['statename'], 'RUNNING')
        self.assert_(isinstance(p2['pid'], int))
