#!/usr/bin/python

import kivy, plyer
import datetime, time
import os

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from kivy.uix.stencilview import StencilView
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeViewNode, TreeView, TreeViewLabel
from kivy.uix.widget import Widget

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.effects.scroll import ScrollEffect

from plyer import notification
from plyer import vibrator

from kivy.properties import StringProperty, BooleanProperty

import requests


######## KLASA JAKOBA
class KNAPIclient():
    def __init__(self, server='blackyk.ddns.net:52352'):
        self.server = server

    def retrieveAll(self):
        response = requests.get('http://' + str(self.server) + '/api1/?format=json')
        return response.json()

    def retrieveByID(self, id):
        response = requests.get('http://' + str(self.server) + '/api1/' + str(id) + '/?format=json')
        return response.json()

    def availableKeys(self):
        return ["id", "title", "startDate", "startTime", "length", "authors"]

    def getServer(self):
        return str(self.server)

    def returnFiles(self, id):
        response = requests.get('http://' + str(self.server) + '/api1/files/' + str(id) + '/?format=json')
        return response.json()


#=====================SCREENS=========================

class SM(ScreenManager):
    def __init__(self, **kwargs):
        super(SM, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.onBackBtn)
        
    def onBackBtn(self, window, key, *args):
        if key == 27:
            self.transition.direction = 'right'
            self.current = 'start'
            return True
        return False

class StartScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class LecturesScreen(Screen):
    pass

class MapScreen(Screen):
    pass

class MyLayout(Screen):
    def send_notification(self, text):
        
        for i in range(5):
            title = "Lecture "+str(i)+" is starting soon!"
            notification.notify(title=title, message=text, app_name='ConferencePi', timeout=1)
            time.sleep(2)
            vibrator.vibrate(time=2)

#====================WIDGETS==========================

class CustomTV(TreeView):

######### KLASA DRZEWA, ORYGINALNIE MIALA USTAWIONE, ZE TYLKO PO KLIKNIECIU W STRZALECZKE ROZWIJALY SIE LISCIE, TERAZ JEST SPOKO B)

    def on_touch_down(self, touch):
        node = self.get_node_at_pos(touch.pos)
        if not node:
            return
        if node.disabled:
            return
        self.toggle_node(node)
        node.dispatch('on_touch_down', touch)
        return True

class LectureTree(BoxLayout):

    def __init__(self, **kwargs):
        super(LectureTree, self).__init__(**kwargs)

        ########## AKTUALIZUJE DRZEWO CO 45 SEKUND
        Clock.schedule_interval(self.scheduled_update, 45)

        self.sv = ScrollView(do_scroll_x=False, pos = (0, 0))
        self.tv = self.populate()
        self.sv.add_widget(self.tv)
        self.add_widget(self.sv)

    def scheduled_update(self, dt):
        self.update()

    def populate(self):

        self.cli = KNAPIclient()
        self.server = self.cli.getServer()
        global gserver
        gserver = self.cli.getServer()

        tv = CustomTV(root_options=dict(text='Tree One'),
                      hide_root=True,
                      indent_level=10,
                      size_hint_y=None)
        
        tv.bind(minimum_height=tv.setter('height'))

################## TUTAJ DODAWANE SA LISCIE DO DRZEWA Z WYKLADAMI, MOZNA ZWIEKSZYC ICH ROZMIARY, OGARNALEM SCROLLOWANIE TEJ LISTY WIEC POWINNO BYC SPOKO

        for each in self.cli.retrieveAll():
            lecture = tv.add_node(TreeViewLabel(text=each["title"], font_size=Window.size[1]/25, is_open = False))
            
            info_node = tv.add_node(TreeViewLabel(text="Info", is_open = False, font_size=Window.size[1]/30, no_selection = True), lecture)
            description_node = tv.add_node(TreeViewLabel(text="Description", is_open = False, font_size=Window.size[1]/30, no_selection = True), lecture)
            resources_node = tv.add_node(TreeViewLabel(text="Resources", is_open = False, font_size=Window.size[1]/30, no_selection = True), lecture)
            moje_id = each['id']
            for key in each:
                if key == "id" or key == "title":
                    pass
                elif key == "description":
                    key_node = tv.add_node(TreeViewLabel(text=str(each[key]), is_open = False, font_size=Window.size[1]/35, no_selection = True), description_node)
                elif key == "resources":
                    for file in self.cli.returnFiles(moje_id):
                        key_node = tv.add_node(TreeViewResource(resource_name=file["name"], filename=file["filename"], server=self.server, no_selection=True), resources_node)
                else:    
                    key_node = tv.add_node(TreeViewLabel(text=str(key)+": "+str(each[key]), is_open = False, font_size=Window.size[1]/35, no_selection = True), info_node)
        
        return tv

    def update(self):
        self.sv.remove_widget(self.tv)
        self.tv = self.populate()
        self.sv.add_widget(self.tv)

########### PONIZSZE DWIE METODY CHYBA DO WYWALENIA, TO JEST SPRAWDZANE W USLUDZE W TLE

    def check_if_starting_soon(self, dt):
        for lecture in self.cli.retrieveAll(): 
            self.notify_starting_soon(lecture["startDate"], lecture["startTime"], lecture["title"], 5)

    def notify_starting_soon(self, date, time, title, timeout):
        datetime_object = datetime.datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M:%S")
        if datetime.timedelta(minutes = int(timeout)) - datetime.timedelta(seconds = 15) < datetime_object - datetime.datetime.now() <= datetime.timedelta(minutes = int(timeout)):
            notification.notify(title="Oooo, startin soon", message="Lecture "+title+" is starting soon", app_name='ConferencePi', timeout=1)
            return True
        else:
            return False


class TreeViewResource(BoxLayout, TreeViewNode):
    ######### LISC RESOURCE - MA LABEL I PRZYCISK KTORY POBIERA PLIKI
    resource_name = StringProperty()
    filename = StringProperty()
    server = StringProperty()

    def download_file(self):
        try:
            ######### POKI CO POBIERAMY DO FOLDERU /sdcard - MOZNA ZMIENIC NA INNY
            local_file = os.path.join( "/sdcard/", str(self.resource_name))

            ######### TRZEBA UZGODNIC JAKI BEDZIE LINK DO SCIAGANIA, POKI CO JEST http://server/plik
            response = requests.get( "http://" + str(self.server)+"/"+str(self.resource_name) , stream=True)
            with open(local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            ######### POWIADOMIENIE O POPRAWNYM SCIAGNIECIU PLIKU - ZAKOMENTOWANE WIBRACJE, DZIALAJA, MOZNA WLACZYC
            notification.notify(title="File downloaded :)", message="File "+str(self.resource_name)+" has been succesfully downloaded!", app_name='ConferencePi', timeout=1)
            """vibrator.vibrate(0.1)
            time.sleep(0.25)
            vibrator.vibrate(0.1)"""
        except Exception, e:
            print repr(e)
            notification.notify(title="Something went wrong :(", message="File "+str(self.resource_name)+" couldn't be downloaded...", app_name='ConferencePi', timeout=1)
            """vibrator.vibrate(0.1)
            time.sleep(0.25)
            vibrator.vibrate(0.1)"""

class StencilBox(BoxLayout, StencilView):
    pass

class MyApp(App):
    def build(self):
        ###########JEZELI ODPALAMY APKE NA ANDROIDZIE TO URUCHAMIAMY USLUGE
        if platform == 'android':
            try:
                from jnius import autoclass
                self.service = autoclass('lab.agh.confpi.ServiceMyservice')
                mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                argument = ''
                self.service.start(mActivity, argument)
            except Exception, e:
                pass

if __name__ == "__main__":
    MyApp().run()
