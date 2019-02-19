#!/usr/bin/env python2
from __future__ import division
import os, sys, time, random, atexit, threading, ast, ConfigParser, logging
log_level_disable = logging.DEBUG #logging.DEBUG
config_path = '/home/pigaming/RetroArena/scriptmodules/supplementary/esbgm/addons.ini' # '~/github/emulationstation-bgm/addons.ini' #
log_path = os.path.join(os.path.dirname(os.path.expanduser(config_path)), 'esbgm.log')
proc_names = ['htop'] #None
# proc_names = ["wolf4sdl-3dr-v14", "wolf4sdl-gt-v14", "wolf4sdl-spear", "wolf4sdl-sw-v14", 
    # "xvic","xvic cart","xplus4","xpet","x128","x64sc","x64","PPSSPPSDL","prince",
    # "OpenBOR","Xorg","retroarch","ags","uae4all2","uae4arm","capricerpi","linapple",
    # "hatari","stella","atari800","xroar","vice","daphne.bin","reicast","pifba","osmose",
    # "gpsp","jzintv","basiliskll","mame","advmame","dgen","openmsx","mupen64plus","gngeo",
    # "dosbox","ppsspp","simcoupe","scummvm","snes9x","pisnes","frotz","fbzx","fuse","gemrb",
    # "cgenesis","zdoom","eduke32","lincity","love","kodi","alephone","micropolis","openbor",
    # "openttd","opentyrian","cannonball","tyrquake","ioquake3","residualvm","xrick","sdlpop",
    # "uqm","stratagus","wolf4sdl","solarus_run","mplayer","omxplayer","omxplayer.bin"]

help_message = "\
    Usage: derp derp\n\
    ##FIXIT##\n\
    RIP HELP\n\
    I wasn't paid for this\n\
    I wish I were\n\
    It's 2:30am\n\
    #BadProgrammerHabits"

##############################################################################
# Non-blocking readlines generator
# http://code.activestate.com/recipes/578900/
##############################################################################
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
##############################################################################

logging.basicConfig(filename=log_path, level=logging.DEBUG)
logging.disable(log_level_disable)
class Player(object):
    def __init__(self):
        logging.debug("Instantiating all music player variables")
        self.config = {
            'music_dir'     : None,
            'max_volume'    : None,
            'fade_duration' : None,
            'step_duration' : None,
            'reset'         : None,
        }
        self.current_song = -1
        self.library = None
        self.playlist = None
        self.status = 0 # 0 = Stopped, 1 = Playing, 2 = Paused
        self.fade_status = 0 # 0 = Not Fading, 1 = Fade In, 2 = Fade Out
        logging.debug("Instantiated all music player variables")
    @property
    def max_volume(self):
        return self.config['max_volume']
    @property
    def music_dir(self):
        return self.config['music_dir']
    
    @max_volume.setter
    def max_volume(self, volume):
        logging.debug("Changing volume state to match max_volume: {}".format(volume))
        self.fade(self.mixer.get_volume(), volume, fade_duration=400, step_duration=20)
    @music_dir.setter
    def music_dir(self, directory):
        logging.debug("Changing music directory: {}".format(directory))
        music_path = os.path.expanduser(directory)
        self.library = [filename for filename in os.listdir(music_path) if filename.endswith(".mp3") or filename.endswith(".ogg")]
        logging.debug("Created music library: {}".format(self.library))
        self.playlist = self.library[:]
        random.shuffle(self.playlist)
        logging.debug("Created randomized playlist: {}".format(self.playlist))

    def update_config(self, config={}):
        logging.debug("Updating live music player variables")
        config = {key: config[key] for key in config.keys() if key in self.config.keys()}
        logging.debug("Converting config values to correct types")
        if 'max_volume' in config: config['max_volume'] = float(config['max_volume'])
        if 'fade_duration' in config: config['fade_duration'] = int(config['fade_duration'])
        if 'step_duration' in config: config['step_duration'] = int(config['step_duration'])
        if 'reset' in config:
            if config['reset'] == 'True':
                config['reset'] = True
            elif config['reset'] == 'False':
                config['reset'] = False
        self.config.update(config)
        logging.debug("Changing player states to match updated variables")
        self.music_dir = self.config['music_dir']
        self.max_volume = self.config['max_volume']
        logging.debug("Updated live music player variables: {}".format(config))

class MusicPlayer(Player):
    def __init__(self):
        super(MusicPlayer, self).__init__()
        logging.debug("Initializing pygame mixer")
        from pygame import mixer
        mixer.init()
        self.mixer = mixer.music
        logging.debug("Creating threading lock and force flag")
        self.lock = threading.Lock()
        self.force_event = threading.Event()
        logging.debug("Completed music player initialization")
        
    def load_song(self, song_path):
        logging.debug("Loading new song")
        song_name = os.path.basename(song_path)
        if song_name == song_path:
            logging.debug("Provided song doesn't have a path, {} will be used".format(self.config['music_dir']))
            song_name = song_path
            song_path = os.path.join(self.config['music_dir'], song_name)
        self.current_song = -1
        if song_name in self.playlist:
            self.current_song = self.playlist.index(song_name)
        logging.debug("Loading {} into memory, currently playing music will end".format(song_path))
        self.mixer.load(os.path.expanduser(song_path))
        logging.debug("{} has been loaded".format(song_name))
    
    def get_random(self):
        logging.debug("Getting random song from playlist: {}".format(self.playlist))
        song_name = random.choice(self.playlist)
        if self.current_song != -1:
            if song_name == self.playlist[self.current_song] and len(self.playlist) > 1:
                logging.debug("Failed to obtain unique song")
                song_name = self.get_random()
        logging.debug("Obtained random song: {}".format(song_name))
        return song_name
        
    def get_next(self):
        logging.debug("Getting next song in playlist: {}".format(self.playlist))
        index = 0
        if self.current_song < len(self.playlist)-1:
            index = self.current_song + 1
        song_name = self.playlist[index]
        logging.debug("Obtained next song: {}".format(song_name))
        return song_name
        
    def get_prev(self):
        logging.debug("Getting previous song in playlist: {}".format(self.playlist))
        index = len(self.playlist)-1
        if self.current_song > 0:
            index = self.current_song - 1
        song_name = self.playlist[index]
        logging.debug("Obtained previous song: {}".format(song_name))
        return song_name

    def play(self, song_name=None, fade_duration=None, step_duration=None, force=False, rand=False):
        logging.debug("Play command received, creating new play_thread")
        if force: self.force_event.set()
        t = threading.Thread(target=self.play_thread, kwargs={'song_name': song_name, 'fade_duration': fade_duration, 'step_duration': step_duration, 'force': force, 'rand': rand})
        t.start()
        logging.debug("Play_thread added")
    def stop(self, fade_duration=None, step_duration=None, force=False):
        logging.debug("Stop command received, creating new stop_thread")
        if force: self.force_event.set()
        t = threading.Thread(target=self.stop_thread, kwargs={'fade_duration': fade_duration, 'step_duration': step_duration, 'force': force})
        t.start()
        logging.debug("Stop_thread added")
    
    def play_thread(self, song_name=None, fade_duration=None, step_duration=None, force=False, rand=False):
        with self.lock:
            logging.debug("Play_thread {} obtained thread lock".format(threading.current_thread()))
            if not self.force_event.is_set() or force:
                if (not song_name and not self.mixer.get_busy()) or rand: song_name = self.get_random()
                if song_name: self.load_song(song_name)
                self.mixer.set_volume(0)
                logging.debug("Play_thread {}: Set volume to 0".format(threading.current_thread()))
                if self.mixer.get_busy():
                    self.mixer.unpause()
                else:
                    self.mixer.play()
                self.status = 1
                logging.debug("Play_thread {}: Started music playback".format(threading.current_thread()))
            self.fade(0, self.config['max_volume'], fade_duration=fade_duration, step_duration=step_duration, force=force)
            logging.debug("Play_thread {}: Music player status set to playing".format(threading.current_thread()))
            logging.debug("Play_thread {}: Completed task, releasing lock".format(threading.current_thread()))

    def stop_thread(self, fade_duration=None, step_duration=None, force=False):
        with self.lock:
            logging.debug("Stop_thread {} obtained thread lock".format(threading.current_thread()))
            self.fade(self.mixer.get_volume(), 0, fade_duration=fade_duration, step_duration=step_duration, force=force)
            if not self.force_event.is_set() or force:
                if self.config['reset']:
                    self.mixer.stop()
                    self.status = 0
                    logging.debug("Stop_thread {}: Music player status set to pause".format(threading.current_thread()))
                else:
                    self.mixer.pause()
                    self.status = 2
                    logging.debug("Stop_thread {}: Music player status set to pause".format(threading.current_thread()))
            logging.debug("Stop_thread {}: Completed task, releasing lock".format(threading.current_thread()))

    def fade(self, start_volume, end_volume, fade_duration=None, step_duration=None, force=False):
        logging.debug("Parent: {} | Fade for volume: {} -> {}".format(threading.current_thread(), start_volume, end_volume))
        if not fade_duration: fade_duration = self.config['fade_duration']
        if not step_duration: step_duration = self.config['step_duration']
        fade_duration = int(fade_duration)
        step_duration = int(step_duration)
        try:
            steps = fade_duration / step_duration
        except ZeroDivisionError:
            steps = None
        vps = vdelta = end_volume - start_volume
        if steps:
            vps = vdelta / steps
        logging.debug("Parent: {} | Volume change per step = {}".format(threading.current_thread(), vps))
        if start_volume > end_volume:
            vol_g = start_volume
            vol_l = end_volume
            self.fade_status = 2
        elif start_volume < end_volume:
            vol_g = end_volume
            vol_l = start_volume
            self.fade_status = 1
        else:
            vol_g = vol_l = end_volume
        while vol_g > vol_l:
            if self.force_event.is_set() and not force: 
                logging.debug("Parent: {} | Force command found, breaking".format(threading.current_thread()))
                break
            if vps > 0:
                vol_l = volume = vol_l + vps
            elif vps < 0:
                vol_g = volume = vol_g + vps
            self.mixer.set_volume(volume)
            time.sleep(step_duration/1000)
        self.fade_status = 0
        if not self.force_event.is_set(): self.mixer.set_volume(end_volume)
        if self.force_event.is_set() and force: self.force_event.clear(); logging.debug("Parent: {} | Clearing force event".format(threading.current_thread()))
        logging.debug("Parent: {} | Fade complete, End volume: {} / Current volume: {}".format(threading.current_thread(), end_volume, self.mixer.get_volume()))

class Configurator():
    def __init__(self, config_path=None):
        logging.debug("Instantiating all configurator variables")
        self.config_path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'addons.ini')
        if config_path:
            self.config_path = os.path.realpath(os.path.expanduser(config_path))
        self.cfg_name = 'EmulationStationBGM'
        logging.debug("Configuration Path: {} | Section: {}".format(self.config_path, self.cfg_name))
        self.parser = ConfigParser.ConfigParser()
        self.defaults = {
            'enabled'         : 'True',
            'pipe_file'       : '/dev/shm/esbgm',
            'start_delay'     : '0',
            'start_song'      : '',
            'proc_delay'      : '3000',
            'proc_fade'       : '800',
            'proc_volume'     : '0.01',
            'main_loop_sleep' : '1000',
            'music_dir'       : '~/RetroArena/bgm',
            'max_volume'      : '0.20',
            'fade_duration'   : '3000',
            'step_duration'   : '20',
            'reset'           : 'False',
        }
        logging.debug("Instantiated all configurator variables")

    def read_config(self):
        logging.debug("Reading config: {}".format(self.config_path))
        if not os.path.isfile(self.config_path):
            open(self.config_path, 'a').close()
        self.parser.read(self.config_path)
        config_file = {section :dict(self.parser.items(section)) for section in self.parser.sections() if section in self.cfg_name}
        config = {}
        if self.cfg_name in config_file.keys():
            config.update(config_file[self.cfg_name])
        logging.debug("Read config values: {}".format(config))
        return config
        
    def write_config(self, valid_config):
        logging.debug("Writing to config")
        config = self.sanitize_config(valid_config)
        write_config = False
        if not self.parser.has_section(self.cfg_name):
            self.parser.add_section(self.cfg_name)
            write_config = True
        for option in self.defaults.keys():
            if not self.parser.has_option(self.cfg_name, option) or ( self.parser.has_option(self.cfg_name, option) and config[option] != self.parser.get(self.cfg_name, option) ):
                self.parser.set(self.cfg_name, option, config[option])
                logging.debug("Adding to config: {} = {}".format(option, config[option]))
                write_config = True
        if write_config:
            with open(self.config_path, 'w') as f:
                self.parser.write(f)
            logging.debug("Wrote to config")
        logging.debug("Finished writing to config")

    def verify_config(self, cfg_delta):
        logging.debug("Verifying config data: {}".format(cfg_delta))
        verified_cfg_delta = cfg_delta.copy()
        for option in cfg_delta.keys():
            logging.debug("Verifying config entry for {}".format(option))
            invalid_warning = ""
            check_pass = False
            if cfg_delta[option]:
                try:
                    if option in ['enabled', 'reset']:
                        if verified_cfg_delta[option] == 'True' or verified_cfg_delta[option] == 'False':
                            check_pass = True
                        invalid_warning = "'{}' must be True/False".format(option)
                    elif option in ['start_delay', 'proc_delay', 'proc_fade', 'main_loop_sleep', 'fade_duration', 'step_duration']:
                        if int(verified_cfg_delta[option]) >= 0:
                            check_pass = True
                        invalid_warning = "'{}' must be an interger value greater or equal to zero".format(option)
                    elif option in ['proc_volume', 'max_volume']:
                        if 0 <= float(verified_cfg_delta[option]) <= 1:
                            check_pass = True
                        invalid_warning = "'{}' must be a float value between or equal to 0-1".format(option)
                    elif option in 'start_song':
                        song_path = verified_cfg_delta[option]
                        song_name = os.path.basename(song_path)
                        if song_name.endswith('.mp3') or song_name.endswith('.ogg'):
                            if song_name == song_path:
                                song_path = os.path.join(self.parser.get(self.cfg_name, 'music_dir'), song_path)
                            song_path = os.path.expanduser(song_path)
                            if os.path.isfile(os.path.expanduser(song_path)):
                                check_pass = True
                        invalid_warning = "'{}' must be a case-sensitive filename within the music directory OR a path to a .mp3/.ogg file".format(option)
                    elif option in 'music_dir':
                        music_dir = os.path.expanduser(verified_cfg_delta[option])
                        if not os.path.isdir(music_dir):
                            invalid_warning = "'{}': {} does not exist OR is not a directory".format(option, music_dir)
                        elif not [filename for filename in os.listdir(music_dir) if filename.endswith(".mp3") or filename.endswith(".ogg")]:
                            invalid_warning = "'{}': {} does not have any .mp3/.ogg files".format(option, music_dir)
                        else:
                            check_pass = True
                    elif option in 'pipe_file':
                        pipe_dir = os.path.dirname(os.path.expanduser(verified_cfg_delta[option]))
                        if os.path.isdir(pipe_dir) and os.access(pipe_dir, os.W_OK):
                            check_pass = True
                        invalid_warning = "shits and giggles"
                except Exception as e:
                    invalid_warning = "Unexpected breaking option provided: {}".format(e)
                if not check_pass: logging.warning("{}".format(invalid_warning))
            if not check_pass:
                verified_cfg_delta.pop(option, None)
        logging.debug("Verified config data: {}".format(verified_cfg_delta))
        return verified_cfg_delta
    
    def sanitize_config(self, cfg_delta):
        logging.debug("Sanitizing configs and including defaults")
        config_file = self.verify_config(self.read_config())
        config_changes = self.verify_config(cfg_delta)
        config = self.defaults.copy()
        config.update(config_file)
        config.update(config_changes)
        logging.debug("Sanitized configs")
        return config

class Application:
    def __init__(self, config_path=None, process_names=None):
        logging.debug("Instantiating all application variables")
        self.process_names = set(['omxplayer.bin'])
        if process_names:
            self.process_names.update(process_names)
        self.config = {
            'enabled'         : None,
            'pipe_file'       : None,
            'start_delay'     : None,
            'start_song'      : None,
            'proc_delay'      : None,
            'proc_fade'       : None,
            'proc_volume'     : None,
            'max_volume'      : None,
            'main_loop_sleep' : None,
        }
        self.c = Configurator(config_path=config_path)
        self.mp = None
        self.mute = False
        self.proc_mute = False
        self.proc_countdown = 0
        logging.debug("Instantiated all application variables")
    
    def start_configurator(self):
        logging.debug("Starting configurator, updating configs")
        cfg = self.c.sanitize_config({})
        self.update_config(config=cfg)
        if self.mp:
            self.mp.update_config(config=cfg)
        self.c.write_config({})
        logging.debug("Finished updating configurations")
    
    def update_config(self, config={}):
        logging.debug("Updating live application variables")
        config = {key: config[key] for key in config.keys() if key in self.config.keys()}
        logging.debug("Converting config values to correct types")
        if 'start_delay' in config: config['start_delay'] = int(config['start_delay'])
        if 'proc_delay' in config: config['proc_delay'] = int(config['proc_delay'])
        if 'proc_fade' in config: config['proc_fade'] = int(config['proc_fade'])
        if 'proc_volume' in config: config['proc_volume'] = float(config['proc_volume'])
        if 'max_volume' in config: config['max_volume'] = float(config['max_volume'])
        if 'main_loop_sleep' in config: config['main_loop_sleep'] = int(config['main_loop_sleep'])
        if 'enabled' in config:
            if config['enabled'] == 'True':
                config['enabled'] = True
            elif config['enabled'] == 'False':
                config['enabled'] = False
        self.config.update(config)
        logging.debug("Updated live application variables: {}".format(config))
    
    def run(self):
        self.init_parent()
        self.main_loop()
    
    def init_parent(self):
        logging.debug("Instantiating new parent pseudo-daemon")
        self.mp = MusicPlayer()
        self.start_configurator()
        if not self.config['enabled']:
            logging.debug("EmulationStation BGM is currently disabled, quitting process to maximize available resources.")
            print("EmulationStation BGM must be enabled in order to run.")
            sys.exit()
        pipe_file = "{}.{}".format(os.path.expanduser(self.config['pipe_file']), os.getpid())
        logging.debug("Creating new pipe: {}".format(pipe_file))
        os.mkfifo(pipe_file)
        logging.debug("Registering clean_pipe at exit")
        atexit.register(self.clean_pipe, pipe_file)
        # Start delay and start song
        if self.config['start_delay']:
            logging.debug("Start delay: {}".format(self.config['start_delay']))
            time.sleep(self.config['start_delay']/1000)
        if self.config['start_song']:
            logging.debug("Start song: {}".format(self.config['start_song']))
            self.mp.play(song_name=self.config['start_song'], force = True)
        logging.debug("Instantiated parent pseudo-daemon")
    
    def main_loop(self):
        logging.debug("Opening pipe-in and entering main loop")
        pipein = os.open("{}.{}".format(os.path.expanduser(self.config['pipe_file']), os.getpid()), os.O_RDONLY|os.O_NONBLOCK) #Non-blocking open
        pipe_reader = readline(pipein)
        while True:
            logging.debug("Start of main loop")
            # Process looping checks
            self.read_pipe(pipe_reader)
            # If manually muted, other looping checks should not change player state
            if not self.mute:
                self.process_monitor()
                self.play_on_idle()
            logging.debug("End of main loop")
            time.sleep(self.config['main_loop_sleep']/1000)
    
    def read_pipe(self, pipe_reader):
        logging.debug("Reading in next line from pipe")
        line = next(pipe_reader)
        if line:
            logging.debug("Arguments found in pipe: {}".format(line))
            args = ast.literal_eval(line)
            args = self.parse_args(args)
            self.process_args(args)
            if not self.config['enabled']: sys.exit() ##FIXIT## Fade out before exit?
        logging.debug("Finished reading pipe")
    
    def parse_args(self, args):
        # Args should be passed in as a list and will be processed into a dictionary
        logging.debug("Parsing arguments into dictionary: {}".format(args))
        parsed_args = {'player_cmd': {}, 'values': {}, 'flags': {'force': False, 'random': False}}
        if not args[0] in ['set', 'play', 'stop', 'next', 'prev', 'quit']:
            logging.warning("Missing player command, tossing all arguments")
        else:
            player_cmd = args.pop(0)
            flags = {'force': False, 'random': False}
            values = {
                'song_name': None,
                'enabled': None,
                'pipe_file': None,
                'start_delay': None,
                'start_song': None,
                'proc_delay': None,
                'proc_fade': None,
                'proc_volume': None,
                'main_loop_sleep': None,
                'music_dir': None,
                'max_volume': None,
                'fade_duration': None,
                'step_duration': None,
                'reset': None,
            }
            while args:
                try:
                    arg = args.pop(0)
                    if arg in ['--force', '--random']: flags.update({ arg[2:]: True }); continue # Process force/random flags
                    values.update({option: args.pop(0) for option in values.keys() if arg in '--{}'.format(option)}) # Add all known options with arguments to values
                except IndexError:
                    logging.warning("Missing an argument")
            parsed_args.update({'player_cmd': player_cmd, 'values': values, 'flags': flags})
        logging.debug("Parsing complete: {}".format(parsed_args))
        return parsed_args
    
    def process_args(self, args):
        # Sanitized args should be passed as dictionary
        logging.debug("Processing arguments into actions: {}".format(args))
        values = self.c.verify_config(args['values'])
        if 'set' in args['player_cmd']:
            self.update_config(config=values)
            if self.mp:
                self.mp.update_config(config=values)
            self.c.write_config(values)
        elif self.mp:  # Pseudo-daemon specific player commands.
            # Update argument values with verified versions (argument values default to None)
            args['values'].update(values)
            if 'play' in args['player_cmd']:
                self.mute = False
                self.mp.play(song_name=args['values']['song_name'], fade_duration=args['values']['fade_duration'], step_duration=args['values']['step_duration'], force=args['flags']['force'], rand=args['flags']['random'])
            elif 'stop' in args['player_cmd']:
                self.mute = True
                self.mp.stop(fade_duration=args['values']['fade_duration'], step_duration=args['values']['step_duration'], force=args['flags']['force'])
            elif 'next' in args['player_cmd']:
                self.mute = False
                self.mp.play(song_name=self.mp.get_next(), fade_duration=args['values']['fade_duration'], step_duration=args['values']['step_duration'], force=args['flags']['force'])
            elif 'prev' in args['player_cmd']:
                self.mute = False
                self.mp.play(song_name=self.mp.get_prev(), fade_duration=args['values']['fade_duration'], step_duration=args['values']['step_duration'], force=args['flags']['force'])
            elif 'quit' in args['player_cmd']:
                sys.exit()
        logging.debug("Processing arguments complete")
    
    def process_monitor(self):
        logging.debug("Checking running processes for flagged process names: {}".format(self.process_names))
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        for pid in pids:
            try:
                procname = open(os.path.join('/proc',pid,'comm'),'rb').read()
            except IOError: 
                continue
            if procname[:-1] in self.process_names:
                #Turn down the music if actually playing (not paused)
                logging.debug("Flagged process found: {} | Process countdown: {} | Player Status: {}".format(procname[:-1], self.proc_countdown, self.mp.status))
                if self.mp.status == 1 and self.proc_countdown == 0:
                    if self.config['proc_volume']:
                        logging.debug("Proc_volume: {} | Fading volume to match proc_volume".format(self.config['proc_volume']))
                        self.mp.fade(self.mp.mixer.get_volume(), self.config['proc_volume'], fade_duration=self.config['proc_fade'], step_duration=10) #Proc_step?
                    else:
                        logging.debug("Proc_volume: {} | Proc_volume should be zero, stopping music".format(self.config['proc_volume']))
                        # Will start a new song if reset flag is True ##FIXIT## ?
                        self.mp.stop(fade_duration=self.config['proc_fade'], force=True)
                    self.proc_mute = True
                logging.debug("Refreshing process countdown timer: {}".format(self.config['proc_delay']))
                if self.proc_mute: self.proc_countdown = self.config['proc_delay']
        # Fade in after countdown
        if self.proc_countdown <= 0 and self.proc_mute:
            logging.debug("Countdown complete, resuming music")
            if self.config['proc_volume']:
                self.mp.fade(self.mp.mixer.get_volume(), self.config['max_volume'], fade_duration=self.config['proc_fade'], step_duration=10) #Proc_step?
            else:
                self.mp.play(fade_duration=self.config['proc_fade'])
            self.proc_countdown = 0
            self.proc_mute = False
        if self.proc_countdown > 0 and self.proc_mute:
            self.proc_countdown -= self.config['main_loop_sleep']
            logging.debug("Current countdown: {} | Countdown increment: {}".format(self.proc_countdown, self.config['main_loop_sleep']))
        logging.debug("Process monitor check complete")
        
    def play_on_idle(self):
        logging.debug("Checking play on idle...")
        if not self.mp.mixer.get_busy(): self.mp.status = 0
        # The next song will not play when a flagged process is active. Maybe ##FIXIT##
        if not self.mp.status == 1 and not self.mp.fade_status and not self.proc_mute:
            logging.debug("Music is not playing and fading, playing song.")
            self.mp.play()
        logging.debug("Play on idle check complete")
    
    def controller(self, parent_PID, args):
        if parent_PID:
            pipeout = os.open('{}.{}'.format(self.config['pipe_file'], parent_PID), os.O_WRONLY)
            os.write(pipeout, '%s\n' % args)
        else:
            self.start_configurator()
            args = self.parse_args(args)
            self.process_args(args)

    def clean_pipe(self, pipe_file):
        logging.debug("Cleaning pipe file: {}".format(pipe_file))
        os.remove(pipe_file)


def check_pipes(pipe_file):
    logging.debug("Checking for previous pipes: {}".format(os.path.dirname(pipe_file)))
    PID = None
    for filename in os.listdir(os.path.dirname(pipe_file)):
        if os.path.basename(pipe_file) in filename:
            logging.debug("Previous pipe found: {}".format(filename))
            check_PID = filename.split('.')[1]
            remove_pipe = True
            try:
                with open('/proc/{}/cmdline'.format(check_PID), 'r') as f:
                    cmdline = f.read()
                    remove_pipe = False
                    logging.debug("PID is a current active process")
            except IOError:
                logging.debug("No actively running PIDs")
            if not remove_pipe:
                if os.path.basename(sys.argv[0]) in cmdline:
                    logging.debug("PID cmdline matches: {}".format(os.path.basename(sys.argv[0])))
                    PID = check_PID
            if remove_pipe:
                logging.debug("Removing {}, doesn't reference any active EmulationStation BGM instance".format(filename))
                os.remove(os.path.join(os.path.dirname(pipe_file), filename))
    logging.debug("Finished pipe check, returning PID: {}".format(PID))
    return PID

if __name__ == "__main__":
    logging.debug("----------= EmulationStation BGM =----------")
    if (len(sys.argv) > 1 and sys.argv[1] == 'help') or len(sys.argv) == 1:
        print(help_message)
        sys.exit()
    app = Application(config_path=config_path, process_names=proc_names)
    logging.debug("v IGNORE vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
    logging.disable(logging.WARNING)
    app.start_configurator()
    logging.disable(log_level_disable)
    logging.debug("^ IGNORE ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    PID = check_pipes(os.path.expanduser(app.config['pipe_file']))
    if not PID and len(sys.argv) > 1 and sys.argv[1] == 'start':
            logging.debug("Running pseudo-daemon instance")
            app.run()
    elif len(sys.argv) > 1:
        logging.debug("Running controller instance")
        app.controller(PID, sys.argv[1:])
