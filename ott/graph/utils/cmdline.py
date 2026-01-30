import os
from ott.utils import otp_utils


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
