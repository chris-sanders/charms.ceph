import io
import unittest
from shutil import rmtree
from tempfile import mkdtemp
from threading import Timer
import json
from subprocess import CalledProcessError
import nose.plugins.attrib
import os
import time
from contextlib import contextmanager

from mock import patch, call, MagicMock
import ceph_helpers as ceph_utils
import six

if not six.PY3:
    builtin_open = '__builtin__.open'
else:
    builtin_open = 'builtins.open'

LS_POOLS = """
images
volumes
rbd
"""

LS_RBDS = """
rbd1
rbd2
rbd3
"""

IMG_MAP = """
bar
baz
"""


@contextmanager
def patch_open():
    """Patch open() to allow mocking both open() itself and the file that is
    yielded.

    Yields the mock for "open" and "file", respectively."""
    mock_open = MagicMock(spec=open)
    mock_file = MagicMock(spec=io.FileIO)

    @contextmanager
    def stub_open(*args, **kwargs):
        mock_open(*args, **kwargs)
        yield mock_file

    with patch(builtin_open, stub_open):
        yield mock_open, mock_file


class CephCrushmapTests(unittest.TestCase):
    def setUp(self):
        super(CephCrushmapTests, self).setUp()

    @patch.object(ceph_utils.Crushmap, 'load_crushmap')
    def test_crushmap_buckets(self, load_crushmap):
        load_crushmap.return_value = ""
        crushmap = ceph_utils.Crushmap()
        crushmap.add_bucket("test")
        self.assertEqual(
            crushmap.buckets(), [ceph_utils.Crushmap.Bucket("test", -1)])

    @patch.object(ceph_utils.Crushmap, 'load_crushmap')
    def test_parsed_crushmap(self, load_crushmap):
        load_crushmap.return_value = """# begin crush map
tunable choose_local_tries 0
tunable choose_local_fallback_tries 0
tunable choose_total_tries 50
tunable chooseleaf_descend_once 1
tunable chooseleaf_vary_r 1
tunable straw_calc_version 1

# devices
device 0 osd.0
device 1 osd.1
device 2 osd.2

# types
type 0 osd
type 1 host
type 2 chassis
type 3 rack
type 4 row
type 5 pdu
type 6 pod
type 7 room
type 8 datacenter
type 9 region
type 10 root

# buckets
host ip-172-31-33-152 {
    id -2		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.0 weight 0.003
}
host ip-172-31-54-117 {
    id -3		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.1 weight 0.003
}
host ip-172-31-30-0 {
    id -4		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.2 weight 0.003
}
root default {
    id -1		# do not change unnecessarily
    # weight 0.009
    alg straw
    hash 0	# rjenkins1
    item ip-172-31-33-152 weight 0.003
    item ip-172-31-54-117 weight 0.003
    item ip-172-31-30-0 weight 0.003
}

# rules
rule replicated_ruleset {
    ruleset 0
    type replicated
    min_size 1
    max_size 10
    step take default
    step chooseleaf firstn 0 type host
    step emit
}

# end crush map"""
        crushmap = ceph_utils.Crushmap()
        self.assertEqual(
            [ceph_utils.Crushmap.Bucket("default", -1, True)],
            crushmap.buckets())
        self.assertEqual([-4, -3, -2, -1], crushmap._ids)

    @patch.object(ceph_utils.Crushmap, 'load_crushmap')
    def test_build_crushmap(self, load_crushmap):
        load_crushmap.return_value = """# begin crush map
tunable choose_local_tries 0
tunable choose_local_fallback_tries 0
tunable choose_total_tries 50
tunable chooseleaf_descend_once 1
tunable chooseleaf_vary_r 1
tunable straw_calc_version 1

# devices
device 0 osd.0
device 1 osd.1
device 2 osd.2

# types
type 0 osd
type 1 host
type 2 chassis
type 3 rack
type 4 row
type 5 pdu
type 6 pod
type 7 room
type 8 datacenter
type 9 region
type 10 root

# buckets
host ip-172-31-33-152 {
    id -2		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.0 weight 0.003
}
host ip-172-31-54-117 {
    id -3		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.1 weight 0.003
}
host ip-172-31-30-0 {
    id -4		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.2 weight 0.003
}
root default {
    id -1		# do not change unnecessarily
    # weight 0.009
    alg straw
    hash 0	# rjenkins1
    item ip-172-31-33-152 weight 0.003
    item ip-172-31-54-117 weight 0.003
    item ip-172-31-30-0 weight 0.003
}

# rules
rule replicated_ruleset {
    ruleset 0
    type replicated
    min_size 1
    max_size 10
    step take default
    step chooseleaf firstn 0 type host
    step emit
}

# end crush map"""
        expected = """# begin crush map
tunable choose_local_tries 0
tunable choose_local_fallback_tries 0
tunable choose_total_tries 50
tunable chooseleaf_descend_once 1
tunable chooseleaf_vary_r 1
tunable straw_calc_version 1

# devices
device 0 osd.0
device 1 osd.1
device 2 osd.2

# types
type 0 osd
type 1 host
type 2 chassis
type 3 rack
type 4 row
type 5 pdu
type 6 pod
type 7 room
type 8 datacenter
type 9 region
type 10 root

# buckets
host ip-172-31-33-152 {
    id -2		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.0 weight 0.003
}
host ip-172-31-54-117 {
    id -3		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.1 weight 0.003
}
host ip-172-31-30-0 {
    id -4		# do not change unnecessarily
    # weight 0.003
    alg straw
    hash 0	# rjenkins1
    item osd.2 weight 0.003
}
root default {
    id -1		# do not change unnecessarily
    # weight 0.009
    alg straw
    hash 0	# rjenkins1
    item ip-172-31-33-152 weight 0.003
    item ip-172-31-54-117 weight 0.003
    item ip-172-31-30-0 weight 0.003
}

# rules
rule replicated_ruleset {
    ruleset 0
    type replicated
    min_size 1
    max_size 10
    step take default
    step chooseleaf firstn 0 type host
    step emit
}

# end crush map

root test {
    id -5    # do not change unnecessarily
    # weight 0.000
    alg straw
    hash 0  # rjenkins1
}

rule test {
    ruleset 0
    type replicated
    min_size 1
    max_size 10
    step take test
    step chooseleaf firstn 0 type host
    step emit
}"""
        crushmap = ceph_utils.Crushmap()
        crushmap.add_bucket("test")
        self.assertEqual(expected, crushmap.build_crushmap())

    def test_crushmap_string(self):
        result = ceph_utils.Crushmap.bucket_string("fast", -21)
        expected = """root fast {
    id -21    # do not change unnecessarily
    # weight 0.000
    alg straw
    hash 0  # rjenkins1
}

rule fast {
    ruleset 0
    type replicated
    min_size 1
    max_size 10
    step take fast
    step chooseleaf firstn 0 type host
    step emit
}"""
        self.assertEqual(expected, result)


class CephUtilsTests(unittest.TestCase):
    def setUp(self):
        super(CephUtilsTests, self).setUp()
        [self._patch(m) for m in [
            'check_call',
            'check_output',
            'log',
        ]]

    def _patch(self, method):
        _m = patch.object(ceph_utils, method)
        mock = _m.start()
        self.addCleanup(_m.stop)
        setattr(self, method, mock)

    @patch('os.path.exists')
    def test_create_keyring(self, _exists):
        """It creates a new ceph keyring"""
        _exists.return_value = False
        ceph_utils.create_keyring('cinder', 'cephkey')
        _cmd = ['ceph-authtool', '/etc/ceph/ceph.client.cinder.keyring',
                '--create-keyring', '--name=client.cinder',
                '--add-key=cephkey']
        self.check_call.assert_called_with(_cmd)

    @patch('os.path.exists')
    def test_create_keyring_already_exists(self, _exists):
        """It creates a new ceph keyring"""
        _exists.return_value = True
        ceph_utils.create_keyring('cinder', 'cephkey')
        self.assertTrue(self.log.called)
        self.check_call.assert_not_called()

    @patch('os.remove')
    @patch('os.path.exists')
    def test_delete_keyring(self, _exists, _remove):
        """It deletes a ceph keyring."""
        _exists.return_value = True
        ceph_utils.delete_keyring('cinder')
        _remove.assert_called_with('/etc/ceph/ceph.client.cinder.keyring')
        self.assertTrue(self.log.called)

    @patch('os.remove')
    @patch('os.path.exists')
    def test_delete_keyring_not_exists(self, _exists, _remove):
        """It creates a new ceph keyring."""
        _exists.return_value = False
        ceph_utils.delete_keyring('cinder')
        self.assertTrue(self.log.called)
        _remove.assert_not_called()

    @patch('os.path.exists')
    def test_create_keyfile(self, _exists):
        """It creates a new ceph keyfile"""
        _exists.return_value = False
        with patch_open() as (_open, _file):
            ceph_utils.create_key_file('cinder', 'cephkey')
            _file.write.assert_called_with('cephkey')
        self.assertTrue(self.log.called)

    @patch('os.path.exists')
    def test_create_key_file_already_exists(self, _exists):
        """It creates a new ceph keyring"""
        _exists.return_value = True
        ceph_utils.create_key_file('cinder', 'cephkey')
        self.assertTrue(self.log.called)

    @patch('os.mkdir')
    @patch.object(ceph_utils, 'apt_install')
    @patch('os.path.exists')
    def test_install(self, _exists, _install, _mkdir):
        _exists.return_value = False
        ceph_utils.install()
        _mkdir.assert_called_with('/etc/ceph')
        _install.assert_called_with('ceph-common', fatal=True)

    @patch.object(ceph_utils, 'ceph_version')
    def test_get_osds(self, version):
        version.return_value = '0.56.2'
        self.check_output.return_value = json.dumps([1, 2, 3])
        self.assertEquals(ceph_utils.get_osds('test'), [1, 2, 3])

    @patch.object(ceph_utils, 'ceph_version')
    def test_get_osds_argonaut(self, version):
        version.return_value = '0.48.3'
        self.assertEquals(ceph_utils.get_osds('test'), None)

    @patch.object(ceph_utils, 'ceph_version')
    def test_get_osds_none(self, version):
        version.return_value = '0.56.2'
        self.check_output.return_value = json.dumps(None)
        self.assertEquals(ceph_utils.get_osds('test'), None)

    @patch.object(ceph_utils, 'get_osds')
    @patch.object(ceph_utils, 'pool_exists')
    @patch.object(ceph_utils.Pool, 'get_pgs')
    @patch.object(ceph_utils, 'get_erasure_profile')
    def test_create_erasure_pool(self, _erasure_profile, _pgs, _exists,
                                 _get_osds):
        """It creates rados pool correctly with a default erasure profile """
        _exists.return_value = False
        _get_osds.return_value = [1, 2, 3]
        _pgs.return_value = 100
        _erasure_profile.return_value = {"k": 2, "m": 1}
        erasure_pool = ceph_utils.ErasurePool(service='cinder',
                                              name='foo',
                                              erasure_code_profile="default")
        erasure_pool.create()
        self.check_call.assert_has_calls([
            call(['ceph', '--id', 'cinder', 'osd', 'pool',
                  'create', 'foo', '100', '100', 'erasure', 'default']),
        ])

    @patch.object(ceph_utils, 'get_osds')
    @patch.object(ceph_utils, 'pool_exists')
    @patch.object(ceph_utils.Pool, 'get_pgs')
    @patch.object(ceph_utils, 'get_erasure_profile')
    def test_create_erasure_local_pool(self, _erasure_profile, _pgs, _exists,
                                       _get_osds):
        """It creates rados pool correctly with a default erasure profile """
        _exists.return_value = False
        _get_osds.return_value = [1, 2, 3]
        _pgs.return_value = 100
        _erasure_profile.return_value = {"k": 2, "m": 1, "l": 1}

        local_erasure_pool = ceph_utils.ErasurePool(
            service='cinder',
            name='foo',
            erasure_code_profile="default")
        local_erasure_pool.create()

        self.check_call.assert_has_calls([
            call(['ceph', '--id', 'cinder', 'osd', 'pool',
                  'create', 'foo', '100', '100', 'erasure', 'default']),
        ])

    @patch.object(ceph_utils, 'get_osds')
    @patch.object(ceph_utils, 'pool_exists')
    @patch.object(ceph_utils.Pool, 'get_pgs')
    def test_create_pool(self, _pgs, _exists, _get_osds):
        """It creates rados pool correctly with default replicas """
        _exists.return_value = False
        _get_osds.return_value = [1, 2, 3]
        _pgs.return_value = 100
        replicated_pool = ceph_utils.ReplicatedPool(service='cinder',
                                                    name='foo', replicas=3)
        replicated_pool.create()
        self.check_call.assert_has_calls([
            call(['ceph', '--id', 'cinder', 'osd', 'pool',
                  'create', 'foo', '100']),
            call(['ceph', '--id', 'cinder', 'osd', 'pool', 'set',
                  'foo', 'size', '3'])
        ])

    @patch.object(ceph_utils, 'get_osds')
    @patch.object(ceph_utils, 'pool_exists')
    @patch.object(ceph_utils.Pool, 'get_pgs')
    def test_create_pool_2_replicas(self, _pgs, _exists, _get_osds):
        """It creates rados pool correctly with 3 replicas"""
        _exists.return_value = False
        _get_osds.return_value = [1, 2, 3]
        _pgs.return_value = 150
        replicated_pool = ceph_utils.ReplicatedPool(service='cinder',
                                                    name='foo',
                                                    replicas=2)
        replicated_pool.create()
        self.check_call.assert_has_calls([
            call(['ceph', '--id', 'cinder', 'osd', 'pool',
                  'create', 'foo', '150']),
            call(['ceph', '--id', 'cinder', 'osd', 'pool', 'set',
                  'foo', 'size', '2'])
        ])

    @patch.object(ceph_utils, 'get_osds')
    @patch.object(ceph_utils, 'pool_exists')
    @patch.object(ceph_utils.Pool, 'get_pgs')
    def test_create_pool_argonaut(self, _pgs, _exists, _get_osds):
        """It creates rados pool correctly with 3 replicas"""
        _exists.return_value = False
        _get_osds.return_value = None
        _pgs.return_value = 200

        replicated_pool = ceph_utils.ReplicatedPool(service='cinder',
                                                    name='foo',
                                                    replicas=3)
        replicated_pool.create()
        # ceph_utils.create_pool(service='cinder', pool_class=replicated_pool)
        self.check_call.assert_has_calls([
            call(['ceph', '--id', 'cinder', 'osd', 'pool',
                  'create', 'foo', '200']),
            call(['ceph', '--id', 'cinder', 'osd', 'pool', 'set',
                  'foo', 'size', '3'])
        ])

    @patch.object(ceph_utils, 'pool_exists')
    @patch.object(ceph_utils.Pool, 'get_pgs')
    def test_create_pool_already_exists(self, _pgs, _exists):
        _exists.return_value = True
        _pgs.return_value = 200
        replicated_pool = ceph_utils.ReplicatedPool(service='cinder',
                                                    name='foo')
        replicated_pool.create()
        self.assertFalse(self.log.called)
        self.check_call.assert_not_called()

    def test_keyring_path(self):
        """It correctly dervies keyring path from service name"""
        result = ceph_utils._keyring_path('cinder')
        self.assertEquals('/etc/ceph/ceph.client.cinder.keyring', result)

    def test_keyfile_path(self):
        """It correctly dervies keyring path from service name"""
        result = ceph_utils._keyfile_path('cinder')
        self.assertEquals('/etc/ceph/ceph.client.cinder.key', result)

    def test_pool_exists(self):
        """It detects an rbd pool exists"""
        self.check_output.return_value = LS_POOLS
        self.assertTrue(ceph_utils.pool_exists('cinder', 'volumes'))

    def test_pool_does_not_exist(self):
        """It detects an rbd pool exists"""
        self.check_output.return_value = LS_POOLS
        self.assertFalse(ceph_utils.pool_exists('cinder', 'foo'))

    def test_pool_exists_error(self):
        """ Ensure subprocess errors and sandboxed with False """
        self.check_output.side_effect = CalledProcessError(1, 'rados')
        self.assertFalse(ceph_utils.pool_exists('cinder', 'foo'))

    def test_rbd_exists(self):
        self.check_output.return_value = LS_RBDS
        self.assertTrue(ceph_utils.rbd_exists('service', 'pool', 'rbd1'))
        self.check_output.assert_called_with(
            ['rbd', 'list', '--id', 'service', '--pool', 'pool']
        )

    def test_rbd_does_not_exist(self):
        self.check_output.return_value = LS_RBDS
        self.assertFalse(ceph_utils.rbd_exists('service', 'pool', 'rbd4'))
        self.check_output.assert_called_with(
            ['rbd', 'list', '--id', 'service', '--pool', 'pool']
        )

    def test_rbd_exists_error(self):
        """ Ensure subprocess errors and sandboxed with False """
        self.check_output.side_effect = CalledProcessError(1, 'rbd')
        self.assertFalse(ceph_utils.rbd_exists('cinder', 'foo', 'rbd'))

    def test_create_rbd_image(self):
        ceph_utils.create_rbd_image('service', 'pool', 'image', 128)
        _cmd = ['rbd', 'create', 'image',
                '--size', '128',
                '--id', 'service',
                '--pool', 'pool']
        self.check_call.assert_called_with(_cmd)

    def test_delete_pool(self):
        ceph_utils.delete_pool('cinder', 'pool')
        _cmd = [
            'ceph', '--id', 'cinder',
            'osd', 'pool', 'delete',
            'pool', '--yes-i-really-really-mean-it'
        ]
        self.check_call.assert_called_with(_cmd)

    def test_get_ceph_nodes(self):
        self._patch('relation_ids')
        self._patch('related_units')
        self._patch('relation_get')
        units = ['ceph/1', 'ceph2', 'ceph/3']
        self.relation_ids.return_value = ['ceph:0']
        self.related_units.return_value = units
        self.relation_get.return_value = '192.168.1.1'
        self.assertEquals(len(ceph_utils.get_ceph_nodes()), 3)

    def test_get_ceph_nodes_not_related(self):
        self._patch('relation_ids')
        self.relation_ids.return_value = []
        self.assertEquals(ceph_utils.get_ceph_nodes(), [])

    def test_configure(self):
        self._patch('create_keyring')
        self._patch('create_key_file')
        self._patch('get_ceph_nodes')
        self._patch('modprobe')
        _hosts = ['192.168.1.1', '192.168.1.2']
        self.get_ceph_nodes.return_value = _hosts
        _conf = ceph_utils.CEPH_CONF.format(
            auth='cephx',
            keyring=ceph_utils._keyring_path('cinder'),
            mon_hosts=",".join(map(str, _hosts)),
            use_syslog='true'
        )
        with patch_open() as (_open, _file):
            ceph_utils.configure('cinder', 'key', 'cephx', 'true')
            _file.write.assert_called_with(_conf)
            _open.assert_called_with('/etc/ceph/ceph.conf', 'w')
        self.modprobe.assert_called_with('rbd')
        self.create_keyring.assert_called_with('cinder', 'key')
        self.create_key_file.assert_called_with('cinder', 'key')

    def test_image_mapped(self):
        self.check_output.return_value = IMG_MAP
        self.assertTrue(ceph_utils.image_mapped('bar'))

    def test_image_not_mapped(self):
        self.check_output.return_value = IMG_MAP
        self.assertFalse(ceph_utils.image_mapped('foo'))

    def test_image_not_mapped_error(self):
        self.check_output.side_effect = CalledProcessError(1, 'rbd')
        self.assertFalse(ceph_utils.image_mapped('bar'))

    def test_map_block_storage(self):
        _service = 'cinder'
        _pool = 'bar'
        _img = 'foo'
        _cmd = [
            'rbd',
            'map',
            '{}/{}'.format(_pool, _img),
            '--user',
            _service,
            '--secret',
            ceph_utils._keyfile_path(_service),
        ]
        ceph_utils.map_block_storage(_service, _pool, _img)
        self.check_call.assert_called_with(_cmd)

    def test_filesystem_mounted(self):
        self._patch('mounts')
        self.mounts.return_value = [['/afs', '/dev/sdb'], ['/bfs', '/dev/sdd']]
        self.assertTrue(ceph_utils.filesystem_mounted('/afs'))
        self.assertFalse(ceph_utils.filesystem_mounted('/zfs'))

    @patch('os.path.exists')
    def test_make_filesystem(self, _exists):
        _exists.return_value = True
        ceph_utils.make_filesystem('/dev/sdd')
        self.assertTrue(self.log.called)
        self.check_call.assert_called_with(['mkfs', '-t', 'ext4', '/dev/sdd'])

    @patch('os.path.exists')
    def test_make_filesystem_xfs(self, _exists):
        _exists.return_value = True
        ceph_utils.make_filesystem('/dev/sdd', 'xfs')
        self.assertTrue(self.log.called)
        self.check_call.assert_called_with(['mkfs', '-t', 'xfs', '/dev/sdd'])

    @patch('os.chown')
    @patch('os.stat')
    def test_place_data_on_block_device(self, _stat, _chown):
        self._patch('mount')
        self._patch('copy_files')
        self._patch('umount')
        _stat.return_value.st_uid = 100
        _stat.return_value.st_gid = 100
        ceph_utils.place_data_on_block_device('/dev/sdd', '/var/lib/mysql')
        self.mount.assert_has_calls([
            call('/dev/sdd', '/mnt'),
            call('/dev/sdd', '/var/lib/mysql', persist=True)
        ])
        self.copy_files.assert_called_with('/var/lib/mysql', '/mnt')
        self.umount.assert_called_with('/mnt')
        _chown.assert_called_with('/var/lib/mysql', 100, 100)

    @patch('shutil.copytree')
    @patch('os.listdir')
    @patch('os.path.isdir')
    def test_copy_files_is_dir(self, _isdir, _listdir, _copytree):
        _isdir.return_value = True
        subdirs = ['a', 'b', 'c']
        _listdir.return_value = subdirs
        ceph_utils.copy_files('/source', '/dest')
        for d in subdirs:
            _copytree.assert_has_calls([
                call('/source/{}'.format(d), '/dest/{}'.format(d),
                     False, None)
            ])

    @patch('shutil.copytree')
    @patch('os.listdir')
    @patch('os.path.isdir')
    def test_copy_files_include_symlinks(self, _isdir, _listdir, _copytree):
        _isdir.return_value = True
        subdirs = ['a', 'b', 'c']
        _listdir.return_value = subdirs
        ceph_utils.copy_files('/source', '/dest', True)
        for d in subdirs:
            _copytree.assert_has_calls([
                call('/source/{}'.format(d), '/dest/{}'.format(d),
                     True, None)
            ])

    @patch('shutil.copytree')
    @patch('os.listdir')
    @patch('os.path.isdir')
    def test_copy_files_ignore(self, _isdir, _listdir, _copytree):
        _isdir.return_value = True
        subdirs = ['a', 'b', 'c']
        _listdir.return_value = subdirs
        ceph_utils.copy_files('/source', '/dest', True, False)
        for d in subdirs:
            _copytree.assert_has_calls([
                call('/source/{}'.format(d), '/dest/{}'.format(d),
                     True, False)
            ])

    @patch('shutil.copy2')
    @patch('os.listdir')
    @patch('os.path.isdir')
    def test_copy_files_files(self, _isdir, _listdir, _copy2):
        _isdir.return_value = False
        files = ['a', 'b', 'c']
        _listdir.return_value = files
        ceph_utils.copy_files('/source', '/dest')
        for f in files:
            _copy2.assert_has_calls([
                call('/source/{}'.format(f), '/dest/{}'.format(f))
            ])

    @patch.object(ceph_utils.Pool, 'get_pgs')
    def test_ensure_ceph_storage(self, _pgs):
        self._patch('pool_exists')
        self.pool_exists.return_value = False
        self._patch('create_pool')
        self._patch('rbd_exists')
        self.rbd_exists.return_value = False
        self._patch('create_rbd_image')
        self._patch('image_mapped')
        self.image_mapped.return_value = False
        self._patch('map_block_storage')
        self._patch('filesystem_mounted')
        self.filesystem_mounted.return_value = False
        self._patch('make_filesystem')
        self._patch('service_stop')
        self._patch('service_start')
        self._patch('service_running')
        self.service_running.return_value = True
        self._patch('place_data_on_block_device')
        _pgs.return_value = 200

        _service = 'mysql'
        _pool = 'foo'
        _rbd_img = 'foo'
        _mount = '/var/lib/mysql'
        _services = ['mysql']
        _blk_dev = '/dev/rbd1'
        ceph_utils.ensure_ceph_storage(_service, _pool,
                                       _rbd_img, 1024, _mount,
                                       _blk_dev, 'ext4', _services)
        self.create_pool.assert_called_with(_service, _pool, replicas=3)
        self.create_rbd_image.assert_called_with(_service, _pool,
                                                 _rbd_img, 1024)
        self.map_block_storage.assert_called_with(_service, _pool, _rbd_img)
        self.make_filesystem.assert_called_with(_blk_dev, 'ext4')
        self.service_stop.assert_called_with(_services[0])
        self.place_data_on_block_device.assert_called_with(_blk_dev, _mount)
        self.service_start.assert_called_with(_services[0])

    def test_make_filesystem_default_filesystem(self):
        """make_filesystem() uses ext4 as the default filesystem."""
        device = '/dev/zero'
        ceph_utils.make_filesystem(device)
        self.check_call.assert_called_with(['mkfs', '-t', 'ext4', device])

    def test_make_filesystem_no_device(self):
        """make_filesystem() raises an IOError if the device does not exist."""
        device = '/no/such/device'
        with self.assertRaises(IOError) as cm:
            ceph_utils.make_filesystem(device, timeout=0)
        e = cm.exception
        self.assertEquals(device, e.filename)
        self.assertEquals(os.errno.ENOENT, e.errno)
        self.assertEquals(os.strerror(os.errno.ENOENT), e.strerror)
        self.log.assert_called_with(
            'Gave up waiting on block device %s' % device, level='ERROR')

    @nose.plugins.attrib.attr('slow')
    def test_make_filesystem_timeout(self):
        """
        make_filesystem() allows to specify how long it should wait for the
        device to appear before it fails.
        """
        device = '/no/such/device'
        timeout = 2
        before = time.time()
        self.assertRaises(IOError, ceph_utils.make_filesystem, device,
                          timeout=timeout)
        after = time.time()
        duration = after - before
        self.assertTrue(timeout - duration < 0.1)
        self.log.assert_called_with(
            'Gave up waiting on block device %s' % device, level='ERROR')

    @nose.plugins.attrib.attr('slow')
    def test_device_is_formatted_if_it_appears(self):
        """
        The specified device is formatted if it appears before the timeout
        is reached.
        """

        def create_my_device(filename):
            with open(filename, "w") as device:
                device.write("hello\n")

        temp_dir = mkdtemp()
        self.addCleanup(rmtree, temp_dir)
        device = "%s/mydevice" % temp_dir
        fstype = 'xfs'
        timeout = 4
        t = Timer(2, create_my_device, [device])
        t.start()
        ceph_utils.make_filesystem(device, fstype, timeout)
        self.check_call.assert_called_with(['mkfs', '-t', fstype, device])

    def test_existing_device_is_formatted(self):
        """
        make_filesystem() formats the given device if it exists with the
        specified filesystem.
        """
        device = '/dev/zero'
        fstype = 'xfs'
        ceph_utils.make_filesystem(device, fstype)
        self.check_call.assert_called_with(['mkfs', '-t', fstype, device])
        self.log.assert_called_with(
            'Formatting block device %s as '
            'filesystem %s.' % (device, fstype), level='INFO'
        )

    @patch.object(ceph_utils, 'relation_ids')
    @patch.object(ceph_utils, 'related_units')
    @patch.object(ceph_utils, 'relation_get')
    def test_ensure_ceph_keyring_no_relation_no_data(self, rget, runits, rids):
        rids.return_value = []
        self.assertEquals(False, ceph_utils.ensure_ceph_keyring(service='foo'))
        rids.return_value = ['ceph:0']
        runits.return_value = ['ceph/0']
        rget.return_value = ''
        self.assertEquals(False, ceph_utils.ensure_ceph_keyring(service='foo'))

    @patch.object(ceph_utils, '_keyring_path')
    @patch.object(ceph_utils, 'create_keyring')
    @patch.object(ceph_utils, 'relation_ids')
    @patch.object(ceph_utils, 'related_units')
    @patch.object(ceph_utils, 'relation_get')
    def test_ensure_ceph_keyring_with_data(self, rget, runits,
                                           rids, create, _path):
        rids.return_value = ['ceph:0']
        runits.return_value = ['ceph/0']
        rget.return_value = 'fookey'
        self.assertEquals(True,
                          ceph_utils.ensure_ceph_keyring(service='foo'))
        create.assert_called_with(service='foo', key='fookey')
        _path.assert_called_with('foo')
        self.assertFalse(self.check_call.called)

        _path.return_value = '/etc/ceph/client.foo.keyring'
        self.assertEquals(
            True,
            ceph_utils.ensure_ceph_keyring(
                service='foo', user='adam', group='users'))
        create.assert_called_with(service='foo', key='fookey')
        _path.assert_called_with('foo')
        self.check_call.assert_called_with([
            'chown',
            'adam.users',
            '/etc/ceph/client.foo.keyring'
        ])

    @patch('os.path.exists')
    def test_ceph_version_not_installed(self, path):
        path.return_value = False
        self.assertEquals(ceph_utils.ceph_version(), None)

    @patch.object(ceph_utils, 'check_output')
    @patch('os.path.exists')
    def test_ceph_version_error(self, path, output):
        path.return_value = True
        output.return_value = b''
        self.assertEquals(ceph_utils.ceph_version(), None)

    @patch.object(ceph_utils, 'check_output')
    @patch('os.path.exists')
    def test_ceph_version_ok(self, path, output):
        path.return_value = True
        output.return_value = \
            'ceph version 0.67.4 (ad85b8bfafea6232d64cb7ba76a8b6e8252fa0c7)'
        self.assertEquals(ceph_utils.ceph_version(), '0.67.4')

    @patch.object(ceph_utils.Pool, 'get_pgs')
    def test_ceph_broker_rq_class(self, _get_pgs):
        _get_pgs.return_value = 200
        rq = ceph_utils.CephBrokerRq(
            request_id="3f8941ec-9707-11e6-a0e3-305a3a7cf348")
        rq.add_op_create_pool(name='pool1', replica_count=1, pg_num=200)
        rq.add_op_create_pool(name='pool2', pg_num=200)
        expected = json.dumps({"api-version": 1,
                               "request-id":
                                   "3f8941ec-9707-11e6-a0e3-305a3a7cf348",
                               "ops": [{"op": "create-pool",
                                        "replicas": 1, "pg_num": 200,
                                        "name": "pool1", "weight": None},
                                       {"op": "create-pool",
                                        "replicas": 3, "pg_num": 200,
                                        "name": "pool2", "weight": None}]
                               })
        self.assertEqual(rq.request, expected)

    def test_ceph_broker_rsp_class(self):
        rsp = ceph_utils.CephBrokerRsp(json.dumps({'exit-code': 0,
                                                   'stderr': "Success"}))
        self.assertEqual(rsp.exit_code, 0)
        self.assertEqual(rsp.exit_msg, "Success")
