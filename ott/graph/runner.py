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


def start_server(graph_dir, version, port, sec_port=None):
    """ starts the OTP server """
    if sec_port is None:
        sec_port = int(port) + 1

    ret_val = otp_utils.run_otp_server(graph_dir, otp_version=version, port=port, ssl=sec_port)
    if ret_val:
        ret_val = otp_utils.wait_for_otp(f"http://localhost:{port}/otp", otp_version=version)

    return ret_val


def start_otp_server(cl):
    start_server(cl.x)
