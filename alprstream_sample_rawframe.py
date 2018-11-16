# -*- coding: utf-8 -*-
import os
import re
import sys
import ctypes

from openalpr import Alpr
from openalpr import AlprStream
#from alprstream import AlprStream


def print_frame_results(self, rframes):
    for frame_index in range(len(rframes)-1):
        rf = rframes[frame_index]
	for i in range(len(rf.results.plates)-1):
	    print("Frame ", rf.frame_number, " result: ", rf.results.plates[i].bestPlate.characters)



def print_group_results(self, groups):
    for group_index in range(len(groups)-1):
        group = groups[group_index]

	print("Group (", group.epoch_ms_time_start, " - ", group.epoch_ms_time_end, ") ", group.best_plate_number)


def list_files_in_dir(self, dirPath):
    if opendir (dirPath) != NULL:
        ''' print all the files and directories within directory '''
        while readdir (dir) != NULL:
            if strcmp(ent.d_name, ".") != 0 and strcmp(ent.d_name, "..") != 0:
                #stringstream fullpath
                fullpath << dirPath << "/" << ent.d_name
                files.push_back(fullpath.str())
        closedir (dir)
    else:
        ''' could not open directory '''
        perror ("")
        return files

    return files


if __name__ == '__main__':

    print ("Initializing")
    STARTING_EPOCH_TIME_MS = 1500294710000
    LICENSEPLATE_COUNTRY = "us"
    LICENSE_KEY = ""

    # Size of image buffer to maintain in stream queue -- This only matters if you are feeding
    # images/video into the buffer faster than can be processed (i.e., a background thread)
    # Setting self to the batch size since we're feeding in images synchronously, it's only needed to
    # hold a single batch

    # Batch size and GPU ID set in openalpr.conf
    # Video buffer frames controls the number of frames to buffer in memory.  Must be >= gpu batch size
    VIDEO_BUFFER_SIZE = 15

    # The stream will assume sequential frames.  If there is no motion from frame to frame, then
    # processing can be skipped for some frames
    USE_MOTION_DETECTION = False

    alpr_stream = AlprStream(VIDEO_BUFFER_SIZE, USE_MOTION_DETECTION)
    alpr = Alpr(LICENSEPLATE_COUNTRY, "", "", LICENSE_KEY)

    if not alpr.isLoaded():
	print ("Error loading OpenALPR library.")
        exit(1)


    print("Initialization complete")

    # It's important that the image dimensions are consistent within a batch and that you
    # only drive OpenALPR with few various image sizes.  The memory for each image size is
    # cached on the GPU for efficiency, using many different image sizes will degrade performance
    input_images = list_files_in_dir("/tmp/imagebatchtest")

    for i in range(len(input_images)-1):
	print("Batching image ", i, ": ", input_images[i])

        img = cv.imread(input_images[i], 1)

        # Push the raw BGR pixel data
        # Use the arbitrary starting epoch time + 100ms for each image
        alpr_stream.push_frame(img.data, img.elemSize(), img.cols, img.rows, STARTING_EPOCH_TIME_MS + (i * 100))

        BATCH_SIZE = 10
        if alpr_stream.get_queue_size() >= BATCH_SIZE or i == input_images.size()-1:
            # Process a batch once the stream is full or it's the last image

            frame_results = alpr_stream.process_batch(alpr)
            print_frame_results(frame_results)

            # After each batch processing, can check to see if any groups are ready
            # "Groups" form based on their timestamp and plate numbers on each stream
            # The stream object has configurable options for how long to wait before
            # completing a plate group.  You may peek at the active list without popping.
	    print("After batching there are: ", alpr_stream.peek_active_groups().size(), " active groups")

            group_results = alpr_stream.pop_completed_groups()
            print_group_results(group_results)

    print("Done")