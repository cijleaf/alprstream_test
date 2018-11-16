# -*- coding: utf-8 -*-

import ctypes
import json
import platform
from threading import Lock

mutex = Lock()

# We need to do things slightly differently for Python 2 vs. 3
# ... because the way str/unicode have changed to bytes/str
if platform.python_version_tuple()[0] == '2':
    # Using Python 2
    bytes = str
    _PYTHON_3 = False
else:
    # Assume using Python 3+
    unicode = str
    _PYTHON_3 = True


def _convert_to_charp(string):
    # Prepares function input for use in c-functions as char*
    if type(string) == unicode:
        return string.encode("UTF-8")
    elif type(string) == bytes:
        return string
    else:
        raise TypeError("Expected unicode string values or ascii/bytes values. Got: %r" % type(string))


def _convert_from_charp(charp):
    # Prepares char* output from c-functions into Python strings
    if _PYTHON_3 and type(charp) == bytes:
        return charp.decode("UTF-8")
    else:
        return charp


class AlprStream:
    def __init__(self, frame_queue_size, use_motion_detection = 1):
	"""
        Initializes an AlprStream instance in memory.
        :param frame_queue_size: The size of the video buffer to be filled by incoming video frames
        :param use_motion_detection: Whether or not to enable motion detection on this stream
        """
	frame_queue_size = _convert_to_charp(frame_queue_size)
	use_motion_detection = _convert_to_charp(use_motion_detection)

	# platform.system() calls popen which is not threadsafe on Python 2.x
        mutex.acquire()
	try:
            # Load the .dll for Windows and the .so for Unix-based
            self._alprstreampy_lib = ctypes.cdll.LoadLibrary("libalprstream.so")
        except OSError as e:
            nex = OSError("Unable to locate the ALPRStream library. Please make sure that ALPRStream is properly "
                          "installed on your system and that the libraries are in the appropriate paths.")
            if _PYTHON_3:
                nex.__cause__ = e;
            raise nex
        finally:
            mutex.release()

        self._initialize_func = self._alprstreampy_lib.initialize
        self._initialize_func.restype = ctypes.c_void_p
        self._initialize_func.argtypes = [ctypes.c_uint, ctypes.c_uint]

        self._is_loaded_func = self._alprstreampy_lib.isLoaded
        self._is_loaded_func.restype = ctypes.c_bool
        self._is_loaded_func.argtypes = [ctypes.c_void_p]

        self._dispose_func = self._alprstreampy_lib.dispose
        self._dispose_func.argtypes = [ctypes.c_void_p]

        try:
            import numpy as np
            import numpy.ctypeslib as npct
            self._recognize_raw_image_func = self._alprstreampy_lib.recognizeRawImage
            self._recognize_raw_image_func.restype = ctypes.c_void_p
            array_1_uint8 = npct.ndpointer(dtype=np.uint8, ndim=1, flags='CONTIGUOUS')
            self._recognize_raw_image_func.argtypes = [
                ctypes.c_void_p, array_1_uint8, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        except ImportError:
            self._recognize_raw_image_func = None

        self._get_queue_size_func = self._alprstreampy_lib.getQueueSize
        self._get_queue_size_func.restype = ctypes.c_uint
        self._get_queue_size_func.argtypes = [ctypes.c_void_p]

        self._connect_video_stream_url_func = self._alprstreampy_lib.connectVideoStreamUrl
        self._connect_video_stream_url_func.restype = ctypes.c_void_p
        self._connect_video_stream_url_func.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

        self._get_stream_url_func = self._alprstreampy_lib.getStreamUrl
        self._get_stream_url_func.restype = ctypes.c_char_p
        self._get_stream_url_func.argtypes = [ctypes.c_void_p]

        self._disconnect_video_stream_func = self._alprstreampy_lib.disconnectVideoStream
        self._disconnect_video_stream_func.restype = ctypes.c_void_p
        self._disconnect_video_stream_func.argtypes = [ctypes.c_void_p]

        self._connect_video_file_func = self._alprstreampy_lib.connectVideoFile
        self._connect_video_file_func.restype = ctypes.c_void_p
        self._connect_video_file_func.argtypes = [ctypes.c_char_p, ctypes.c_uint]

        self._disconnect_video_file_func = self._alprstreampy_lib.disconnectVideoFile
        self._disconnect_video_file_func.restype = ctypes.c_void_p
        self._disconnect_video_file_func.argtypes = [ctypes.c_void_p]

        self._video_file_active_func = self._alprstreampy_lib.videoFileActive
        self._video_file_active_func.restype = ctypes.c_bool
        self._video_file_active_func.argtypes = [ctypes.c_void_p]

        self._get_video_file_fps_func = self._alprstreampy_lib.getVideoFileFps
        self._get_video_file_fps_func.restype = ctypes.c_double
        self._get_video_file_fps_func.argtypes = [ctypes.c_void_p]

        self._push_frame_func = self._alprstreampy_lib.pushFrame
        self._push_frame_func.restype = ctypes.c_uint
        self._push_frame_func.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]

        self.alprstream_pointer = self._initialize_func(frame_queue_size, use_motion_detection)
        self.loaded = True


    def unload(self):
        """
        Unloads AlprStream from memory.
        :return: None
        """
        if self.loaded:
            self.loaded = False
            self._alprstreampy_lib.dispose(self.alprstream_pointer)


    def is_loaded(self):
        """
        Checks if AlprStream is loaded.
        :return: A bool representing if AlprStream is loaded or not
        """
        if not self.loaded:
            return False

        return self._is_loaded_func(self.alprstream_pointer)


    def get_queue_size(self):
        """
        Check the size of the video buffer
        :return: The total number of images waiting to be processed on the video buffer
        """
        size = self._get_queue_size_func(self.alprstream_pointer)
        return size


    def connect_video_stream_url(self, url, gstreamer_pipeline_format = ""):
        """
        Spawns a thread that connects to the specified RTSP/MJPEG URL The thread continually fills the processing queue with images from the stream
        :param: url: the full URL to be used to connect to the video stream
        :param: gstreamer_pipeline_format: An optional override for the GStreamer format. Use {url} for a marker to substitude the url value
        """
        url = _convert_to_charp(url)
        gstreamer_pipeline_format = _convert_to_charp(gstreamer_pipeline_format)
        self._connect_video_stream_func(self.alprstream_pointer, url, gstreamer_pipeline_format)


    def get_stream_url(self):
        """
        Get the stream URL.
        :return: the stream URL that is currently being used to stream
        """
        url = self._get_stream_url_func(self.alprstream_pointer)
        url = _convert_to_charp(url)
        return url


    def disconnect_video_stream(self):
        """
        Disconnect the video stream if you no longer wish for it to push frames to the video buffer.
        """
        self._disconnect_video_stream_func(self.alprstream_pointer)


    def connect_video_file(self, video_file_path, video_start_time):
        """
        Spawns a thread that fills the processing queue with frames from a video file The thread will slow down to make sure that it does not overflow the queue The “video_start_time” is used to us with the epoch start time of of the video
        :param video_file_path: The location on disk to the video file.
        :param video_start_time: The start time of the video in epoch ms. This time is used as an offset for identifying the epoch time for each frame in the video
        """
        video_file_path = _convert_to_charp(video_file_path)
        self._connect_video_file_cunc(self.alprstream_pointer, video_file_path, video_start_time)


    def disconnect_video_file(self):
        """
        If you wish to stop the video, calling this function will remove it from the stream
        """
        self._disconnect_video_file_func(self.alprstream_pointer)


    def video_file_active(self):
        """
        Check the status of the video file thread
        :return: True if currently active, false if inactive or complete
        """
        status = self._video_file_active_func(self.alprstream_pointer)
        return status


    def get_video_file_fps(self):
        """
        Get the frames per second for the video file.
        return: Get the frames per second for the video file.
        """
        frames = self._get_video_file_fps_func(self.alprstream_pointer)
        return frames


    def push_frame(self, pixelData, bytesPerPixel, imgWidth, imgHeight, frame_epoch_time = -1):
        """
        Push raw image data onto the video input buffer.
        :param pixelData: raw image bytes for BGR channels
        :param bytesPerPixel: Number of bytes for each pixel (e.g., 3)
        :param imgWidth: Width of the image in pixels
        :param imgHeight: Height of the image in pixels
        :param frame_epoch_time: The time when the image was captured. If not specified current time will be used
        :return: The video input buffer size after adding this image
        """
        pixelData = _convert_to_charp(pixelData)
        videoBufferSize = self._push_frame_func(self.alprstream_pointer, pixelData, bytesPerPixel, imgWidth, imgHeight, frame_epoch_time)
        return videoBufferSize


    def __del__(self):
        if self.is_loaded():
            self.unload()


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_loaded():
            self.unload()