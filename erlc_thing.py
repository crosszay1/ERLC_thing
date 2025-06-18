try:
    import os

    print("THIS PROGRAM WILL CRASH IF YOU HAVE NOT INSTALLED THE FOLLOWING LIBRARIES")
    print("sounddevice")
    print("numpy")
    print("pynput")
    print("pyautogui")
    print("pydirectinput")
    print("configparser")
    print("whisper via typing: pip install git+https://github.com/openai/whisper.git")
    print("")
    print("press ENTER to continue")
    input("")
    os.system('cls' if os.name == 'nt' else 'clear')

    """
    requirements:
      pip install git+https://github.com/openai/whisper.git
      pip install sounddevice numpy pynput pyautogui
    """
    import os
    import whisper, sounddevice as sd, numpy as np, pyautogui, threading, queue, time, pydirectinput as pg
    from pynput import keyboard
    import configparser
    config = configparser.ConfigParser()
    #debug stuff
    #print(sd.query_devices())
    #debug stuff
    HOTKEY = keyboard.Key.alt_l        # change to whatever key you want
    SAMPLERATE = 16_000                # Whisper likes 16 kHz mono
    CHANNELS = 1
    MODEL_NAME = "base"                # tiny / small / base / medium / large

    model         = whisper.load_model(MODEL_NAME)
    audio_q       = queue.Queue()      # holds raw float32 chunks
    record_flag   = threading.Event()  # True while key is down
    terminate_app = threading.Event()  # ctrl‑c friendly shutdown

    def audio_callback(indata, frames, time_info, status):
        if record_flag.is_set():
            mono = indata.mean(axis=1, keepdims=True)   # down‑mix
            audio_q.put(mono.copy())

    PREFERRED_DEVICE = 4  # <- your mic device index here
    def audio_worker():
        with sd.InputStream(samplerate=SAMPLERATE,
                            channels=CHANNELS,
                            callback=audio_callback,
                            device=PREFERRED_DEVICE,
                            dtype='float32'):
            # Keep thread alive until main program exits
            while not terminate_app.is_set():
                time.sleep(0.1)

    def key_listener():
        def on_press(key):
            if key == HOTKEY and not record_flag.is_set():
                # flush any old audio still in queue
                while not audio_q.empty(): audio_q.get()
                record_flag.set()
                print("🎙️  recording…")
                pg.press('t')
        def on_release(key):
            if key == HOTKEY:
                record_flag.clear()
                # collect everything recorded so far
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
                terminate_app.set()     # allow graceful exit
                return False            # stop listener

        with keyboard.Listener(on_press=on_press,
                               on_release=on_release) as listener:
            listener.join()

    def transcribe_and_type(audio):
        # Whisper expects float32 numpy array in range −1..1 at 16 kHz
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
        print("Startup Finished!")
        pyautogui.FAILSAFE = False      # let mouse to top‑left corner cancel if needed
        threading.Thread(target=audio_worker, daemon=True).start()
        key_listener()

    def setup():
        global CHANNELS, PREFERRED_DEVICE, HOTKEY
        print("welcome to my ERLC script!")
        print("would you like to:")
        print("[1] setup the script with new settings")
        print("[2] load exisitng settings")
        print("[3] view credits")
        setting_choice = int(input('please say either 1 or 2: ' ))

        if setting_choice == 1:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Setup process will begin momentarily, Here it a quick Tutroial on how to use")
            print("Press and hold a key of your choice to activate the script")
            print("upon activation, the script will press t to activate the in-game radio")
            print("the script will then start recording your voice, say whatever you want!")
            print("when you stop holding the key, it will stop recording, type what you said, and press enter!")
            print("")
            print("thats it for the tutorial!")
            print("Press ENTER for configuration")
            input()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("you will be shown a list of audio devices on your system, on the left side of each one will be a number, please enter the number that corresponds with the microphone you would like to use")
            print("Press ENTER to continue")
            input()
            print(sd.query_devices())
            print("")
            print("")
            PREFERRED_DEVICE = int(input('ENTER HERE: '))
            print("Now please enter the number of channels you want to use. if you dont know what these are, just put '1'")
            CHANNELS = int(input('Enter here: '))
            os.system('cls' if os.name == 'nt' else 'clear')
            print("What key would you like to press to toggle the mic on/off? (I recommend alt_l (which is left alt))")
            preffered_key = input('Hot‑key (e.g. alt_l): ').strip()
            #HOTKEY = keyboard.Key.preffered_key
            HOTKEY = getattr(keyboard.Key, preffered_key)
            os.system('cls' if os.name == 'nt' else 'clear')
            print("okley dokely, thats basically it!")

            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("save settings?")
            print("[1] save settings")
            print("[2] dont save settings")
            save_preference = int(input('response here: '))
            if save_preference == 1:
                #print("save")
                config['Settings'] = {'PREFERRED_DEVICE': PREFERRED_DEVICE, 'CHANNELS': CHANNELS, 'preffered_key' : preffered_key}
                with open('settings.ini', 'w') as configfile:
                    config.write(configfile)
            elif save_preference == 2:
                print("ok")
                pass
            else:
                print("you know what you did")
                exit()
            print("Initiating startup...")
            startup()

        elif setting_choice == 2:
            if os.path.exists("settings.ini"):
                pass
            else:
                print("No file exists goofball!")
                print("look what you've done!!!! the program is now exiting!!!")
                print("exiting")
                exit()
            config.read('settings.ini')
            PREFERRED_DEVICE = int(config['Settings']['PREFERRED_DEVICE'])
            CHANNELS = int(int(config['Settings']['CHANNELS']))

            preffered_key = config['Settings']['preffered_key'].strip()
            HOTKEY = getattr(keyboard.Key, preffered_key)
            startup()
        elif setting_choice == 3:
            print("Welcome to the credits")
            print("")
            print("programming - crosszay")
            print("Inspiration - A Youtube short I watched at 10pm and now cant seem to find")
            print("testing - crosszay")
            print("special thanks - chatgpt for indenting things for me | that cool guy who made the youtube short")
            print("")
            print("Contact")
            print("want to contact me for some reason? Send me a message on discord!")
        else:
            print("thats not a valid answer!")
            print("exiting")
            exit()    
        
    setup()

except Exception as e:
    os.system('cls' if os.name == 'nt' else 'clear')
    print("darn it!")
    print("a critical error occured, and shut down the program")
    print("Restarting the program will most likely fix this error... if it doesn't, try deleting settings.ini")
    print("")
    print("if your a super-duper cool person, make a bug ticket on my non-existent discord server that I might make later in the future")
    print("")
    print("")
    print("if your me, (hi me!) or someone who for some reason wants to know why the program crashed, the error message is below")
    print("--start--")
    print(f"{e}")
    print("--end--")
    exit()