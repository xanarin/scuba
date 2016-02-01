 # coding=utf-8
from __future__ import print_function

from nose.tools import *
from .utils import *
from unittest import TestCase

import logging
import os
from os.path import join
from tempfile import mkdtemp
from shutil import rmtree

import scuba.config

class TestConfig(TestCase):
    def setUp(self):
        self.orig_path = os.getcwd()

        self.path = mkdtemp('scubatest')
        os.chdir(self.path)
        logging.info('Temp path: ' + self.path)

    def tearDown(self):
        rmtree(self.path)
        self.path = None

        os.chdir(self.orig_path)
        self.orig_path = None

    ######################################################################
    # Find config

    def test_find_config_cur_dir(self):
        '''find_config can find the config in the current directory'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: busybox\n')

        path, rel = scuba.config.find_config()
        assert_paths_equal(path, self.path)
        assert_paths_equal(rel, '')


    def test_find_config_parent_dir(self):
        '''find_config cuba can find the config in the parent directory'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: busybox\n')

        os.mkdir('subdir')
        os.chdir('subdir')

        # Verify our current working dir
        assert_paths_equal(os.getcwd(), join(self.path, 'subdir'))

        path, rel = scuba.config.find_config()
        assert_paths_equal(path, self.path)
        assert_paths_equal(rel, 'subdir')

    def test_find_config_way_up(self):
        '''find_config can find the config way up the directory hierarchy'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: busybox\n')

        subdirs = ['foo', 'bar', 'snap', 'crackle', 'pop']

        for sd in subdirs:
            os.mkdir(sd)
            os.chdir(sd)

        # Verify our current working dir
        assert_paths_equal(os.getcwd(), join(self.path, *subdirs))

        path, rel = scuba.config.find_config()
        assert_paths_equal(path, self.path)
        assert_paths_equal(rel, join(*subdirs))

    def test_find_config_nonexist(self):
        '''find_config raises ConfigError if the config cannot be found'''
        assert_raises(scuba.config.ConfigError, scuba.config.find_config)

    ######################################################################
    # Load config

    def test_load_config_empty(self):
        '''load_config raises ConfigError if the config is empty'''
        with open('.scuba.yml', 'w') as f:
            pass

        assert_raises(scuba.config.ConfigError, scuba.config.load_config, '.scuba.yml')

    def test_load_unexpected_node(self):
        '''load_config raises ConfigError on unexpected config node'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: busybox\n')
            f.write('unexpected_node_123456: value\n')

        assert_raises(scuba.config.ConfigError, scuba.config.load_config, '.scuba.yml')

    def test_load_config_minimal(self):
        '''load_config loads a minimal config'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: busybox\n')

        config = scuba.config.load_config('.scuba.yml')
        assert_equals(config.image, 'busybox')

    def test_load_config_with_aliases(self):
        '''load_config loads a config with aliases'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: busybox\n')
            f.write('aliases:\n')
            f.write('  foo: bar\n')
            f.write('  snap: crackle pop\n')

        config = scuba.config.load_config('.scuba.yml')
        assert_equals(config.image, 'busybox')
        assert_equals(len(config.aliases), 2)
        assert_seq_equal(config.aliases['foo'], ['bar'])
        assert_seq_equal(config.aliases['snap'], ['crackle', 'pop'])



    def test_load_config_image_from_yaml(self):
        '''load_config loads a config using !from_yaml'''
        with open('.gitlab.yml', 'w') as f:
            f.write('image: debian:8.2\n')

        with open('.scuba.yml', 'w') as f:
            f.write('image: !from_yaml .gitlab.yml image\n')

        config = scuba.config.load_config('.scuba.yml')
        assert_equals(config.image, 'debian:8.2')

    def test_load_config_image_from_yaml_nested_keys(self):
        '''load_config loads a config using !from_yaml with nested keys'''
        with open('.gitlab.yml', 'w') as f:
            f.write('somewhere:\n')
            f.write('  down:\n')
            f.write('    here: debian:8.2\n')

        with open('.scuba.yml', 'w') as f:
            f.write('image: !from_yaml .gitlab.yml somewhere.down.here\n')

        config = scuba.config.load_config('.scuba.yml')
        assert_equals(config.image, 'debian:8.2')

    def test_load_config_image_from_yaml_nested_key_missing(self):
        '''load_config raises ConfigError when !from_yaml references nonexistant key'''
        with open('.gitlab.yml', 'w') as f:
            f.write('somewhere:\n')
            f.write('  down:\n')

        with open('.scuba.yml', 'w') as f:
            f.write('image: !from_yaml .gitlab.yml somewhere.NONEXISTANT\n')

        assert_raises(scuba.config.ConfigError, scuba.config.load_config, '.scuba.yml')

    def test_load_config_image_from_yaml_missing_file(self):
        '''load_config raises ConfigError when !from_yaml references nonexistant file'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: !from_yaml .NONEXISTANT.yml image\n')

        assert_raises(scuba.config.ConfigError, scuba.config.load_config, '.scuba.yml')

    def test_load_config_image_from_yaml_unicode_args(self):
        '''load_config raises ConfigError when !from_yaml has unicode args'''
        with open('.scuba.yml', 'w') as f:
            f.write('image: !from_yaml .NONEXISTANT.yml ½\n')

        assert_raises(scuba.config.ConfigError, scuba.config.load_config, '.scuba.yml')

    def test_load_config_image_from_yaml_missing_arg(self):
        '''load_config raises ConfigError when !from_yaml has missing args'''
        with open('.gitlab.yml', 'w') as f:
            f.write('image: debian:8.2\n')

        with open('.scuba.yml', 'w') as f:
            f.write('image: !from_yaml .gitlab.yml\n')

        assert_raises(scuba.config.ConfigError, scuba.config.load_config, '.scuba.yml')

    ######################################################################
    # process_command

    def test_process_command_no_aliases(self):
        '''process_command handles no aliases'''
        cfg = scuba.config.ScubaConfig(
                image = 'na',
                )
        result = cfg.process_command(['cmd', 'arg1', 'arg2'])
        assert_equal(result, ['cmd', 'arg1', 'arg2'])

    def test_process_command_aliases_unused(self):
        '''process_command handles unused aliases'''
        cfg = scuba.config.ScubaConfig(
                image = 'na',
                aliases = dict(
                    apple = 'banana',
                    cat = 'dog',
                    ),
                )
        result = cfg.process_command(['cmd', 'arg1', 'arg2'])
        assert_equal(result, ['cmd', 'arg1', 'arg2'])

    def test_process_command_aliases_used_noargs(self):
        '''process_command handles aliases with no args'''
        cfg = scuba.config.ScubaConfig(
                image = 'na',
                aliases = dict(
                    apple = 'banana',
                    cat = 'dog',
                    ),
                )
        result = cfg.process_command(['apple', 'arg1', 'arg2'])
        assert_equal(result, ['banana', 'arg1', 'arg2'])

    def test_process_command_aliases_used_withargs(self):
        '''process_command handles aliases with args'''
        cfg = scuba.config.ScubaConfig(
                image = 'na',
                aliases = dict(
                    apple = 'banana cherry "pie is good"',
                    cat = 'dog',
                    ),
                )
        result = cfg.process_command(['apple', 'arg1', 'arg2'])
        assert_equal(result, ['banana', 'cherry', 'pie is good', 'arg1', 'arg2'])