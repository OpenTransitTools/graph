"""
This code does the following:
  4. start the graph (webapp api)
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
