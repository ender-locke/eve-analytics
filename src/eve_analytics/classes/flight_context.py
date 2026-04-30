from json import loads
from pathlib import Path
import urllib.request
from PIL import Image
import numpy as np


class FlightContext:
    ctx_loc = Path(__file__).resolve().parent / "../config/config.json"

    def __init__(self):
        self._load_ctx()
        self._cache_imgs()

    def __repr__(self) -> str:
        """
        Returns a string representation of the FlightContext instance.

        Returns:
            str: A formatted string indicating the ctx.
        """
        return f"<FlightDiagram>"

    def _cache_imgs(self):
        with urllib.request.urlopen(self.icons["reload"]) as response:
            self.reload_img = np.array(Image.open(response))

        with urllib.request.urlopen(self.icons["drone"]) as response:
            self.drone_img = np.array(Image.open(response))

        with urllib.request.urlopen(self.icons["ecm"]) as response:
            self.jam_img = np.array(Image.open(response))


    @property
    def damage(self) -> dict:
        return self._damage

    @property
    def hp_scatter(self) -> dict:
        return self._hp_scatter

    @property
    def gj_scatter(self) -> dict:
        return self._gj_scatter

    @property
    def generate_pilot_diagrams(self) -> bool:
        return self._gen_pilot_diagrams

    @property
    def generate_offensive_pilot_diagrams(self) -> bool:
        return self._gen_off_fleet_diagrams

    @property
    def generate_defensive_pilot_diagrams(self) -> bool:
        return self._gen_def_fleet_diagrams

    @property
    def dps_summed(self) -> bool:
        return self._dps_summed

    @property
    def pod_dps(self) -> bool:
        return self._pod_dps_separated

    @property
    def drone_dps(self) -> bool:
        return self._drone_dps_separated

    @property
    def query_vars(self) -> dict:
        return {
            "dps_secs": self._dps_seconds
        }

    @property
    def colors(self) -> dict:
        return self._colors

    @property
    def icons(self) -> dict:
        return {
            "cap": self._cap_img_url,
            "links": self._links_img_url,
            "reload": self._reload_img_url,
            "being_scrammed": self._being_scrammed_img_url,
            "ecm": self._ecm_img_url,
            "drone": self._drone_img_url,
            "scram": self._scram_img_url,
            "base": self._base_img_url
        }

    @property
    def markers(self) -> dict:
        return {
            "cap_y": self._marker_cap_y,
        }

    def _load_ctx(self):
        with open(self.ctx_loc, "r") as f:
            ctx_json = loads(f.read())

        incoming_dmg = {
            "dmg_list": ctx_json['damage']['incoming'],
            "hex": ctx_json['colors']['damage_in_hex'],
        }
        outgoing_dmg = {
            "dmg_list": ctx_json['damage']['outgoing'],
            "hex": ctx_json['colors']['damage_out_hex'],
        }
        incoming_drone_dmg = {
            "dmg_list": ctx_json['damage']['incoming_drones'],
            "hex": ctx_json['colors']['drone_damage_in_hex'],
        }
        outgoing_drone_dmg = {
            "dmg_list": ctx_json['damage']['outgoing_drones'],
            "hex": ctx_json['colors']['drone_damage_out_hex'],
        }
        incoming_pod_dmg = {
            "dmg_list": ctx_json['damage']['incoming_pods'],
            "hex": ctx_json['colors']['pod_damage_in_hex'],
        }
        outgoing_pod_dmg = {
            "dmg_list": ctx_json['damage']['outgoing_pods'],
            "hex": ctx_json['colors']['pod_damage_out_hex'],
        }

        self._damage = {
            "incoming": incoming_dmg,
            "outgoing": outgoing_dmg,
            "incoming drone": incoming_drone_dmg,
            "outgoing drone": outgoing_drone_dmg,
            "incoming pods": incoming_pod_dmg,
            "outgoing pods": outgoing_pod_dmg
        }

        self._colors = {
            "incoming_reps_hex": ctx_json['colors']['reps_in_hex'],
            "outgoing_reps_hex": ctx_json['colors']['reps_out_hex'],
            "incoming_dmg_hex": ctx_json['colors']['damage_in_hex'],
            "outgoing_dmg_hex": ctx_json['colors']['damage_out_hex'],
            "incoming_drone_dmg_hex": ctx_json['colors']['drone_damage_in_hex'],
            "outgoing_drone_dmg_hex": ctx_json['colors']['drone_damage_out_hex'],
            "outgoing_nos_hex": ctx_json['colors']['nos_out_hex'],
            "incoming_nos_hex": ctx_json['colors']['nos_in_hex'],
            "outgoing_neuts_hex": ctx_json['colors']['neuts_out_hex'],
            "incoming_neuts_hex": ctx_json['colors']['neuts_in_hex'],
            "outgoing_pod_dmg_hex": ctx_json['colors']['pod_damage_out_hex'],
            "incoming": ctx_json['colors']['pod_damage_in_hex'],
        }

        self._cap_img_url =  ctx_json["icons"]["cap_url"]
        self._links_img_url = ctx_json["icons"]["links_url"]
        self._reload_img_url = ctx_json["icons"]["reload_url"]
        self._being_scrammed_img_url = ctx_json["icons"]["being_scrammed_url"]
        self._ecm_img_url = ctx_json["icons"]["ecm_url"]
        self._drone_img_url = ctx_json["icons"]["drone_url"]
        self._scram_img_url = ctx_json["icons"]["scram_url"]
        self._base_img_url = ctx_json["icons"]["base_url"]

        self._marker_cap_y = ctx_json["markers"]["cap_y"]

        self._dps_summed = ctx_json["flags"]["dps_summed"]
        self._drone_dps_separated = ctx_json["flags"]["drones_dps_separated"]
        self._pod_dps_separated = ctx_json["flags"]["breacher_pod_dps_separated"]
        self._gj_scatter = ctx_json["flags"]["gj_scatter"]
        self._hp_scatter = ctx_json["flags"]["hp_scatter"]
#        self._gen_fleet_diagrams = ctx_json["flags"]["fleet_diagrams"]
        self._gen_pilot_diagrams = ctx_json["flags"]["pilot_diagrams"]
        self._gen_off_fleet_diagrams = ctx_json["flags"]["offensive_fleet_diagrams"]
        self._gen_def_fleet_diagrams = ctx_json["flags"]["defensive_fleet_diagrams"]

        self._dps_seconds = ctx_json["query_vars"]["dps_secs"]

