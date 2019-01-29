#!/usr/bin/env python2
from __future__ import division
import os, sys, time, random, atexit, threading, ast, ConfigParser, logging
config_path = None # '~/RetroPie/scripts/addons.ini'
proc_names = None # ["wolf4sdl-3dr-v14", "wolf4sdl-gt-v14", "wolf4sdl-spear", "wolf4sdl-sw-v14", "xvic","xvic cart","xplus4","xpet","x128","x64sc","x64","PPSSPPSDL","prince","OpenBOR","Xorg","retroarch","ags","uae4all2","uae4arm","capricerpi","linapple","hatari","stella","atari800","xroar","vice","daphne.bin","reicast","pifba","osmose","gpsp","jzintv","basiliskll","mame","advmame","dgen","openmsx","mupen64plus","gngeo","dosbox","ppsspp","simcoupe","scummvm","snes9x","pisnes","frotz","fbzx","fuse","gemrb","cgenesis","zdoom","eduke32","lincity","love","kodi","alephone","micropolis","openbor","openttd","opentyrian","cannonball","tyrquake","ioquake3","residualvm","xrick","sdlpop","uqm","stratagus","wolf4sdl","solarus_run","mplayer","omxplayer","omxplayer.bin"]

#logging.basicConfig(filename='example.log',level=logging.DEBUG)
class Player(object):
    def __init__(self):
        self._max_volume = None
        self._fade_duration = None
        self._step_duration = None
        self._reset = None
        self._music_dir = None
        self._enabled = None
        self._current_song = -1
        self._library = None
        self._playlist = None
        self.is_Playing = False
    
    # Property Getters
    @property
    def max_volume(self):
        return self._max_volume
    @property
    def fade_duration(self):
        return self._fade_duration
    @property
    def step_duration(self):
        return self._step_duration
    @property
    def reset(self):
        return self._reset
    @property
    def enabled(self):
        return self._enabled
    @property
    def music_dir(self):
        return self._music_dir
    
    # Property Setters
    @max_volume.setter
    def max_volume(self, volume):
        if not 0 <= volume and not volume <= 1:
            print("Max volume must be a value between 0.0 to 1.0")
            return
        self._max_volume = float(volume)
        self._fade(self.mixer.get_volume(), self._max_volume, fade_duration=400, step_duration=20)
    @fade_duration.setter
    def fade_duration(self, duration):
        if not duration >= 0:
            print("Fade duration (ms) must be a value greater or equal to 0ms.")
            return
        self._fade_duration = int(duration)
    @step_duration.setter
    def step_duration(self, duration):
        if not duration >= 0:
            print("Step duration (ms) must be a value greater or equal to 0ms.")
            return
        self._step_duration = int(duration)
    @reset.setter
    def reset(self, boolean):
        if boolean.lower() in 'true':
            boolean = True
        elif boolean.lower() in 'false':
            boolean = False
        else:
            print("Reset must be a boolean value (True/False).")
            return
        self._reset = boolean
    @enabled.setter
    def enabled(self, boolean):
        if boolean.lower() in 'true':
            boolean = True
        elif boolean.lower() in 'false':
            boolean = False
        else:
            print("Enabled status must be a boolean value (True/False).")
            return
        self._enabled = boolean
        if not boolean:
            self.stop(fade_duration=300, force=True)
    @music_dir.setter
    def music_dir(self, music_dir):
        music_path = os.path.expanduser(music_dir)
        if not os.path.isdir(music_path):
            print("Could not find {}".format(music_path))
            return
        library = [filename for filename in os.listdir(music_path) if filename.endswith(".mp3") or filename.endswith(".ogg")] # Find everything that's .mp3 or .ogg
        if not library:
            print("No music found in directory. Please add .ogg or .mp3 files to {}".format(music_path))
            return
        self._library = library
        self._music_dir = music_path
        self._playlist = self._library[:]
        random.shuffle(self._playlist)
    
    def stop(self, *args, **kwargs):
        pass

class MusicPlayer(Player):
    def __init__(self):
        super(MusicPlayer, self).__init__()
        from pygame import mixer
        mixer.init()
        self.mixer = mixer.music
        self._lock = threading.Lock()
        self._force_event = threading.Event()
        
    def set_config(self, section, config):
        #logging.debug("Setting music player configs")
        if config.get(section, 'max_volume'):    self.max_volume    = config.get(section, 'max_volume')
        if config.get(section, 'fade_duration'): self.fade_duration = config.get(section, 'fade_duration')
        if config.get(section, 'step_duration'): self.step_duration = config.get(section, 'step_duration')
        if config.get(section, 'reset'):         self.reset         = config.get(section, 'reset')
        if config.get(section, 'music_dir'):     self.music_dir     = config.get(section, 'music_dir')
        if config.get(section, 'enabled'):       self.enabled       = config.get(section, 'enabled')
        
    def load_song(self, song_name):
        #logging.debug("Loading {} into memory, currently playing music will end.".format(song_name))
        self._current_song = self._playlist.index(song_name)
        self.mixer.load(os.path.join(os.path.expanduser(self._music_dir), song_name))
    
    def get_random(self):
        song_name = random.choice(self._playlist)
        if song_name == self._playlist[self._current_song] and len(self._playlist) > 1:
            song_name = self.get_random()
        #logging.debug("Getting random song: {}".format(song_name))
        #random.shuffle(self._playlist)
        return song_name
    def get_next(self):
        index = 0
        if self._current_song < len(self._playlist)-1:
            index = self._current_song + 1
        song_name = self._playlist[index]
        #logging.debug("Getting next song: {}".format(song_name))
        return song_name
    def get_prev(self):
        index = len(self._playlist)-1
        if self._current_song > 0:
            index = self._current_song - 1
        song_name = self._playlist[index]
        #logging.debug("Getting previous song: {}".format(song_name))
        return song_name
    
    def play(self, song_name=None, fade_duration=None, step_duration=None, force=False, rand=False):
        #logging.debug("Play cmd pre-thread")
        if self._enabled:
            if force: self._force_event.set()
            t = threading.Thread(target=self._play, kwargs={'song_name': song_name, 'fade_duration': fade_duration, 'step_duration': step_duration, 'force': force, 'rand': rand})
            t.start()
    def stop(self, fade_duration=None, step_duration=None, force=False):
        #logging.debug("Stop cmd pre-thread")
        if force: self._force_event.set()
        t = threading.Thread(target=self._stop, kwargs={'fade_duration': fade_duration, 'step_duration': step_duration, 'force': force})
        t.start()
    
    def _play(self, song_name=None, fade_duration=None, step_duration=None, force=False, rand=False):
        with self._lock:
            #logging.debug("Play cmd thread")
            self.is_Playing = True
            if not self._force_event.is_set() or force:
                if (not song_name and not self.mixer.get_busy()) or rand: song_name = self.get_random()
                if song_name: self.load_song(song_name)
                self.mixer.set_volume(0)
                if self.mixer.get_busy():
                    self.mixer.unpause()
                else:
                    self.mixer.play()
            self._fade(0, self.max_volume, fade_duration=fade_duration, step_duration=step_duration, force=force)

    def _stop(self, fade_duration=None, step_duration=None, force=False):
        with self._lock:
            #logging.debug("Stop cmd thread")
            self.is_Playing = False
            self._fade(self.mixer.get_volume(), 0, fade_duration=fade_duration, step_duration=step_duration, force=force)
            if not self._force_event.is_set() or force:
                if self.reset:
                    self.mixer.stop()
                else:
                    self.mixer.pause()

    def _fade(self, start_volume, end_volume, fade_duration=None, step_duration=None, force=False):
        #logging.debug("Fade for volume: {} -> {}".format(start_volume, end_volume))
        if not fade_duration: fade_duration = self.fade_duration
        if not step_duration: step_duration = self.step_duration
        steps = fade_duration / step_duration
        vdelta = end_volume - start_volume
        if steps:
            vps = vdelta / steps
        else:
            vps = vdelta
        if start_volume > end_volume:
            vol_g = start_volume
            vol_l = end_volume
        elif start_volume < end_volume:
            vol_g = end_volume
            vol_l = start_volume
        else:
            vol_g = vol_l = end_volume
        while vol_g > vol_l:
            if self._force_event.is_set() and not force: 
                #print("Force command found, breaking thread. {}".format(self.mixer.get_volume()))
                break
            if vps > 0:
                vol_l = volume = vol_l + vps
            elif vps < 0:
                vol_g = volume = vol_g + vps
            self.mixer.set_volume(volume)
            time.sleep(step_duration/1000)
        if not self._force_event.is_set(): self.mixer.set_volume(end_volume)
        if self._force_event.is_set() and force: self._force_event.clear(); #print("Force cleared.")

class Application:
    def __init__(self, config_path=None, proc_names=None):
        self.mp = None
        if config_path:
            self._config_path = os.path.expanduser(config_path)
        else:
            self._config_path = os.path.join(sys.path[0],'addons.ini')
        # Load configs
        self._cfg_section = 'EmulationStationBGM'
        self.c = self._configs()
        self.pipe = os.path.expanduser('{}.{}'.format(self.c.get(self._cfg_section, 'pipe_file'), os.getpid()))
        self.proc_delay = int(self.c.get(self._cfg_section, 'proc_delay'))
        self.proc_fade = int(self.c.get(self._cfg_section, 'proc_fade'))
        self.proc_names = proc_names
        if not self.proc_names: 
            self.proc_names = ["omxplayer.bin", 'htop']
        self.countdown = 0
        self.proc_mute = False
        self.main_loop_sleep = 1
        self.manual_stop = False
        
    def _configs(self, custom_config={}):
        #logging.debug("Read/Write configs")
        cfg_path = self._config_path
        save_cfg = False
        defaults = {
            'pipe_file'     : '/dev/shm/esbgm',
            'music_dir'     : '/home/pi/RetroPie/music',
            'max_volume'    : '0.20',
            'fade_duration' : '3000',
            'step_duration' : '20',
            'start_delay'   : '0',
            'reset'         : 'False',
            'start_song'    : '',
            'enabled'       : 'True',
            'proc_delay'    : '2000',
            'proc_fade'     : '600',
        }
        if custom_config:
            defaults.update(custom_config)
        if not os.path.isfile(cfg_path):
            open(cfg_path, 'a').close()
            save_cfg = True
        c = ConfigParser.ConfigParser()
        c.read(cfg_path)
        if not c.has_section(self._cfg_section):
            c.add_section(self._cfg_section)
            save_cfg = True
        for option in defaults.keys():
            if option == 'proc_delay': self.proc_delay = int(defaults[option])  # Live edits to config
            if option == 'proc_fade': self.proc_fade = int(defaults[option])    # Live edits to config
            if option in custom_config.keys() or not c.has_option(self._cfg_section, option):
                c.set(self._cfg_section, option, defaults[option])
                save_cfg = True
        if self.mp:
            self.mp.set_config(self._cfg_section, c)
        if save_cfg:
            with open(cfg_path, 'w') as f:
                c.write(f)
        return c
    
    def controller(self, parent_PID, args):
        pipeout = os.open('{}.{}'.format(self.c.get(self._cfg_section, 'pipe_file'), parent_PID), os.O_WRONLY)
        os.write(pipeout, '%s\n' % args)
        
    def run(self):
        self._init()
        self._main_loop()
    
    def _init(self):
        #logging.debug("Initialize player and starting defaults")
        # Initialize pipe & register clean-up
        os.mkfifo(self.pipe)
        atexit.register(self._clean_pipe)
        # Initialize music player
        self.mp = MusicPlayer()
        # Pass configs to music player
        self.mp.set_config(self._cfg_section, self.c)
        # Start delay and start song
        if self.c.get(self._cfg_section, 'start_delay'):
            start_delay = float(self.c.get(self._cfg_section, 'start_delay'))
            time.sleep(start_delay/1000)
        start_song = self.c.get(self._cfg_section, 'start_song')
        start_song_path = os.path.join(os.path.expanduser(self.c.get(self._cfg_section, 'music_dir')), start_song)
        if start_song and os.path.isfile(start_song_path):
            self.mp.play(song_name=self.c.get(self._cfg_section, 'start_song'))
        
    def _main_loop(self):
        #pipein = open(self.pipe, 'r')
        #logging.debug("Main loop")
        pipein = os.open(self.pipe, os.O_RDONLY|os.O_NONBLOCK) #Non-blocking open
        pipe_read = readline(pipein)
        while True:
            #logging.debug("Start of loop")
            if not self.mp.mixer.get_busy(): self.mp.is_Playing = False
            #line = pipein.readline()
            #line = os.read(pipein, 1024) #Non-blocking read-in (Need to do buffer management to break at '\n' or '\r')
            line = next(pipe_read)
            if line:
                self._parse_args(line)
            # Process checks
            # Other looping checks
            self._process_monitor()
            if not self.mp.mixer.get_busy() and not self.manual_stop:
                #logging.debug("Mixer not busy, playing song.")
                self.mp.play()
            #logging.debug("End of loop")
            time.sleep(self.main_loop_sleep)

    def _clean_pipe(self):
        pipe_dir = os.path.dirname(self.pipe)
        pipe_name = os.path.basename(self.pipe)
        for filename in os.listdir(pipe_dir):
            if pipe_name in filename:
                os.remove(os.path.join(pipe_dir, pipe_name))
            #print("Cleaned out {}".format(os.path.join(pipe_dir, pipe_name)))
        
    def _parse_args(self, args):
        if args:
            #logging.debug(args)
            args = ast.literal_eval(args) ## THIS CAUSES PROBLEMS ##FIXIT##
            player_cmd = args.pop(0)
            song_name = start_delay = music_dir = max_volume = fade_duration = step_duration = reset = start_song = enabled = pipe_file = proc_delay = proc_fade = None
            force = rand = False
            while args:
                try:
                    arg = args.pop(0)
                    if arg in ['--song_name']: song_name = args.pop(0)
                    elif arg in ['--start_delay']: start_delay = args.pop(0)
                    elif arg in ['--music_dir']: music_dir = args.pop(0)
                    elif arg in ['--volume']: max_volume = args.pop(0)
                    elif arg in ['--fade_duration']: fade_duration = int(args.pop(0)) # Change to int to pass args to other player_cmds (play, stop, next, prev)
                    elif arg in ['--step_duration']: step_duration = int(args.pop(0)) # Change to int to pass args to other player_cmds (play, stop, next, prev)
                    elif arg in ['--reset']: reset = args.pop(0)
                    elif arg in ['--start_song']: start_song = args.pop(0)
                    elif arg in ['--enable']: enabled = 'True'
                    elif arg in ['--disable']: enabled = 'False'
                    elif arg in ['--pipe_file']: pipe_file = args.pop(0)
                    elif arg in ['--proc_delay']: proc_delay = args.pop(0)
                    elif arg in ['--proc_fade']: proc_fade = args.pop(0)
                    elif arg in ['--force']: force = True
                    elif arg in ['--random']: rand = True
                    elif arg in ['-h', '--help']: print("Spit out a help thing. ##FIXIT##")
                    else: print("Garbaged argument: {}".format(arg))
                except IndexError:
                    print("Missing argument.")
            if player_cmd == 'set':
                values = {}
                if start_delay:     values.update({'start_delay': start_delay})
                if music_dir:       values.update({'music_dir': music_dir})
                if max_volume:      values.update({'max_volume': max_volume})
                if fade_duration:   values.update({'fade_duration': str(fade_duration)}) # Revert change to int back to str to pass to configparser
                if step_duration:   values.update({'step_duration': str(step_duration)})
                if reset:           values.update({'reset': reset})
                if start_song:      values.update({'start_song': start_song})
                if enabled:         values.update({'enabled': enabled})
                if pipe_file:       values.update({'pipe_file': pipe_file})
                if proc_delay:       values.update({'proc_delay': proc_delay})
                if proc_fade:       values.update({'proc_fade': proc_fade})
                self._configs(custom_config=values)
            elif player_cmd == 'play':
                self.manual_stop = False
                self.mp.play(song_name=song_name, fade_duration=fade_duration, step_duration=step_duration, force=force, rand=rand)
            elif player_cmd == 'stop':
                self.manual_stop = True
                self.mp.stop(fade_duration=fade_duration, step_duration=step_duration, force=force)
            elif player_cmd == 'next':
                self.manual_stop = False
                self.mp.play(song_name=self.mp.get_next(), fade_duration=fade_duration, step_duration=step_duration, force=force)
            elif player_cmd == 'prev':
                self.manual_stop = False
                self.mp.play(song_name=self.mp.get_prev(), fade_duration=fade_duration, step_duration=step_duration, force=force)
            elif player_cmd == 'quit':
                sys.exit()

    def _process_monitor(self):
        #logging.debug("Process monitor")
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        for pid in pids:
            try:
                procname = open(os.path.join('/proc',pid,'comm'),'rb').read()
            except IOError: 
                continue
            if procname[:-1] in self.proc_names:
                #Turn down the music if actually playing (not paused)
                if self.mp.is_Playing:
                    self.proc_mute = True
                    self.mp.stop(fade_duration=self.proc_fade, force=True)
                while os.path.exists(os.path.join('/proc',pid)):
                    time.sleep(3)
                    self.countdown = self.proc_delay
        if self.countdown <= 0 and self.proc_mute:
            self.proc_mute = False
            self.mp.play(fade_duration=self.proc_fade)
        if self.countdown > 0 and self.proc_mute:
            self.countdown -= (self.main_loop_sleep * 1000) # number is equal to mainloop time.sleep() * 1000

def readline(pipein):
    buffered_lines = bytearray()
    while True:
        try: 
            line = os.read(pipein, 1024)
        except BlockingIOError:
            yield ""
            continue
        if not line:
            if buffered_lines:
                yield buffered_lines.decode('UTF-8')
                buffered_lines.clear()
            else:
                yield ""
            continue
        buffered_lines.extend(line)
        while True:
            r = buffered_lines.find(b'\r')
            n = buffered_lines.find(b'\n')
            if r == -1 and n == -1: break
            if r == -1 or r > n:
                yield buffered_lines[:(n+1)].decode('UTF-8')
                buffered_lines = buffered_lines[(n+1):]
            elif n == -1 or n > r:
                yield buffered_lines[:r].decode('UTF-8') #+ '\n'
                if n == r+1:
                    buffered_lines = buffered_lines[(r+2):]
                else:
                    buffered_lines = buffered_lines[(r+1):]

if __name__ == "__main__":
    app = Application(config_path=config_path, proc_names=proc_names)
    ## Search for pipe and open pipe
    pipe_dir = os.path.dirname(app.c.get(app._cfg_section, 'pipe_file'))
    pipe_file = os.path.basename(app.c.get(app._cfg_section, 'pipe_file'))
    PID = None
    for filename in os.listdir(pipe_dir):
        if pipe_file in filename:
            check_PID = filename.split('.')[1]
            cmdline = None
            remove_pipe = False
            try:
                with open('/proc/{}/cmdline'.format(check_PID), 'r') as f:
                    cmdline = f.read()
            except IOError:
                remove_pipe = True
            if not remove_pipe:
                if os.path.basename(sys.argv[0]) in cmdline:
                    PID = check_PID
                else:
                    remove_pipe = True
            if remove_pipe:
                bad_pipe = '{}.{}'.format(app.c.get(app._cfg_section, 'pipe_file'), check_PID)
                os.remove(bad_pipe)
    if not PID:
        if len(sys.argv) > 1:
            print("EmulationStation BGM has not been started, but since there are command args, I will assume that EmulationStation BGM crashed somewhere.")
            sys.exit()
        app.run()
    elif PID and len(sys.argv) > 1:
        app.controller(PID, sys.argv[1:])
        
