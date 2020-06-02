# SPDX-License-Identifier: MIT
# Copyright (c) 2019-2020 The Pybricks Authors

import os
import argparse
import subprocess
from pathlib import Path
import mpy_cross


BUILD_DIR = "build"
TMP_PY_SCRIPT = "_tmp.py"
TMP_MPY_SCRIPT = "_tmp.mpy"


def make_build_dir():
    # Create build folder if it does not exist
    if not os.path.exists(BUILD_DIR):
        os.mkdir(BUILD_DIR)

    # Raise error if there happens to be a file by this name
    if os.path.isfile(BUILD_DIR):
        raise OSError("A file named build already exists.")


def get_mpy_bytes_from_file(mpy_cross, path):
    """Compile a Python file with mpy-cross and return as bytes."""

    # Show mpy_cross version
    proc = subprocess.Popen([mpy_cross, "--version"])
    proc.wait()

    # Make the build directory
    make_build_dir()

    # Cross-compile Python file to .mpy and raise errors if any
    mpy_path = os.path.join(BUILD_DIR, Path(path).stem + ".mpy")
    proc = subprocess.run(
        [mpy_cross, path, "-mno-unicode", "-o", mpy_path], check=True
    )

    # Read the .mpy file and return as bytes
    with open(mpy_path, "rb") as mpy:
        return mpy.read()


def get_mpy_bytes_from_str(mpy_cross, string):
    """Compile a Python command with mpy-cross and return as bytes."""

    # Make the build directory
    make_build_dir()

    # Path to temporary file
    py_path = os.path.join(BUILD_DIR, TMP_PY_SCRIPT)

    # Write Python command to a file and convert as if it is a regular script.
    with open(py_path, "w") as f:
        f.write(string + "\n")

    # Convert to mpy and get the bytes
    return get_mpy_bytes_from_file(mpy_cross, py_path)


def get_mpy_arg_parser(description):
    parser = argparse.ArgumentParser(description)

    # Arguments for the user script
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", dest="file", nargs="?", const=1, type=str)
    group.add_argument("--string", dest="string", nargs="?", const=1, type=str)

    # Optional mpy cross argument
    parser.add_argument(
        "--mpy_cross", dest="mpy_cross", nargs="?", type=str, required=False
    )
    return parser


def get_mpy_bytes(args):

    # Use given mpy cross if given or else default to version from PyPI
    if args.mpy_cross:
        mpy_cross_path = args.mpy_cross
    else:
        mpy_cross_path = mpy_cross.mpy_cross

    # Convert either the file or the string to mpy format
    if args.file:
        return get_mpy_bytes_from_file(mpy_cross_path, args.file)

    if args.string:
        return get_mpy_bytes_from_str(mpy_cross_path, args.string)


if __name__ == "__main__":

    # Parse all arguments
    parser = get_mpy_arg_parser(
        description="Convert MicroPython scripts or commands to .mpy bytes."
    )
    args = parser.parse_args()

    # Use arguments to produce mpy bytes
    data = get_mpy_bytes(args)

    # Print as string as a sanity check.
    print("\nBytes:")
    print(data)

    # Print the bytes as a C byte array for development of new MicroPython
    # ports without usable I/O, REPL or otherwise.
    WIDTH = 8
    print(
        "\n// MPY file. Version: {0}. Size: {1}".format(data[1], len(data))
        + "\nconst uint8_t script[] = "
    )
    for i in range(0, len(data), WIDTH):
        chunk = data[i:i + WIDTH]
        hex_repr = ["0x{0}".format(hex(i)[2:].zfill(2).upper()) for i in chunk]
        print("    " + ", ".join(hex_repr) + ",")
    print("};")
