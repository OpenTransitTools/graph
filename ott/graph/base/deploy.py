from ott.utils import web_utils
from ott.utils import file_utils
from ott.utils import otp_utils
from ott.utils import object_utils

from ott.utils.parse.cmdline import otp_cmdline

from .otp_builder import OtpBuilder

import os
import datetime
import logging
log = logging.getLogger(__file__)


class OtpExporter(OtpBuilder):
    """ deploy OTP graphs source from the 'build' server (SVR)
    """
    def __init__(self):
        super(OtpExporter, self).__init__(dont_update=True)
        self.graphs = otp_utils.get_graphs(self)

    def export_graphs(self, server_filter=None, graph_filter=None):
        """ copy new graphs from build server to configured set of production servers
            (basically scp Graph.obj-new, otp.v-new and otp.jar-new over to another server)
        """
        ret_val = True

        if self.graphs is None or len(self.graphs) < 1:
            log.info("no [otp] graphs configured in the .ini file")
            return ret_val

        # step A: grab config .ini (from app.ini) variables for the server(s) to scp OTP graphs to
        #         note, we need these server(s) to be 'known_hosts'
        user = self.config.get_json('user', section='deploy')
        servers = self.config.get_json('servers', section='deploy')
        otp_base_dir = self.config.get_json('otp_base_dir', section='deploy')

        def scp_graph(server, graph):
            """ sub-routine to scp Graph.obj-new, otp.v-new and (optionally) otp.jar-new over to
                a given server.  crazy part of this code is all the path (string) manipulation
                in step 1 below...
            """
            global ret_val

            graph_dir = otp_utils.config_graph_dir(graph, self.this_module_dir)
            server_dir = file_utils.append_to_path(otp_base_dir, graph.get('name'))

            # step 1: create file paths to *-new files locally, and also path where we'll scp these files
            log_v_path = otp_utils.get_vlog_file_path(graph_dir)
            log_v_new = file_utils.make_new_path(log_v_path)
            log_v_svr = file_utils.append_to_path(server_dir, os.path.basename(log_v_new), False)

            graph_path = otp_utils.get_graph_path(graph_dir, otp_version=graph.get('version'))
            graph_new = file_utils.make_new_path(graph_path)
            graph_svr = file_utils.append_to_path(server_dir, os.path.basename(graph_new), False)

            jar_path = otp_utils.get_otp_path(graph_dir)
            jar_new = file_utils.make_new_path(jar_path)
            jar_svr = file_utils.append_to_path(server_dir, os.path.basename(jar_new), False)

            # step 1b: these are the other OTP artifacts, like OSM, GTFS and JSON (config) files
            osm_paths = otp_utils.get_osm_paths(graph_dir)
            gtfs_paths = otp_utils.get_gtfs_paths(graph_dir)
            config_paths = otp_utils.get_config_paths(graph_dir)

            # step 2: we are going to attempt to scp Graph.obj-new over to the server(s)
            #         note: the server paths (e.g., graph_svr, etc...) are relative to the user's home account
            if file_utils.is_min_sized(graph_new):
                scp = None
                try:
                    log.info("scp {} over to {}@{}:{}".format(graph_new, user, server, graph_svr))
                    scp, ssh = web_utils.scp_client(host=server, user=user)
                    scp.put(graph_new, graph_svr)
                    scp.put(log_v_new, log_v_svr)
                    if file_utils.is_min_sized(jar_new):
                        scp.put(jar_new, jar_svr)
                    for p in osm_paths:
                        scp.put(p, server_dir)
                    for p in gtfs_paths:
                        scp.put(p, server_dir)
                    for p in config_paths:
                        scp.put(p, server_dir)
                except Exception as e:
                    log.warning(e)
                    ret_val = False
                finally:
                    if scp:
                        scp.close()

        # step B: loop thru each server, and scp a graph (and log and jar) to that server
        # import pdb; pdb.set_trace()
        for s in servers:
            if object_utils.is_not_match(server_filter, s):
                continue
            for g in self.graphs:
                if object_utils.is_not_match(graph_filter, g.get('name')):
                    continue
                scp_graph(server=s, graph=g)

        # step C: remove the -new files (so we don't keep deploying / scp-ing)
        for g in self.graphs:
            if object_utils.is_not_match(graph_filter, g.get('name')):
                continue
            otp_utils.rm_new(graph_dir=g.get('dir'), otp_version=g.get('version'))

        return ret_val

    @classmethod
    def export(cls):
        parser = cls.get_args()
        otp_cmdline.server_option(parser)
        args = parser.parse_args()

        log.info("\nRunning otp_exporter.py at {0}\n".format(datetime.datetime.now()))
        d = OtpExporter()
        d.export_graphs(server_filter=args.server, graph_filter=args.name)

    @classmethod
    def package_new(cls):
        """ convenience routine will take Graph.obj and simply copy it to Graph.obj-new
            intended to run manually if we need to export a graph by hand
        """
        args = cls.get_args('bin/otp_package_new', True)
        graph_filter = args.name

        log.info("\nPackage new\n".format())
        d = OtpExporter()
        for g in d.graphs:
            # step 0: do we filter this graph?
            if object_utils.is_not_match(graph_filter, g['name']):
                continue

            dir = g.get('dir', './')
            version = g.get('version', otp_utils.OTP_VERSION)

            # step 1: is otp.v doesn't exist or is a bit old, create it
            vlog_path = otp_utils.get_vlog_file_path(graph_dir=dir)
            if file_utils.exists(vlog_path) is False or file_utils.file_age(vlog_path) > 1:
                d.update_vlog(g)

            # step 2: package it...
            otp_utils.package_new(graph_dir=dir, otp_version=version)

    @classmethod
    def otp_v_new(cls):
        """ update otp.v """
        args = cls.get_args('bin/otp_v_new', True)
        graph_filter = args.name

        log.info("\nCreate new otp.v\n".format())
        d = OtpExporter()
        for g in d.graphs:
            if object_utils.is_not_match(graph_filter, g.get('name')):
                continue
            d.update_vlog(g)

    @classmethod
    def get_args(cls, prog_name='bin/otp-exporter', make_args=False):
        """
        make the cli argparse for OTP graph exporting
        """
        parser = otp_cmdline.base_parser(prog_name)
        ret_val = parser
        if make_args:
            ret_val = parser.parse_args()
        return ret_val


def main():
    # import pdb; pdb.set_trace()
    OtpExporter.export()


if __name__ == '__main__':
    main()






class OtpBuilder(CacheBase):
    """
    build an OTP graph
    """
    name = None
    graph_size = 30000000

    def __init__(self, name, base='otp', force_update=False, dont_update=False):
        super(OtpBuilder, self).__init__('otp')
        self.name = name


    def config_graph_dirs(self, name, force_update=False, dont_update=False):
        """
        read the config for graph specs like graph dir and web port (for running OTP)
        this routine will gather config .json files, .osm files and gtfs .zips into the graph folder
        graphs = otp_utils.get_graphs(self)

            dir = otp_utils.config_graph_dir(g, self.this_module_dir)
            ver = g.get('version')
            if ver is None:
                ver = otp_utils.get_otp_version_simple(dir)
            name = otp_utils.get_graph_name(ver)
            g['version'] = ver
            g['graph_name'] = name
            g['dir'] = dir
            g['path'] = os.path.join(dir, name)
            g['failed'] = name + "-failed-tests"


        if graphs:
            for g in graphs:
                if name and len(name) > 1 and name != g.get('name'): continue
                set_graph_details(g)                
                filter = g.get('filter')
                dir = g.get('dir')
                if force_update or not dont_update:
                    # import pdb; pdb.set_trace()
                    OsmCache.check_osm_file_against_cache(dir, force_update, otp_utils.build_with_pbf(g.get('version')))
                    GtfsCache.check_feeds_against_cache(self.feeds, dir, force_update, filter)
        """
        graphs = None
        return graphs

    def update_vlog(self, graph):
        """
        out gtfs feed(s) version numbers and dates to the otp.v log file
        gtfs_msg = GtfsInfo.get_cache_msgs(graph.get('dir'), self.feeds, graph.get('filter'))
        osm_msg = OsmInfo.get_cache_msgs(graph.get('dir'))
        otp_utils.append_vlog_file(graph.get('dir'), gtfs_msg + osm_msg)
        """


    def build_graph(self, graph, java_mem=None, force_update=False):
        """
        build the graph...as long as the Graph.obj file looks out of date
        """
        success = True

        # step 1: set some params
        rebuild_graph = force_update

        # step 2: check graph file is fairly recent and properly sized
        if not file_utils.exists_and_sized(graph.get('path'), self.graph_size):
            rebuild_graph = True

        # step 3: check the cache files
        if file_utils.dir_has_newer_files(graph.get('path'), graph.get('dir'), offset_minutes=60, include_filter=".jar,.json,.osm,.pbf,.zip"):
            rebuild_graph = True

        # step 4: build graph is needed
        if rebuild_graph:
            success = False

            # step 4b: run the builder multiple times until we get a good looking Graph.obj
            for n in range(1, 5):
                # import pdb; pdb.set_trace()
                log.info(" build attempt {0} of a new graph ".format(n))
                file_utils.rm(graph.get('path'))
                otp_utils.run_graph_builder(graph.get('dir'), graph.get('version'), java_mem=java_mem)
                time.sleep(10)
                if file_utils.exists_and_sized(graph.get('path'), self.graph_size, self.expire_days):
                    success = True
                    break
                else:
                    log.warn("\n\nGRAPH DIDN'T BUILD ... WILL TRY TO BUILD AGAIN\n\n")
                    time.sleep(15)

        return success, rebuild_graph

    def test_graph(self, graph, suite_dir=None, java_mem=None, start_server=True):
        """
        will test a given graph against a suite of tests
        """
        success = True
        delay = 1
        if start_server:
            success = otp_utils.run_otp_server(graph.get('dir'), graph.get('version'), java_mem=java_mem, **graph)
            delay = 60
        if success:
            success = TestRunner.test_graph_factory_config(graph, suite_dir=suite_dir, delay=delay)
            if not success:
                log.warn("graph {} *did not* pass some tests!!!".format(graph.get('name')))
        else:
            log.warn("was unable to start the OTP server using graph {}!!!".format(graph.get('name')))
        return success

    def build_and_test_graphs(self, java_mem=None, force_update=False, start_server=True, graph_filter=None):
        """
        will build and test each of the graphs we have in self.graphs
        """
        ret_val = True
        if self.graphs:
            # step 1: loop thru all graph configs ... building and testing new graphs
            for g in self.graphs:
                #import pdb; pdb.set_trace()
                # step 1b: if we're filtering graphs by name, only run that specific graph
                if graph_filter and g.get('name') != graph_filter: continue
                elif graph_filter is None and g.get('skip'): continue

                # step 2: build this graph
                success, rebuilt = self.build_graph(g, java_mem, force_update)

                # step 3: test the successfully built new graph (restarting a new OTP server for the graph)
                if success and rebuilt and not g.get('skip_tests'):
                    success = self.test_graph(graph=g, java_mem=java_mem, start_server=start_server)
                    ret_val = success

                # step 3b: failed to build the graph ... send a warning
                elif not success:
                    ret_val = False
                    log.warn("graph build failed for graph {}".format(g.get('name')))

                # step 4: so we rebuilt the graph and any testing that was done was also a success...
                if rebuilt:
                    dir = g.get('dir', './')
                    version = g.get('version', otp_utils.OTP_VERSION)

                    # step 4b: update the vlog and package the graph as new
                    if success:
                        self.update_vlog(graph=g)
                        otp_utils.package_new(graph_dir=dir, otp_version=version)

                    # step 4c: shut down any graph that
                    if g.get('post_shutdown'):
                        otp_utils.kill_otp_server(dir)
        return ret_val

    def only_test_graphs(self, java_mem=None, break_on_fail=False, start_server=True, graph_filter=None):
        """
        will test each of the graphs we have in self.graphs
        """
        ret_val = True
        if self.graphs:
            for g in self.graphs:
                if graph_filter and g.get('name') != graph_filter: continue
                success = self.test_graph(graph=g, java_mem=java_mem, start_server=start_server)
                if not success:
                    ret_val = False
                    if break_on_fail:
                        break
        return ret_val

    @classmethod
    def build(cls):
        """ effectively the main routine for building new graphs from the command line """
        success = False

        # step 1: config the builder system
        args, parser = OtpBuilder.get_args()
        b = OtpBuilder(args.name, force_update=args.force, dont_update=args.dont_update)
        java_mem = "-Xmx1236m" if args.mem else None

        if args.mock:
            # step 2: just going to much with the vlogs, etc... as a mock build & test
            graph = otp_utils.find_graph(b.graphs, args.name)
            b.update_vlog(graph)
            success = True
        else:
            # step 3: we're going to try and build 1 or all graphs in the config

            # step 3a: are we being asked to filter only one graph to build and/or test ?
            graph_filter = None
            if args.name != "all":
                graph = otp_utils.find_graph(b.graphs, args.name)
                if graph:
                    graph_filter = args.name
                else:
                    graph_filter = "unknown graph"
                    log.warn("I don't know how to build graph '{}'".format(args.name))

            # step 3b: build and/or test one or all graphs in the config file (won't do anything with an "unknown" graph name
            if args.test:
                success = b.only_test_graphs(java_mem=java_mem, start_server=not args.dont_restart, graph_filter=graph_filter)
            else:
                success = b.build_and_test_graphs(java_mem=java_mem, force_update=args.force, start_server=not args.dont_restart, graph_filter=graph_filter)

        if args.email and (not success or args.force):
            otp_utils.send_build_test_email(args.email)

        return success

    @classmethod
    def get_args(cls):
        """
        make the cli argparse for OTP graph building and testing
        """
        parser = otp_utils.get_initial_arg_parser('otp-builder')
        parser.add_argument('--test',        '-t', action='store_true', help="to just run tests vs. building the graph")
        parser.add_argument('--no_tests',    '-n', action='store_true', help="build graph w/out testing")
        parser.add_argument('--dont_update', '-d', action='store_true', help="don't update data regardless of state")
        parser.add_argument('--dont_restart',      action='store_true', help="don't restart OTP when testing new graphs, etc...")
        parser.add_argument('--mock',        '-m', action='store_true', help="mock up the otp.v to make it look like the graph built and tested")
        parser.add_argument('--mem',        '-lm', action='store_true', help="should we run otp/java with smaller memory footprint?")
        parser.add_argument('--email',       '-e', help="email address(es) to be contacted if we can't build a graph, or the tests don't pass.")

        args = parser.parse_args()
        return args, parser
