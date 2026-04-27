from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
import urllib.request
from urllib.error import HTTPError
from PIL import Image
from matplotlib.patches import FancyBboxPatch


def add_bg_leg(ax, box_x = 0.86, box_y = 0.07, box_width = 0.11, box_height = 0.08):

    icon_bg = FancyBboxPatch(
        (box_x, box_y),
        box_width,
        box_height,
        transform=ax.transAxes,   # IMPORTANT: same coordinate system
        boxstyle="square,pad=0.02",
        facecolor="#1a1a2e",         # matches your legend theme
        edgecolor="white",
        linewidth=1.5,
        alpha=0.65,
        zorder=2                     # behind icons/text
    )

    ax.add_patch(icon_bg)


def get_eve_icon(base_url, id):
    try:
        with urllib.request.urlopen(base_url.replace("EVE_ID", str(id))) as response:
            ship_img = np.array(Image.open(response))
    except HTTPError as e:
        print(f'http eve img error id is {id}')
        return None

    return ship_img


def add_icon_legend(ax, icon_dict, start_x=0.01, start_y=0.05, y_spacing=0.04):
    """
    icon_dict = {
        "Reload": reload_img,
        "Cap Booster": cap_img,
        "Drone Event": drone_img
    }
    """
    y = start_y

    for label, img in icon_dict.items():
        imagebox = OffsetImage(img, zoom=0.2)  # adjust size here
        ab = AnnotationBbox(
            imagebox,
            (start_x, y),
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(0, 0.5)
        )
        ax.add_artist(ab)

        ax.text(
            start_x + 0.02,
            y,
            label,
            transform=ax.transAxes,
            color="white",
            fontsize=8,
            va="center"
        )

        y += y_spacing
