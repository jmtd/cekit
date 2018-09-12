import glob
import os
import subprocess
import yaml

from cekit.builder import Builder


def test_osbs_builder_defaults(mocker):
    mocker.patch.object(subprocess, 'check_output')

    builder = Builder('osbs', 'tmp', {})

    assert builder._release is False
    assert builder._rhpkg == 'fedpkg'
    assert builder._nowait is False


def test_osbs_builder_redhat(mocker):
    mocker.patch.object(subprocess, 'check_output')

    builder = Builder('osbs', 'tmp', {'redhat': True})

    assert builder._rhpkg == 'rhpkg'


def test_osbs_builder_use_rhpkg_staget(mocker):
    mocker.patch.object(subprocess, 'check_output')

    params = {'stage': True,
              'redhat': True}
    builder = Builder('osbs', 'tmp', params)

    assert builder._rhpkg == 'rhpkg-stage'


def test_osbs_builder_custom_commit_msg(mocker):
    mocker.patch.object(subprocess, 'check_output')

    params = {'stage': True,
              'commit_msg': 'foo'}
    builder = Builder('osbs', 'tmp', params)

    assert builder._commit_msg == 'foo'


def test_osbs_builder_nowait(mocker):
    mocker.patch.object(subprocess, 'check_output')

    params = {'nowait': True}
    builder = Builder('osbs', 'tmp', params)

    assert builder._nowait is True


def test_osbs_builder_user(mocker):
    mocker.patch.object(subprocess, 'check_output')

    params = {'user': 'UserFoo'}
    builder = Builder('osbs', 'tmp', params)

    assert builder._user == 'UserFoo'


def test_merge_container_yaml_no_limit_arch(mocker, tmpdir):
    mocker.patch.object(glob, 'glob', return_value=False)
    mocker.patch.object(subprocess, 'check_output')

    builder = Builder('osbs', 'tmp', {})
    builder.dist_git_dir = str(tmpdir.mkdir('target'))

    container_yaml_f = 'container.yaml'

    source = 'souce_cont.yaml'
    with open(source, 'w') as file_:
        yaml.dump({'tags': ['foo']}, file_)

    builder._merge_container_yaml(source, container_yaml_f)

    with open(container_yaml_f, 'r') as file_:
        container_yaml = yaml.safe_load(file_)
    os.remove(container_yaml_f)

    assert 'paltforms' not in container_yaml


def test_merge_container_yaml_limit_arch(mocker, tmpdir):
    mocker.patch.object(glob, 'glob', return_value=True)
    mocker.patch.object(subprocess, 'check_output')
    builder = Builder('osbs', 'tmp', {})
    builder.dist_git_dir = str(tmpdir.mkdir('target'))

    container_yaml_f = 'container.yaml'

    source = 'souce_cont.yaml'
    with open(source, 'w') as file_:
        yaml.dump({'tags': ['foo']}, file_)

    builder._merge_container_yaml(source, container_yaml_f)

    with open(container_yaml_f, 'r') as file_:
        container_yaml = yaml.safe_load(file_)
    os.remove(container_yaml_f)

    assert 'x86_64' in container_yaml['platforms']['only']
    assert len(container_yaml['platforms']['only']) == 1


class DistGitMock(object):
    def add(self):
        pass

    def stage_modified(self):
        pass


def create_osbs_build_object(mocker, builder_type, params):
    mocker.patch.object(subprocess, 'check_output')
    mocker.patch('cekit.tools.decision')

    builder = Builder(builder_type, 'tmp', params)
    builder.dist_git_dir = '/tmp'
    builder.dist_git = DistGitMock()
    builder.artifacts = []
    return builder


def test_osbs_builder_run_rhpkg_stage(mocker):
    mocker.patch.object(subprocess, 'check_output')

    params = {'stage': True,
              'redhat': True}

    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'osbs', params)
    builder.build()

    check_call.assert_called_once_with(['rhpkg-stage', 'container-build', '--scratch'])


def test_osbs_builder_run_rhpkg(mocker):
    mocker.patch.object(subprocess, 'check_output')

    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'osbs', {'redhat': True})
    builder.build()

    check_call.assert_called_once_with(['rhpkg', 'container-build', '--scratch'])


def test_osbs_builder_run_rhpkg_nowait(mocker):
    mocker.patch.object(subprocess, 'check_output')
    params = {'nowait': True,
              'redhat': True}

    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'osbs', params)
    builder.build()

    check_call.assert_called_once_with(['rhpkg', 'container-build', '--nowait', '--scratch'])


def test_osbs_builder_run_rhpkg_user(mocker):
    params = {'user': 'Foo',
              'redhat': True}

    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'osbs', params)
    builder.build()

    check_call.assert_called_once_with(['rhpkg', '--user', 'Foo', 'container-build', '--scratch'])


def test_osbs_builder_run_rhpkg_target(mocker):
    params = {'target': 'Foo',
              'redhat': True}

    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'osbs', params)
    builder.build()

    check_call.assert_called_once_with(['rhpkg', 'container-build', '--target', 'Foo', '--scratch'])


def test_docker_builder_defaults():
    params = {'tags': ['foo', 'bar']}
    builder = Builder('docker', 'tmp', params)

    assert builder._tags == ['foo', 'bar']


def test_buildah_builder_run(mocker):
    params = {'tags': ['foo', 'bar']}
    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'buildah', params)
    builder.build()

    check_call.assert_called_once_with(['sudo',
                                        'buildah',
                                        'build-using-dockerfile',
                                        '-t', 'foo',
                                        '-t', 'bar',
                                        'tmp/image'])


def test_buildah_builder_run_pull(mocker):
    params = {'tags': ['foo', 'bar'], 'pull': True}
    check_call = mocker.patch.object(subprocess, 'check_call')
    builder = create_osbs_build_object(mocker, 'buildah', params)
    builder.build()

    check_call.assert_called_once_with(['sudo',
                                        'buildah',
                                        'build-using-dockerfile',
                                        '--pull-always',
                                        '-t', 'foo',
                                        '-t', 'bar',
                                        'tmp/image'])
