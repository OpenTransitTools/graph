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
from ott.utils import file_utils
from ott.utils import otp_utils
from .utils.cmdline import *
from .utils.deploy import *
from .base.build import *

# 
cwd = os.getcwd()
gtfs_path = os.path.join(cwd, "..", "gtfs")
osm_path = os.path.join(cwd, "..", "osm")
ned_path = os.path.join(cwd, "..", "ned")


def builder(graph_dir, version):
    clean(graph_dir)
    copy(graph_dir, gtfs_path, osm_path, ned_path)
    build(graph_dir, version)
    ret_val = file_utils.exists(graph_dir, "graph.obj" if otp_utils.OTP_2 else "Graph.obj")
    return ret_val


def runner(graph_dir, version, port, sec_port=None, skip_tests=False):
    if sec_port is None:
        sec_port = int(port) + 1

    ret_val = otp_utils.run_otp_server(graph_dir, otp_version=version, port=port, ssl=sec_port)
    if not skip_tests and otp_utils.wait_for_otp(f"http://localhost:{port}/otp", otp_version=version):
        ret_val = test(port)

    return ret_val


def loader(cl):
    #import pdb; pdb.set_trace()
    #b = builder(cl.otp_graph_dir)
    b = True
    if b:
        r = runner(cl.otp_path, cl.version, cl.port, cl.sec_port, skip_tests=cl.no_tests)
        if r:
            gtfs_v = os.path.join(gtfs_path, "gtfs.v")
            osm_v = os.path.join(osm_path, "osm.v")
            ass = pack_assets(cl.otp_path, cl.version, gtfs_v, osm_v)
            for s in cl.servers:
                scp(cl.otp_path, ass, s)


def rtp():
    cl = cmd_line('rtp', port=52425)
    loader(cl)


def call():
    cl = cmd_line('rtp', port=52425, v=otp_utils.OTP_1)
    loader(cl)


def main():
    # build rtp graph
    cl = cmd_line('rtp', port=52425)
    loader(cl)

    # build call graph
    cl.port = 52225
    cl.otp_instance = 'call'
    cl.version = otp_utils.OTP_1
    loader(cl)
    
    #etc...

