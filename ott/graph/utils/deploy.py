import os
from ott.utils import otp_utils
from ott.utils import file_utils

import logging
logging.basicConfig()
log = logging.getLogger(__file__)


def start_api(path, version, port, sec_port):

    return True


def is_otp_up(port):
    return True


def test(path):
    return True


def deploy(path):
    return True


def pack_assets(path, version, otp_v="", gtfs_v=""):
    """
    convenience routine will take g/Graph.obj and simply copy it to g/Graph.obj-new
    """
    log.info(f"package {path}'s (version {version} assets with -new suffix")

    # step 1: ...
    otp_utils.append_vlog_new(path, otp_v, gtfs_v)
    otp_utils.package_new(graph_dir=path, otp_version=version)

    # step 2: create file paths to *-new files locally, and also path where we'll scp these files
    log_v_path = otp_utils.get_vlog_file_path(path)
    log_v_new = file_utils.make_new_path(log_v_path)

    graph_path = otp_utils.get_graph_path(path, otp_version=version)
    graph_new = file_utils.make_new_path(graph_path)

    jar_path = otp_utils.get_otp_path(path)
    jar_new = file_utils.make_new_path(jar_path)

    # step 1b: these are the other OTP artifacts, like OSM, GTFS and JSON (config) files
    config_paths = otp_utils.get_config_paths(path)

    return [log_v_new, graph_new, jar_new] + config_paths


def scp(path, assets, server):
    log.info(f"scp {path}/{assets} (-new suffix) to {server}")    
    #file_utils.scp()

