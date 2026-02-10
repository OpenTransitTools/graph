"""
This code does the following:
  1. clean out old data junk
  2. copy new GTFS and OSM data to the given OTP directory
  3. build the graph
  4. start the graph (webapp api)
  5. test that graph
  6. update otp.v -and- create the .jar-new and .obj-new deploy assets
  7. deploy those assets to stag and prod servers
"""
from ott.utils import otp_utils
from ott.tests.otp import test

from .builder import build_new_graph
from . import graph_dir
from . import runner
from . import deployer

import logging
log = logging.getLogger(__file__)


def cmd_line(do_parse=True):
    # TODO: read a .ini file from ~/otp/otp.ini to override the graph_dir, ports, etc...
    def_graph = graph_dir
    def_port = int(52425)
    def_sec  = int(52225)
    def_svrs = ['cs-st-mapapp01', 'rj-st-mapapp01', 'cs-pd-mapapp01', 'rj-pd-mapapp01', 'cs-pd-mapapp02', 'rj-pd-mapapp02']

    parser = otp_utils.get_initial_arg_parser(f"poetry run otp-builder")
    parser.add_argument('--graph_dir', '-gd', default=def_graph, help="OTP directory full path (graph_dir)")
    parser.add_argument('--port',      '-p',  default=def_port, help="OTP port")
    parser.add_argument('--sec_port',    '-sp', default=def_sec, help="OTP security port")
    parser.add_argument('--version',      '-v',  default=otp_utils.OTP_2, help=f"OTP version ({otp_utils.OTP_1} or {otp_utils.OTP_2})")
    parser.add_argument('--no_tests',    '-n',  action='store_true', help="build graph w/out testing")
    parser.add_argument('--servers',     '-s',  default=def_svrs, help="build graph w/out testing")
    args = parser.parse_args() if do_parse else parser
    return args


class otp():
    cl = cmd_line()

    @classmethod
    def build(cls):
        bs = build_new_graph(cls.cl)
        log.info(f"graph build for {cls.cl.graph_dir}: success == {bs}")
        return bs

    @classmethod
    def test(cls):
        url = otp_utils.get_api_url(cls.cl.version, cls.cl.port)
        test_success = test.all(url, cls.cl.graph_dir)
        log.info(f"testing graph {cls.cl.graph_dir} ({url}): success == {test_success}")
        return test_success

    @classmethod
    def start(cls):
        return runner.start_otp_server(cls.cl)

    @classmethod
    def start_new(cls):
        return runner.start_new_otp(cls.cl)

    @classmethod
    def make_new_files(cls):
        deployer.make_new_files(cls.cl)

    @classmethod
    def update_otp_v(cls):
        deployer.update_otp_v(cls.cl)

    @classmethod
    def package(cls):
        ret_val = False
        runner.kill_otp_server(cls.cl)
        if cls.build():
            if cls.start():
                if cls.test():
                    ret_val = True
                    cls.update_otp_v()
                    cls.make_new_files()
        return ret_val

    @classmethod
    def scp(cls):
        for s in cls.cl.servers:
            deployer.scp(s, cls.cl)
