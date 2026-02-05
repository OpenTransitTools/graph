import os
from ott.utils import file_utils
from ott.utils import otp_utils

import logging
log = logging.getLogger(__file__)


from . import gtfs_path, osm_path


def get_assets(path, version):
    log.info(f"package {path}'s (version {version} assets with -new suffix")

    # step 1: create file paths to *-new files locally, and also path where we'll scp these files
    log_v_path = otp_utils.get_vlog_file_path(path)
    log_v_new = file_utils.make_new_path(log_v_path)

    graph_path = otp_utils.get_graph_path(path, otp_version=version)
    graph_new = file_utils.make_new_path(graph_path)

    jar_path = otp_utils.get_otp_path(path)
    jar_new = file_utils.make_new_path(jar_path)

    # step 2: include these other OTP artifacts, like OSM, GTFS and JSON (config) files
    config_paths = otp_utils.get_config_paths(path)

    return [log_v_new, graph_new, jar_new] + config_paths


def scp(server, cl):
    assets = get_assets(cl.graph_dir, cl.version)
    msg = f"scp {cl.graph_dir}/{assets} (-new suffix) to {server}"
    log.info(msg)
    print(server)
    for a in assets:
        print(f"{a} -> {cl.graph_dir}")
        #file_utils.scp(server, a)


def update_otp_v(cl):
    gtfs_v = os.path.join(gtfs_path, "gtfs.v")
    osm_v = os.path.join(osm_path, "osm.v")
    otp_utils.append_vlog_new(cl.graph_dir, osm_v, gtfs_v)


def make_new_files(cl):
    otp_utils.package_new(graph_dir=cl.graph_dir, otp_version=cl.version)
