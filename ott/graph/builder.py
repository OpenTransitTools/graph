"""
This code does the following:
  1. cleans out old data junk from the graph dir
  2. copy new GTFS and OSM data to the given OTP directory  
  3. build the graph
"""
import os
import re
from pathlib import Path

from ott.utils import file_utils
from ott.utils import otp_utils

import logging
log = logging.getLogger(__file__)

from . import gtfs_path, osm_path, ned_path


def clean(graph_dir, gtfs_ext=".gtfs.zip", osm_ext=".osm.pdb"):
    """
    remove GTFS, OSM and graph .obj files
    """
    file_utils.rm_files(graph_dir, ext=gtfs_ext)
    file_utils.rm_files(graph_dir, ext=osm_ext)
    file_utils.rm_files(graph_dir, ext="-new")

    g = file_utils.find_files_in_subdirs(graph_dir, ext=gtfs_ext)
    o = file_utils.find_files_in_subdirs(graph_dir, ext=osm_ext)
    if len(g) > 0 or len(o) > 0:
        log.warning(f"Seeing either OSM {o} and/or GTFS {g} files, when I wanted them all gone.")


def get_feeds(graph_dir, feed_files=["build-config.json", "feeds.json"]):
    ret_val = []

    for f in feed_files:
        config_file = os.path.join(graph_dir, f)
        if Path(config_file).is_file():
            # matches all "source": " directives, striping out the '.gtfs.zip' names
            pattern = r'"source":\s*"([^"]+\.gtfs\.zip)"'

            # re.findall returns a list of strings matching the text inside the ([...]) group
            with open(config_file, 'r', encoding='utf-8') as file:
                content = file.read()
                file_names = re.findall(pattern, content)
                if file_names:
                    ret_val = ret_val + file_names

    return ret_val


def copy(graph_dir, gtfs_path="gtfs", osm_path="osm", ned_path="ned", gtfs_ext=".gtfs.zip", osm_ext=".osm.pbf"):
    """
    copy GTFS and OSM data
    """
    # step 1: OSM
    file_utils.cp_files(osm_path, graph_dir, ext=osm_ext)

    # step 2: GTFS files (based on OTP build .json)
    files = get_feeds(graph_dir)
    if files and len(files) > 0:
        for f in files:
            file_utils.cp_files(gtfs_path, graph_dir, ext=f)
    else:
       file_utils.cp_files(gtfs_path, graph_dir, ext=gtfs_ext)

    # step 3: NED elevation files
    ned_dir=os.path.join(graph_dir, "ned")
    file_utils.mkdir(ned_dir)
    file_utils.cp_files(ned_path, ned_dir, ext=".tiff")
    file_utils.cp_files(ned_path, ned_dir, ext=".gtx")


def build(graph_dir, version, gtfs_ext=".gtfs.zip", osm_ext=".osm.pbf"):
    """
    build the graph
    """
    # step 1: remove the graph .obj file(s)
    otp_utils.rm_new(graph_dir)
    file_utils.rm_files(graph_dir, ext=".obj")
    o = file_utils.find_files_in_subdirs(graph_dir, ext=".obj")
    if len(o) > 0:
        log.warning(f"Couldn't remove old (graph) .obj files ({o})")

    # step 2: make sure we have data
    g = file_utils.find_files_in_subdirs(graph_dir, ext=gtfs_ext)
    o = file_utils.find_files_in_subdirs(graph_dir, ext=osm_ext)
    if len(g) < 1 or len(o) < 1:
        log.warning(f"Not seeing either OSM {o} and/or GTFS {g} files")

    # step 3: build
    otp_utils.run_graph_builder(graph_dir, version)

    ret_val = otp_utils.check_graph_size(graph_dir, version)
    return ret_val


def check_feeds(graph_dir):
    """
    check all the GTFS feeds to see if they look like GTFS data
    so, DON'T BUILD a graph if any feed:
     1) is not a zip file
     2) doesn't have a valid trips.txt file

    TODO fix gtfs_etl to also test feeds, and stop the deployment of data if feed looks bogus
    """
    ret_val = True
    feeds = file_utils.find_files_in_subdirs(graph_dir, ext=".gtfs.zip")
    for f in feeds:
        # TODO: assert that the feed looks valid
        if f:
            #ret_val = False
            log.error("Feed {f} is broken...") #todo format flag
            break
    return ret_val


def build_new_graph(cl):
    # import pdb; pdb.set_trace()
    ret_val = False
    clean(cl.graph_dir)
    copy(cl.graph_dir, gtfs_path, osm_path, ned_path)
    if check_feeds(cl.graph_dir):
        build(cl.graph_dir, cl.version)
        ret_val = file_utils.exists(cl.graph_dir, "graph.obj" if cl.version == otp_utils.OTP_2 else "Graph.obj")
    return ret_val
