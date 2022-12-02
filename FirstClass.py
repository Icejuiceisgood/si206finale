import sqlite3
import requests
import json
import random
from bs4 import BeautifulSoup
import requests

class FirstClass:


    # initializes database and tables
    def createStructure(cur,conn):
        conn = sqlite3.connect('PokeDatabase')
        cur=conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, PokemonName STRING)")
        cur.execute("CREATE TABLE IF NOT EXISTS PokemonToMoves (PokemonID INTEGER, MoveID INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS Moves (MoveID INTEGER PRIMARY KEY, TypeID INTEGER, MoveName STRING, Accuracy STRING, Power INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS Type (TypeID INTEGER PRIMARY KEY, TypeName STRING)")
        conn.commit()

    # chooses the pokemon being focused on, returns a dictionary where the key is pokemon and value are their types
    def getPokemonNameTypes(limit):
            url="https://pogoapi.net/api/v1/pokemon_types.json"
            r=requests.get(url)
            listing= json.loads(r.text)
            random.shuffle(listing)
            returnedPokemonDiction={}
            val=0
            for num in listing:
                if val >= limit:
                    break
                elif val < limit and num["form"]=="Normal":
                    val+=1
                    returnedPokemonDiction[num["pokemon_name"]]=num["type"][0]
                else:
                    continue
            return returnedPokemonDiction

    # returns a dictionary where the key is pokemon and value are their moves
    def getPokemonMoves(pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonMoveDiction={}
        for pokemon in pokemonNames:
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon +"/"
            r=requests.get(url)
            diction=json.loads(r.text)
            returnedPokemonMoveDiction[pokemon]=diction["moves"]
        return returnedPokemonMoveDiction
    

    #returns a dictionary where the key is a pokemon move and value is a dictionary where power and accuracy are keys, and values are their actual values
    def getMoveInfo(pokemonMoveDiction):
        pokemonMoves=list(pokemonMoveDiction.values())
        returnedMNAPDiction={}
        for moveList in pokemonMoves:
            for move in moveList:
                if move not in returnedMNAPDiction:
                    r= requests.get('https://bulbapedia.bulbagarden.net/wiki/' + move + "_(move)")
                    soup= BeautifulSoup(r.content, 'html.parser')
                    tags= soup.find_all(class_='explain')
                    # typer= soup.find_all(class_='movetypeentry')
                    power= tags[1].text
                    accuracy= tags[2].text
                    diction={}
                    diction["power"]=power
                    diction["accuracy"]= accuracy
                    # diction["type"]=
                    returnedMNAPDiction[move]= diction
        return returnedMNAPDiction


    def insertDataTypes(cur,conn, pokemonTypeDiction, pokemonMoveDiction):
        conn = sqlite3.connect('PokeDatabase')
        cur=conn.cursor()
        typeIter=0
        listing=[]
        for pokemon in pokemonTypeDiction:
            if pokemonTypeDiction[pokemon] not in listing:
                listing.append(pokemonTypeDiction[pokemon])
        for move in pokemonMoveDiction:
            if pokemonMoveDiction[move]["type"] not in listing:
                listing.append(pokemonMoveDiction[move]["type"])
        for type in listing:
            cur.execute("INSERT OR IGNORE INTO Type (TypeID, TypeName) VALUES (?,?)",(typeIter,type))
            typeIter+=1
        conn.commit()



r= requests.get('https://bulbapedia.bulbagarden.net/wiki/Scratch_(move)')
soup= BeautifulSoup(r.content, 'html.parser')
tags= soup.find('b')
print(tags.text)
