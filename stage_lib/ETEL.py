import time
import numpy as np
import pysoslab_etel_stage as py_stage_etel

STAGE_ETEL_IP = "10.110.1.200"
# LINEAR_STAGE_OFFSET = -43 + 188
LINEAR_STAGE_OFFSET = -43 


def test_stage(stage_etel) -> None:
    """
    test_stage
    """

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        # print("LINEAR_TARGET", get_current_position(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET))
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, 30.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        # print("ROTARY_DEVICE", get_current_position(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE))
        time.sleep(0.2)

    # stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, 30.0, 50.0)
    # while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
    #     time.sleep(0.2)

    # stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, -30.0, 50.0)
    # while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
    #     time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, -90.0, 50.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
        # print("ROTARY_TARGET", get_current_position(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET))
        time.sleep(0.2)

    # stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 30.0, 30.0)
    # while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
    #     time.sleep(0.2)

    # stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, -30.0, 30.0)
    # while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
    #     time.sleep(0.2)


def search_home(stage_etel, axis_index) -> bool:
    """
    search_home
    """
    retval = False

    if not stage_etel.servoOn(axis_index):
        print(f"Failed to servo ON [Axis={axis_index}]")

    if not stage_etel.isHomePosition(axis_index):
        if axis_index == py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET:
            stage_etel.moveTo(
                py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 1000.0, 200.0
            )
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)

        retval = stage_etel.moveToHomePosition(axis_index)
        if retval:
            while not stage_etel.isHomePosition(axis_index):
                time.sleep(1)
        else:
            print(f"Failed to moveToHomePosition [Axis={axis_index}]")

    return retval

def get_current_position(stage_etel, axis_index) -> int:
    """
    Current Position of the axis
    """
    retval = 0

    # if not stage_etel.servoOn(axis_index):
    #     print(f"Failed to servo ON [Axis={axis_index}]")

    retval = stage_etel.currentPosition(axis_index)

    return retval


def init_stage(stage_etel, offset=LINEAR_STAGE_OFFSET) -> None:
    """
    init_stage
    """
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE)
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET)
    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, offset
    )


def disconnect_stage(stage_etel: py_stage_etel.stage_etel) -> None:
    """
    disconnect_stage
    """
    stage_etel.stop(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
    stage_etel.stop(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET)
    stage_etel.stop(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE)
    stage_etel.disconnect()
    time.sleep(0.1)


def unittest() -> None:
    """
    unittest
    """
    print("[ test_stage_etel is started ]\n")

    stage_etel = py_stage_etel.stage_etel()
    if stage_etel.connect(STAGE_ETEL_IP, 3):
        time.sleep(0.1)

        init_stage(stage_etel)
        test_stage(stage_etel)
    disconnect_stage(stage_etel)

    print("\n[ test_stage_etel is finished ]")


if __name__ == "__main__":
    unittest()
