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
	    print("Frame", rf.frame_number, "result: ", rf.results.plates[i].bestPlate.characters)

def print_group_results(self, groups):
    for group_index in range(len(groups)-1):
        group = groups[group_index]
	print("Group (", group.epoch_ms_time_start, " - ", group.epoch_ms_time_end, ") ", group.best_plate_number)

def list_files_in_dir(self, dirPath):
    #if (open(dirPath) != ''):
    if open(dirPath, "r") != '':
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
    print("Initializing")
    #alpr_stream_lib = ctypes.cdll.LoadLibrary('/usr/lib/libalprstream.so')
    STARTING_EPOCH_TIME_MS = 1500294710000
    LICENSEPLATE_COUNTRY = "us"
    VIDEO_BUFFER_SIZE = 15
    USE_MOTION_DETECTION = False
    
    alpr_stream = AlprStream(VIDEO_BUFFER_SIZE, USE_MOTION_DETECTION)
    alpr = Alpr(LICENSEPLATE_COUNTRY, "", "SEpKS0xNTkewsbKztLW2t7i5uru8vb7C2Nje36WgpaetqqOvpaqvqpORl5CdkZ+QAHddFHPee9CiEPnPDHq90vCB7TcEJPm0Gq7MdB/0jGqrJmBzTXii59+J12zZ7GfsRL+a1VqbuOWZM+fkI3PoXzw53kOuwEr0RcEnEfFu8kXh8546xlSRYQSwoKoq84/B")

    print("Initialization complete")

    input_images = list_files_in_dir("/tmp/imagebatchtest")

    for i in range(len(input_images)-1):
	print ("Batching image ", i, ": ", input_images[i])
        img = cv.imread(input_images[i], 1)
        alpr_stream.push_frame(img.data, img.elemSize(), img.cols, img.rows, STARTING_EPOCH_TIME_MS + (i * 100))

        BATCH_SIZE = 10
        if alpr_stream.get_queue_size() >= BATCH_SIZE or i == input_images.size()-1:

            frame_results = alpr_stream.process_batch(alpr)
            print_frame_results(frame_results)

	    print ("After batching there are: ", alpr_stream.peek_active_groups().size(), " active groups")
            group_results = alpr_stream.pop_completed_groups()
            print_group_results(group_results)

    print("Done")