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
import os
from ott.utils import otp_utils
from ott.tests.otp import test

from .builder import build_new_graph
from . import runner
from . import deployer

import logging
log = logging.getLogger(__file__)


def cmd_line(otp_instance, port, sec_port=None, v=otp_utils.OTP_2, base_dir='otp', do_parse=True):
    cwd = os.getcwd()
    otp_dir = os.path.join(base_dir, otp_instance)  # ./otp/rtp or ./otp/call, etc...
    otp_path = os.path.join(cwd, otp_dir)

    parser = otp_utils.get_initial_arg_parser(f"poetry run {otp_instance}-builder")
    parser.add_argument('--instance',  '-i',  default=otp_instance, help="OTP instance (eg: 'rtp', 'call', 'api', etc...)")
    parser.add_argument('--otp_dir',   '-od', default=otp_dir, help="OTP directory relative path")
    parser.add_argument('--graph_dir', '-gd', default=otp_path, help="OTP directory full path (graph_dir)")
    parser.add_argument('--port',      '-p',  default=int(port), help="OTP port")
    parser.add_argument('--sec_port',  '-sp', default=sec_port, help="OTP security port")
    parser.add_argument('--version',   '-v',  default=v, help=f"OTP version ({otp_utils.OTP_1} or {otp_utils.OTP_2})")
    parser.add_argument('--no_tests',  '-n',  action='store_true', help="build graph w/out testing")
    parser.add_argument('--servers',   '-s',  default=['cs-st-mapapp01', 'rj-st-mapapp01', 'cs-pd-mapapp01', 'rj-pd-mapapp01', 'cs-pd-mapapp02', 'rj-pd-mapapp02'], help="build graph w/out testing")
    args = parser.parse_args() if do_parse else parser
    return args


class base():
    # import pdb; pdb.set_trace()
    cl = None

    @classmethod
    def build(cls):
        bs = build_new_graph(cls.cl)
        log.info(f"graph build for {cls.cl.instance}: success == {bs}")
        return bs

    @classmethod
    def test(cls):
        url = otp_utils.get_api_url(cls.cl.version, cls.cl.port)
        test_success = test.all(url)
        log.info(f"testing graph {cls.cl.instance} ({url}): success == {test_success}")
        return test_success

    @classmethod
    def start(cls):
        return runner.start_otp_server(cls.cl)

    @classmethod
    def start_new(cls):
        return runner.start_new_otp(cls.cl)

    @classmethod
    def update_otp_v(cls):
        deployer.update_otp_v(cls.cl.graph_dir, cls.cl.version)

    @classmethod
    def package(cls):
        ret_val = False
        if cls.build():
            if cls.start():
                if cls.test():
                    ret_val = True
                    cls.update_otp_v()
        return ret_val

    @classmethod
    def scp(cls):
        for s in cls.cl.servers:
            deployer.scp(s, cls.cl)


class rtp(base):
    cl = cmd_line('rtp', port=52425)    

class otp2(base):
    """ trimet only OTP 2.x instance for new call.trimet.org, etc... """
    cl = cmd_line('otp2', port=52225)

class otp1(base):
    cl = cmd_line('otp1', port=51115, v=otp_utils.OTP_1)

class old_call(base):
    """ for legacy call running OTP 1.x """
    #import pdb; pdb.set_trace()
    cl = cmd_line('otp', port=52225, v=otp_utils.OTP_1)
