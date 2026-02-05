"""
This code does the following:
  1. cleans out old data junk from the graph dir
  2. copy new GTFS and OSM data to the given OTP directory  
  3. build the graph
"""
import os
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


def copy(graph_dir, gtfs_path="gtfs", osm_path="osm", ned_path="ned", gtfs_ext=".gtfs.zip", osm_ext=".osm.pbf"):
    """
    copy GTFS and OSM data
    """
    file_utils.cp_files(gtfs_path, graph_dir, ext=gtfs_ext)
    file_utils.cp_files(osm_path, graph_dir, ext=osm_ext)
    file_utils.cp_files(ned_path, os.path.join(graph_dir, "ned"), ext="*.*")


def build(graph_dir, version, gtfs_ext=".gtfs.zip", osm_ext=".osm.pbf"):
    """
    build the graph
    """
    # step 1: remove the graph .obj file(s)
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


def build_new_graph(cl):
    # import pdb; pdb.set_trace()
    clean(cl.graph_dir)
    copy(cl.graph_dir, gtfs_path, osm_path, ned_path)
    build(cl.graph_dir, cl.version)
    ret_val = file_utils.exists(cl.graph_dir, "graph.obj" if cl.version == otp_utils.OTP_2 else "Graph.obj")
    return ret_val
