import datetime, time
import requests
from plyer import notification

########## TO JEST KOD USLUGI DZIALAJACEJ W TLE


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

class BackgroundService():
    def __init__(self):
        self.cli = KNAPIclient()

    def check_if_starting_soon(self):
        for lecture in self.cli.retrieveAll(): 
            self.notify_starting_soon(lecture["startDate"], lecture["startTime"], lecture["title"], 5)

###########SPRAWDZA CZY KTORYS WYKLAD ZACZYNA SIE NIEDLUGO
    def notify_starting_soon(self, date, time, title, timeout):
        datetime_object = datetime.datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M:%S")
        if datetime.timedelta(minutes = int(timeout)) - datetime.timedelta(seconds = 15) < datetime_object - datetime.datetime.now() <= datetime.timedelta(minutes = int(timeout)):
            notification.notify(title="Oooo, startin soon", message="Lecture "+title+" is starting soon", app_name='ConferencePi', timeout=1)
            return True
        else:
            return False

def main():
	bg = BackgroundService()
	while True:
		bg.check_if_starting_soon()
		time.sleep(15)

if __name__ == "__main__":
	main()