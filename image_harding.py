#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Handle images and screenshots.
This module can take screenshot of windows that are in the background.
"""

STRICT_TYPES = True # If you want to have stict type checking: pip install typeguard

__version__ = 231219_204614
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

from ctypes import windll
from typing import Optional, Union, Tuple
import win32gui
import win32ui
import PIL
import pyscreeze
try:
    if not STRICT_TYPES:
        raise ImportError("Skipping the import of typeguard reason: STRICT_TYPES == False")
    from typeguard import typechecked
except:
    from typing import TypeVar
    _T = TypeVar("_T")

    def typechecked(target: _T, **kwargs) -> _T:
        return target if target else typechecked

@typechecked
def locate(arg_needle_image: Union[PIL.Image.Image, str], arg_haystack_image: Union[PIL.Image.Image, str], arg_grayscale: bool = True, arg_confidence: float = 0.95):
    ''' Try to find image arg_needle_image in arg_haystack_image. Returns a tuple where the image was found '''
    if isinstance(arg_needle_image, str):
        arg_needle_image = PIL.Image.open(arg_needle_image)
    if isinstance(arg_haystack_image, str):
        arg_haystack_image = PIL.Image.open(arg_haystack_image)

    return pyscreeze.locate(arg_needle_image, arg_haystack_image, grayscale=arg_grayscale, confidence=arg_confidence)

@typechecked
def locate_in_window(arg_window_title_or_hwnd: Union[str, int], arg_needle_image: Union[PIL.Image.Image, str], arg_region: Optional[Tuple[float, float, float, float]] = None, arg_grayscale: bool = True, arg_confidence: float = 0.95):
    ''' Try to find image arg_needle_image in a screenshot of a window. Returns a tuple where the image was found '''
    l_screenshot = screenshot_window(arg_window_title_or_hwnd, arg_region)
    return locate(arg_needle_image, l_screenshot, arg_grayscale, arg_confidence)

@typechecked
def screenshot_window(arg_window_title_or_hwnd: Union[str, int], arg_region: Optional[Tuple[float, float, float, float]] = None, arg_nFlags_to_PrintWindow: int = 3) -> Optional[PIL.Image.Image]:
    ''' Takes a screenshot of a window (can be in the background)
        If you get a blank image, try to set arg_nFlags_to_PrintWindow = 0 (and test 1, 2 also)
        This is the nFlags to PrintWindow, the documentation say that there can only be PW_CLIENTONLY
        but that's false, there is at least #define PW_RENDERFULLCONTENT 0x00000002 also
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
        res = res.crop(arg_region)

    return res
