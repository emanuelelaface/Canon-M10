# -*- coding: utf-8 -*-

from remi.gui import *
from remi import start, App
import cv2
import numpy
import chdkptp
import time
import threading
import rawpy

class OpenCVVideoWidget(Image):
    def __init__(self, **kwargs):
        super(OpenCVVideoWidget, self).__init__("/%s/get_image_data" % id(self), **kwargs)
        self.frame_index = 0
        self.frame = numpy.full((480, 720,3),155, dtype=numpy.uint8)

    def update(self, app_instance):
        self.frame_index = numpy.random.randint(1e8)
        app_instance.execute_javascript("""
            var url = '/%(id)s/get_image_data?index=%(frame_index)s';
            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.responseType = 'blob'
            xhr.onload = function(e){
                urlCreator = window.URL || window.webkitURL;
                urlCreator.revokeObjectURL(document.getElementById('%(id)s').src);
                imageUrl = urlCreator.createObjectURL(this.response);
                document.getElementById('%(id)s').src = imageUrl;
            }
            xhr.send();
            """ % {'id': id(self), 'frame_index':self.frame_index})

    def get_image_data(self, index=0):
        ret, jpeg = cv2.imencode('.jpeg', self.frame)
        if ret:
            headers = {'Content-type': 'image/jpeg'}
            return [jpeg.tostring(), headers]
        return None, None

class M10GUI(App):
    def __init__(self, *args, **kwargs):
        if not 'editing_mode' in kwargs.keys():
            super(M10GUI, self).__init__(*args, static_file_path={'my_res':'./res/'})
        self.stop_event = threading.Event()
        self.stop_event.clear()

    def log_message(self, *args, **kwargs):
        pass

    def idle(self):
        if self.live_view_check.get_value():
            vp, bm = self.get_live_view()
            self.image.frame = numpy.clip(vp.astype(numpy.uint16)+ bm.astype(numpy.uint16),0,255).astype(numpy.uint8)
            self.image.update(self)

        if time.time()-self.timer > 10:
            try:
                self.temperature_label.set_text('Temp (\xb0C): '+str(self.camera.lua_execute('get_temperature(1)')))
                self.battery_label.set_text('Batt (V): '+str(self.camera.lua_execute('get_vbatt()')/1000.))
            except:
                None
            self.timer = time.time()
        pass
    
    def main(self):
        self.timer = time.time()
        return M10GUI.construct_ui(self)

    def on_close(self):
        self.stop_event.set()
        super(M10GUI, self).on_close()
        
    @staticmethod
    def construct_ui(self):
        container = GridBox(width='100%', height='100%', style={'margin':'0px auto', "background-color":"#d5d0c7"})
        container.attributes.update({"class":"Widget","editor_constructor":"()","editor_varname":"container","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Widget"})

        container.set_from_asciiart("""
            |              |              |              | iso_label    | shutter_label | pics_label   | time_label        | live_view_label   | zoom_label     |
            | shoot_button | video_button | stop_button  | iso_menu     | shutter_value | pics_value   | time_value        | live_view_check   | zoom_menu      |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | image        | image        | image        | image        | image         | image        | image             | image             | image          |
            | lua_label    | lua_label    | lua_value    | lua_value    | lua_value     | lua_value    | lua_value         | lua_value         | lua_value      |
            | status_label | status_label | status_label | status_label | status_label  | status_label | temperature_label | battery_label     | connect_button |
            """, 1, 1)

        self.shoot_button = Button('Shoot')
        self.shoot_button.set_enabled(False)
        self.shoot_button.style.update({"width":"100%","height":"100%"})
        self.shoot_button.attributes.update({"class":"Button","editor_constructor":"('Shoot')","editor_varname":"shoot_button","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Button"})
        self.shoot_button.onclick.do(self.start_shoot)
        self.video_button = Button('Video')
        self.video_button.set_enabled(False)
        self.video_button.style.update({"width":"100%","height":"100%"})
        self.video_button.attributes.update({"class":"Button","editor_constructor":"('Video')","editor_varname":"video_button","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Button"})
        self.video_button.onclick.do(self.start_video)
        self.stop_button = Button('Stop')
        self.stop_button.set_enabled(False)
        self.stop_button.style.update({"width":"100%","height":"100%"})
        self.stop_button.attributes.update({"class":"Button","editor_constructor":"('Stop')","editor_varname":"stop_button","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Button"})
        self.stop_button.onclick.do(self.stop_action)
        self.iso_menu = DropDown.new_from_list(('Auto','100','125','160','200','250','320','400', '500','640','800','1000','1250','1600','2000','2500', '3200','4000','5000','6400','8000','10000','12800'))
        self.iso_menu.set_enabled(False)
        self.iso_menu.set_value('Auto')
        self.iso_menu.attributes.update({"class":"DropDown","editor_constructor":"()","editor_varname":"iso_menu","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"DropDown"})
        self.iso_menu.onchange.do(self.set_iso)
        self.shutter_value = TextInput(True,'')
        self.shutter_value.set_enabled(False)
        self.shutter_value.attributes.update({"class":"TextInput","autocomplete":"off","editor_constructor":"(False,'')","editor_varname":"shutter_value","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"TextInput"})
        self.shutter_value.onchange.do(self.change_shutter)
        iso_label = Label('ISO')
        iso_label.attributes.update({"class":"Label","editor_constructor":"('ISO')","editor_varname":"iso_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        shutter_label = Label('Shutter')
        shutter_label.attributes.update({"class":"Label","editor_constructor":"('Shutter')","editor_varname":"shutter_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.pics_value = TextInput(True,'')
        self.pics_value.set_enabled(False)
        self.pics_value.attributes.update({"class":"TextInput","autocomplete":"off","editor_constructor":"(False,'')","editor_varname":"pics_value","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"TextInput"})
        pics_label = Label('Pics')
        pics_label.attributes.update({"class":"Label","editor_constructor":"('Pics')","editor_varname":"pics_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.time_value = TextInput(True,'')
        self.time_value.set_enabled(False)
        self.time_value.attributes.update({"class":"TextInput","autocomplete":"off","editor_constructor":"(False,'')","editor_varname":"time_value","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"TextInput"})
        time_label = Label('Hold')
        time_label.attributes.update({"class":"Label","editor_constructor":"('Time')","editor_varname":"time_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.live_view_check = CheckBox(False,'')
        self.live_view_check.set_enabled(False)
        self.live_view_check.onchange.do(self.toggle_live)
        self.live_view_check.attributes.update({"class":"checkbox","value":"","type":"checkbox","autocomplete":"off","editor_constructor":"(False,'')","editor_varname":"live_view_check","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"CheckBox"})
        live_view_label = Label('Live')
        live_view_label.attributes.update({"class":"Label","editor_constructor":"('Live')","editor_varname":"live_view_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.zoom_menu = DropDown.new_from_list(('1', '5', '10'))
        self.zoom_menu.set_enabled(False)
        self.zoom_menu.set_value('1')
        self.zoom_menu.attributes.update({"class":"DropDown","editor_constructor":"()","editor_varname":"zoom_menu","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"DropDown"})
        self.zoom_menu.onchange.do(self.change_zoom)
        zoom_label = Label('Zoom')
        zoom_label.attributes.update({"class":"Label","editor_constructor":"('Zoom')","editor_varname":"zoom_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.image = OpenCVVideoWidget(width='100%', height='100%')
        self.image.attributes.update({"class":"Image","width":"720","height":"480","editor_constructor":"(720,480)","editor_varname":"image","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Image"})
        infos_label = Label('Infos')
        infos_label.attributes.update({"class":"Label","editor_constructor":"('Infos')","editor_varname":"infos_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.temperature_label = Label('Temp (\xb0C):')
        self.temperature_label.attributes.update({"class":"Label","editor_constructor":"('Temp (ºC):')","editor_varname":"temperature_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.battery_label = Label('Batt (V):')
        self.battery_label.attributes.update({"class":"Label","editor_constructor":"('Batt (V):')","editor_varname":"battery_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.connect_button = Button('Connect')
        self.connect_button.style.update({"width":"100%","height":"100%"})
        self.connect_button.attributes.update({"class":"Button","editor_constructor":"('Connect')","editor_varname":"connect_button","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Button"})
        self.connect_button.onclick.do(self.init_camera)
        lua_label = Label('Lua Execute:')
        lua_label.attributes.update({"class":"Label","editor_constructor":"('Lua Execute:')","editor_varname":"lua_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        self.lua_value = TextInput(True,'')
        self.lua_value.set_enabled(False)
        self.lua_value.attributes.update({"class":"TextInput","autocomplete":"off","editor_constructor":"(False,'')","editor_varname":"lua_value","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"TextInput"})
        self.lua_value.onchange.do(self.exec_lua)
        self.status_label = Label('Camera not connected')
        self.status_label.attributes.update({"class":"Label","editor_constructor":"('')","editor_varname":"status_label","editor_tag_type":"widget","editor_newclass":"False","editor_baseclass":"Label"})
        container.append({'shoot_button':self.shoot_button, 'video_button':self.video_button, 'stop_button':self.stop_button, 'iso_menu':self.iso_menu, 'shutter_value':self.shutter_value, 'iso_label':iso_label, 'shutter_label':shutter_label, 'pics_value':self.pics_value, 'pics_label':pics_label, 'time_value':self.time_value, 'time_label':time_label, 'live_view_check':self.live_view_check, 'live_view_label':live_view_label, 'zoom_menu':self.zoom_menu, 'zoom_label':zoom_label, 'image':self.image, 'temperature_label':self.temperature_label, 'battery_label':self.battery_label, 'connect_button':self.connect_button, 'lua_label':lua_label, 'lua_value':self.lua_value, 'status_label':self.status_label})

        self.container = container
        return self.container

    def set_status_label(self, text):
        with self.update_lock:
            self.status_label.set_text(text)
    
    ##### Here the GUI is over and starts the camera
    def init_camera(self, widget):
        def erase_ok(widget):
            try:
                device=chdkptp.list_devices()
                self.camera=chdkptp.ChdkDevice(device[0])
            except:
                self.status_label.set_text('Error: camera not connected')
                return

            self.camera.switch_mode('record')
            self.camera.lua_execute('set_backlight(0)')
            self.camera.lua_execute('call_event_proc("UI.CreatePublic")')

            self.purge_files()
            self.status_label.set_text('Camera connected')
        
            self.connect_button.set_enabled(False)
            self.iso_menu.set_enabled(True)
            self.shutter_value.set_enabled(True)
            self.pics_value.set_enabled(True)
            self.shoot_button.set_enabled(True)
            self.video_button.set_enabled(True)
            self.live_view_check.set_enabled(True)
            self.lua_value.set_enabled(True)

            self.iso_menu.set_value(self.get_iso())
            self.shutter_value.set_value(str(self.get_camera_shutter_time()))
            self.pics_value.set_value('1')

            if self.camera.lua_execute('get_drive_mode()') == 1:
                if float(self.shutter_value.get_value()) < 1:
                    self.time_value.set_enabled(True)
                    self.time_value.set_value('0')
            else:
                self.time_value.set_value('0')
            self.temperature_label.set_text('Temp (\xb0C): '+str(self.camera.lua_execute('get_temperature(1)')))
            self.battery_label.set_text('Batt (V): '+str(self.camera.lua_execute('get_vbatt()')/1000.))

        erase_dialog=GenericDialog(title='WARNING',message='All your data on the camera will be erased!')
        erase_dialog.style.update({"margin":"0px","width":"500px","height":"100px","top":"10px","left":"10px","position":"absolute","overflow":"auto"})
        erase_dialog.show(self)
        erase_dialog.confirm_dialog.do(erase_ok)

    def toggle_live(self, widget, value):
        if self.live_view_check.get_value():
            self.zoom_menu.set_enabled(True)
        else:
            self.zoom_menu.set_enabled(False)

    def get_iso(self):
        return self.camera.lua_execute('get_iso_mode()')

    def set_iso(self, widget, iso):
        iso = self.iso_menu.get_value()
        if iso == 'Auto':
            iso='0'
        self.camera.lua_execute('set_iso_mode('+iso+')')
        self.camera.lua_execute('press("shoot_half")')

    def get_camera_shutter_time(self):
        time = self.camera.lua_execute('tv96_to_usec(get_user_tv96())')
        if time < 1000000:
            return time/1000000.
        else:
            return time/1000000

    def change_shutter(self, widget, value):
        try:
            time=int(float(self.shutter_value.get_text())*1000000)
        except:
            self.status_label.set_text('Error: shutter time must be a number')
            return

        if time > 32000000:
            time=32000000
        if time < 250:
            time=250
        self.camera.lua_execute('set_user_tv96(usec_to_tv96('+str(time)+'))\n' \
                                'press("shoot_half")\n' \
                                'repeat\n' \
                                '   sleep(10)\n' \
                                'until get_shooting()\n' \
                                'return')
        self.text_line_message='Done'

    def purge_files(self):
        for i in self.list_files():
            self.camera.delete_files(i)

    def list_files(self):
        file_list=[]
        for i in self.camera.list_files():
            if 'CANONMSC' not in i:
                file_list+=self.camera.list_files(i[:-1])
        return file_list

    def change_zoom(self, widget, zoom):
        zoom = int(self.zoom_menu.get_value())
        if zoom==1:
            self.camera.lua_execute('post_levent_to_ui(0x11ea,0)\n' \
                                    'press("shoot_half")\n' \
                                    'repeat\n' \
                                    '   sleep(10)\n' \
                                    'until get_shooting()\n' \
                                    'return')
            self.iso_menu.set_enabled(True)
            self.shutter_value.set_enabled(True)
        if zoom==5:
            self.camera.lua_execute('post_levent_to_ui(0x11ea,0)\n' \
                                    'press("shoot_half")\n' \
                                    'repeat\n' \
                                    '   sleep(10)\n' \
                                    'until get_shooting()\n' \
                                    'return')
            self.camera.lua_execute('post_levent_to_ui(0x11ea,1)\n' \
                                    'press("shoot_half")\n' \
                                    'repeat\n' \
                                    '   sleep(10)\n' \
                                    'until get_shooting()\n' \
                                    'return')
            self.iso_menu.set_enabled(False)
            self.shutter_value.set_enabled(False)
        if zoom==10:
            self.camera.lua_execute('post_levent_to_ui(0x11ea,1)\n' \
                                    'press("shoot_half")\n' \
                                    'repeat\n' \
                                    '   sleep(10)\n' \
                                    'until get_shooting()\n' \
                                    'call_event_proc("PTM_SetCurrentItem",0x80b8,2)\n'
                                    'press("shoot_half")\n' \
                                    'repeat\n' \
                                    '   sleep(10)\n' \
                                    'until get_shooting()\n' \
                                    'return')
            self.iso_menu.set_enabled(False)
            self.shutter_value.set_enabled(False)


    def start_shoot(self, widget):
        try:
            float(self.shutter_value.get_value())
            float(self.time_value.get_value())
            int(self.pics_value.get_value())
        except:
            return
        self.shoot_button.set_enabled(False)
        self.video_button.set_enabled(False)
        self.stop_button.set_enabled(True)
        self.live_view_check.set_value(False)
        self.live_view_check.set_enabled(False)
        tr = threading.Thread(target=self.shoot_pic, args=(self.stop_event,))
        tr.start()

    def start_video(self, widget):
        try:
            float(self.shutter_value.get_value())
            float(self.time_value.get_value())
            int(self.pics_value.get_value())
        except:
            return
        if float(self.shutter_value.get_value()) < 1:
            self.status_label.set_text('Video length must be at least 1 second')
            return
        self.shoot_button.set_enabled(False)
        self.video_button.set_enabled(False)
        self.stop_button.set_enabled(True)
        self.live_view_check.set_value(False)
        self.live_view_check.set_enabled(False)
        tr = threading.Thread(target=self.shoot_video, args=(self.stop_event,))
        tr.start()

    def shoot_pic(self, stop_event):
        record_counter = 0
        timer=int(time.time())
        shutter_time=str(int(numpy.rint(float(self.shutter_value.get_value())*1000000)))
        while record_counter < int(self.pics_value.get_value()) and not stop_event.isSet():
            if float(self.shutter_value.get_value()) >= 1 or float(self.time_value.get_value()) == 0:
                self.camera.lua_execute('set_tv96_direct(usec_to_tv96('+shutter_time+'))\n' \
                                         'press("shoot_half")\n' \
                                         'repeat\n' \
                                         '   sleep(10)\n' \
                                         'until get_shooting()\n' \
                                         'press("shoot_full")\n' \
                                         'return')
            else:
                self.camera.lua_execute('set_tv96_direct(usec_to_tv96('+shutter_time+'))\n' \
                                         'press("shoot_half")\n' \
                                         'repeat\n' \
                                         '   sleep(10)\n' \
                                         'until get_shooting()\n' \
                                         'press("shoot_full")\n' \
                                         'sleep('+str(int(numpy.rint(float(self.time_value.get_value())*1000)))+')\n' \
                                         'release("shoot_full")\n' \
                                         'return')

            if float(self.shutter_value.get_value()) <= 1:
                self.status_label.set_text('Photo '+str(record_counter+1)+' of '+str(self.pics_value.get_value()))
                time.sleep(float(self.shutter_value.get_value()))
            else:
                seconds=0
                while seconds<float(self.shutter_value.get_value()):
                    if stop_event.isSet():
                        self.set_status_label('Aborting, waiting '+str(int(float(self.shutter_value.get_value())-seconds))+' seconds for the last photo')
                    else:
                        self.set_status_label('Photo '+str(record_counter+1)+' of '+str(self.pics_value.get_value())+' due in '+str(int(float(self.shutter_value.get_value())-seconds))+' seconds')
                    time.sleep(1)
                    seconds+=1

            self.set_status_label('Downloading photos from the camera')
            while len(self.list_files()) == 0:
                time.sleep(1)
            for i in self.list_files():
                localfile=i.split('/')[3]
                self.camera.download_file(i,localfile)
            if 'JPG' in localfile:
                self.image.frame=cv2.resize(cv2.imread(localfile.split('.')[0]+'.JPG'), (720, 480))
            else:
                raw=rawpy.imread(localfile.split('.')[0]+'.CR2')
                self.image.frame=cv2.resize(raw.postprocess(half_size=True, user_flip=False)[...,::-1], (720, 480))
                raw.close()

            with self.update_lock:
                self.image.update(self)
            self.purge_files()
            record_counter += 1

        stop_event.clear()
        self.set_status_label('Done')
        with self.update_lock:
            self.shoot_button.set_enabled(True)
            self.video_button.set_enabled(True)
            self.stop_button.set_enabled(False)
            self.live_view_check.set_enabled(True)

    def shoot_video(self, stop_event):
        record_counter = 0
        while record_counter < int(self.pics_value.get_value()) and not stop_event.isSet():
            seconds=0
            self.camera.lua_execute('press("video")')
            while seconds<float(self.shutter_value.get_value()) and not stop_event.isSet():
                self.set_status_label('Video '+str(record_counter+1)+' of '+str(self.pics_value.get_value())+' due in '+str(int(float(self.shutter_value.get_value())-seconds))+' seconds')
                time.sleep(1)
                seconds+=1
            self.camera.lua_execute('press("video")')
            self.set_status_label('Downloading video from the camera')
            while self.camera.lua_execute('get_movie_status()') != 1:
                time.sleep(1)
            for i in self.list_files():
                localfile=i.split('/')[3]
                self.camera.download_file(i,localfile)
            self.purge_files()
            record_counter += 1

        stop_event.clear()
        self.set_status_label('Done')
        with self.update_lock:
            self.shoot_button.set_enabled(True)
            self.video_button.set_enabled(True)
            self.stop_button.set_enabled(False)
            self.live_view_check.set_enabled(True)

    def stop_action(self, widget):
        self.status_label.set_text('Abotring...')
        self.stop_event.set()

    def get_live_view(self):
        self.camera._lua.eval("""
            function()
                status, err = con:live_dump_start('/tmp/live_view_frame')
                for i=1,1 do
                    status, err = con:live_get_frame(29)
                    status, err = con:live_dump_frame()
                end
                status, err = con:live_dump_end()
                return err
            end
        """)()
        lv_aspect_ratio = {0:'LV_ASPECT_4_3', 1:'LV_ASPECT_16_9', 2:'LV_ASPECT_3_2'}
        fb_type = {0:12, 1:8, 2:16, 3:16, 4:8 }
        file_header_dtype = numpy.dtype([('magic','int32'),('header_size', 'int32'),('version_major', 'int32'),('version_minor','int32')])
        frame_length_dtype = numpy.dtype([('length','int32')])
        frame_header_dtype = numpy.dtype([('version_major','int32'),('version_minor', 'int32'),('lv_aspect_ratio', 'int32'),
            ('palette_type','int32'), ('palette_data_start','int32'), ('vp_desc_start','int32'), ('bm_desc_start','int32'),
            ('bmo_desc_start','int32')])
        block_description_dtype = numpy.dtype([('fb_type','int32'),('data_start','int32'),('buffer_width','int32'),
            ('visible_width','int32'),('visible_height','int32'),('margin_left','int32'), ('margin_top','int32'),
            ('margin_right','int32'),('margin_bottom','int32')])

        myFile = open('/tmp/live_view_frame','r')

        file_header=numpy.fromfile(myFile, dtype=file_header_dtype, count=1)
        frame_length=numpy.fromfile(myFile, dtype=frame_length_dtype, count=1)
        frame_header=numpy.fromfile(myFile, dtype=frame_header_dtype, count=1)
        vp_description=numpy.fromfile(myFile, dtype=block_description_dtype, count=1)
        vp_bpp = fb_type[int(vp_description['fb_type'])]
        vp_frame_size=vp_description['buffer_width']*vp_description['visible_height']*vp_bpp/8 # in byte !
        vp_frame_size = int(vp_frame_size[0])

        bm_description=numpy.fromfile(myFile, dtype=block_description_dtype, count=1)
        bm_bpp = fb_type[int(bm_description['fb_type'])]
        bm_frame_size=bm_description['buffer_width']*bm_description['visible_height']*bm_bpp/8
        bm_frame_size = int(bm_frame_size[0])

        bmo_description=numpy.fromfile(myFile, dtype=block_description_dtype, count=1)
        bmo_bpp = fb_type[int(bmo_description['fb_type'])]
        bmo_frame_size=bmo_description['buffer_width']*bmo_description['visible_height']*bmo_bpp/8
        bmo_frame_size = int(bmo_frame_size[0])

        if vp_description['data_start'] > 0:
            vp_raw_img=numpy.fromfile(myFile, dtype=numpy.uint8, count=vp_frame_size)
            y=vp_raw_img[1::2].reshape(int(vp_description['visible_height']),int(vp_description['buffer_width']))
            u=numpy.empty(vp_frame_size//2, dtype=numpy.uint8)
            u[0::2]=vp_raw_img[0::4]
            u[1::2]=vp_raw_img[0::4]
            u=u.reshape(int(vp_description['visible_height']),int(vp_description['buffer_width']))
            v=numpy.empty(vp_frame_size//2, dtype=numpy.uint8)
            v[0::2]=vp_raw_img[2::4]
            v[1::2]=vp_raw_img[2::4]
            v=v.reshape(int(vp_description['visible_height']),int(vp_description['buffer_width']))
            raw_yuv=numpy.dstack((y,u,v))[:,0:int(vp_description['visible_width']),:]
            vp_rgb=cv2.cvtColor(raw_yuv, cv2.COLOR_YUV2BGR)
        if bm_description['data_start'] > 0:
            bm_raw_img=numpy.fromfile(myFile, dtype=numpy.uint8, count=bm_frame_size)
            y=bm_raw_img[1::2].reshape(int(bm_description['visible_height']),int(bm_description['buffer_width']))
            u=numpy.empty(bm_frame_size//2, dtype=numpy.uint8)
            u[0::2]=bm_raw_img[0::4]
            u[1::2]=bm_raw_img[0::4]
            u=u.reshape(int(bm_description['visible_height']),int(bm_description['buffer_width']))
            v=numpy.empty(bm_frame_size//2, dtype=numpy.uint8)
            v[0::2]=bm_raw_img[2::4]
            v[1::2]=bm_raw_img[2::4]
            v=v.reshape(int(bm_description['visible_height']),int(bm_description['buffer_width']))
            raw_yuv=numpy.dstack((y,u,v))[:,0:int(bm_description['visible_width']),:]
            bm_rgb=cv2.cvtColor(raw_yuv, cv2.COLOR_YUV2BGR)
        if bmo_description['data_start'] >0:
            bmo_raw_img=numpy.fromfile(myFile, dtype=numpy.int32, count=bmo_frame_size)
        myFile.close()
        if vp_rgb.shape[0]==408: # Workaround for video mode
            extension=numpy.zeros((480,720,3))
            extension[36:444, :, :]=vp_rgb # (480-408)/2:480-(480-408)/2, :, :
            vp_rgb=extension
        return vp_rgb, bm_rgb

    def exec_lua(self, widget, value):
        try:
            self.camera.lua_execute(str(self.lua_value.get_value())+'\n' \
                                        'press("shoot_half")\n' \
                                        'repeat\n' \
                                        '   sleep(10)\n' \
                                        'until get_shooting()\n' \
                                        'return')
            self.status_label.set_text('Done')
        except:
            self.status_label.set_text('Error executing LUA')

if __name__ == "__main__":
    start(M10GUI, address='0.0.0.0', port=8081, multiple_instance=False, enable_file_cache=True, start_browser=False, debug=False, update_interval = 0.01)
