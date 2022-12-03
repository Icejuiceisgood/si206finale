import sqlite3
import requests
import json
import random
from bs4 import BeautifulSoup
import requests
import unicodedata

class FirstClass:

    pokemonLimit=25

    # initializes database and tables
    def createStructure(self,cur,conn):
        cur.execute("CREATE TABLE IF NOT EXISTS Pokemon (PokemonID INTEGER PRIMARY KEY, TypeID INTEGER, PokemonName STRING UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS PokemonToMoves (PokemonID INTEGER, MoveID INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS Moves (MoveID INTEGER PRIMARY KEY, TypeID INTEGER, MoveName STRING UNIQUE, Accuracy FLOAT, Power INTEGER, Strength FLOAT)")
        cur.execute("CREATE TABLE IF NOT EXISTS Type (TypeID INTEGER PRIMARY KEY, TypeName STRING UNIQUE)")
        conn.commit()

    # chooses the pokemon being focused on, returns a dictionary where the key is pokemon and value are their types
    def getPokemonNameTypes(self):
        limit= FirstClass.pokemonLimit
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

    # returns a dictionary where the key is pokemon and value are their list of moves
    def getPokemonMoves(self,pokemonDiction):
        pokemonNames= list(pokemonDiction.keys())
        returnedPokemonMoveDiction={}
        limit=0
        for pokemon in pokemonNames:
            url= "https://pokeapi.co/api/v2/pokemon/" + pokemon.lower() + "/"
            r=requests.get(url)
            if r.ok:
                diction=json.loads(r.text)
                movelist=[]
                for move in diction['moves']:
                    movelist.append(move['move']['name'])
                random.shuffle(movelist)
                returnedPokemonMoveDiction[pokemon]=movelist[0:15]
                
        return returnedPokemonMoveDiction
    

    #returns a dictionary where the key is a pokemon move and value is a dictionary where power and accuracy are keys, and values are their actual values
    def getMoveInfo(self,pokemonMoveDiction):
        pokemonMoves=list(pokemonMoveDiction.values())
        returnedMNAPDiction={}
        for moveList in pokemonMoves:
            for move in moveList:
                if move not in returnedMNAPDiction:
                    r= requests.get('https://bulbapedia.bulbagarden.net/wiki/' + move + "_(move)")
                    if r.ok:
                        soup= BeautifulSoup(r.content, 'html.parser')
                        tags= soup.find_all('td')
                        typer= soup.find_all('b')
                        power= tags[7].text
                        accuracy= tags[8].text
                        power = unicodedata.normalize('NFKD',power).strip()
                        accuracy = unicodedata.normalize('NFKD',accuracy).strip()
                        type= typer[3].text
                        diction={}
                        diction["power"]= power
                        diction["accuracy"]= accuracy[:-1]
                        try:
                            pow =int(power)
                            acc=int(accuracy[:-1])
                        except:
                            continue
                        diction["type"]= type
                        returnedMNAPDiction[move]= diction
        return returnedMNAPDiction


    #inserts data into type table
    def insertTypeData(self,cur,conn, pokemonDiction, pokemonMNAPDiction):
        listing=[]
        for pokemon in pokemonDiction:
            if pokemonDiction[pokemon] not in listing:
                listing.append(pokemonDiction[pokemon])
        for move in pokemonMNAPDiction:
            if pokemonMNAPDiction[move]["type"] not in listing:
                listing.append(pokemonMNAPDiction[move]["type"])
        for type in listing:
            cur.execute("INSERT OR IGNORE INTO Type (TypeName) VALUES (?)",(type,))
        conn.commit()


    #inserts data into moves table
    def insertMoveData(self,cur,conn,pokemonMNAPDiction):
        for moveName, moveVals in pokemonMNAPDiction.items():
            name=moveName
            power=int(pokemonMNAPDiction[moveName]["power"])
            type= pokemonMNAPDiction[moveName]["type"]
            accuracy=(float(pokemonMNAPDiction[moveName]["accuracy"]))/100
            strength= float(power * accuracy)
            cur.execute("Select * from Type")
            for row in cur:
                if row[1]==type:
                    cur.execute("INSERT OR IGNORE INTO Moves (TypeID,MoveName,Accuracy,Power,Strength) VALUES (?,?,?,?,?)",(int(row[0]),name,accuracy,power,strength))
                    break
        conn.commit()
    

    # inserts data into Pokemon table
    def insertPokemonData(self,cur,conn,pokemonDiction):
        for pokemonName,pokemonVals in pokemonDiction.items():
            name=pokemonName
            type=pokemonVals
            cur.execute("Select * from Type")
            for row in cur:
                if row[1]==type:
                    cur.execute("INSERT OR IGNORE INTO Pokemon (TypeID,PokemonName) VALUES (?,?)",(int(row[0]),name))
                    break
        conn.commit()

    
    # inserts data in PokemonToMoves Table
    def insertPokemonToMovesData(self,cur, conn, pokemonMoveDiction):
        for pokemonName,pokemonMoveList in pokemonMoveDiction.items():
            pokemonID=0
            cur.execute("Select * from Pokemon")
            for row in cur:
                if row[2]==pokemonName:
                    pokemonID= int(row[0])
                    break
            for move in pokemonMoveList:
                cur.execute("Select * from Moves")
                moveID=0
                for row in cur:
                    if row[2]==move:
                        moveID=int(row[0])
                        cur.execute("INSERT OR IGNORE INTO PokemonToMoves (PokemonID,MoveID) VALUES (?,?)",(pokemonID,moveID))
                        break
        conn.commit()

def main():
    conn = sqlite3.connect('PokeDatabase')
    cur=conn.cursor()
    server = FirstClass()
    server.createStructure(cur,conn)
    pokemonDiction= server.getPokemonNameTypes()
    pokemonMoveDiction=server.getPokemonMoves(pokemonDiction)
    mnapDiction=server.getMoveInfo(pokemonMoveDiction)
    server.insertTypeData(cur,conn,pokemonDiction,mnapDiction)
    server.insertMoveData(cur,conn,mnapDiction)
    server.insertPokemonData(cur,conn,pokemonDiction)
    server.insertPokemonToMovesData(cur,conn,pokemonMoveDiction)


main()
