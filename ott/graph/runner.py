"""
This code does the following:
  4. start the graph (webapp api)
"""
import os
from ott.utils import otp_utils


def kill_otp_server(cl):
    otp_utils.kill_otp_server(cl.graph_dir)


def start_otp_server(cl):
    """ starts the OTP server """
    sec_port = cl.sec_port if cl.sec_port else int(cl.port) + 1
    ret_val = otp_utils.run_otp_server(cl.graph_dir, otp_version=cl.version, port=cl.port, ssl=sec_port)
    if ret_val:
        ret_val = otp_utils.wait_for_otp(f"http://localhost:{cl.port}/otp", otp_version=cl.version)

    return ret_val


def start_new_otp(cl):
    kill_otp_server(cl)
    otp_utils.mv_new_files_into_place(cl.graph_dir, "OLD")
    otp_utils.rm_new(cl.graph_dir)
    start_otp_server(cl)
