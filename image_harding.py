#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Handle images and screenshots.
This module can take screenshot of windows that are in the background.
"""

STRICT_TYPES = True # If you want to have stict type checking: pip install typeguard

__version__ = 240224_190345
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2024"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

from ctypes import windll
from typing import Optional, Union, Tuple
import win32gui
import win32ui
import PIL # pip install pillow
import pyscreeze # pip install opencv-python
try:
    if not STRICT_TYPES:
        raise ImportError("Skipping the import of typeguard reason: STRICT_TYPES == False")
    from typeguard import typechecked
except:
    STRICT_TYPES = False
    from typing import TypeVar
    _T = TypeVar("_T")

    def typechecked(target: _T, **kwargs) -> _T: # type: ignore
        return target if target else typechecked # type: ignore

@typechecked
def locate(arg_needle_image: Union[PIL.Image.Image, str],
           arg_haystack_image: Union[PIL.Image.Image, str],
           arg_grayscale: bool = True,
           arg_confidence: float = 0.95
           ) -> Optional[Tuple[int, int, int, int]]:
    ''' Try to find image arg_needle_image in arg_haystack_image.
    arg_needle_image: str | PIL.Image.Image     If it's a string, then this is a file path to the image.
    arg_haystack_image: str | PIL.Image.Image   If it's a string, then this is a file path to the image.
    
    Returns a Tuple[left: int, top: int, width: int, height: int] where the image was found. Returns None if the image cannot be found. '''
    if isinstance(arg_needle_image, str):
        arg_needle_image = PIL.Image.open(arg_needle_image)
    if isinstance(arg_haystack_image, str):
        arg_haystack_image = PIL.Image.open(arg_haystack_image)

    try:
        l_located_image = pyscreeze.locate(arg_needle_image, arg_haystack_image, grayscale=arg_grayscale, confidence=arg_confidence)
    except:
        return None
    if not l_located_image:
        return None
    return (int(l_located_image.left), int(l_located_image.top), int(l_located_image.width), int(l_located_image.height))

@typechecked
def screenshot_window(arg_window_title_or_hwnd: Union[str, int],
                      arg_region: Optional[Tuple[int, int, int, int]] = None,
                      arg_nFlags_to_PrintWindow: int = 3
                      ) -> Optional[PIL.Image.Image]:
    ''' Takes a screenshot of a window (can be in the background)
        If you get a blank image, try to set arg_nFlags_to_PrintWindow = 0 (and test 1, 2 also)
        This is the nFlags to PrintWindow, the documentation say that there can only be PW_CLIENTONLY
        but that's false, there is at least #define PW_RENDERFULLCONTENT 0x00000002 also

        arg_window_title_or_hwnd: str | int                                   If str: then this is the window title, if int: then this is a HWND (handle to window))
        arg_region: Tuple[x: int, y: int, width: int, height: int] | None     Cut out the given region from the fullscreen screenshot. If None: return full screenshot

    '''

    if isinstance(arg_window_title_or_hwnd, int):
        hwnd = arg_window_title_or_hwnd
    elif isinstance(arg_window_title_or_hwnd, str):
        hwnd = win32gui.FindWindow(None, arg_window_title_or_hwnd)
    else:
        return None

    if not hwnd:
        return None

    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #left, top, right, bot = win32gui.GetClientRect(hwnd)

    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)
    windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), arg_nFlags_to_PrintWindow) # https://stackoverflow.com/questions/19695214/screenshot-of-inactive-window-printwindow-win32gui#comment115017065_24352388
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    res = PIL.Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    if arg_region:
        arg_region_width_height = (arg_region[0], arg_region[1], arg_region[0] + arg_region[2], arg_region[1] + arg_region[3])
        res = res.crop(arg_region_width_height)

    return res

@typechecked
def locate_in_window(arg_window_title_or_hwnd: Union[str, int],
                     arg_needle_image: Union[PIL.Image.Image, str],
                     arg_region: Optional[Tuple[int, int, int, int]] = None,
                     arg_grayscale: bool = True,
                     arg_confidence: float = 0.95
                     ) -> Optional[Tuple[int, int, int, int]]:
    ''' Try to find image arg_needle_image in a screenshot of a window.
    Returns a Tuple[left: int, top: int, width: int, height: int] where the image was found '''
    l_screenshot: Optional[PIL.Image.Image] = screenshot_window(arg_window_title_or_hwnd=arg_window_title_or_hwnd, arg_region=arg_region)
    l_located = locate(arg_needle_image=arg_needle_image, arg_haystack_image=l_screenshot, arg_grayscale=arg_grayscale, arg_confidence=arg_confidence) if l_screenshot else None
    if l_located and arg_region:
        l_located = (l_located[0] + arg_region[0], l_located[1] + arg_region[1], l_located[2], l_located[3])

    return l_located

