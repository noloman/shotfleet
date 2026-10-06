#!/usr/bin/env python3
"""Run one read, then list the Apple frameworks this process has loaded (dyld image list): is CoreML/Espresso/ANE/Vision in there?"""
import ctypes, sys, cpu_ocr
cpu_ocr.read(sys.argv[1], "en")
d = ctypes.CDLL(None); d._dyld_get_image_name.restype = ctypes.c_char_p
names = [d._dyld_get_image_name(i).decode() for i in range(d._dyld_image_count())]
for n in names:
    if any(k in n for k in ("CoreML", "Espresso", "AppleNeuralEngine", "ANE", "Vision", "MLCompute", "Metal", "Accelerate", "libonnxruntime")): print(n)
print(len(names), "images in all")
