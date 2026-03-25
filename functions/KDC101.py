from pylablib.devices import Thorlabs
import numpy as np


class KDC101():
    def __init__(self):
        self.devices = (Thorlabs.list_kinesis_devices())
        print(f"{self.devices} is initialized")
        self.stage = Thorlabs.KinesisMotor(self.devices[0][0])
        self.set_velocity(spd_min_mmps=0, spd_acc=4.5, spd_mmps=2.4)

    def is_homed(self):
        self.homed = self.stage.is_homed()
        if self.homed:
            print(f"{self.devices[0][0]} is homed")
        else:
            print(f"{self.devices[0][0]} is not homed")
        return self.homed
    
    def home_search(self):
        self.set_velocity()
        print("home search start")
        Thorlabs.KinesisMotor.home(self.stage)

        while Thorlabs.KinesisMotor.is_moving(self.stage):
            pass
        print("home search finish")

    def set_velocity(self, spd_min_mmps=0, spd_acc=4.5, spd_mmps=2.4):
        self.spd_min_mmps = np.clip(spd_min_mmps, 0, 2.4)
        self.spd_mmps = np.clip(spd_mmps, 0, 2.4)
        self.spd_acc = np.clip(spd_acc, 0, 4.5)
        self.device_spd_min_mmps = spd_min_mmps * 34555.0
        self.device_spd_acc = spd_acc * 34555.0
        self.device_spd_mmps = spd_mmps * 34555.0
        Thorlabs.KinesisMotor.setup_velocity(self.stage, self.device_spd_min_mmps, self.device_spd_acc, self.device_spd_mmps)

        print(f'velocity[mm/s]={spd_mmps}, spd_acc[mm/s^2]={spd_acc}, min_velocity[mm/s]={spd_min_mmps}')

    def move(self, target_pos):
        device_target_pos = target_pos * 34555.0
        Thorlabs.KinesisMotor.move_to(self.stage, device_target_pos)
        print(f"stage move to {target_pos}")

    def close(self):
        self.stage.close()
        print(f"{self.devices[0][0]} is closed")

    def is_moving(self):
        return Thorlabs.KinesisMotor.is_moving(self.stage)
    
    def stop(self):
        Thorlabs.KinesisMotor.stop(self.stage)
        print(f"{self.devices[0][0]} movement stopped")


if __name__ == "__main__":
    thorlabs_stage = KDC101()

    if thorlabs_stage.is_homed():
        pass
        print(f"{thorlabs_stage.devices} is homed already")
    else:
        thorlabs_stage.home_search()

    thorlabs_stage.set_velocity(spd_min_mmps=0, spd_acc=4.5, spd_mmps=1)
    thorlabs_stage.move(target_pos=10.0)

    thorlabs_stage.close()