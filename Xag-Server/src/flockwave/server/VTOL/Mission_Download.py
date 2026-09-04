import simplekml
from .new_left import main as VPL
from .new_Right import main as VPR
from flockwave.server.model import UAV


def download_mission_kml(kml_file: str, mission: list[float]) -> None:
    kml = simplekml.Kml()
    if len(mission) > 0:
        for i, cmd in enumerate(mission):
            kml.newpoint(name="{}_coordinate".format(i), coords=[(cmd[0], cmd[1])])
    kml.save(kml_file)


async def main(
    selected_turn: str,
    numOfDrones: int,
    mission: list[float],
    landingMission: list[float],
    uavs: dict[str, UAV],
) -> bool:
    if len(mission) > 0:
        download_mission_kml(
            "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/Xag-Server/src/flockwave/server/VTOL/kmls/Forward-Mission.kml",
            mission,
        )
        download_mission_kml(
            "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/Xag-Server/src/flockwave/server/VTOL/kmls/Reverse-Mission.kml",
            landingMission,
        )
        if selected_turn == "left":
            await VPL(numOfDrones, uavs)
        elif selected_turn == "right":
            await VPR(numOfDrones, uavs)

    return True

async def landing_main(landingMission,numOfDrones,uavs):
    if len(landingMission) > 0:
        download_mission_kml(
            "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/Xag-Server/src/flockwave/server/VTOL/kmls/Reverse-Mission.kml",
            landingMission,
        )
    await VPR(numOfDrones, uavs)
    return  True