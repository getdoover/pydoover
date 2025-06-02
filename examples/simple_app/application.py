from pydoover.docker import DockerApplication, run_app

from app_config import SampleConfig


class SampleApplication(DockerApplication):
    config: SampleConfig  # not necessary, but helps your IDE provide autocomplete!

    def setup(self):
        print(f"Hello! The funny config message is: {self.config.funny_message.value}!")

    def main_loop(self):
        if self.config.outputs_enabled.value is True:
            print("We are allowed to set outputs!")

        for i in range(self.config.num_di.value):
            status = self.platform_iface.get_di(i)
            if status:
                print(f"DI {i} is active!")
            else:
                print(f"DI {i} is not active!")


if __name__ == "__main__":
    run_app(SampleApplication(config=SampleConfig()))
