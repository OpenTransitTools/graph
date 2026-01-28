import os

from ott.utils import otp_utils
from ott.utils import file_utils

import logging
log = logging.getLogger(__file__)


"""
remove GTFS, OSM and graph .obj files
"""
def clean(graph_path, gtfs_ext=".gtfs.zip", osm_ext=".osm.pdb"):
    file_utils.rm_files(graph_path, ext=gtfs_ext)
    file_utils.rm_files(graph_path, ext=osm_ext)

    g = file_utils.find_files_in_subdirs(graph_path, ext=gtfs_ext)
    o = file_utils.find_files_in_subdirs(graph_path, ext=osm_ext)
    if len(g) > 0 or len(o) > 0:
        log.warning(f"Seeing either OSM {o} and/or GTFS {g} files, when I wanted them all gone.")        

    file_utils.rm_files(graph_path, ext=".obj")
    o = file_utils.find_files_in_subdirs(graph_path, ext=".obj")
    if len(o) > 0:
        log.warning(f"Couldn't remove old (graph) .obj files ({o})")


"""
copy GTFS and OSM data
"""
def copy(graph_path, gtfs_path="gtfs", osm_path="osm", ned_path="ned", gtfs_ext=".gtfs.zip", osm_ext=".osm.pbf"):
    file_utils.cp_files(os.path.join("..", gtfs_path), graph_path, ext=gtfs_ext)
    file_utils.cp_files(os.path.join("..", osm_path), graph_path, ext=osm_ext)
    file_utils.cp_files(os.path.join("..", ned_path), os.path.join(graph_path, ned_path), ext="*.*")


"""
"""
def build(graph_path, version="v2", gtfs_ext=".gtfs.zip", osm_ext=".osm.pbf"):
    # step 1: remove the graph .obj file(s)
    file_utils.rm_files(graph_path, ext=".obj")
    o = file_utils.find_files_in_subdirs(graph_path, ext=".obj")
    if len(o) > 0:
        log.warning(f"Couldn't remove old (graph) .obj files ({o})")

    # step 2: make sure we have data
    g = file_utils.find_files_in_subdirs(graph_path, ext=gtfs_ext)
    o = file_utils.find_files_in_subdirs(graph_path, ext=osm_ext)
    if len(g) < 1 or len(o) < 1:
        log.warning(f"Not seeing either OSM {o} and/or GTFS {g} files")

    # step 3: build    
    otp_utils.run_graph_builder(graph_path, version)
    #os.system("java")




"""
1. 
2. copy new GTFS and OSM
3. build
4. test
5. create otp.v
6. create -new
"""


