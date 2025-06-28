print("Making Sure All Dependencies Are Installed")
try:
    import sys
    import subprocess
    from importlib.util import find_spec
    from importlib import metadata  # std‑lib in Py ≥3.8

    def check_and_install_dependencies():
        """
        Checks for required Python packages.  If any are missing *or* NumPy is not
        exactly 2.2.0, prompts the user to install the correct versions.
        """

        required_packages = [
            "sounddevice",
            "numpy",           # we’ll enforce 2.2.0 below
            "pynput",
            "pyautogui",
            "pydirectinput",
            "configparser",
            "whisper",
        ]

    #create list of uninstalled packages
        missing = []

        for package in required_packages:
            if find_spec(package) is None:
                # Not installed at all
                missing.append(package)
            elif package == "numpy":
                # Installed — but do we have the right version?
                installed = metadata.version("numpy")
                if installed != "2.2.0":
                    print(f"NumPy {installed} found; 2.2.0 required.")
                    missing.append(package)

    # No issues? carry on.
        if not missing:
            print("All dependencies satisfied.")
            return
    #tell user what they have not installed :(
        print("The following packages (or versions) are required:")
        for pkg in missing:
            if pkg == "numpy":
                print("  • numpy==2.2.0")
            else:
                print(f"  • {pkg}")

    #prompt until user stops giving us annoying invalid answers
        while True:
            answer = input("\nInstall them now? (y/n): ").strip().lower()
            if answer in ("y", "yes"):
                break
            if answer in ("n", "no"):
                print("\nExiting: cannot continue without the required packages.")
                print("")
                print("EXITING in 5 seconds")
                time.sleep(5)
                sys.exit(1)
            print("Please enter 'y' or 'n'.")

    
    #Assemble pip install targets and run pip        #
    
        install_targets = []
        for pkg in missing:
            if pkg == "numpy":
                install_targets.append("numpy==2.2.0")
            elif pkg == "whisper":
                install_targets.append("git+https://github.com/openai/whisper.git")
            else:
                install_targets.append(pkg)

        print("\nInstalling packages …")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *install_targets],
                check=True
            )
            print("\n Installation complete.  Please restart this script.")
            print("")
            print("Exiting in 5 seconds")
            time.sleep(5)
            sys.exit(1)
        except subprocess.CalledProcessError as err:
            print(f"\n pip failed with error: {err}")
            print("")
            print("Press ENTER to exit")
            input()
        sys.exit(1)
    check_and_install_dependencies()
    print("")
    print("Loading...")
    print("This may take a a sec (1-10 seconds)")
    """
    requirements:
      pip install git+https://github.com/openai/whisper.git
      pip install sounddevice numpy pynput pyautogui
    """
    import whisper, sounddevice as sd, numpy as np, pyautogui, threading, queue, time, pydirectinput as pg
    from pynput import keyboard
    import configparser
    import os
    config = configparser.ConfigParser()

    HOTKEY      = keyboard.Key.alt_l        # manual changing, remove laters
    SAMPLERATE  = 16_000                    # Whisper likes 16 kHz mono
    CHANNELS    = 1
    MODEL_NAME  = "base"                    # tiny / small / base / medium / large
    PREFERRED_DEVICE = 4                    # <- mic device index here

    model         = whisper.load_model(MODEL_NAME)
    audio_q       = queue.Queue()      # holds raw float32 chunks
    record_flag   = threading.Event()  # True while key is down
    terminate_app = threading.Event()  # ctrl‑c friendly shutdown
    def clearscreen():
        os.system('cls' if os.name == 'nt' else 'clear')
    def audio_callback(indata, frames, time_info, status):
        if record_flag.is_set():
            mono = indata.mean(axis=1, keepdims=True)   # down‑mix
            audio_q.put(mono.copy())

    def validate_device_and_channels(dev_index: int, channels: int) -> None:
        """Raise ValueError if the device index is invalid or the channel
        count exceeds what the device supports."""
        devices = sd.query_devices()                 # list of all devices

        # --- index in range? 
        if dev_index < 0 or dev_index >= len(devices):
            raise ValueError(
                f"Device index {dev_index} is out of range; "
                f"valid indices are 0‑{len(devices) - 1}."
                
            )

        # --- channel count valid?
        info   = sd.query_devices(dev_index)         
        max_in = info['max_input_channels']
        if channels > max_in:
            raise ValueError(
                f"Device '{info['name']}' supports only {max_in} input channel(s), "
                f"but you asked for {channels}."
            )
            
    def audio_worker():
        with sd.InputStream(samplerate=SAMPLERATE,
                            channels=CHANNELS,
                            callback=audio_callback,
                            device=PREFERRED_DEVICE,
                            dtype='float32'):
            while not terminate_app.is_set():
                time.sleep(0.1)

    def key_listener():
        def on_press(key):
            if key == HOTKEY and not record_flag.is_set():
                while not audio_q.empty():
                    audio_q.get()          # flush old audio
                record_flag.set()
                print("🎙️  recording…")
                pg.press('t')

        def on_release(key):
            if key == HOTKEY:
                record_flag.clear()
                buffers = []
                while not audio_q.empty():
                    buffers.append(audio_q.get())

                if buffers:
                    audio = np.concatenate(buffers, axis=0).flatten()
                    threading.Thread(target=transcribe_and_type,
                                     args=(audio,),
                                     daemon=True).start()
                print("⏹️  stopped.")
            elif key == keyboard.Key.esc:
                terminate_app.set()
                return False               # stop listener

        with keyboard.Listener(on_press=on_press,
                               on_release=on_release) as listener:
            listener.join()

    def transcribe_and_type(audio):
        print("🧠  transcribing…")
        result = model.transcribe(audio, language="en", fp16=False)
        text   = result["text"].strip()
        if text:
            print("⌨️  typing:", text)
            pg.press('/')
            pyautogui.write(text)
            pg.press('enter')
        else:
            print("…no speech detected.")

    def startup():
        clearscreen()
        print("Startup Finished!")
        print("the script is now running! Enter a game of erlc, hold down your hotkey, and enjoy!")
        print("happy roleplaying!")
        print("")
        print("")
        pyautogui.FAILSAFE = False
        threading.Thread(target=audio_worker, daemon=True).start()
        key_listener()


    # ---------- helper for safe integer input ----------
    def ask_int(prompt: str, valid: tuple[int, ...]):
        while True:
            choice = input(prompt).strip()
            if choice.isdecimal():
                value = int(choice)
                if value in valid:
                    return value
            clearscreen()
            print(f"'{choice}' isn’t a valid option.\n")
            print("welcome to my ERLC script!")
            print("would you like to:")
            print("[1] setup the script with new settings")
            print("[2] load existing settings (buggy at times)")
            print("[3] view credits")
            
    # ---------- Main setup menu ----------
    def setup():
        global CHANNELS, PREFERRED_DEVICE, HOTKEY

        while True:                                     # top‑level menu loop
            clearscreen()
            print("welcome to my ERLC script!")
            print("would you like to:")
            print("[1] setup the script with new settings")
            print("[2] load existing settings (buggy at times)")
            print("[3] view credits")
            setting_choice = ask_int(
                "Please enter the number that corresponds with your choice!: ",
                (1, 2, 3)
            )

            # ---- option 1: new settings ----
            if setting_choice == 1:
                clearscreen()
                print("Setup process will begin momentarily. Here is a quick tutorial on how to use:")
                print("• Hold your chosen hot‑key to activate the script")
                print("• The script presses 't', records, then types what you said and hits ENTER")
                print("\nPress ENTER for configuration")
                input()
                clearscreen()
                if os.path.exists("settings.ini"):
                    os.remove("settings.ini")
                print("You will see a list of audio devices. Enter the number for your microphone.")
                print("Press ENTER to continue")
                input()
                print(sd.query_devices())
                print("")
                while True:
                    try:
                        PREFERRED_DEVICE = int(input('ENTER HERE: '))
                        validate_device_and_channels(PREFERRED_DEVICE, 1)
                        clearscreen()
                        break
                    except ValueError:
                        clearscreen()
                        print(sd.query_devices())
                        print("")
                        pass
                print("\nNow enter the number of channels you want to use (1 is fine in most cases)")
                print("")
                while True:
                    try:
                        CHANNELS = int(input('Enter here: '))
                        validate_device_and_channels(PREFERRED_DEVICE, CHANNELS)
                        clearscreen()
                        break
                    except ValueError:
                        clearscreen()
                        print("\nNow enter the number of channels you want to use (1 is fine in most cases)")
                        print("")
                        pass
                print("What key would you like to press to toggle the mic on/off? (e.g. alt_l)")
                print("")
                print("NOTE: I am aware some inputs are being excepted despite the fact they are invalid. Please use alt_l for now (this is the left alt on your keyboard)")
                print("if you do not choose to abide by this warning, you continue at your own risk, and cannot be mad at me if the script does not work")
                while True:
                    try:
                        preferred_key = input('Hot‑key: ').strip()
                        HOTKEY = getattr(keyboard.Key, preferred_key)
                        clearscreen()
                        break
                    except AttributeError as e:
                        clearscreen()
                        print("thats not a valid answer")
                        print("")
                        print("What key would you like to press to toggle the mic on/off? (e.g. alt_l)")
                        pass


                print("Save settings?")
                save_preference = ask_int("1 = save, 2 = don't save: ", (1, 2))
                if save_preference == 1:
                    config['Settings'] = {
                        'PREFERRED_DEVICE': PREFERRED_DEVICE,
                        'CHANNELS': CHANNELS,
                        'preferred_key': preferred_key
                    }
                    with open('settings.ini', 'w') as configfile:
                        config.write(configfile)

                print("Initiating startup...\n")
                startup()
                return                              # leave setup after successful start

            # ---- option 2: load settings ----
            elif setting_choice == 2:
                if not os.path.exists("settings.ini"):
                    clearscreen()
                    print("\nNo settings.ini found. Choose option 1 first.\n")
                    print("Press ENTER to return to menu")
                    input()
                    continue                        # back to main menu
                try:
                    config.read('settings.ini')
                    PREFERRED_DEVICE = int(config['Settings']['PREFERRED_DEVICE'])
                    CHANNELS        = int(config['Settings']['CHANNELS'])
                    preferred_key   = config['Settings']['preferred_key'].strip()
                    HOTKEY = getattr(keyboard.Key, preferred_key)

                    validate_device_and_channels(PREFERRED_DEVICE, CHANNELS)

                    startup()
                    return
                except Exception as e:
                    clearscreen()                  # leave setup after successful start
                    print("error reading settings.ini")
                    print("")
                    os.remove("settings.ini")
                    print("settings.ini has been deleted")
                    print("")
                    print("")
                    print("Please Select Option 1 to set things up again")
                    print("Press ENTER to return to main menu")
                    input()
                    clearscreen()
                    continue
            # ---- option 3: credits ----
            else:
                clearscreen()
                print("Welcome to the credits\n")
                print("programming - crosszay")
                print("inspiration - A YouTube short I watched at 10 pm and now can't seem to find")
                print("testing - crosszay")
                print("special thanks - ChatGPT for indenting things for me")
                print("Community discord server is: https://discord.gg/9F59Dks4bp")
                print("\nPress ENTER to return to the menu")
                input()
                clearscreen()
                # loop continues to show the main menu again
    setup()
except Exception as e:
    clearscreen()
    print("darn it!")
    print("A critical error occurred and shut down the program.")
    print("Restarting the program will most likely fix this error…")
    print("If it doesn't, try deleting settings.ini.") #I don't think this is necessary because we already delete if loading fails, but I supposed this is a good backup... there was an issue earlier where the try loop failed to catch the error. if that happens again, this is good
    print("\nIf you're a super‑duper cool person, file a bug ticket on my Discord server! (https://discord.gg/9F59Dks4bp)\n")
    print("")
    print("error is below")
    print("--start--")
    print(f"{e}")
    print("--end--")
    print("")
    print("")
    print("Press ENTER to EXIT")
    input()
    exit()
