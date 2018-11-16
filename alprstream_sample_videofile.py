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


if __name__ == '__main__':

    print("Initializing")
    STARTING_EPOCH_TIME_MS = 1500294710000
    LICENSEPLATE_COUNTRY = "us"
    LICENSE_KEY = "123"
    VIDEO_FILE = "/tmp/video.mp4"


    # Size of image buffer to maintain in stream queue -- This only matters if you are feeding
    # images/video into the buffer faster than can be processed (i.e., a background thread)
    # Setting self to the batch size since we're feeding in images synchronously, it's only needed to
    # hold a single batch

    # Batch size and GPU ID set in openalpr.conf
    # Video buffer frames controls the number of frames to buffer in memory.  Must be >= gpu batch size
    VIDEO_BUFFER_SIZE = 15

    # The stream will assume sequential frames.  If there is no motion from frame to frame, then
    # processing can be skipped for some frames
    USE_MOTION_DETECTION = True

    alpr_stream = AlprStream(VIDEO_BUFFER_SIZE, USE_MOTION_DETECTION)
    alpr = Alpr(LICENSEPLATE_COUNTRY, "", "", LICENSE_KEY)

    if not alpr.isLoaded():
	print("Error loading OpenALPR library.")
        exit(1)

    print("Initialization complete")

    # It's important that the image dimensions are consistent within a batch and that you
    # only drive OpenALPR with few various image sizes.  The memory for each image size is
    # cached on the GPU for efficiency, using many different image sizes will degrade performance


    alpr_stream.connect_video_file(VIDEO_FILE, STARTING_EPOCH_TIME_MS)

    while (alpr_stream.video_file_active() or alpr_stream.get_queue_size() > 0):

	print("Queue size: ", alpr_stream.get_queue_size())

        # If processing on the CPU there is no benefit to a batch size > 1.
        BATCH_SIZE = 10

        # Process a batch as fast as we can, batches won't necessarily be full

        frame_results = alpr_stream.process_batch(alpr)
        print_frame_results(frame_results)

        # After each batch processing, can check to see if any groups are ready
        # "Groups" form based on their timestamp and plate numbers on each stream
        # The stream object has configurable options for how long to wait before
        # completing a plate group.  You may peek at the active list without popping.
	print("After batching there are: ", alpr_stream.peek_active_groups().size(), " active groups")

        group_results = alpr_stream.pop_completed_groups()
        print_group_results(group_results)


        # Sleep a little bit so we don't spin the CPU looping
        usleep(1000)

    print("Done")