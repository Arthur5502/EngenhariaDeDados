import requests

class extract():
    
    def __init__(self):
        pass
    
    def teste(self):
        print("Teste")
        
    def extract_uni(self, country):
        url = f'http://universities.hipolabs.com/search?country={country}'
        response = requests.get(url)
        uni_dict = response.json()
        return uni_dict