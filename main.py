"""Given a video, hide messages in frames.
Requires ffmpeg and steghide in PATH.
TODO: Fix building process not recognising frames
TODO: Maintain audio in video"""

import subprocess
import cv2
import sys
import os
import argparse
import shutil


def getFrameCount(vc, spacing):
    """Given a video, prints the total frame count and frames to be processed and returns the total count"""
    total_frame_count = int(vc.get(cv2.CAP_PROP_FRAME_COUNT))
    print("{} frames in video\n{} frames to be signed".format(total_frame_count, total_frame_count // spacing))

    return total_frame_count


def openVideo(filename):
    """Given a video file, returns a video capture"""
    vc = cv2.VideoCapture(filename)
    if not vc.isOpened():
        print("Input video {} not found".format(filename))
        sys.exit()
    return vc


def createPath(path):
    """Given a path, creates a temporary folder"""
    try:
        os.mkdir(path)
    except OSError:
        print("A folder with the name {} already exists".format(path))
        sys.exit()


def deletePath(path):
    """Given a path, deletes it"""
    try:
        shutil.rmtree(path)
    except OSError:
        print("Unable to delete {}".format(path))
        sys.exit()


def encodeFrame(frame, number):
    """Given a frame, encodes the message and writes it into the temporary folder"""
    temp_file = './{}/temp.jpg'.format(args.tempfolder)
    out_file = './{}/frame{:06d}.jpg'.format(args.tempfolder, number)
    cv2.imwrite(temp_file, frame)
    command_encode = 'steghide embed -ef {} -cf {} -p {} -sf {} -f -q'.format(args.message, temp_file, args.password,
                                                                              out_file)
    subprocess.call(command_encode)


def writeFrame(frame, number):
    """Given a frame, writes it into the temporary folder"""
    out_file = './{}/frame{:06d}.jpg'.format(args.tempfolder, number)
    cv2.imwrite(out_file, frame)


def displayProgress(count, total):
    progress = count * 50 // total
    sys.stdout.write("\r[{}>{}] Frame: {}".format('=' * progress, '-' * (50 - progress), count))
    sys.stdout.flush()


def constructVideo(path, framerate, filename):
    command = "ffmpeg -framerate {} -i {}/frame%06d {}".format(framerate, path, filename)
    subprocess.call(command, shell=True)


# Setup parser
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-m', '--message', type=str, default='sig.txt', help='File name with signature')
parser.add_argument('-i', '--input', type=str, default='in.mp4', help='Input file name')
parser.add_argument('-o', '--output', type=str, default='out.mp4', help='Output file name')
parser.add_argument('-s', '--spacing', type=int, default=10, help='Spacing between frames with signature')
parser.add_argument('-p', '--password', type=str, default='pass', help='Password used to encode and decode frames')
parser.add_argument('-tf', '--tempfolder', type=str, default='TEMP', help='Name of temporary file storing images')
args = parser.parse_args()

# Encodes every frame if 0 is input instead of 1
if args.spacing == 0:
    args.spacing = 1

# Open video capture
vc = openVideo(args.input)
framerate = vc.get(cv2.CAP_PROP_FPS)

# Print frame information about frames
total_frame_count = getFrameCount(vc, args.spacing)

# Create temporary folder
createPath(args.tempfolder)

# Loop through all the frames
rval = 1
frame_count = 0
while rval:
    # Display progress
    frame_count += rval
    displayProgress(frame_count, total_frame_count)

    # Read the next frame
    rval, frame = vc.read()

    # Decide whether to encode it or not
    if not frame_count % args.spacing:
        encodeFrame(frame, frame_count)
    else:
        writeFrame(frame, frame_count)

# Display completed progress
print("\r[{}] Frame: {}".format('=' * 51, frame_count - 1))

# Construct video
print("Building {}".format(args.output))
constructVideo(args.tempfolder, framerate, args.output)

# Delete temporary folder
print("Deleting ./{}".format(args.tempfolder))
deletePath(args.tempfolder)

print('Done')
