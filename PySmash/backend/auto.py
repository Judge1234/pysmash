class Smasher:
    def __init__(self, driver, url):
        self.driver = driver
        self.url = url
        self.fields = {}

    def start(self):
        self.driver.get(self.url)

    def quit(self):
        self.driver.close()
 
    def __repr__(self):
        return f'Smasher: {self.url}'
